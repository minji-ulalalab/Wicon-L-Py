'''
Created on 2022. 02. 05.

@author: sg.an
'''
import traceback, socket


class WiconClientFunction:
    conf = None
    exh = None
    logger = None
    _wicon_socket = 0
    
    ## 생성자
    def __init__(self, resources):
        self._resources = resources
        self.conf = resources["conf"]
        self.exh = resources["exh"]
        self.logger = resources["logger"]
             
    def wicon_client_function_init_socket(self):
        try :
            ret = -1
            if(self._wicon_socket != 0):
                self._wicon_socket = 0
            
            self._wicon_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._wicon_socket.settimeout(0.5)
            ret = 0
        except Exception as ex:
            self.exh.systemError(traceback.format_exc())
            ret = -1
        finally :
            return ret

    def wicon_client_function_set_server(self, server_url, server_port):
        try :
            ret = -1
            host = socket.gethostbyname(server_url)
            url = (host, server_port)
            ret = url
        except Exception as ex:
            self.exh.systemError(traceback.format_exc())
            ret = -1
        finally :
            return ret

    def wicon_client_function_connect_server(self, url):
        try :
            ret = -1
            self._wicon_socket.connect(url)
            ret = 0
        except Exception as ex:
            self.exh.systemError(traceback.format_exc())
            ret = -1
        finally :
            return ret

    def wicon_client_function_recv_ack(self):
        try :
            ret = -1
            ack = self._wicon_socket.recv(1024)
            print("%s" %(ack))
            ret = 0
        except Exception as ex:
            self.exh.systemError(traceback.format_exc())
            ret = -1
        finally :
            return ret

    def wicon_client_function_send_data(self, msg):
        try :
            ret = -1
            self._wicon_socket.send(msg.encode('utf-8'))
            print("%s" %(msg))
            ret = 0
        except Exception as ex:
            self.exh.systemError(traceback.format_exc())
            ret = -1
        finally :
            return ret
 