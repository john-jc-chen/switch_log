import serial_rx_tx
import time
import sys
import os
import subprocess
import _thread
import re

logFile = None
writeable = False

username = "ADMIN"
passwd = "ADMIN"
comport = "COM1"
baudrate = "9600"
serial_number = ''
CMM_username = "ADMIN"
CMM_passwd = "ADMIN"
IP = ''
boot_menu = False
login_f = False
next_command = False

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
    elif commands[0].startswith("IP:"):
        IP = commands[0][3:].rstrip()
        #print(baudrate)
        commands.pop(0)
    elif commands[0].startswith("*****Commands Start From Here*****"):
        commands.pop(0)
        break
    else:
        commands.pop(0)

serialPort = serial_rx_tx.SerialPort()

def OnReceiveSerialData(message):
    global writeable
    global of
    global serial_number
    global login_f
    global next_command

    #print(message)
    if b'\x1b[100B\r\x1b[K\r--More--\x1b[K\x1b\r                \r\x1b[K' in message:
        message = message[44:]
    if message[:5] == b'\x1b[27m':
        message =  message[6:]
    str_message = message.decode("utf-8").rstrip().lstrip()
    #str_message = str_message.lstrip(chr(27))
    if str_message.endswith("SMIS#") and login_f:
        writeable = True
        next_command = True
    if " Supermicro Switch" in message:
        login_f = True

    print(str_message)
    if writeable and str_message != "SMIS#" and str_message != "":
        of.write(str_message + "\n")
    m = re.findall(r"Switch Serial\s+Number\s+\:\s?(\w+)", str_message)
    if m:
        serial_number = str(m[0])
        #print(m, serial_number,  str_message)
def reset():
    serial_number = ''
    login_f = False
    next_command = False


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

def SetNetwork(IP):
    serialPort.Send_raw('q')
    time.sleep(1.0)
    backspace = bytearray([8 for i in range(16)])
    serialPort.serialport.write(backspace)
    time.sleep(1.0)
    serialPort.Send(IP)
    time.sleep(1.0)
    serialPort.Send("")
    time.sleep(1.0)
    serialPort.Send("")
    time.sleep(1.0)
    serialPort.Send("")
    time.sleep(1.0)
    serialPort.Send("y")
    time.sleep(1.0)
def bootmenue():
    while True:
        time.sleep(1.0)
        if serialPort.serialport.in_waiting > 0:
            message = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8")
            message = message.rstrip()
            print(message)
            if " MBM-XEM-002 Boot Menu " in message:
                serialPort.serialport.write(" ".encode('utf-8'))
                break
OpenCommand()
if serialPort.IsOpen():
    bootmenue()
    serialPort.RegisterReceiveCallback(OnReceiveSerialData)
    #time.sleep(1.0)
    SetNetwork(IP)
    serialPort.Send("")

    while not login_f:
        time.sleep(2.0)
        #print('login',login_f)
    serialPort.Send("")
    login(username, passwd)
    of.write(time.strftime("%m-%d-%Y %H:%M:%S", time.gmtime()))
    serialPort.Send("")
    for command in commands:
        command = re.sub(r'\#.*$','',command).rstrip()
        if command == '':
            continue
        while not next_command:
            serialPort.Send("")
            time.sleep(1.0)
        print(command)
        command = command.rstrip()
        serialPort.Send(command)
        #for c in command:
        #   serialPort.serialport.write(c.encode("utf-8"))
        of.write("\n")
        next_command = False
    #serialPort.serialport.write("\r".encode("utf-8"))
    #input()
    #while serialPort.serialport.inWaiting() > 0:
#   pass
    while not next_command:
        pass
    serialPort.Send("reload")
    time.sleep(2.0)
    print("y")
    serialPort.serialport.write("y".encode('utf-8'))
    time.sleep(1.0)
    print("y")
    serialPort.serialport.write("y".encode('utf-8'))
    time.sleep(1.0)
    print("y")
    serialPort.serialport.write("y\n".encode('utf-8'))
    print("before fun")
    bootmenue()
    serialPort.serialport.write("r".encode('utf-8'))
    #logout()
    #reset()
    #thread.exit()
else:
    print("Not sent - COM port is closed\r\n")
of.close()
#serialPort.Close()
file_name = serial_number + '.log'
#print("mv command_log.txt " + file_name)
os.system("mv command_log.txt " + file_name)
