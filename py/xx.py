import OPi.GPIO as GPIO
import time
import serial
from RPLCD.i2c import CharLCD


#SETUP
GPIO.setmode(GPIO.SUNXI)
GPIO.setwarnings(False)
GPIO.setup("PI3", GPIO.OUT)
GPIO.setup("PI4", GPIO.OUT)


# Open the first time
# Open the first time
while True:
    try:
            print("Detected HIGH signal")
            # Main task
            GPIO.output("PI3", GPIO.HIGH)
            print("GPIO ON")
            time.sleep(1)
            GPIO.output("PI3", GPIO.LOW)
            print("GPIO OFF")
            time.sleep(1)
            GPIO.output("PI4", GPIO.HIGH)
            time.sleep(1)
            GPIO.output("PI4", GPIO.LOW)
            time.sleep(1)


    except KeyboardInterrupt:
        print("Interrupted by user")
        GPIO.cleanup()
        break

