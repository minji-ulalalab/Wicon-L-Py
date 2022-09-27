'''
Created on 2022. 02. 06.

@author: sg.an
'''

import resource
import traceback, time
import RPi.GPIO as GPIO
from common.dbClient import BACKUPDBCLIENT
from enum import Enum

class STATE(Enum):
    WAIT = 0
    BACKUP_CHECK = 1
    INIT_PROTOCOL = 2
    MAKE_PROTOCOL = 3    

class DigitalCounter:
    conf = None
    exh = None
    logger = None
    state = None

    DI_PIN_1 = 4
    DI_PIN_2 = 27

    di_1_count = 0
    
    both_falling_flag = False
    both_start_time = 0
    both_end_time = 0
    both_count = 0

    msg = None

    _version = None
    _is_backup = False

    _db_client = None

    ## 생성자
    def __init__(self, resources, version):
        self.conf = resources["conf"]
        self.exh = resources["exh"]
        self.logger = resources["logger"]
        self._db_client = BACKUPDBCLIENT(resources)
        self._version = version
                     
    
    # qr입력 및 서버 전송          
    def run(self, data_queue, backup_queue):
        try:
            self.init_gpio()
            self.state = STATE.BACKUP_CHECK
            while True:
                
                if (self.state == STATE.WAIT):
                    #print("Digital Counter is waiting...\n")
                    time.sleep(1)
                    self.state = STATE.MAKE_PROTOCOL

                elif (self.state == STATE.BACKUP_CHECK):
                    self._db_client.db_connect()

                    db_rows = self._db_client.db_read_and_delete_data()
                    rows_len = len(db_rows)
                    if(rows_len > 0):
                        for i in range(0, rows_len):
                            print(f"db_rows : {db_rows[i][0]}")
                            backup_queue.put(db_rows[i][0])
                        print(backup_queue)
                        self._is_backup = True
                        self.state = STATE.INIT_PROTOCOL 
                    else:
                        # db에 데이터가 없으면 backup flag false
                        self._is_backup = False
                        self.state = STATE.INIT_PROTOCOL 

                    self._db_client.db_commit()
                    self._db_client.db_close()
                
                elif (self.state == STATE.INIT_PROTOCOL):
                    self.msg = self.conf.wicon_id + ",000000000000," + self._version + ",000,0.0000,0.0000,0.0000,0.0000\n"
                    data_queue.put(self.msg)
                    self.state = STATE.MAKE_PROTOCOL
                
                elif (self.state == STATE.MAKE_PROTOCOL):
                    send_time = time.strftime('%y%m%d%H%M%S',time.gmtime())
                    if(self.conf.counter_sensor_count == 2):
                        self.msg = "%s,%s,%s,001,-99,%d\n" %(self.conf.wicon_id,send_time,self._version,self.both_count)
                    else:
                        self.msg = "%s,%s,%s,001,-99,%d\n" %(self.conf.wicon_id,send_time,self._version,self.di_1_count)

                    # 큐 사이즈가 full이 아니면 데이터를 계속 넣음
                    if(data_queue.full() == False):
                        #print("put")
                        data_queue.put(self.msg)
                    # 큐가 풀이 되면 큐의 데이터를 백업파일에 저장, -> 백업 플래그 셋 -> 큐 비우고 신규 데이터 집어넣음
                    else:
                        self.write_backup(data_queue)
                        data_queue.queue.clear()
                        
                    if(self._is_backup == True):
                        if(backup_queue.empty()):
                            self.read_backup(backup_queue)
                    self.state = STATE.WAIT
            
            
        except Exception as ex:
            self.exh.systemError(traceback.format_exc())

    def init_gpio(self):
        self.logger.debug("DIGITAL COUNTER SENSOR INIT GPIO.\n")
        print("DIGITAL COUNTER SENSOR INIT GPIO.\n")
        GPIO.setmode(GPIO.BCM)

        if(self.conf.counter_sensor_count == 2):
            self.logger.debug("CH1 INIT.\n")
            GPIO.setup(self.DI_PIN_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.logger.debug("CH2 INIT.\n")
            GPIO.setup(self.DI_PIN_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)


            if(self.conf.debouncing == True):
                self.logger.debug("CH1 APPLY DEBOUNCE.\n")
                GPIO.add_event_detect(self.DI_PIN_1, GPIO.BOTH, callback=self.di_two_sensor_interrupt, bouncetime=self.conf.debounce_time_ms)
                self.logger.debug("CH2 APPLY DEBOUNCE.\n")
                GPIO.add_event_detect(self.DI_PIN_2, GPIO.BOTH, callback=self.di_two_sensor_interrupt, bouncetime=self.conf.debounce_time_ms)
            else:
                GPIO.add_event_detect(self.DI_PIN_1, GPIO.BOTH, callback=self.di_two_sensor_interrupt)
                GPIO.add_event_detect(self.DI_PIN_2, GPIO.BOTH, callback=self.di_two_sensor_interrupt)
        else:
            self.logger.debug("CH1 INIT.\n")
            GPIO.setup(self.DI_PIN_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            if(self.conf.debouncing == True):
                self.logger.debug("CH1 APPLY DEBOUNCE.\n")
                GPIO.add_event_detect(self.DI_PIN_1, GPIO.FALLING, callback=self.di_one_sensor_interrupt, bouncetime=self.conf.debounce_time_ms)
            else:
                GPIO.add_event_detect(self.DI_PIN_1, GPIO.FALLING, callback=self.di_one_sensor_interrupt)
                
    def di_one_sensor_interrupt(self, channel):
        #print("DI 1 detect!")        
        if(self.di_1_count >= self.conf.counter_max_count):
            self.di_1_count = 0
            self.logger.debug("CH1 OVERFLOW.\n")
            self.state = STATE.INIT_PROTOCOL
        else:
            self.state = STATE.MAKE_PROTOCOL
        self.di_1_count += 1

    def di_two_sensor_interrupt(self, channel):
        if ( (GPIO.input(self.DI_PIN_1)) and (GPIO.input(self.DI_PIN_2)) ):
        #if ( (GPIO.input(self.DI_PIN_1)) and 0 ):
        #if ( (GPIO.input(self.DI_PIN_1)) and 1 ):
            if(self.both_falling_flag == False):

                self.both_start_time = time.time()
                self.both_falling_flag = True
                print("both falling edge detect!")
        else:
            
            if(self.both_falling_flag == True):
                print("rising edge detect!")
                self.both_falling_flag = False
                self.both_end_time = time.time()
                period = self.both_end_time - self.both_start_time
                self.both_end_time = 0
                self.both_start_time = 0
                print("########### falling period %f ##########" %period)
                if(period >= 0.1):
                    print("count up!")
                    if(self.both_count >= self.conf.counter_max_count):
                        self.both_count = 0
                        self.logger.debug("BOTH OVERFLOW.\n")
                        self.state = STATE.INIT_PROTOCOL
                    else:
                        self.state = STATE.MAKE_PROTOCOL
                    self.both_count += 1

    def write_backup(self, data):
        
        self._db_client.db_connect()
        
        size = data.qsize()
        for i in range(0,size):
            self._db_client.db_write_data(data.get())
        
        self._db_client.db_commit()
        self._db_client.db_close()

        self._is_backup = True


    def read_backup(self, data): 
        
        self._db_client.db_connect()

        db_rows = self._db_client.db_read_and_delete_data()
        rows_len = len(db_rows)
        if(rows_len > 0):
            for i in range(0, rows_len):
                print(f"db_rows : {db_rows[i][0]}")
                data.put(db_rows[i][0])
            print(data)
        else:
            # db에 데이터가 없으면 backup flag false
            self._is_backup = False

        self._db_client.db_commit()
        self._db_client.db_close()      
        



    def is_backup(self):
        return self._is_backup