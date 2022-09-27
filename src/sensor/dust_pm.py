'''
Created on 2022. 03. 24.

@author: sg.an
'''
import sys
import logging
import threading
import smbus
import traceback, time
import board,busio
import numpy as np
from common.dbClient import BACKUPDBCLIENT
from enum import Enum
from queue import Queue
from datetime import datetime

MASS_DENSITY_PM_TYPES = ["pm1.0", "pm2.5", "pm10"]
MASS_DENSITY_BLOCK_SIZE = 4
ADDRESS_MASS_DENSITY_HEAD = 0
ADDRESS_MASS_DENSITY_TAIL = 11
ADDRESS_MASS_DENSITY_LENGTH = (ADDRESS_MASS_DENSITY_TAIL - ADDRESS_MASS_DENSITY_HEAD) + 1

PARTICLE_COUNT_PM_TYPES = ["pm0.5", "pm1.0", "pm2.5", "N/A", "pm5.0", "pm7.5", "pm10"]
PARTICLE_COUNT_BLOCK_SIZE = 2
ADDRESS_PARTICLE_COUNT_HEAD = 12
ADDRESS_PARTICLE_COUNT_TAIL = 25
ADDRESS_PARTICLE_COUNT_LENGTH = (ADDRESS_PARTICLE_COUNT_TAIL - ADDRESS_PARTICLE_COUNT_HEAD) + 1

DATA_LENGTH_HEAD = ADDRESS_MASS_DENSITY_HEAD
DATA_LENGTH_TAIL = ADDRESS_PARTICLE_COUNT_TAIL
TOTAL_DATA_LENGTH = ADDRESS_MASS_DENSITY_LENGTH + ADDRESS_PARTICLE_COUNT_LENGTH

class STATE(Enum):
    INIT_I2C = 0
    WAIT = 1
    BACKUP_CHECK = 2
    INIT_PROTOCOL = 3
    READ_DATA = 4
    PROCESS_DATA = 5
    MAKE_PROTOCOL = 6


class DustPM:
    conf = None
    exh = None
    logger = None
    state = None

    _pm_sensor = None
    _mass_density_data = None
    _particle_count_data = None
    _mass_10 = None
    _mass_25 = None
    _mass_100 = None
    _par_5 = None
    _par_10 = None
    _par_25 = None
    _par_50 = None
    _par_75 = None
    _par_100 = None

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
            self.state = STATE.INIT_I2C
            while True:
                if (self.state == STATE.INIT_I2C):
                    print("STATE.INIT_I2C")
                    self.logger.debug("STATE.INIT_I2C")
                    self.conf.read_i2c()
                    ret = self.init_i2c_sensor()
                    print("ret: "+str(ret))
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
                    self._msg = self.conf.wicon_id + ",000000000000," + self._version + ",000,0.0000,0.0000,0.0000,0.0000\n"
                        
                    data_queue.put(self._msg)
                    self.state = STATE.READ_DATA
                    
                elif (self.state == STATE.READ_DATA):#이부분 필요성
                    print("STATE.READ_DATA")
                    self.logger.debug("STATE.READ_DATA")
                    start_time = time.time()

                    if (ret == True):
                        self.state = STATE.PROCESS_DATA
                    else :
                        self.state = STATE.INIT_I2C
                
                elif (self.state == STATE.PROCESS_DATA):
                    self.logger.debug("STATE.PROCESS_DATA")
                    print("STATE.PROCESS_DATA")
                    self._msg_data = self.process_dust_data()
                    if self._msg_data == -1:
                        self.state = STATE.READ_DATA
                    else:
                        self.state = STATE.MAKE_PROTOCOL
 
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
        self.logger.debug("I2C DUST SENSOR INIT.\n")
        print("I2C DUST SENSOR INIT.\n")
        ret = False
        try:
            self._pm_sensor = SNGCJA5(i2c_bus_no=int(self.conf.i2c_bus_no))
            ret = True
        except Exception as ex:
            ret = False
            #self.exh.systemError(traceback.format_exc())
            self.logger.error(ex)
        return ret

    def process_dust_data(self):
        
        send_time = time.strftime('%y%m%d%H%M%S',time.gmtime())
        
        msg_data = ""
        result = self._pm_sensor.get_measurement()

        if (result=={}):
            msg_data = -1
        else:
            print(str(send_time)+ "\n" + str(result))
            self.logger.debug("sensor:\n"+str(result)+"\n"+str(send_time))
            _mass_density_data = result["sensor_data"]["mass_density"]
            _particle_count_data = result["sensor_data"]["particle_count"]
            _mass_10 = str(_mass_density_data["pm1.0"]) #pm1.0
            _mass_25 = str(_mass_density_data["pm2.5"]) #pm2.5
            _mass_100 = str(_mass_density_data["pm10"]) #pm10
        
            _par_5 = str(_particle_count_data["pm0.5"])
            _par_10 = str(_particle_count_data["pm1.0"])
            _par_25 = str(_particle_count_data["pm2.5"])
            _par_50 = str(_particle_count_data["pm5.0"])
            _par_75 = str(_particle_count_data["pm7.5"])
            _par_100 = str(_particle_count_data["pm10"])

            msg_data = ",%s,%s,%s#%s#%s#%s#%s#%s#%s"%(_mass_10,_mass_25, _mass_100, _par_5, _par_10, _par_25, _par_50, _par_75, _par_100 ) 

            print("==========msg=============")
            print(msg_data)
            #time.sleep(int(self.conf.i2c_dust_time))


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

