'''
Created on 2022. 02. 03.

@author: sg.an
'''
import os, json

class Config:
    __config = None
    
    __default_config = None
    __app_name = None
    __run_mode = None
    __server_url = None
    __server_port = None
    __sensor = None
    __wicon_id = None
    __period = None

    __base_dir = None
    __logs_dir = None
    __backup_dir = None

    __digital_config = None
    __debouncing = None
    __debounce_time_ms = None
    __digital_mode = None
    __counter_sensor_count = None
    __counter_max_count = None
    __offset_time = None
    __edge = None
    
    __i2c_config = None
    __i2c_mode = None
    __ir_temp_data_mode = None
    __ir_temp_match = None
    __ir_temp_five_point = None
    
    
    def __init__(self):
        print('Read Config.json.\n')
        try :
            config_dir = os.getcwd()
            os_type = os.name
            config_file=None
            print(config_dir)
            if os_type.upper() == "NT":
                config_file  = config_dir+"\\resource\\Config.json"
            elif os_type.upper() == "POSIX":
                config_file = config_dir+"/resource/Config.json"
            else :
                config_file = config_dir+"/resource/Config.json"
            print(config_file)
            if os.path.isfile(config_file) == False:
                raise Exception("There is no Config.json\n")

            with open(config_file, "rt", encoding="utf-8") as file:
                self.__config = json.load(file)
        except Exception as ex:
            print(str(ex))

    def read_default(self):
        ret = -1
        print('Read default config.\n')
        try :
            self.default_config = self.__config['DEFAULT']
            
            self.app_name = self.default_config['APPLICATION_NAME']
            self.run_mode = self.default_config['RUN_MODE']
            self.server_url = self.default_config['SERVER_URL']
            self.server_port = self.default_config['SERVER_PORT']
            self.sensor = self.default_config['SENSOR']
            self.wicon_id = self.default_config['WICON_ID']
            self.period = self.default_config['PERIOD_S']

            if(self.app_name == None or self.run_mode == None or self.server_url == None or self.server_port == None
               or self.sensor == None or self.wicon_id == None or self.period == None) :
                print('There is no default config data.\n')
                return ret

            self.base_dir = self.__config[self.run_mode.upper()]['BASE_DIR']
            self.logs_dir = self.__config[self.run_mode.upper()]['LOGS_DIR']
            self.backup_dir = self.__config[self.run_mode.upper()]['BACKUP_DIR']
            ret = self
            print('Done.\n') 
        except Exception as ex:
            print(str(ex))
            ret = -1
        finally:
            return ret

    def read_digital(self):
        ret = -1
        print('Read the digital sensor information.\n')
        try :
            self.digital_config = self.__config['DIGITAL']
            
            self.debouncing = self.digital_config['DEBOUNCING']
            self.debounce_time_ms = self.digital_config['DEBOUNCE_TIME_MS']
            self.digital_mode = self.digital_config['MODE']
            
            if(self.digital_config == None or self.debouncing == None 
               or self.debounce_time_ms == None or self.digital_mode == None) :
                print('There is no digital sensor information.\n')
                return ret

            if(self.digital_mode == "COUNTER"):
                self.counter_sensor_count = self.digital_config[self.digital_mode]['SENSOR_COUNT']
                self.counter_max_count = self.digital_config[self.digital_mode]['MAX_COUNT']
            elif(self.digital_mode == "TIMING"):
                self.offset_time = self.digital_config[self.digital_mode]['OFFSET_TIME']
            elif(self.digital_mode == "DIGITAL"):
                self.edge = self.digital_config[self.digital_mode]['EDGE']
            else:
                return ret
                
            ret = 0
            print('Done.\n')        
            
        except Exception as ex:
            print(str(ex))

        finally:
            return ret
    
    def read_i2c(self):
        ret = -1
        print('Read the i2c sensor information.\n')
        try :
            self.i2c_config = self.__config['I2C']
            
            self.i2c_mode = self.i2c_config['MODE']
            
            if(self.i2c_config == None or self.i2c_mode == None) :
                print('There is no i2c sensor information.\n')
                return ret
            
            if(self.i2c_mode == "IR_TEMP"):
                self.ir_temp_data_mode = self.i2c_config[self.i2c_mode]['DATA_MODE']
                if(self.ir_temp_data_mode == "MATCH"):
                    self.ir_temp_match = self.i2c_config[self.i2c_mode]['MATCH']
                    
                elif(self.ir_temp_data_mode == "FIVE_POINT"):
                    self.ir_temp_five_point = self.i2c_config[self.i2c_mode]['FIVE_POINT']
            elif(self.i2c_mode == "DUST"):
                self.i2c_bus_no = self.i2c_config[self.i2c_mode]['BUS_NO']      
                self.i2c_dust_time = self.i2c_config[self.i2c_mode]['TIME'] 
            elif(self.i2c_mode == "VIBRATION"):
                pass
            else:
                return ret
            
            print('Done.\n') 
            ret = 0
        except Exception as ex:
            print(str(ex))
        finally :
            return ret

    # getter
    @property
    def config(self):
        return self.__config

    # getter
    @property
    def default_config(self):
        return self.__default_config

    # getter
    @property
    def app_name(self):
        return self.__app_name

    # getter
    @property
    def run_mode(self):
        return self.__run_mode

    # getter
    @property
    def server_url(self):
        return self.__server_url

    # getter
    @property
    def server_port(self):
        return self.__server_port

    # getter
    @property
    def sensor(self):
        return self.__sensor

    # getter
    @property
    def wicon_id(self):
        return self.__wicon_id

    # getter
    @property
    def period(self):
        return self.__period

    # getter
    @property
    def base_dir(self):
        return self.__base_dir

    # getter
    @property
    def logs_dir(self):
        return self.__logs_dir

    # getter
    @property
    def backup_dir(self):
        return self.__backup_dir
    
    # getter
    @property
    def digital_config(self):
        return self.__digital_config
    
    # getter
    @property
    def debouncing(self):
        return self.__debouncing

    # getter
    @property
    def debounce_time_ms(self):
        return self.__debounce_time_ms

    # getter
    @property
    def digital_mode(self):
        return self.__digital_mode

    # getter
    @property
    def counter_sensor_count(self):
        return self.__counter_sensor_count

    # getter
    @property
    def counter_max_count(self):
        return self.__counter_max_count

    # getter
    @property
    def offset_time(self):
        return self.__offset_time
    
    # getter
    @property
    def edge(self):
        return self.__edge
        
    # getter
    @property
    def i2c_config(self):
        return self.__i2c_config
    
    # getter
    @property
    def i2c_mode(self):
        return self.__i2c_mode

    # getter
    @property
    def ir_temp_data_mode(self):
        return self.__ir_temp_data_mode
    
    # getter
    @property
    def ir_temp_match(self):
        return self.__ir_temp_match
    
    # getter
    @property
    def ir_temp_five_point(self):
        return self.__ir_temp_five_point

    # setter
    @config.setter
    def config(self, value):
        self.__config = value
    
    # setter
    @default_config.setter
    def default_config(self, value):
        self.__default_config = value

    # setter
    @app_name.setter
    def app_name(self, value):
        self.__app_name = value

    # setter
    @run_mode.setter
    def run_mode(self, value):
        self.__run_mode = value

    # setter
    @server_url.setter
    def server_url(self, value):
        self.__server_url = value
    
    # setter
    @server_port.setter
    def server_port(self, value):
        self.__server_port = value

    # setter
    @sensor.setter
    def sensor(self, value):
        self.__sensor = value
    
    # setter
    @wicon_id.setter
    def wicon_id(self, value):
        self.__wicon_id = value

    # setter
    @period.setter
    def period(self, value):
        self.__period = value
    
    # setter
    @base_dir.setter
    def base_dir(self, value):
        self.__base_dir = value

    # setter
    @logs_dir.setter
    def logs_dir(self, value):
        self.__logs_dir = value

    # setter
    @backup_dir.setter
    def backup_dir(self, value):
        self.__backup_dir = value
        
    # setter
    @digital_config.setter
    def digital_config(self, value):
        self.__digital_config = value

    # setter
    @debouncing.setter
    def debouncing(self, value):
        self.__debouncing = value

    # setter
    @debounce_time_ms.setter
    def debounce_time_ms(self, value):
        self.__debounce_time_ms = value

    # setter
    @digital_mode.setter
    def digital_mode(self, value):
        self.__digital_mode = value

    # setter
    @counter_sensor_count.setter
    def counter_sensor_count(self, value):
        self.__counter_sensor_count = value

    # setter
    @counter_max_count.setter
    def counter_max_count(self, value):
        self.__counter_max_count = value

    # setter
    @offset_time.setter
    def offset_time(self, value):
        self.__offset_time = value
    
    # setter
    @edge.setter
    def edge(self, value):
        self.__edge = value
    
    # setter
    @i2c_config.setter
    def i2c_config(self, value):
        self.__i2c_config = value

    # setter
    @i2c_mode.setter
    def i2c_mode(self, value):
        self.__i2c_mode = value

    # setter
    @ir_temp_data_mode.setter
    def ir_temp_data_mode(self, value):
        self.__ir_temp_data_mode = value
        
    # setter
    @ir_temp_match.setter
    def ir_temp_match(self, value):
        self.__ir_temp_match = value
        
    # setter
    @ir_temp_five_point.setter
    def ir_temp_five_point(self, value):
        self.__ir_temp_five_point = value