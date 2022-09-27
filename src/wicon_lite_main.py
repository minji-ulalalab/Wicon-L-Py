'''
Created on 2022. 02. 04.

@author: sg.an
'''

from common.config import Config
from common.exceptionHandler import ExceptionHandler
from common.logger import Log
from common.led import LED
from common.button import BUTTON
from client.wiconClientThread import WiconClientThread
from sensor.digital_counter import DigitalCounter
from sensor.ir_thermopile import IRThermopile
from sensor.dust_pm import DustPM
from queue import Queue
import threading
from signal import signal, SIGPIPE, SIG_DFL

       
def main():
    signal(SIGPIPE, SIG_DFL)#broken pip error시 종료됨
    version = "v1.201"
    conf = Config()
    conf = conf.read_default()
    if conf == -1:
        print('error : read config file.\n')

    print(conf)
    log = Log(conf).logger
    exh = ExceptionHandler(log)
    
    resources = {
        "conf":conf,
        "logger":log,
        "exh":exh
    }
    led_inst = LED(resources)

    led_inst.led_init_gpio()
    led_inst.red_led_on_off(1)
    print('Start the ulalaLAB %s\n' % conf.app_name)
    log.debug('Start the ulalaLAB %s\n' % conf.app_name)
    
    normal_q = Queue(maxsize=10)
    backup_q = Queue(maxsize=10)
    sensor_thread = None

    all_threads = []
    if conf.sensor == "DIGITAL":
        conf.read_digital()
        if conf.digital_mode == "COUNTER":
            sensor_thread = DigitalCounter(resources, version)
            th = threading.Thread(target=sensor_thread.run, args=(normal_q,backup_q,))
            th.start()
            all_threads.append(th)
        elif conf.digital_mode == "TIMING":
            pass
        elif conf.digital_mode == "DIGITAL":
            pass
        else:
            print('There is no digital sensor mode.\n')
            log.error('There is no digital sensor mode.\n')
            quit()
    elif conf.sensor == "I2C":
        conf.read_i2c()
        if conf.i2c_mode == "IR_TEMP":
            sensor_thread = IRThermopile(resources, version)
            th = threading.Thread(target=sensor_thread.run, args=(normal_q,backup_q,))
            th.start()
            all_threads.append(th)
        elif conf.i2c_mode == "DUST":
            sensor_thread = DustPM(resources, version)
            th = threading.Thread(target=sensor_thread.run, args=(normal_q,backup_q,))
            th.start()
            all_threads.append(th)
        elif conf.i2c_mode == "VIBRATION":
            pass
        else:
            print('There is no I2C sensor mode.\n')
            log.error('There is no I2C sensor mode.\n')
            quit()
    else:
        print('There is no sensor mode.\n')
        log.error('There is no sensor mode.\n')
        quit()

    wicon_client_thread = WiconClientThread(resources, led_inst)
    th = threading.Thread(target=wicon_client_thread.run, args=(normal_q,backup_q,))
    th.start()
    all_threads.append(th)
    
    button_thread = BUTTON(resources)
    th = threading.Thread(target=button_thread.run_button_thread)
    th.start()
    all_threads.append(th)

    for thread in all_threads:
        thread.join()

if __name__ == "__main__":
    main()
