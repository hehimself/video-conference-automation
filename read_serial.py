import serial
s = serial.Serial('COM6')
try:
    while True:
        x = s.readline()
        decoded_bytes = float(x[0:len(x)-2].decode("utf-8"))
        print(decoded_bytes)
        if decoded_bytes > 21:
            print("Hot")
except KeyboardInterrupt:
    exit("Ende")