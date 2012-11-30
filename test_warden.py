import time
import warden
from warden import Carbonthread

t1= Carbonthread(Carbonthread.CACHE)
t1.start()
time.sleep(1)

t2= Carbonthread(Carbonthread.AGGREGATOR)
t2.start()

time.sleep(6)
print('WORK WORK WORK')

t1.stop()
t1.join()
t2.join()
print('done.')

