# encoding: utf-8

import thread, threading, time
import shutil, os, re
import signal, sys
import socket
import subprocess
import json

LOGS_PATH = 'logs'

class Client():
    output_lock = threading.Lock()

    def __init__(self, idx, vars):
        self.idx = idx
        self.vars = vars
        self.log_path = os.path.join(LOGS_PATH, socket.gethostname(), str(os.getpid()), str(idx))
        self.cookie_path = os.path.join(self.log_path, 'cookie')
        self.log_fd = None
    
    def log(self, msg):
        self.output_lock.acquire()
        try:
            print msg
        finally:
            self.output_lock.release()

    def run(self):
        # self.log('in run ' + str(self.idx))

        if os.path.exists(self.log_path):
            shutil.rmtree(self.log_path)
        os.makedirs(self.log_path)

        self.run_startup()
        self.run_loop()
    
    def read_cmds(self, filename):
        cmds = []
        for x in open(filename).readlines():
            if '#' in x:
                cmds.append(x[:x.index('#')])
            else:
                cmds.append(x)
        cmds = [x.strip() for x in cmds if len(x.strip()) > 0]
        return cmds
    
    def run_startup(self):
        # self.log('begin run_startup')
        self.log_fd = open(os.path.join(self.log_path, 'startup.log'), 'w')

        cmds = self.read_cmds('startup.cmds')
        for i in range(len(cmds)):
            self.run_cmd(i+1, cmds[i])
        
        self.log_fd.close()
        # self.log('end run_startup')
    
    def run_loop(self):
        # self.log('begin run_loop')
        self.log_fd = open(os.path.join(self.log_path, 'loop.log'), 'w')

        cmds = self.read_cmds('loop.cmds')
        while True:
            for i in range(len(cmds)):
                self.run_cmd(i+1, cmds[i])
        
        # self.log('end run_loop')
    
    def run_cmd(self, line_no, cmd):
        for (k,v) in self.vars.items():
            cmd = cmd.replace('${%s}' % k, v)
        if re.compile(r'^\d+$').match(cmd):
            time.sleep(int(cmd))
        else:
            tokens = cmd.split()

            commands = 'curl --write-out %{http_code} --silent --output /dev/null'.split()
            commands.append('-b')
            commands.append(self.cookie_path)
            commands.append('--connect-timeout')
            commands.append('10')
            commands.append(tokens[1])
            for x in tokens[2:]:
                commands.append('-f')
                commands.append(x)

            start_time = time.time()*1000
            p = subprocess.Popen(commands, stdout=subprocess.PIPE)
            p.wait()
            time_elapsed =  int(round(time.time()*1000 - start_time))
            exit_code = p.returncode
            status_code = p.stdout.read()

            if exit_code != 0 or time_elapsed > 500:
                self.log_fd.write('%d %s %d %s\n' % (exit_code, status_code, time_elapsed, ' '.join(commands)))
                self.log_fd.flush()

                self.log('%d %s %d' % (exit_code, status_code, time_elapsed))

def quit(signum, frame):
    print 'You choose to stop me.'
    sys.exit()

def main():
    if len(sys.argv) == 1:
        if os.path.exists(LOGS_PATH):
            shutil.rmtree(LOGS_PATH)
        os.mkdir(LOGS_PATH)
    # signal.signal(signal.SIGINT, quit)
    # signal.signal(signal.SIGTERM, quit)

    threads = []
    for i in range(100):
        c = Client(i, json.loads(open('vars.json').read()))
        t = threading.Thread(target=c.run)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

if __name__ == '__main__':
    main()