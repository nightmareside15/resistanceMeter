from RPLCD.i2c import CharLCD
import time

lcd = CharLCD(i2c_expander='PCF8574',
	address =0x27,
	port=0,
	cols=16, rows=2)

lcd.write_string('   RESISTANCE      TESTER')
time.sleep(60)
lcd.clear()
