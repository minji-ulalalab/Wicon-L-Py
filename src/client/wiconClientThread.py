
'''
Created on 2022. 02. 05.

@author: sg.an
'''
import traceback, time
from client.wiconClientFunction import WiconClientFunction
from enum import Enum

class WICON_CLIENT_STATE(Enum):
    INIT_SOCKET = 0
    SET_SERVER = 1
    CONNECT_SERVER = 2
    TRANSFER_INIT_MSG = 3
    CHECK_BACKUP_DATA = 4
    SEND_NORMAL_DATA_TO_WIMX = 5
    SEND_BACKUP_DATA_TO_WIMX = 6
    RESEND_DATA_TO_WIMX = 7
    WAIT = 8

class WiconClientThread:
    conf = None
    exh = None
    logger = None
    _period = None
    _wimx_msg = None
    _led_instance = None
    _second_socket = False

    ## 생성자
    def __init__(self, resources, led):
        self._resources = resources
        self.conf = resources["conf"]
        self.exh = resources["exh"]
        self.logger = resources["logger"]
        self._period = self.conf.period
        self._led_instance = led
             
    def run(self, normal_queue, backup_queue):
        try:
            wicon_client_function = WiconClientFunction(self._resources)
            if( (self.conf.sensor == "I2C") and (self.conf.i2c_mode == "IR_TEMP") and (self.conf.ir_temp_data_mode == "WHOLE") ):
                self.logger.debug("WHOLE MODE : SECOND CLIENT")
                print("WHOLE MODE : SECOND CLIENT")
                second_client_function = WiconClientFunction(self._resources)
                self._second_socket = True
                self.run_wimx_client_state_machine(wicon_client_function, normal_queue, backup_queue, second_client_function)
            else:
                self.run_wimx_client_state_machine(wicon_client_function, normal_queue, backup_queue)
        except Exception as ex:
            self.logger.error(ex)

    def run_wimx_client_state_machine(self, client_function, normal_queue, backup_queue, second_client = None):
        self.logger.debug("Run the wim-x client thread.\n")
        print("Run the wim-x client thread.\n")
        retry_flag = False
        
        self._state = WICON_CLIENT_STATE.INIT_SOCKET
        while True:
            if(self._state == WICON_CLIENT_STATE.INIT_SOCKET):
                self.logger.debug("WICON_CLIENT_STATE.INIT_SOCKET\n")
                print("WICON_CLIENT_STATE.INIT_SOCKET\n")
                ret = client_function.wicon_client_function_init_socket()
                if(ret <= 0):
                    self._state = WICON_CLIENT_STATE.SET_SERVER
                    if(self._second_socket == True):
                        ret = second_client.wicon_client_function_init_socket()
                        
            elif(self._state == WICON_CLIENT_STATE.SET_SERVER):
                self.logger.debug("WICON_CLIENT_STATE.SET_SERVER\n")
                print("WICON_CLIENT_STATE.SET_SERVER\n")

                # server url dns query and get ip address
                server_url = self.conf.server_url
                server_port = self.conf.server_port
                ret_url = client_function.wicon_client_function_set_server(server_url, server_port)

                # if get ip address success, try to connect wim-x server
                if(ret_url != -1):
                    ret_con = client_function.wicon_client_function_connect_server(ret_url)
                    if(ret_con != -1):# if connect wim-x server success, change state
                        if(self._second_socket == True):
                            second_client.wicon_client_function_connect_server(ret_url)
                        self._state = WICON_CLIENT_STATE.CHECK_BACKUP_DATA
                        self._led_instance.green_led_on_off(1)
                    else:
                        self._state = WICON_CLIENT_STATE.WAIT
                else: # if get ip address fail, go to wait state and wait 1s
                    self._state = WICON_CLIENT_STATE.WAIT

            elif(self._state == WICON_CLIENT_STATE.CHECK_BACKUP_DATA):

                if(backup_queue.empty()):
                    print("there is no backup data.\n")
                    self.logger.debug("there is no backup data.\n")
                    if(retry_flag == False):
                        self._state = WICON_CLIENT_STATE.SEND_NORMAL_DATA_TO_WIMX
                    else:
                        self._state = WICON_CLIENT_STATE.RESEND_DATA_TO_WIMX
                else:
                    print("there is backup data.\n")
                    self.logger.debug("there is backup data.\n")
                    self._state = WICON_CLIENT_STATE.SEND_BACKUP_DATA_TO_WIMX

            elif(self._state == WICON_CLIENT_STATE.SEND_NORMAL_DATA_TO_WIMX):
                self.logger.debug("WICON_CLIENT_STATE.SEND_NORMAL_DATA_TO_WIMX\n")
                print("WICON_CLIENT_STATE.SEND_NORMAL_DATA_TO_WIMX\n")
                
                #while True:
                if(normal_queue.empty()):
                    self.logger.debug("normal_queue is empty.")
                    time.sleep(self._period)
                    self._state = WICON_CLIENT_STATE.CHECK_BACKUP_DATA
                    #break
                    
                else:
                    ret_send = -1
                    ret_recv = -1
                    self._wimx_msg = normal_queue.get()
                    print(self._wimx_msg)
                    start_time = time.time()
                    if(self._second_socket == True):
                        msg = self._wimx_msg.split('|')
                        #print("second socket")
                        #print(msg[0])
                        #print(msg[1])
                        ret_send = client_function.wicon_client_function_send_data(msg[0])
                        ret_send = second_client.wicon_client_function_send_data(msg[1])
                    else :
                        ret_send = client_function.wicon_client_function_send_data(self._wimx_msg)
                    if(ret_send == 0):
                        self._led_instance.green_led_on_off(1)
                        ret_recv = client_function.wicon_client_function_recv_ack()
                    time.sleep(0.2)
                    self._led_instance.green_led_on_off(0)
                    end_time = time.time()

                    if(ret_send == 0 and ret_recv == 0):
                        retry_flag = False
                        period = self._period - (end_time - start_time)
                        print("process time : %f" % (end_time - start_time))
                        print("period : %f" % period)
                        if(period > 0):
                            self.logger.debug("period over! : %f" % period)
                            #time.sleep(self._period)
                        self._state = WICON_CLIENT_STATE.CHECK_BACKUP_DATA

                    else:
                        self._state = WICON_CLIENT_STATE.RESEND_DATA_TO_WIMX
                
                        
            elif(self._state == WICON_CLIENT_STATE.RESEND_DATA_TO_WIMX):
                self.logger.debug("WICON_CLIENT_STATE.RESEND_DATA_TO_WIMX\n")
                print("WICON_CLIENT_STATE.RESEND_DATA_TO_WIMX\n")

                retry_count = 3
                while retry_count > 0:
                    if(self._second_socket == True):
                        msg = self._wimx_msg.split('|')
                        #print("second socket")
                        #print(msg[0])
                        #print(msg[1])
                        ret_send = client_function.wicon_client_function_send_data(msg[0])
                        ret_send = second_client.wicon_client_function_send_data(msg[1])
                    else :
                        ret_send = client_function.wicon_client_function_send_data(self._wimx_msg)
                    if(ret_send == 0):
                        self._led_instance.green_led_on_off(1)
                        ret_recv = client_function.wicon_client_function_recv_ack()
                        self._led_instance.green_led_on_off(0)
                        if(ret_recv == 0):
                            break
                    retry_count -= 1
                if(retry_count <= 0):
                    self._state = WICON_CLIENT_STATE.INIT_SOCKET
                    retry_flag = True
                else:
                    self._state = WICON_CLIENT_STATE.CHECK_BACKUP_DATA
                    retry_flag = False

            elif(self._state == WICON_CLIENT_STATE.SEND_BACKUP_DATA_TO_WIMX):
                self.logger.debug("WICON_CLIENT_STATE.SEND_BACKUP_DATA_TO_WIMX\n")
                print("WICON_CLIENT_STATE.SEND_BACKUP_DATA_TO_WIMX\n")
                
                #while True:
                if(backup_queue.empty()):
                    time.sleep(self._period)
                    self.logger.debug("backup_queue is empty.")
                    self._state = WICON_CLIENT_STATE.CHECK_BACKUP_DATA
                    #break
                    
                else:
                    ret_send = -1
                    ret_recv = -1
                    self._wimx_msg = backup_queue.get()
                    print(self._wimx_msg)
                    start_time = time.time()
                    if(self._second_socket == True):
                        msg = self._wimx_msg.split('|')
                        #print("second socket")
                        #print(msg[0])
                        #print(msg[1])
                        ret_send = client_function.wicon_client_function_send_data(msg[0])
                        ret_send = second_client.wicon_client_function_send_data(msg[1])
                    else :
                        ret_send = client_function.wicon_client_function_send_data(self._wimx_msg)
                    if(ret_send == 0):
                        self._led_instance.green_led_on_off(1)
                        ret_recv = client_function.wicon_client_function_recv_ack()
                    time.sleep(0.2)
                    self._led_instance.green_led_on_off(0)
                    end_time = time.time()

                    if(ret_send == 0 and ret_recv == 0):
                        retry_flag = False
                        period = self._period - (end_time - start_time)
                        print("process time : %f" % (end_time - start_time))
                        print("period : %f" % period)
                        if(period > 0):
                            self.logger.debug("period over! : %f" % period)
                            #time.sleep(self._period)
                        self._state = WICON_CLIENT_STATE.CHECK_BACKUP_DATA

                    else:
                        self._state = WICON_CLIENT_STATE.RESEND_DATA_TO_WIMX

            elif(self._state == WICON_CLIENT_STATE.WAIT):
                time.sleep(self._period)
                self._state = WICON_CLIENT_STATE.INIT_SOCKET
            else:
                pass
 