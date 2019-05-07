import serial

serialConnection = None
def openSerial(port, baudrate):
    global serialConnection
    serialConnection = serial.Serial(port, baudrate)
    print(serialConnection.name)
    print(serialConnection.is_open)

def getSerialConnection():
    global serialConnection
    return serialConnection

def closeSerialConnection():
    global serialConnection
    serialConnection.close()
