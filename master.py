# encoding: utf-8

import subprocess
import shutil, os, sys

LOGS_PATH = 'logs'

def main():
    if os.path.exists(LOGS_PATH):
        shutil.rmtree(LOGS_PATH)
    os.mkdir(LOGS_PATH)

    ps = []
    for i in range(5):
        p = subprocess.Popen('python main.py --no-rmdir'.split())
        ps.append(p)
    for p in ps:
        p.wait()

if __name__ == '__main__':
    main()