'''
Created on 2021. 12. 04.

@author: sg.an
'''
# -*- coding: utf-8 -*-
from datetime import datetime
import os, json
import logging.config
from time import time

class Log:
    
    __log_level_map = {
        'debug' : logging.DEBUG,
        'info' : logging.INFO,
        'warn' : logging.WARN,
        'error' : logging.ERROR
        }

    __logger=None
    
    def __init__(self, conf):
        print('>> Begin initialization of Logging object.')
        
        #baseDir = os.getcwd()
        baseDir = conf.base_dir
        osNm = os.name
        cfgFile=None
        print(baseDir)
        if osNm.upper() == "NT":
            cfgFile = baseDir+"\\resource\\loggingConfig.json"
        elif osNm.upper() == "POSIX":
            cfgFile = baseDir+"/resource/loggingConfig.json"
        else:
            cfgFile = baseDir+"/resource/loggingConfig.json"

        #print(cfgFile)
                    
        with open(cfgFile, "rt", encoding="utf-8") as file:
            logConf = json.load(file)
        
        
        logConf['handlers']['file_debug']['filename'] = conf.logs_dir+"ulalaLAB_WICON-L_DEBUG.log"
        logConf['handlers']['file_error']['filename'] = conf.logs_dir+"ulalaLAB_WICON-L_ERROR.log"

        logging.config.dictConfig(logConf)
        
        now = datetime.now()
        strDateTime = now.strftime("%H%M%S%f")
        self.__logger = logging.getLogger(conf.app_name+"_"+strDateTime)
        
        print(">> Done initialization of Logging object. logger : ["+conf.app_name+"_"+strDateTime+"]")
        
    
    @staticmethod
    def debug(self, msg):
        self.__logger.debug(msg)
    
    
    @staticmethod
    def info(self, msg):
        self.__logger.info(msg)
    
    
    @staticmethod
    def warn(self, msg):
        self.__logger.warn(msg)
    
    
    @staticmethod
    def error(self, msg):
        self.__logger.error(msg)
    

    @property
    def logger(self):
        return self.__logger


    # setter
    @logger.setter
    def logger(self, value):
        self.__logger = value
