import OPi.GPIO as GPIO
import time
import serial
from RPLCD.i2c import CharLCD


#SETUP
GPIO.setmode(GPIO.SUNXI)
GPIO.setwarnings(False)
GPIO.setup("PI3", GPIO.IN) #start  button
GPIO.setup("PI2", GPIO.OUT) # on/off lamp relay
GPIO.setup("PI16", GPIO.OUT) #  lamp selection. HIGH = OK (GREEN), LOW = NG (RED + BUZZER)

lcd = CharLCD(i2c_expander='PCF8574',
        address = 0x27,
        port=3,
        cols=20, rows=4)

#turn off all relay
GPIO.output("PI2", GPIO.LOW)
GPIO.output("PI16", GPIO.LOW)



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
                lcd.clear()
                lcd.write_string('  CONNECTED  ')
                print("Serial connected")
                lcd.clear();
                return ser
        except serial.SerialException as e:
            lcd.clear();
            lcd.cursor_pos = (0,0);
            lcd.write_string('  WAITING FOR USB')
            lcd.cursor_pos = (1,0);
            lcd.write_string('  ====>>****<<====')
            lcd.cursor_pos = (2, 0)
            lcd.write_string('  MAKE SURE THE USB')
            lcd.cursor_pos = (3, 0);
            lcd.write_string('   IS CONNECTED   ')
            print(f"Waiting for serial: {e}")
            time.sleep(2)

# Open the first time
ser = open_serial()

try:
    while True:
        try:
            print("LCD IS HERE")
            lcd.cursor_pos = (0, 0);
            lcd.write_string("   RESISTANCE   ");
            lcd.cursor_pos =(1,0);
            lcd.write_string("   COMPARATOR   ")
 
            if GPIO.input("PI3") == GPIO.HIGH:
                print("Detected HIGH signal")
                lcd.clear();
                # Main task
                ser.write(b'MEAS:RES?\r\n')
                time.sleep(0.5);
                response = ser.readline().decode().strip();
                lcd.cursor_pos  = (0, 0);
                lcd.write_string(f"{response} Ohm");
                lcd.cursor_pos = (1, 0);
                lcd.write_string("OK");
                print(f"Resistance: {response} Ohm");
                time.sleep(3);


                GPIO.output("PI2", GPIO.HIGH)
                print("GPIO ON")
                time.sleep(1)
                GPIO.output("PI2", GPIO.LOW)
                print("GPIO OFF")
                time.sleep(1)
            else:
                print("Waiting for HIGH...")
                time.sleep(0.2)

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


