import serial_rx_tx
import time
import sys
import os
import subprocess
import _thread
import re
from datetime import datetime

logFile = None
writeable = False
bootmenu = False

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
        ary = commands[0].split(":")
        if len(ary) == 2:
            username = ary[1].rstrip()
        #print(username)
        commands.pop(0)
    elif commands[0].startswith("Password:"):
        ary = commands[0].split(":")
        if len(ary) == 2:
            passwd = ary[1].rstrip()
        #print(passwd)
        commands.pop(0)
    elif commands[0].startswith("COM Port:"):
        ary = commands[0].split(":")
        if len(ary) == 2:
            comport = ary[1].rstrip()
        #print(comport)
        commands.pop(0)
    elif commands[0].startswith("Baud Rate:"):
        ary = commands[0].split(":")
        if len(ary) == 2:
            baudrate = ary[1].rstrip()
        #print(baudrate)
        commands.pop(0)
    # elif commands[0].startswith("IP:"):
    #     IP = commands[0][3:].rstrip()
    #     #print(baudrate)
    #     commands.pop(0)
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
    global bootmenu

    #print(message)
    if b'\x1b[100B\r\x1b[K\r--More--\x1b[K\x1b\r                \r\x1b[K' in message:
        message = message[44:]
        serialPort.serialport.write(" ".encode('utf-8'))
    if message[:5] == b'\x1b[27m':
        message =  message[6:]
    str_message = message.decode("utf-8", errors='ignore').rstrip().lstrip()
    #str_message = str_message.lstrip(chr(27))
    print(str_message)
    if str_message.endswith("SMIS#"):
        if login_f == True:
            writeable = True
            next_command = True
        login_f = True
    # if "Incorrect Login/Password"in str_message:
    #     login_f = False
    # elif "login:" in str_message:
    #     login_f = True

    # if "Active  CMM1(2)" in message:
    #     serialPort.serialport.write(" ".encode('utf-8'))
    #     bootmenu = True
    #print(str_message)
    if  of and writeable and str_message != "SMIS#" and str_message != "":
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
    print("Connecting to {}".format(comport))
    serialPort.Open(comport,baudrate)
    print("COM Port Opened\r\n")

def login(username, passwd,serialPort):
    username += "\r"
    serialPort.serialport.write(username.encode("utf-8"))
    time.sleep(0.5)
    data = serialPort.serialport.readline().decode("utf-8", errors='ignore')
    print(data)
    passwd += "\r"
    serialPort.serialport.write(passwd.encode("utf-8"))
    time.sleep(1.0)
    data = serialPort.serialport.read(serialPort.serialport.in_waiting).decode("utf-8", errors='ignore')
    print(data)
    if "SMIS#" not in data:
        passwd =  passwd.rstrip()
        print("Failed to login with the password \"" + passwd + "\"\n Leave scrip!!!")
        serialPort.Close()
        try:
            del serialPort
            sys.exit()
        except Exception as e:
            print(str(e))



def logout():
    str = "exit\r"
    serialPort.serialport.write(str.encode("utf-8",errors='ignore'))
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
        print('bootmenu')
        if serialPort.serialport.in_waiting > 0:
            message = serialPort.serialport.readline().decode("utf-8",errors='ignore')
            message = message.rstrip()
            print(message)
            if " MBM-XEM-002 Boot Menu " in message:
                serialPort.serialport.write("".encode('utf-8'))
                break
OpenCommand()
if serialPort.IsOpen():
    #bootmenue()
    # while not bootmenu:
    #     pass
    # bootmenu = False
    # SetNetwork(IP)
    serialPort.Send("")
    serialPort.Send("")
    while not login_f:
        message = serialPort.serialport.readline().decode("utf-8",errors='ignore')
        print(message)
        if "login:" in message:
            login_f = True
            login(username, passwd,serialPort)
            break
        elif "Supermicro Switch" in message:
            serialPort.Send("")
        elif "SMIS#"  in message:
            login_f = True
            break
        time.sleep(0.1)

    serialPort.RegisterReceiveCallback(OnReceiveSerialData)
    of.write(datetime.now().strftime("%m-%d-%Y %H:%M:%S") + "\n")
    serialPort.Send("")
    for command in commands:
        command = re.sub(r'\#.*$','',command).rstrip()
        if command == '':
            continue
        while not next_command:
            serialPort.Send("")
            time.sleep(1.0)
        #print(command)
        command = command.rstrip()
        next_command = False
        serialPort.Send(command)
        time.sleep(0.5)
        #for c in command:
        #   serialPort.serialport.write(c.encode("utf-8",errors='ignore'))
        of.write("\n")
    #serialPort.serialport.write("\r".encode("utf-8",errors='ignore'))
    #input()
    # while serialPort.serialport.inWaiting() > 0:
    #     pass
    # writeable = False
    serialPort.Send("")
    while not next_command:
        time.sleep(2.0) #wait for the last command to finish
        serialPort.Send("")
        # print("in loop", next_command)
    time.sleep(2.0)
    of.close()
    serialPort.serialport.write("exit".encode('utf-8'))
    #serialPort.Close()
    file_name = serial_number + '.log'

    if os.name == 'posix':
        log_dir = os.getcwd() + '/log'
    else:
        log_dir = os.getcwd() + "\\log"
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    if os.name == 'posix':
        file_name =log_dir + '/' + file_name
        os.system("mv command_log.txt " + file_name)
    else:
        file_name =log_dir + "\\" + file_name
        os.system("copy command_log.txt " + file_name)
    # bootmenu = False
    # serialPort.serialport.write("reload\r".encode('utf-8'))
    #serialPort.Send("reload")
    #serialPort.serialport.write("y".encode('utf-8'))
    # serialPort.Send_raw("y")
    # while not bootmenu:
    #     pass
    #SetNetwork('192.168.100.102')
    # serialPort.Send("")
    #logout()
    #reset()
    #thread.exit()
else:
    print("Not sent - COM port is closed\r\n")

