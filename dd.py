import OPi.GPIO as GPIO
import time
import serial
import mysql.connector
from RPLCD.i2c import CharLCD


# --- Database connection ---
db = mysql.connector.connect(
    host="localhost",
    user="orangepi",
    password="lti",
    database="resistanceMeter"
)
cursor = db.cursor()


# --- Example insert query ---
sql = """
INSERT INTO measured (date, upperLimit, lowerLimit, measuredValue, judgment)
VALUES (%s, %s, %s, %s, %s)
"""

# Limits
UPPER_LIMIT = 12000.0
LOWER_LIMIT = 8000.0


# --- GPIO setup ---
GPIO.setmode(GPIO.SUNXI)
GPIO.setwarnings(False)
GPIO.setup("PC12", GPIO.IN)   # start button
GPIO.setup("PI3", GPIO.OUT)  # relay
GPIO.setup("PI4", GPIO.OUT) # lamp/buzzer

lcd = CharLCD(i2c_expander='PCF8574',
              address=0x27,
              port=0,
              cols=20, rows=4)

# turn off all relays
GPIO.output("PI3", GPIO.LOW)
GPIO.output("PI4", GPIO.LOW)


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
                time.sleep(1)
                lcd.clear()
                return ser
        except serial.SerialException as e:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string('  WAITING FOR USB')
            lcd.cursor_pos = (1, 0)
            lcd.write_string('  ====>>****<<====')
            lcd.cursor_pos = (2, 0)
            lcd.write_string('  MAKE SURE THE USB')
            lcd.cursor_pos = (3, 0)
            lcd.write_string('   IS CONNECTED   ')
            print(f"Waiting for serial: {e}")
            time.sleep(2)


def read_stable_resistance(ser, settle_time=1.0, tolerance=100):
    """
    Read resistance until value is stable for `settle_time` seconds.
    :param ser: serial port object
    :param settle_time: required stable time in seconds (default 0.3s)
    :param tolerance: allowed fluctuation in Ohms
    :return: stable resistance value (float) or None if failed
    """
    stable_start = None
    last_value = None

    while True:
        ser.write(b'MEAS:RES?\r\n')
        time.sleep(0.1)
        line = ser.readline().decode().strip()

        try:
            value = float(line)
        except ValueError:
            continue  # ignore bad readings

        if last_value is None:
            last_value = value
            stable_start = time.time()
            continue

        if abs(value - last_value) <= tolerance:
            if time.time() - stable_start >= settle_time:
                return value
        else:
            stable_start = time.time()
            last_value = value


# --- Main loop ---
ser = open_serial()

try:
    while True:
        try:
            lcd.cursor_pos = (0, 0)
            lcd.write_string("   RESISTANCE   ")
            lcd.cursor_pos = (1, 0)
            lcd.write_string("   COMPARATOR   ")

            if GPIO.input("PI3") == GPIO.HIGH:
                print("Detected HIGH signal")
                lcd.clear()
                lcd.cursor_pos = (0, 0)
                lcd.write_string("MEASURING VALUE...")
                lcd.cursor_pos = (1, 0)
                lcd.write_string("ENSURE THE VALUE IS") 
                lcd.cursor_pos =  (2, 0)
                lcd.write_string("IS STAY STILL...")
                response = read_stable_resistance(ser, settle_time=0.3, tolerance=0.5)
                if response is not None:
                    # Judgment
                    lcd.clear()
                    if LOWER_LIMIT <= response <= UPPER_LIMIT:
                        judgment = "OK"
                        GPIO.output("PI4", GPIO.HIGH)  # GREEN lamp
                    else:
                        judgment = "NG"
                        GPIO.output("PI4", GPIO.LOW)   # RED lamp/buzzer

                    # Show on LCD
                    lcd.cursor_pos = (0, 0)
                    lcd.write_string(f"{response:.2f} Ohm")
                    lcd.cursor_pos = (1, 0)
                    lcd.write_string(judgment)
                    print(f"Stable Resistance: {response} Ohm, Result: {judgment}")

                    # Save to DB with current datetime
                    values = (time.strftime("%Y-%m-%d %H:%M:%S"), UPPER_LIMIT, LOWER_LIMIT, response, judgment)
                    cursor.execute(sql, values)
                    db.commit()

                    # Pulse relay
                    GPIO.output("PC12", GPIO.HIGH)
                    print("GPIO ON")
                    time.sleep(1)
                    GPIO.output("PC12", GPIO.LOW)
                    print("GPIO OFF")

                    time.sleep(2)  # pause before next measurement

            else:
                print("Waiting for HIGH...")
                time.sleep(0.2)

        except (serial.SerialException, OSError) as e:
            print(f"[!] Serial disconnected: {e}")
            try:
                ser.close()
            except:
                pass
            ser = open_serial()  # reconnect

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    if ser.is_open:
        ser.close()
    GPIO.cleanup()
