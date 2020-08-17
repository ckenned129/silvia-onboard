import time
import math
import datetime
import threading
from mqtt_client import MQTTClient
from random import random
from simple_pid import PID

def run_at_freq(func, freq, *args):
    interval = 1.0 / freq
    synchronizer = threading.Event()
    def run_loop():
        while not synchronizer.wait(interval - time.time() % interval):
            func(*args)

    threading.Thread(target=run_loop).start()
    return (func.__name__, synchronizer.set)  # (name, stop_func)


class Silvia:

    def __init__(self):
        self.is_on = False
        self.temp_f = 0
        self.temp_f_target = 212
        self.control_p = 2
        self.control_i = 0.1
        self.control_d = 2
        self.temp_history = []
        self.shed_on_time = None
        self.sched_off_time = None
        self.last_on_time = time.time()
        self.last_off_time = None
        self.pid_freq = 1
        self.read_freq = 10
        self.post_freq = 10
        self.stop_funcs = []
        self.mqtt_client = MQTTClient()

    def start(self):
        # Start loops and catch stop functions
        pid = PID(self.control_p, self.control_i, self.control_d, setpoint=self.temp_f_target)

        stop_pid = run_at_freq(self.run_pid, self.pid_freq, pid)
        stop_read_temp = run_at_freq(self.read_temp, self.read_freq)
        stop_post_status = run_at_freq(self.post_status, self.post_freq)
        self.stop_funcs = [stop_pid, stop_read_temp, stop_post_status]

        while True:
            time.sleep(1) # Run until interrupt

    def run_pid(self, pid):
        print('Running PID Loop')
        print(pid)
        control = pid(self.temp_f)
        print(control, self.temp_f)
        print(5*random())
        self.temp_f += random() + 0.1*control


    def read_temp(self):
        print('Running Read Temp Loop')


    def post_status(self):
        print('Running Status Loop')
        self.mqtt_client.publish({"message" : self.temp_f})

    def close(self):

        print('\nSIGINT detected. Shutting down...')
        self.mqtt_client.close()
        for name, f in self.stop_funcs:
            print('Stopping', name)
            f()


def main():
    silvia = Silvia()

    try:
        silvia.start()
    except:
        silvia.close()
    return



if __name__ == '__main__':
    main()
