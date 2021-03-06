#

# Serial COM Port receive message event handler

# 8/17/2017, Dale Gambill

# When a line of text arrives from the COM port terminated by a \n character, this module will pass the message to

# the function specified by the instantiator of this class.

#

import serial
import sys
import _thread

class SerialPort:
    def __init__(self):
        self.comportName = ""
        self.baud = 0
        self.timeout = 3
        self.ReceiveCallback = None
        self.isopen = False
        self.receivedMessage = None
        self.serialport = serial.Serial()

    def __del__(self):
        try:
            if self.IsOpen():
                self.serialport.close()
        except:
            print("Destructor error closing COM port: ", sys.exc_info()[1] )



    def RegisterReceiveCallback(self,aReceiveCallback):
        self.ReceiveCallback = aReceiveCallback
        try:
            _thread.start_new_thread(self.SerialReadlineThread, ())
        except:
            print("Error starting Read thread: ", sys.exc_info()[0])

    def SerialReadlineThread(self):
        while True:
            #try:
            if self.isopen:
                if self.serialport.in_waiting > 0:
                    self.receivedMessage = None
                    self.receivedMessage = self.serialport.readline()
                #print(self.receivedMessage)
                #input()
                    if self.receivedMessage:
                    #print(self.receivedMessage)
                    #if self.receivedMessage.startswith('\rSMIS# '):
                    #   write_able = True

                        self.ReceiveCallback(self.receivedMessage)
            # except Exception as e:
            #     print("Error reading COM port: ", str(e))

    def IsOpen(self):
        return self.isopen

    def Open(self,portname,baudrate):
        if not self.isopen:
            # serialPort = 'portname', baudrate, bytesize = 8, parity = 'N', stopbits = 1, timeout = None, xonxoff = 0, rtscts = 0)
            self.serialport.port = portname
            self.serialport.baudrate = baudrate

            try:
                self.serialport.open()
                self.isopen = True

            except:
                print("Error opening COM port: ", sys.exc_info()[1])

    def Close(self):
        if self.isopen:
            try:
                self.serialport.close()
                self.isopen = False
            except:

                print("Close error closing COM port: ", sys.exc_info()[0])

    def Send(self,message):

        if self.isopen:
            try:
                # Ensure that the end of the message has both \r and \n, not just one or the other
                newmessage = message.strip()
                newmessage += '\r\n'
                self.serialport.write(newmessage.encode('utf-8'))
            except:
                print("Error sending message: ", sys.exc_info()[0] )

            else:
                return True
        else:
            return False
    def Send_raw(self,message):
        if self.isopen:
            try:
                self.serialport.write(message.encode('utf-8'))
            except:
                print("Error sending raw message: ", sys.exc_info()[0] )
            else:
                return True
        else:
            return False

