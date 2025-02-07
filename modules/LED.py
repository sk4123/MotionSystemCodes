import serial
import time
import numpy as np

class LED:
    def __init__(self, port):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baud_rate = 9600
        self.ser.timeout = None
        self.command = ""
    
    def connect(self):
        self.ser.open()
        self.__EnableDrivers()
        self.__setPWMFreq(1)
        
    def close(self):
        self.__CloseAllLedsDisableDrivers()
        self.ser.close()

    def ExecuteCommandBuffer(self, command):
        if command is not None:
            self.ser.write(command)
            print('command is sent : '+ command.decode('ascii'))
            try:
                time.sleep(0.01)
                get_command = self.ser.read_until(b'\r')
                print('command received from Data:'+get_command.decode('ascii'))
            except Exception as e:
                print('None Read. Exception:' + str(e))
        else:
            print('No Command is sent')

    def ReadLine(self):
            return_byte_array = self.ser.readline()
            #print(return_byte_array)
            return return_byte_array.decode('ascii')
    
    def __EnableDrivers(self):
        self.ExecuteCommandBuffer(b'\x15\x01')
        self.ExecuteCommandBuffer(b'\x16\x01')
        self.ExecuteCommandBuffer(b'\x17\x01')
        self.ExecuteCommandBuffer(b'\x18\x01')

    def __CloseAllLedsDisableDrivers(self):
        #Close LEDs
        self.ExecuteCommandBuffer(b'\x0B\x00')
        self.ExecuteCommandBuffer(b'\x0C\x00')
        self.ExecuteCommandBuffer(b'\x0D\x00')
        self.ExecuteCommandBuffer(b'\x0E\x00')
        self.ExecuteCommandBuffer(b'\x1E\x01')
        # self.ExecuteCommandBuffer(b'\x1F\x00')
        # self.ExecuteCommandBuffer(b'\x20\x00')
        # self.ExecuteCommandBuffer(b'\x21\x00')
        # self.ExecuteCommandBuffer(b'\x22\x00')
        #Close Drivers
        self.ExecuteCommandBuffer(b'\x15\x00')
        self.ExecuteCommandBuffer(b'\x16\x00')
        self.ExecuteCommandBuffer(b'\x17\x00')
        self.ExecuteCommandBuffer(b'\x18\x00')

    def __setPWMFreq(self, pwdFreqPer):
        second_byte = bytes([int(64*pwdFreqPer)])
        self.ExecuteCommandBuffer(b'\x05'+ second_byte)

    def turnOnLED(self, LED, brightness):
        if LED == 1:
            second_byte = bytes([int(64*brightness)])
            self.ExecuteCommandBuffer(b'\x0B'+ second_byte)
            self.ExecuteCommandBuffer(b'\x1F\x01')
        elif LED == 2:
            second_byte = bytes([int(64*brightness)])
            self.ExecuteCommandBuffer(b'\x0C'+ second_byte)
            self.ExecuteCommandBuffer(b'\x20\x01')
        elif LED == 3:
            second_byte = bytes([int(64*brightness)])
            self.ExecuteCommandBuffer(b'\x0D'+ second_byte)
            self.ExecuteCommandBuffer(b'\x21\x01')
        elif LED == 4:
            second_byte = bytes([int(64*brightness)])
            self.ExecuteCommandBuffer(b'\x0E'+ second_byte)
            self.ExecuteCommandBuffer(b'\x22\x01')
        else:
            print('Input a valid LED')
            return False

    def turnOffLED(self, LED):
        if LED == 1:
            self.ExecuteCommandBuffer(b'\x0B\x00')
            self.ExecuteCommandBuffer(b'\x1F\x00')
        elif LED == 2:
            self.ExecuteCommandBuffer(b'\x0C\x00')
            self.ExecuteCommandBuffer(b'\x20\x00')
        elif LED == 3:
            self.ExecuteCommandBuffer(b'\x0D\x00')
            self.ExecuteCommandBuffer(b'\x21\x00')
        elif LED == 4:
            self.ExecuteCommandBuffer(b'\x0E\x00')
            self.ExecuteCommandBuffer(b'\x22\x00')
        else:
            print('Input a valid LED')
            return False
    
    def turnOffAllLEDs(self):
        self.ExecuteCommandBuffer(b'\x0B\x00')
        self.ExecuteCommandBuffer(b'\x1F\x00')
        self.ExecuteCommandBuffer(b'\x0C\x00')
        self.ExecuteCommandBuffer(b'\x20\x00')
        self.ExecuteCommandBuffer(b'\x0D\x00')
        self.ExecuteCommandBuffer(b'\x21\x00')
        self.ExecuteCommandBuffer(b'\x0E\x00')
        self.ExecuteCommandBuffer(b'\x22\x00')
