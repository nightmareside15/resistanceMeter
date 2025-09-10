import OPi.GPIO as GPIO
import time
import serial

GPIO.setmode(GPIO.SUNXI)
GPIO.setwarnings(False)
GPIO.setup("PI1", GPIO.OUT)
GPIO.setup("PH4", GPIO.IN)




def open_serial():
    while True:
        try:
            ser = serial.Serial(
                port="/dev/ttyUSB0",
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

# Open the first time
ser = open_serial()
    while True:
        try:
        print("LCD IS HERE");
        if GPIO.input("PH4") == GPIO.HIGH:
            print("Detected HIGH signal")
            # Main task
            ser.write(b'hello')
            print("Sent data")
            GPIO.output("PI1", GPIO.HIGH)
            print("GPIO ON")
            time.sleep(1)
            GPIO.output("PI1", GPIO.LOW)
            print("GPIO OFF")
            time.sleep(1)

        except (serial.SerialException, OSError) as e:
            print(f"[!] Serial disconnected: {e}")
            try:
                ser.close()
            except:
                pass
            ser = open_serial()  # Reconnect automatically

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    if ser.is_open:
        ser.close()
    GPIO.cleanup()

