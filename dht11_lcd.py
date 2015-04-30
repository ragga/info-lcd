#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: Michael Wright, Henri Servomaa
#
# Usees the updated Adafruit library at
# https://github.com/adafruit/Adafruit_Python_DHT
# Follow the instructions to install it first

import  os, sys , time , subprocess
import datetime
import RPi.GPIO as GPIO
from numpy import *
import Adafruit_DHT
from time import sleep


## Handle args
sensor_args = { '11': Adafruit_DHT.DHT11,
				'22': Adafruit_DHT.DHT22,
				'2302': Adafruit_DHT.AM2302 }
if len(sys.argv) == 3 and sys.argv[1] in sensor_args:
	sensor = sensor_args[sys.argv[1]]
	pin = sys.argv[2]
else:
	print 'usage: sudo ./dht11_lcd.py [11|22|2302] GPIOpin#'
	print 'example: sudo ./dht11_lcd.py 2302 4 - Read from an AM2302 connected to GPIO #4'
	sys.exit(1)


class Generic_LCD:

    # commands
    LCD_CLEARDISPLAY            = 0x01
    LCD_RETURNHOME              = 0x02
    LCD_ENTRYMODESET            = 0x04
    LCD_DISPLAYCONTROL          = 0x08
    LCD_CURSORSHIFT             = 0x10
    LCD_FUNCTIONSET             = 0x20
    LCD_SETCGRAMADDR            = 0x40
    LCD_SETDDRAMADDR            = 0x80

    # flags for display entry mode
    LCD_ENTRYRIGHT              = 0x00
    LCD_ENTRYLEFT               = 0x02
    LCD_ENTRYSHIFTINCREMENT     = 0x01
    LCD_ENTRYSHIFTDECREMENT     = 0x00

    # flags for display on/off control
    LCD_DISPLAYON               = 0x04
    LCD_DISPLAYOFF              = 0x00
    LCD_CURSORON                = 0x02
    LCD_CURSOROFF               = 0x00
    LCD_BLINKON                 = 0x01
    LCD_BLINKOFF                = 0x00

    # flags for display/cursor shift
    LCD_DISPLAYMOVE             = 0x08
    LCD_CURSORMOVE              = 0x00

    # flags for display/cursor shift
    LCD_DISPLAYMOVE             = 0x08
    LCD_CURSORMOVE              = 0x00
    LCD_MOVERIGHT               = 0x04
    LCD_MOVELEFT                = 0x00

    # flags for function set
    LCD_8BITMODE                = 0x10
    LCD_4BITMODE                = 0x00
    LCD_2LINE                   = 0x08
    LCD_1LINE                   = 0x00
    LCD_5x10DOTS                = 0x04
    LCD_5x8DOTS                 = 0x00

    def __init__(self, pin_rs=22, pin_e=21, pins_db=[24, 17, 23, 4], GPIO = None):
        # Emulate the old behavior of using RPi.GPIO if we haven't been given
        # an explicit GPIO interface to use
        if not GPIO:
            import RPi.GPIO as GPIO

        self.GPIO = GPIO
        self.pin_rs = pin_rs
        self.pin_e = pin_e
        self.pins_db = pins_db

        self.GPIO.setmode(GPIO.BCM)
        self.GPIO.cleanup()
        self.GPIO.setup(self.pin_e, GPIO.OUT)
        self.GPIO.setup(self.pin_rs, GPIO.OUT)

        for pin in self.pins_db:
            self.GPIO.setup(pin, GPIO.OUT)

        self.write4bits(0x33) # initialization
        self.write4bits(0x32) # initialization
        self.write4bits(0x28) # 2 line 5x7 matrix
        self.write4bits(0x0C) # turn cursor off 0x0E to enable cursor
        self.write4bits(0x06) # shift cursor right

        self.displaycontrol = self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF

        self.displayfunction = self.LCD_4BITMODE | self.LCD_1LINE | self.LCD_5x8DOTS
        self.displayfunction |= self.LCD_2LINE

        """ Initialize to default text direction (for romance languages) """
        self.displaymode =  self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT
        self.write4bits(self.LCD_ENTRYMODESET | self.displaymode) #  set the entry mode

        self.clear()


    def clear(self):
        self.write4bits(self.LCD_CLEARDISPLAY) # command to clear display
        self.delayMicroseconds(3000)    # 3000 microsecond sleep, clearing the display takes a long time


    def display(self):
        """ Turn the display on (quickly) """

        self.displaycontrol |= self.LCD_DISPLAYON
        self.write4bits(self.LCD_DISPLAYCONTROL | self.displaycontrol)


    def write4bits(self, bits, char_mode=False):
        """ Send command to LCD """

        self.delayMicroseconds(1000) # 1000 microsecond sleep

        bits=bin(bits)[2:].zfill(8)

        self.GPIO.output(self.pin_rs, char_mode)

        for pin in self.pins_db:
            self.GPIO.output(pin, False)

        for i in range(4):
            if bits[i] == "1":
                self.GPIO.output(self.pins_db[::-1][i], True)

        self.pulseEnable()

        for pin in self.pins_db:
            self.GPIO.output(pin, False)

        for i in range(4,8):
            if bits[i] == "1":
                self.GPIO.output(self.pins_db[::-1][i-4], True)

        self.pulseEnable()


    def delayMicroseconds(self, microseconds):
        seconds = microseconds / float(1000000) # divide microseconds by 1 million for seconds
        sleep(seconds)


    def pulseEnable(self):
        self.GPIO.output(self.pin_e, False)
        self.delayMicroseconds(1)               # 1 microsecond pause - enable pulse must be > 450ns
        self.GPIO.output(self.pin_e, True)
        self.delayMicroseconds(1)               # 1 microsecond pause - enable pulse must be > 450ns
        self.GPIO.output(self.pin_e, False)
        self.delayMicroseconds(1)               # commands need > 37us to settle


    def message(self, text):
        """ Send string to LCD. Newline wraps to second line"""

        for char in text:
            if char == '\n':
                self.write4bits(0xC0) # next line
            else:
                self.write4bits(ord(char),True)


