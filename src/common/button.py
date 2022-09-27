'''
Created on 2022. 04. 28.

@author: sg.an
'''

import traceback, time, os
import RPi.GPIO as GPIO

class BUTTON:
    conf = None
    exh = None
    logger = None

    FUNCTION_KEY_PIN = 27
    _button_flag = None
    _button_count = None
    
    ## 생성자
    def __init__(self, resources):
        self.conf = resources["conf"]
        self.exh = resources["exh"]
        self.logger = resources["logger"]
                     
    def button_init_gpio(self):
        self.logger.debug("BUTTON INIT GPIO.\n")
        print("BUTTON INIT GPIO.\n")
        
        GPIO.setmode(GPIO.BCM)
        
        GPIO.setup(self.FUNCTION_KEY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.FUNCTION_KEY_PIN, GPIO.BOTH, callback=self.function_key_interrupt, bouncetime=5)

        self._button_flag = False
        self._button_count = 0

    def function_key_interrupt(self, channel):
        print("Function Key Falling!")
        if (GPIO.input(self.FUNCTION_KEY_PIN) == 0):
            print("Function Key Low!")
            if(self._button_flag == False):
                self._button_flag = True
        else:
            print("Function Key High")
            if(self._button_flag == True):
                self._button_flag = False
                self._button_count += 1
                print("button count up!")

    def run_button_thread(self):
    
        self.button_init_gpio()
        
        while(True):
            
            if(self._button_count == 1 and self._button_flag == False):
                os.system('sudo reboot')
            elif(self._button_count >= 3 and self._button_flag == False):
                os.system('sudo crontab /home/pi/ap_crontab')
                os.system('sudo sh /home/pi/Wicon-L-Py/scripts/change_to_ap.sh')
                

            time.sleep(2)
