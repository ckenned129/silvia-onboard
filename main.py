import time
import math
import datetime
import threading
import board
import RPi.GPIO as GPIO
from mqtt_client import MQTTClient
from random import random
from simple_pid import PID
from adafruit_max31855 import MAX31855
from busio import SPI
from digitalio import DigitalInOut


def run_at_freq(func, freq, *args):
    interval = 1.0 / freq
    synchronizer = threading.Event()

    def run_loop():
        while not synchronizer.wait(interval - time.time() % interval):
            func(*args)

    threading.Thread(target=run_loop).start()
    return (func.__name__, synchronizer.set)  # (name, stop_func)

def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0


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
        self.pid = PID(self.control_p, self.control_i, self.control_d, setpoint=self.temp_f_target)
        self.pid.output_limits = (0, 100)

        spi = SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = DigitalInOut(board.D5)
        self.sensor = MAX31855(spi, cs)

        he_pin = 26  # GPIO26
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(he_pin, GPIO.OUT)
        self.he_pwm = GPIO.PWM(he_pin, self.pid_freq * 3)
        self.he_pwm.start(0)

    def start(self):
        # Start loops and catch stop functions

        stop_pid = run_at_freq(self.run_pid, self.pid_freq, self.run_pid)
        stop_read_temp = run_at_freq(self.read_temp, self.read_freq)
        stop_post_status = run_at_freq(self.post_status, self.post_freq)
        self.stop_funcs = [stop_pid, stop_read_temp, stop_post_status]

        while True:
            time.sleep(1)  # Run until interrupt

    def run_pid(self, pid):
        control = self.pid(self.temp_f)
        print(f"Temp F {self.temp_f} \t Duty Cycle {control}")
        self.he_pwm.ChangeDutyCycle(control)

    def read_temp(self):
        self.temp_f = c_to_f(self.sensor.temperature)

    def post_status(self):
        self.mqtt_client.publish({"message": self.temp_f})

    def close(self):
        self.mqtt_client.close()
        for name, f in self.stop_funcs:
            print('Stopping', name)
            f()

def main():
    silvia = Silvia()

    try:
        silvia.start()
    except KeyboardInterrupt:
        print('\nSIGINT detected. Shutting down...')
    except BaseException as e:
        print(e)

    silvia.close()
    return

if __name__ == '__main__':
    main()