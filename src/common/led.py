'''
Created on 2022. 02. 06.

@author: sg.an
'''

import traceback, time
import RPi.GPIO as GPIO

class LED:
    conf = None
    exh = None
    logger = None

    RED_LED_PIN = 18
    GREEN_LED_PIN = 17
    
    ## 생성자
    def __init__(self, resources):
        self.conf = resources["conf"]
        self.exh = resources["exh"]
        self.logger = resources["logger"]
                     
    def led_init_gpio(self):
        self.logger.debug("LED INIT GPIO.\n")
        GPIO.setmode(GPIO.BCM)
        
        GPIO.setup(self.RED_LED_PIN, GPIO.OUT)
        GPIO.setup(self.GREEN_LED_PIN, GPIO.OUT)

    def red_led_on_off(self, on_off):
        self.logger.debug("RED LED is %d.\n" % on_off)
        GPIO.output(self.RED_LED_PIN, on_off)

    def green_led_on_off(self, on_off):
        self.logger.debug("GREEN LED is %d.\n" % on_off)
        GPIO.output(self.GREEN_LED_PIN, on_off)

    def red_led_blink(self, blink_time, blink_period):
        self.logger.debug("RED LED is blink. blink time : %d, blink_period : %f\n" %(blink_time,blink_period))
        while blink_time > 0:
            GPIO.output(self.RED_LED_PIN, GPIO.LOW)
            time.sleep(blink_period)
            GPIO.output(self.RED_LED_PIN, GPIO.HIGH)
            time.sleep(blink_period)
            blink_time -= 1

    def green_led_blink(self, blink_time, blink_period):
        self.logger.debug("GREEN LED is blink. blink time : %d, blink_period : %f\n" %(blink_time,blink_period))
        while blink_time > 0:
            GPIO.output(self.GREEN_LED_PIN, GPIO.LOW)
            time.sleep(blink_period)
            GPIO.output(self.GREEN_LED_PIN, GPIO.HIGH)
            time.sleep(blink_period)
            blink_time -= 1
    
    def both_led_blink(self, blink_time, blink_period):
        self.logger.debug("BOTH LED is blink. blink time : %d, blink_period : %f\n" %(blink_time,blink_period))
        while blink_time > 0:
            GPIO.output(self.GREEN_LED_PIN, GPIO.LOW)
            GPIO.output(self.RED_LED_PIN, GPIO.LOW)
            time.sleep(blink_period)
            GPIO.output(self.GREEN_LED_PIN, GPIO.HIGH)
            GPIO.output(self.RED_LED_PIN, GPIO.HIGH)
            time.sleep(blink_period)
            blink_time -= 1
    