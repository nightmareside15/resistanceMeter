import OPi.GPIO as GPIO
import time
import serial
import mysql.connector


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
UPPER_LIMIT = 500.0
LOWER_LIMIT = 400.0

# --- GPIO setup ---
GPIO.setmode(GPIO.SUNXI)
GPIO.setwarnings(False)
GPIO.setup("PI3", GPIO.IN)   # start button
GPIO.setup("PI2", GPIO.OUT)  # relay
GPIO.setup("PI16", GPIO.OUT) # lamp/buzzer

# turn off all relays
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
                print("Serial connected")
                time.sleep(1)
                return ser
        except serial.SerialException as e:
            print(f"Waiting for serial: {e}")
            time.sleep(2)


def read_stable_resistance(ser, settle_time=3.0, tolerance=100):
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
            print("RESISTANCE METER")

            if GPIO.input("PI3") == GPIO.HIGH:
                print("Detected HIGH signal")
                response = read_stable_resistance(ser, settle_time=0.3, tolerance=0.5)
                if response is not None:
                    # Judgment
                    if LOWER_LIMIT <= response <= UPPER_LIMIT:
                        judgment = "OK"
                        GPIO.output("PI16", GPIO.HIGH)  # GREEN lamp
                    else:
                        judgment = "NG"
                        GPIO.output("PI16", GPIO.LOW)   # RED lamp/buzzer

                    # Show on LCD
                    print(f"Stable Resistance: {response} Ohm, Result: {judgment}")

                    # Save to DB with current datetime
                    values = (time.strftime("%Y-%m-%d %H:%M:%S"), UPPER_LIMIT, LOWER_LIMIT, response, judgment)
                    cursor.execute(sql, values)
                    db.commit()

                    # Pulse relay
                    GPIO.output("PI2", GPIO.HIGH)
                    print("GPIO ON")
                    time.sleep(1)
                    GPIO.output("PI2", GPIO.LOW)
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
