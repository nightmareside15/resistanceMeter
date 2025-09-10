import serial
import time

def open_serial():
    while True:
        try:
            ser = serial.Serial(
                port="/dev/ttyUSB0",       # Change if needed
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                writeTimeout=2
            )
            if ser.is_open:
                print("Serial connected")
                return ser
        except serial.SerialException as e:
            print(f"Waiting for serial: {e}")
            time.sleep(2)

ser = open_serial()

try:
    while True:
        # Send the SCPI command for resistance
        ser.write(b"MEAS:RES?\r\n")
        time.sleep(0.5)  # Give GDM-8342 some time to respond

        response = ser.readline().decode().strip()
        print(f"Resistance: {response} Ohms")

        time.sleep(1)  # Adjust delay as needed

except KeyboardInterrupt:
    print("User interrupted")

finally:
    if ser.is_open:
        ser.close()

