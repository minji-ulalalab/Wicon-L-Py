'''
Created on 2021. 12. 04.

@author: sg.an
'''
from common.exceptions.dataException import DataException
from common.exceptions.systemException import SystemException


class ExceptionHandler():
    logger = None
    def __init__(self, logger):
        self.logger = logger
        pass
      
        
    def dataError(self, message):
        tmpMsg = "The stored data has a problem. Ask to Data Administrator.\n"
        tmpMsg += message
        ExceptionHandler.errorLogging(self, tmpMsg)
        raise DataException (message)
 
    
    def systemError(self, message):
        tmpMsg = "The system has a problem. Ask to System Administrator.\n"
        tmpMsg += message
        ExceptionHandler.errorLogging(self, tmpMsg)
        raise SystemException (message)

            
    def errorLogging(self, message):
        self.logger.error(message)
        #raise Exception (message)