# MAIN STARTS
my_ipaddresses = os.popen("/sbin/ip addr show | awk /inet.*eth/'{print $2}'").read()
print "My ip address is :", my_ipaddresses

DHT11 = Adafruit_DHT.DHT11
DHT22 = Adafruit_DHT.DHT22
M2302 = Adafruit_DHT.AM2302

dev_type = M2302

#   pin 25  in the BCM GPIO system
dhtpin = 25

print "Temp sensor connected to bcm gpio pin # ", dhtpin

try:
    print "Initialize LCD"
    lcd = Generic_LCD()
    lcd.clear()
except:
    print "Error: ", sys.exc_info()[0]
    exit


while True :
    try:
        print  "Let's start with a dht.read() "
        genzai = Adafruit_DHT.read_retry(dev_type, dhtpin)
        if  genzai :
            lcd.clear()
            print  "this is a good temp & humid dht.read (genzai)  " , genzai
        else:
            print "Got a bad genzai , i.e. temp & humid number  "
            print "Is genzai printable?  " , genzai
            time.sleep(1.5)
            continue

        humid_str = str(round(genzai[0], 1))
        temp_str = str(round(genzai[1], 1))
        print "formatted temp_str and humid_str before the lcd.message function is called.  " , temp_str , "  " , humid_str

        lcd.message("Temp :  " + temp_str + " oC \nHumid : " + humid_str + " %  " )
        time.sleep(3)

        # should probably check for sane value here
        now = datetime.datetime.now()

        if  now :
            print now.strftime("%Y/%m/%d %H:%M:%S")
            lcd.clear()
        else:
            print "Got a bad datetime "
            print "Is now printable?  " , now
            time.sleep(1)
            continue

        date_tup =  datetime.date.today().strftime("%a"), datetime.date.today().strftime("%b"), datetime.date.today().strftime("%d"), datetime.date.today().strftime("%Y")
        date_str = str(date_tup[0] + ' ' + date_tup[1] + ' ' + date_tup[2] + ' ' + date_tup[3])
        print  "date_str  "  , date_str

        sNowHour = now.strftime("%H")
        sNowMnit = now.strftime("%M")
        sNowSec  = now.strftime("%S")

        iTimeHour = int(sNowHour)                 #  this works to assign a 2 byte string to an integer object
        iTimeMinite = int(sNowMnit)
        iTimeSecond = int(sNowSec)

        #  determine if it is am or pm
        if  ( iTimeHour >= 12) and ( iTimeHour <= 23) :
            iMerdHour = iTimeHour - 12
            if  iTimeHour == 12 :
                iMerdHour = 12
            if ( iMerdHour == 10) or ( iMerdHour == 11) or ( iMerdHour == 12) :
                sTimeSpace = " "
            else:
                sTimeSpace = "  "
            sNowHour = str(iMerdHour)
            sMeridian = "pm"
        else:
            if ( iTimeHour == 10) or ( iTimeHour == 11) :
                sTimeSpace = " "
            else:
                sTimeSpace = " "
            if( iTimeHour == 24 ) :
                iMerdHour =  12
                sNowHour = str(iMerdHour)
                sTimeSpace = " "
            sMeridian = "am"

        sTimeHourMnitMerd = "Time :" + sTimeSpace + sNowHour + ":" + sNowMnit + " " + sMeridian + " "
        print  "hour-minute_string  " , sTimeHourMnitMerd , "  next step sends the time and date message to the LCD "

        lcd.message(sTimeHourMnitMerd + "\n" + date_str )
        print  sTimeHourMnitMerd , "  " , date_str , " message sent to LCD , next a 5 second nap "
        time.sleep(3)

        lcd.clear()
        lcd.message("IPv4 addr " + "\n" + my_ipaddresses)
        time.sleep(2)

        print  "Back from the nap and ready to start at the beginning again"
        print  "  "

    except KeyboardInterrupt:
        GPIO.cleanup()
        print  "Interrupted at", datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        break

    except:
        print "Error: ", sys.exc_info()[0]
        break

print "Shutdown"
