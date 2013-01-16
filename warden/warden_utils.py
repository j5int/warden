import time
import socket
import os

def waitforsocket(host, port, timeout=300, sleeptime=5, conn_timeout=2):
        start = time.time()
        while (time.time()-start)<timeout:
            try:
                s = socket.create_connection((host, port), conn_timeout)
                s.close()
                return True
            except Exception as e:
                time.sleep(sleeptime)
        return False

def normalize_path(path):
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    return path