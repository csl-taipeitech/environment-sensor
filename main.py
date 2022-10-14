#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import MPU925x  # Gyroscope/Acceleration/Magnetometer
import BME280  # Atmospheric Pressure/Temperature and humidity
import LTR390  # UV
import TSL2591  # LIGHT
import SGP40
import json

from machine import Pin, I2C
import network
import ubinascii
import urequests as requests
from secrets import secrets

i2c = I2C(0, scl=Pin(21), sda=Pin(20), freq=100000)
URL = "http://termite.csltaipeitech.com:5000"
SLEEP_SECOND = 0
ONLINE = False


class EscapeCode():
    Clear = '\033[2J\033[1;1H'
    White = '\033[97m'
    Yellow = '\033[38;5;220m'
    Green = '\033[38;5;2m'
    Orange = '\033[38;5;202m'
    Red = '\033[38;5;9m'
    Purple = '\033[38;5;93m'
    Blue = '\033[38;5;19m'
    LightBlue = '\033[38;5;39m'


def connect_wifi():
    wlan.connect(ssid, pw)
    # Listen for connections

    timeout = 10
    while timeout > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        timeout -= 1
        print('Waiting for connection...')
        time.sleep(1)


def send_to_server(sensors_dict):
    payload = json.dumps(sensors_dict)
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request(
            "POST", URL, headers=headers, data=payload, timeout=3)
        print(response.text)
    except Exception as e:
        print(e)
        print("try again...")


print("==================================================")
print("this is Environment Sensor test program...")
print("TSL2591 Light I2C address:0X29")
print("LTR390 UV I2C address:0X53")
print("SGP40 VOC I2C address:0X59")
print("MPU9250 9-DOF I2C address:0X68")
print("bme280 T&H I2C address:0X76")

devices = i2c.scan()
if len(devices) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices))
for device in devices:
    print("Hexa address: ", hex(device))


bme280 = BME280.BME280()
bme280.get_calib_param()
light = TSL2591.TSL2591()
sgp = SGP40.SGP40()
uv = LTR390.LTR390()
mpu = MPU925x.MPU925x()

# Set country to avoid possible errors
rp2.country('DE')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# If you need to disable powersaving mode
# wlan.config(pm = 0xa11140)

# See the MAC address in the wireless chip OTP
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
print('mac = ' + mac)

# Other things to query
# print(wlan.config('channel'))
# print(wlan.config('essid'))
# print(wlan.config('txpower'))

# Load login data from different file for safety reasons
ssid = secrets['ssid']
pw = secrets['pw']

if ONLINE:
    connect_wifi()

try:
    while True:
        time.sleep(SLEEP_SECOND)
        localtime = time.localtime()
        timestamp = time.time()

        bme = []
        bme = bme280.readData()
        pressure = round(bme[0], 2)
        temp = round(bme[1], 2)
        hum = round(bme[2], 2)
        lux = round(light.Lux(), 2)
        uvs = uv.UVS()
        gas = round(sgp.measureRaw(temp, hum), 2)
        icm = []
        icm = mpu.ReadAll()

        sensors_dict = {}
        sensors_dict['mac'] = mac
        sensors_dict['localtime'] = timestamp
        sensors_dict['pressure'] = pressure
        sensors_dict['temp'] = temp
        sensors_dict['hum'] = hum
        sensors_dict['lux'] = lux
        sensors_dict['uv'] = uvs
        sensors_dict['gas'] = gas
        sensors_dict['accel'] = {'x': icm[0], 'y': icm[1], 'z': icm[2]}
        sensors_dict['gyro'] = {'x': icm[3], 'y': icm[4], 'z': icm[5]}
        sensors_dict['mag'] = {'x': icm[6], 'y': icm[7], 'z': icm[8]}

        if ONLINE:
            send_to_server(sensors_dict)

        print("Pressure:", pressure, end="")
        print(",Temp:", temp, end="")
        print(",Humid:", hum, end="")
        print(",Lux:", lux, end="")
        print(",UV:", uv, end="")
        # print(",gas:", 32768-gas, end="")
        print(",Accel X:", icm[0]*9.81/16384, end="")
        print(",Accel Y:", icm[1]*9.81/16384, end="")
        print(",Accel Z:", icm[2]*9.81/16384)

        # print(",Gyro X:", icm[3]/131, end="")
        # print(",Gyro Y:", icm[4]/131, end="")
        # print(",Gyro Z:", icm[5]/131, end="")

        # print(",Mag X:", icm[6]/1000, end="")
        # print(",Mag Y:", icm[7]/1000, end="")
        # print(",Mag Z:", icm[8]/1000)

except KeyboardInterrupt:
    exit()
