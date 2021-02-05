import serial
s = serial.Serial('COM6')
try:
    while True:
        x = s.readline()
        decoded_bytes = float(x[0:len(x)-2].decode("utf-8"))
        print(decoded_bytes)
except KeyboardInterrupt:
    exit("Ende")