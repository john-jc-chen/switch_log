import serial_rx_tx
import time
import sys
import os
import subprocess
import _thread
import re

logFile = None
write_able = False

username = "ADMIN"
passwd = "ADMIN"
comport = "COM1"
baudrate = "9600"
serial_number = ''
CMM_username = "ADMIN"
CMM_passwd = "ADMIN"

f = open(sys.argv[1], 'r')
of = open("command_log.txt", 'w')
commands = f.readlines()

while True:
    if commands[0].startswith("User Name:"):
        username = commands[0][10:].rstrip()
        #print(username)
        commands.pop(0)
    elif commands[0].startswith("Password:"):
        passwd = commands[0][9:].rstrip()
        #print(passwd)
        commands.pop(0)
    elif commands[0].startswith("COM Port:"):
        comport = commands[0][9:].rstrip()
        #print(comport)
        commands.pop(0)
    elif commands[0].startswith("Baud Rate:"):
        baudrate = commands[0][10:].rstrip()
        #print(baudrate)
        commands.pop(0)
    elif commands[0].startswith("*****Commands Start From Here*****"):
        commands.pop(0)
        break
    else:
        commands.pop(0)

serialPort = serial_rx_tx.SerialPort()

def OnReceiveSerialData(message):
    global write_able
    global of
    global serial_number
    #print(message)
    if b'\x1b[100B\r\x1b[K\r--More--\x1b[K\x1b\r                \r\x1b[K' in message:
        message = message[44:]
    if message[:5] == b'\x1b[27m':
        message =  message[6:]
    str_message = message.decode("utf-8").rstrip()
    #str_message = str_message.lstrip(chr(27))
    if str_message.endswith("SMIS#"):
        write_able = True
    print(str_message)
    of.write(str_message + "\n")
    m = re.findall(r"Serial\s+Number\s+\:\s?(\w+)", str_message)

    if m:
        serial_number = m[0]

def OpenCommand():
    global comport
    global baudrate
    #comport = "COM5"
    #baudrate = "9600"
    serialPort.Open(comport,baudrate)
    print("COM Port Opened\r\n")

def login(username, passwd):
    serialPort.Send("")
    time.sleep(1.0)
    username += "\r"
    serialPort.serialport.write(username.encode("utf-8"))
    time.sleep(1.0)
    passwd += "\r"
    serialPort.serialport.write(passwd.encode("utf-8"))
    time.sleep(1.0)
    #data = serialPort.serialport.read(serialPort.serialport.inWaiting())
    #print(data)

def logout():
    str = "exit\r"
    serialPort.serialport.write(str.encode("utf-8"))
    time.sleep(1.0)

def writeCommand(command):
    serialPort.Send(command)
    time.sleep(1.0)

OpenCommand()
if serialPort.IsOpen():
    login(username, passwd)
    serialPort.RegisterReceiveCallback(OnReceiveSerialData)
    time.sleep(2.0)
    serialPort.Send("")
    for command in commands:
        print(command)
        while not write_able:
            serialPort.Send("")
            time.sleep(1.0)
        command = command.rstrip()
        serialPort.Send(command)
        #for c in command:
        #   serialPort.serialport.write(c.encode("utf-8"))
        write_able = False

    #serialPort.serialport.write("\r".encode("utf-8"))
    #input()
    """
    while True:
        command = input()
        if command == 'exit':
            serialPort.Close()
            break
        command = command.rstrip() + "\r"
        serialPort.serialport.write(command.encode("utf-8"))
    """
    #while serialPort.serialport.inWaiting() > 0:
    #   pass

    logout()
    #thread.exit()

else:
    print("Not sent - COM port is closed\r\n")
of.close()
#serialPort.Close()
file_name = serial_number + '.log'
os.system("rename command_log.txt " + file_name)
