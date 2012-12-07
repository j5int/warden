import time
import socket

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
