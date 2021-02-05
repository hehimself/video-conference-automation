import serial

try:
    s = serial.Serial('COM6')
except serial.serialutil.SerialException:
    exit("Serieller Port nicht angeschlossen")

try:
    while True:
        serial_message = s.readline()
        decoded_bytes = float(serial_message[0:len(serial_message)-2].decode("utf-8"))
        print(decoded_bytes)
        if decoded_bytes > 21:
            print("Hot")
except KeyboardInterrupt:
    s.close()
    exit("Ende")