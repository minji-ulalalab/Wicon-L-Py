'''
Created on 2022. 03. 24.

@author: sg.an
'''

import traceback, time
import board,busio
import numpy as np
import adafruit_mlx90640
from common.dbClient import BACKUPDBCLIENT
from enum import Enum

class STATE(Enum):
    INIT_I2C = 0
    WAIT = 1
    BACKUP_CHECK = 2
    INIT_PROTOCOL = 3
    READ_DATA = 4
    PROCESS_DATA = 5
    MAKE_PROTOCOL = 6

class IRThermopile:
    conf = None
    exh = None
    logger = None
    state = None

    _i2c = None
    _mlx_sensor = None
    _frame = None
    _msg_data = None
    _msg = None

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
            start_time = 0
            end_time = 0
            period = 0
            
            self.conf.read_i2c()
            self.init_i2c_sensor()
            self.state = STATE.INIT_I2C
            while True:
                if (self.state == STATE.INIT_I2C):
                    print("STATE.INIT_I2C")
                    self.logger.debug("STATE.INIT_I2C")
                    self.conf.read_i2c()
                    ret = self.init_i2c_sensor()
                    if(ret == True):
                        self.state = STATE.BACKUP_CHECK
                    else:
                        time.sleep(3)
                        self.state = STATE.INIT_I2C

                elif (self.state == STATE.WAIT):
                    print("STATE.WAIT")
                    self.logger.debug("STATE.WAIT")
                    #print("Digital Counter is waiting...\n")
                    period = 1 - (end_time - start_time)
                    print("sensor process time : %f" % (end_time - start_time))
                    print("sensor period : %f" % period)
                    self.logger.debug("sensor period : %f" % period)
                    if period > 0 :
                        time.sleep(period)
                    self.state = STATE.READ_DATA

                elif (self.state == STATE.BACKUP_CHECK):
                    print("STATE.BACKUP_CHECK")
                    self.logger.debug("STATE.BACKUP_CHECK")
                    self._db_client.db_connect()

                    db_rows = self._db_client.db_read_and_delete_data()
                    rows_len = len(db_rows)
                    if(rows_len > 0):
                        for i in range(0, rows_len):
                            print(f"db_rows : {db_rows[i][0]}")
                            backup_queue.put(db_rows[i][0])
                        print(backup_queue)
                        self.logger.debug("backup_queue : ")
                        self.logger.debug(backup_queue)
                        self._is_backup = True
                        self.state = STATE.INIT_PROTOCOL 
                    else:
                        # db에 데이터가 없으면 backup flag false
                        self.logger.debug("no backup data!")
                        self._is_backup = False
                        self.state = STATE.INIT_PROTOCOL 

                    self._db_client.db_commit()
                    self._db_client.db_close()
                
                elif (self.state == STATE.INIT_PROTOCOL):
                    print("STATE.INIT_PROTOCOL")
                    if(self.conf.ir_temp_data_mode == "WHOLE"):
                        prefix = self.conf.wicon_id[0:3]
                        id_number = self.conf.wicon_id[3:10]
                        id_number = int(id_number)+1
                        
                        self._msg = "%s,000000000000,%s,000,0.0000,0.0000,0.0000,0.0000|%s00%d,000000000000,%s,000,0.0000,0.0000,0.0000,0.0000\n" %(self.conf.wicon_id, self._version, prefix, id_number, self._version)
                    else :
                        self._msg = self.conf.wicon_id + ",000000000000," + self._version + ",000,0.0000,0.0000,0.0000,0.0000\n"
                        
                    data_queue.put(self._msg)
                    self.state = STATE.READ_DATA
                    
                elif (self.state == STATE.READ_DATA):
                    print("STATE.READ_DATA")
                    self.logger.debug("STATE.READ_DATA")
                    print("STATE.READ_DATA")
                    start_time = time.time()
                    #self._mlx_sensor.getFrame(self._frame)
                    ret = self.get_frame_data()
                    if (ret == True):
                        self.state = STATE.PROCESS_DATA
                    else :
                        self.state = STATE.INIT_I2C
                
                elif (self.state == STATE.PROCESS_DATA):
                    self.logger.debug("STATE.PROCESS_DATA")
                    print("STATE.PROCESS_DATA")
                    self.state = STATE.MAKE_PROTOCOL
                    
                    if(self.conf.ir_temp_data_mode == "WHOLE"):
                        self._msg_data = self.process_whole_data(self._frame)

                    elif(self.conf.ir_temp_data_mode == "CENTER_MIN_MAX"):
                        self._msg_data = self.process_avg_center_min_max(self._frame)
                    
                    elif(self.conf.ir_temp_data_mode == "MATCH"):
                        if(self.conf.ir_temp_match == "MIN"):
                            self._msg_data = self.process_match_min_center(self._frame)
                        
                        elif(self.conf.ir_temp_match == "MAX"):
                            self._msg_data = self.process_match_max_center(self._frame)
                        
                        else:
                            print("it's not supported match mode.")
                            self.logger.error("it's not supported match mode.")
                            self.state = STATE.INIT_I2C
                    
                    elif(self.conf.ir_temp_data_mode == "FIVE_POINT"):
                        self._msg_data = self.process_five_point(self._frame, self.conf.ir_temp_five_point) 
                    
                    else:
                        print("it's not supported mode.")
                        self.logger.error("it's not supported mode.")
                        self.state = STATE.INIT_I2C
                    
                elif (self.state == STATE.MAKE_PROTOCOL):
                    self.logger.debug("STATE.MAKE_PROTOCOL")
                    print("STATE.MAKE_PROTOCOL")
                    if(self.conf.ir_temp_data_mode != "WHOLE"):
                        send_time = time.strftime('%y%m%d%H%M%S',time.gmtime())
                        self._msg = "%s,%s,%s,001,-99%s\n" %(self.conf.wicon_id,send_time,self._version,self._msg_data)
                    end_time = time.time()
                    # 큐 사이즈가 full이 아니면 데이터를 계속 넣음
                    if(data_queue.full() == False):
                        #print("put")
                        data_queue.put(self._msg)
                    # 큐가 풀이 되면 큐의 데이터를 백업파일에 저장, -> 백업 플래그 셋 -> 큐 비우고 신규 데이터 집어넣음
                    else:
                        self.logger.debug("data_queue is full. put data into backup queue.")
                        print("data_queue is full. put data into backup queue.")
                        self.write_backup(data_queue)
                        data_queue.queue.clear()
                        
                    if(self._is_backup == True):
                        if(backup_queue.empty()):
                            self.read_backup(backup_queue)
                    self.state = STATE.WAIT
            
            
        except Exception as ex:
            self.exh.systemError(traceback.format_exc())
            self.state = STATE.INIT_I2C

    def init_i2c_sensor(self):
        self.logger.debug("I2C SENSOR INIT.\n")
        print("I2C SENSOR INIT.\n")
        ret = False
        try:
            self._i2c = busio.I2C(board.SCL, board.SDA, frequency=400000) # setup I2C
            self._mlx_sensor = adafruit_mlx90640.MLX90640(self._i2c) # begin MLX90640 with I2C comm
            self._mlx_sensor.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ # set refresh rate
            self._frame = np.zeros((24*32,)) # setup array for storing all 768 temperatures
            ret = True
        except Exception as ex:
            ret = False
            #self.exh.systemError(traceback.format_exc())
            self.logger.error(ex)
        return ret
    
    def get_frame_data(self):
        ret = False
        try:
            self._mlx_sensor.getFrame(self._frame)
            print(self._frame)
            ret = True
        except Exception as ex:
            ret = False
            self.logger.error(ex)
        return ret
            
        
    def process_whole_data(self, frame):
        send_time = time.strftime('%y%m%d%H%M%S',time.gmtime())
        
        msg_data = ""
        msg_data2 = ""

        for index, value in enumerate(frame):
            if index < 3 :
                msg_data += ",%.2f" %value
            elif index <= 383:
                msg_data += "#%.2f" %value
            elif index <= 386:
                msg_data2 += ",%.2f" %value
            else :
                msg_data2 += "#%.2f" %value
        prefix = self.conf.wicon_id[0:3]
        id_number = self.conf.wicon_id[3:10]
        
        id_number = int(id_number)+1
        self._msg = "%s,%s,%s,001,-99%s|%s00%d,%s,%s,001,-99%s\n" %(self.conf.wicon_id,send_time,self._version,msg_data, prefix,id_number,send_time,self._version,msg_data2)
        #print("==========msg_data=============")
        #print(msg_data)
        #print("==========msg_data2=============")
        #print(msg_data2)
        print("==========msg=============")
        print(self._msg)
        return self._msg

    def process_avg_center_min_max(self, frame):
        
        msg_data = ""
        msg_data += ",%.2f" %(np.mean(frame)) # avg value
        # min index
        min_index = frame.argmin()
        msg_data += ",%d" %(min_index)
        # max index
        max_index = frame.argmax()
        msg_data += ",%d" %(max_index)
        
        # center 6 by 6
        # 301 302 303 304 305 306
        # 333 334 335 336 337 338
        # 365 366 367 368 369 370
        # 397 398 399 400 401 402
        # 429 430 431 432 433 434
        # 461 462 463 464 465 466
        for i in range(6):
            for j in range(301 + (i * 32), 307 + (i * 32)):
                msg_data += "#%.2f" %(frame[j])
    
        # min 3 by 3
        min_row, min_col = divmod(min_index, 32)
        print("------min point------")
        print(min_row, min_col)
        # first row
        if min_row == 0:
            msg_data += "#NL#NL#NL"
        else:
            if min_col == 0:
                msg_data += "#NL#%.2f#%.2f" %(frame[min_index-32], frame[min_index-31])
            elif min_col == 31:
                msg_data += "#%.2f#%.2f#NL" %(frame[min_index-33], frame[min_index-32])
            else:
                msg_data += "#%.2f#%.2f#%.2f" %(frame[min_index-33], frame[min_index-32], frame[min_index-31])
        
        # second row
        if min_col == 0:
            msg_data += "#NL#%.2f#%.2f" %(frame[min_index], frame[min_index+1])
        elif min_col == 31:
            msg_data += "#%.2f#%.2f#NL" %(frame[min_index-1], frame[min_index])
        else:
            msg_data += "#%.2f#%.2f#%.2f" %(frame[min_index-1], frame[min_index], frame[min_index+1])
            
        # third row
        if min_row == 23:
            msg_data += "#NL#NL#NL"
        else:
            if min_col == 0:
                msg_data += "#NL#%.2f#%.2f" %(frame[min_index+32], frame[min_index+33])
            elif min_col == 31:
                msg_data += "#%.2f#%.2f#NL" %(frame[min_index+31], frame[min_index+32])
            else:
                msg_data += "#%.2f#%.2f#%.2f" %(frame[min_index+31], frame[min_index+32], frame[min_index+33])
        
        # max 3 by 3
        max_row, max_col = divmod(max_index, 32)
        print("------max point------")
        print(max_row, max_col)
        # first row
        if max_row == 0:
            msg_data += "#NL#NL#NL"
        else:
            if max_col == 0:
                msg_data += "#NL#%.2f#%.2f" %(frame[max_index-32], frame[max_index-31])
            elif max_col == 31:
                msg_data += "#%.2f#%.2f#NL" %(frame[max_index-33], frame[max_index-32])
            else:
                msg_data += "#%.2f#%.2f#%.2f" %(frame[max_index-33], frame[max_index-32], frame[max_index-31])
        
        # second row
        if max_col == 0:
            msg_data += "#NL#%.2f#%.2f" %(frame[max_index], frame[max_index+1])
        elif max_col == 31:
            msg_data += "#%.2f#%.2f#NL" %(frame[max_index-1], frame[max_index])
        else:
            msg_data += "#%.2f#%.2f#%.2f" %(frame[max_index-1], frame[max_index], frame[max_index+1])
            
        # third row
        if max_row == 23:
            msg_data += "#NL#NL#NL"
        else:
            if max_col == 0:
                msg_data += "#NL#%.2f#%.2f" %(frame[max_index+32], frame[max_index+33])
            elif max_col == 31:
                msg_data += "#%.2f#%.2f#NL" %(frame[max_index+31], frame[max_index+32])
            else:
                msg_data += "#%.2f#%.2f#%.2f" %(frame[max_index+31], frame[max_index+32], frame[max_index+33])
    
        print("------processed_list------")
        print(msg_data)
        return msg_data
        
    def process_match_min_center(self, frame):
        match = 0
        msg_data = ""
        msg_data += ",%.2f" %(np.mean(frame)) # avg value
        # min value & index
        min_index = frame.argmin()
        msg_data += ",%.2f" %(frame[min_index])
        msg_data += ",%d" %(min_index)
        
        # center 6 by 6
        # 301 302 303 304 305 306
        # 333 334 335 336 337 338
        # 365 366 367 368 369 370
        # 397 398 399 400 401 402
        # 429 430 431 432 433 434
        # 461 462 463 464 465 466
        for i in range(6):
            for j in range(301 + (i * 32), 307 + (i * 32)):
                if(j == min_index):
                    match = 1
        
        msg_data += "#%d" %(match)

        return msg_data
    
    def process_match_max_center(self, frame):
        match = 0
        msg_data = ""
        msg_data += ",%.2f" %(np.mean(frame)) # avg value
        # max value & index
        max_index = frame.argmax()
        msg_data += ",%.2f" %(frame[max_index])
        msg_data += ",%d" %(max_index)
        
        # center 6 by 6
        # 301 302 303 304 305 306
        # 333 334 335 336 337 338
        # 365 366 367 368 369 370
        # 397 398 399 400 401 402
        # 429 430 431 432 433 434
        # 461 462 463 464 465 466
        for i in range(6):
            for j in range(301 + (i * 32), 307 + (i * 32)):
                if(j == max_index):
                    match = 1
        
        msg_data += "#%d" %(match)

        return msg_data
    
    def process_five_point(self, frame, five_point):
        #print(five_point)
        msg_data = ""
        msg_data += ",%.2f" %(frame[five_point[0]])
        msg_data += ",%.2f" %(frame[five_point[1]])
        msg_data += ",%.2f" %(frame[five_point[2]])
        msg_data += "#%.2f" %(frame[five_point[3]])
        msg_data += "#%.2f" %(frame[five_point[4]])

        return msg_data
    
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