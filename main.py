#!/usr/bin/python
# -*- coding:utf-8 -*-
import time
import MPU925x  # Gyroscope/Acceleration/Magnetometer
import BME280  # Atmospheric Pressure/Temperature and humidity
import LTR390  # UV
import TSL2591  # LIGHT
import SGP40
import math
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

    if wlan.isconnected():
        pin16.on()


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

    # path = 'output.txt'
    # f = open(path, 'a')
    # f.write(payload)
    # f.write('\n')
    # f.close()


def get_temp_color(temp):
    temp_color = ''
    if temp > -30:
        temp_color = EscapeCode.Purple
    if temp > -5:
        temp_color = EscapeCode.Blue
    if temp > 5:
        temp_color = EscapeCode.LightBlue
    if temp > 15:
        temp_color = EscapeCode.Green
    if temp > 27:
        temp_color = EscapeCode.Orange
    if temp > 38:
        temp_color = EscapeCode.Red
    return temp_color


def get_humid_color(humid):
    humid_color = ''
    if humid > 0:
        humid_color = EscapeCode.Red
    if humid > 40:
        humid_color = EscapeCode.Green
    if humid > 70:
        humid_color = EscapeCode.Blue
    return humid_color


def get_uv_color(uvs):
    uv_color = ''
    if uvs >= 0:
        uv_color = EscapeCode.Green
    if uvs > 2:
        uv_color = EscapeCode.Yellow
    if uvs > 5:
        uv_color = EscapeCode.Orange
    if uvs > 7:
        uv_color = EscapeCode.Red
    if uvs > 10:
        uv_color = EscapeCode.Purple
    return uv_color


def print_accel(x, y, z):
    x = x * 9.81 / 16384
    y = y * 9.81 / 16384
    z = z * 9.81 / 16384
    x_color = EscapeCode.White
    y_color = EscapeCode.White
    z_color = EscapeCode.White
    if abs(x) > 3:
        x_color = EscapeCode.Red
    if abs(y) > 3:
        y_color = EscapeCode.Red
    if abs(z) > 3:
        z_color = EscapeCode.Red

    print(f"Acceleration\t:\t{x_color}X = %.2f\t{y_color}Y = %.2f\t{z_color}Z = %.2f\t{EscapeCode.White}m/s2"
          % (x, y, z))


def print_gyro(x, y, z):
    x /= 131
    y /= 131
    z /= 131
    x_color = EscapeCode.White
    y_color = EscapeCode.White
    z_color = EscapeCode.White
    if abs(x) > 10:
        x_color = EscapeCode.Yellow
    if abs(y) > 10:
        y_color = EscapeCode.Yellow
    if abs(z) > 10:
        z_color = EscapeCode.Yellow

    print(f"Gyroscope\t:\t{x_color}X = %.2f\t{y_color}Y = %.2f\t{z_color}Z = %.2f\t{EscapeCode.White}°/sec"
          % (x, y, z))


def print_line():
    print('------------------------------------------------------------------------------')


pin16 = Pin(16, Pin.OUT)
pin16.off()

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


#         print("==================================================")
        # print(EscapeCode.Clear, end='')
        # print(EscapeCode.White, end='')
        # print("pressure\t:\t%.2f hPa" % pressure)
        # print(f"temp\t\t:\t{get_temp_color(temp)}%.2f °C" % temp)
        # print(EscapeCode.White, end='')
        # print(f"hum\t\t:\t{get_humid_color(hum)}%.2f ％" % hum)
        # print(EscapeCode.White, end='')
        # print(f"lux\t\t:\t{EscapeCode.Yellow}%d" % lux)
        # print(EscapeCode.White, end='')
        # print(f"uv\t\t:\t{get_uv_color(uvs)}%d" % uvs)
        # print(EscapeCode.White, end='')
        # print("gas\t\t:\t%.2f" % (32768 - gas))
        # print_accel(icm[0], icm[1], icm[2])
        # # print(f"Acceleration\t:\tX = %.2f\tY = %.2f\tZ = %.2f\tm/s2" %
        # #       (icm[0] * 9.81 / 16384,
        # #        icm[1] * 9.81 / 16384,
        # #        icm[2] * 9.81 / 16384))
        # print_gyro(icm[3], icm[4], icm[5])
        # # print("Gyroscope\t:\tX = %.2f\tY = %.2f\tZ = %.2f\t°/sec" %
        # #       (icm[3] / 131,
        # #        icm[4] / 131,
        # #        icm[5] / 131))
        # print("Magnetic\t:\tX = %.2f\tY = %.2f\tZ = %.2f\tµT" %
        #       (icm[6] / 1000,
        #        icm[7] / 1000,
        #        icm[8] / 1000))

        print("Pressure:", pressure, end="")
        print(",temp:", temp, end="")
        print(",humid:", hum, end="")
        print(",lux:", lux, end="")
        print(",uv:", uv, end="")
        # print(",gas:", 32768-gas, end="")
        print(",Accel X:", icm[0]*9.81/16384, end="")
        print(",Accel Y:", icm[1]*9.81/16384, end="")
        print(",Accel Z:", icm[2]*9.81/16384, end="")

        # print(",Gyro X:", icm[3]/131, end="")
        # print(",Gyro Y:", icm[4]/131, end="")
        # print(",Gyro Z:", icm[5]/131, end="")

        # print(",Mag X:", icm[6]/1000, end="")
        # print(",Mag Y:", icm[7]/1000, end="")
        print(",Mag Z:", icm[8]/1000)

except KeyboardInterrupt:
    pin16.off()
    exit()