class SNGCJA5:

    def __init__(self, i2c_bus_no:int, logger:str=None):
        self.logger = None
        if logger:
            self.logger = logging.getLogger(logger)
        self.i2c_address = 0x33
        try:
            self.i2c_bus = smbus.SMBus(i2c_bus_no)
        except OSError as e:
            print("OSError")
            print(e)
        self.__mass_density_addresses = {pm_type: MASS_DENSITY_BLOCK_SIZE*order 
                                            for order, pm_type in enumerate(MASS_DENSITY_PM_TYPES)}

        self.__particle_count_addresses = {pm_type: PARTICLE_COUNT_BLOCK_SIZE*order
                                            for order, pm_type in enumerate(PARTICLE_COUNT_PM_TYPES)}

        self.__data = Queue(maxsize=20)
        self.__run()

    def get_mass_density_data(self, data:list) -> dict:

        return {pm_type: 
            float((data[address+3] << 24 | 
                data[address+2] << 16 | 
                data[address+1] << 8 | 
                data[address]) / 1000) 
                for pm_type, address in self.__mass_density_addresses.items()}

    def get_particle_count_data(self, data:list) -> dict:

        return {pm_type: 
            float((data[address+1] << 8 | data[address])) 
                for pm_type, address in self.__particle_count_addresses.items()
                if pm_type != "N/A"}

    def __read_sensor_data(self) -> None:
        _buff_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        error_check = 0

        while True:
            cnt = 0
            try:
                data = self.i2c_bus.read_i2c_block_data(self.i2c_address, DATA_LENGTH_HEAD, TOTAL_DATA_LENGTH)

                for data_item in data: #전체가 255인 경우 cnt는 26
                    if data_item == 255:
                        cnt += 1
                        print("cnt: "+ str(cnt))

                if cnt == 26: #전체가 255인경우
                    print("data error. change the data from buff.")
                    cnt = 0
                    data = _buff_data
                    error_check += 1
                else:
                    error_check = 0
                    _buff_data = data

                print("data: "+str(data)) 
                mass_density_data = self.get_mass_density_data(data[ADDRESS_MASS_DENSITY_HEAD:ADDRESS_MASS_DENSITY_TAIL+1])
                particle_count_data = self.get_particle_count_data(data[ADDRESS_PARTICLE_COUNT_HEAD:ADDRESS_PARTICLE_COUNT_TAIL+1])

                if self.__data.full():
                    self.__data.get()

                self.__data.put({
                    "sensor_data": {
                        "mass_density": mass_density_data,
                        "particle_count": particle_count_data,
                        "mass_density_unit": "ug/m3",
                        "particle_count_unit": "none"
                    },
                    "timestamp": int(datetime.now().timestamp())
                })

                if error_check > 3:
                    print("PLEASE CHECK SENSOR DATA")
                    error_check = 0


            except KeyboardInterrupt:
                sys.exit()

            except OSError as e:
                if self.logger:
                    self.logger.warning(f"{type(e).__name__}: {e}")
                    self.logger.warning("Sensor is not detected on I2C bus. Terminating...")
                else:
                    print(f"{type(e).__name__}: {e}")
                    print("Sensor is not detected on I2C bus. Terminating...")

                sys.exit(1)

            except Exception as e:
                if self.logger:
                    self.logger.warning(f"{type(e).__name__}: {e}")
                else:
                    print(f"{type(e).__name__}: {e}")

            finally:
                # Data is updated by sensor every 1 second as per specification. 
                # 1-second delay is added to compensate data duplication
                time.sleep(1) 

    def get_measurement(self) -> dict:
        if self.__data.empty():
            return {}

        return self.__data.get()

    def __run(self):
        print("read seonsor data thread start")
        threading.Thread(target=self.__read_sensor_data, daemon=True).start()