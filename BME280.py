#!/usr/bin/python2.7
#coding=UTF-8

from __future__ import division
import datetime
import time
import spidev


 # Operating Modes
BME280_OSAMPLE_1 = 1
BME280_OSAMPLE_2 = 2
BME280_OSAMPLE_4 = 3
BME280_OSAMPLE_8 = 4
BME280_OSAMPLE_16 = 5

# BME280 Registers

BME280_REGISTER_DIG_T1 = 0x88  # Trimming parameter registers
BME280_REGISTER_DIG_T2 = 0x8A
BME280_REGISTER_DIG_T3 = 0x8C

BME280_REGISTER_DIG_P1 = 0x8E
BME280_REGISTER_DIG_P2 = 0x90
BME280_REGISTER_DIG_P3 = 0x92
BME280_REGISTER_DIG_P4 = 0x94
BME280_REGISTER_DIG_P5 = 0x96
BME280_REGISTER_DIG_P6 = 0x98
BME280_REGISTER_DIG_P7 = 0x9A
BME280_REGISTER_DIG_P8 = 0x9C
BME280_REGISTER_DIG_P9 = 0x9E

BME280_REGISTER_DIG_H1 = 0xA1
BME280_REGISTER_DIG_H2 = 0xE1
BME280_REGISTER_DIG_H3 = 0xE2
BME280_REGISTER_DIG_H4 = 0xE3
BME280_REGISTER_DIG_H5 = 0xE4
BME280_REGISTER_DIG_H6 = 0xE5
BME280_REGISTER_DIG_H7 = 0xE6
BME280_REGISTER_DIG_H8 = 0xE7

BME280_REGISTER_CHIPID = 0xD0
BME280_REGISTER_VERSION = 0xD1
BME280_REGISTER_SOFTRESET = 0xE0

BME280_REGISTER_CONTROL_HUM = 0xF2
BME280_REGISTER_CONTROL = 0xF4
BME280_REGISTER_CONFIG = 0xF5
BME280_REGISTER_PRESSURE_DATA = 0xF7
BME280_REGISTER_TEMP_DATA = 0xFA
BME280_REGISTER_HUMIDITY_DATA = 0xFD

BME280_REGISTER_CONTROL_HUM_WRITE = 0x72
BME280_REGISTER_CONTROL_WRITE = 0x74
BME280_REGISTER_CONFIG_WRITE = 0x75
BME280_REGISTER_PRESSURE_DATA_WRITE = 0x77
BME280_REGISTER_TEMP_DATA_WRITE = 0x7A
BME280_REGISTER_HUMIDITY_DATA_WRITE = 0x7D

t1=0
t2=0
t3=0

h1=0
h2=0
h3=0
h4=0
h5=0
h6=0
h7=0
h8=0
t_fine=0

mode = BME280_OSAMPLE_4
spi = spidev.SpiDev()
#spi.max_speed_hz = 5000
spi.open(0, 1)
#spi.max_speed_hz = 5000
def reset():
    spi.xfer2([0x60, 0xB6])

def setup():
    global mode
    to_send=[BME280_REGISTER_CONTROL_HUM_WRITE, mode] #humidity oversampling 1
    spi.xfer2(to_send)
    to_send=[BME280_REGISTER_CONTROL_HUM, 0x00]
    print(spi.xfer2(to_send))

    
    to_send = [BME280_REGISTER_CONTROL_WRITE, ((mode << 5) | (0x01 << 2) | (0x03) )] #registe mesure
    spi.xfer2(to_send)


    to_send = [BME280_REGISTER_CONFIG_WRITE, ((0x05 << 5) | (0x00 << 2) | (0x00) )] #registe config
    spi.xfer2(to_send)



def read_raw_temp():
    global mode
    """Reads the raw (uncompensated) temperature from the sensor."""
    meas = mode
    data = []
    sleep_time = 0.00125 + 0.0023 * (1 << mode)
    sleep_time = sleep_time + 0.0023 * (1 << mode) + 0.000575
    sleep_time = sleep_time + 0.0023 * (1 << mode) + 0.000575
    time.sleep(sleep_time)  # Wait the required time
    for i in range(0xF7,0xFD):
        data.append(spi.xfer2([i, 0x00])[1])
#    msb = spi.xfer2([BME280_REGISTER_TEMP_DATA, 0x00])[1]
#    lsb = spi.xfer2([BME280_REGISTER_TEMP_DATA + 1, 0x00])[1]
#    xlsb = spi.xfer2([BME280_REGISTER_TEMP_DATA + 2, 0x00])[1]


    msb = data[3]
    lsb = data[4]
    xlsb = data [5]
    raw = ((msb << 12) | (lsb << 4) | xlsb >> 4)
    #print("Raw temp = {0:b}".format(raw))
    return float(raw)  #ici raw est un nombre sur 20bits


def read_raw_hum():
    data = []
    for i in range(0xF7, 0xF7 + 8):
        data.append(spi.xfer2([i, 0x00])[1])
    hum_raw = (data[6] << 8) | data[7]    
    return hum_raw

    
    
def realTemp():
    global t1,t2,t3, t_fine
    UT = float(read_raw_temp())
    var1 = (UT / 16384.0 - float(t1) / 1024.0) * float(t2)
    var2 = ((UT / 131072.0 - float(t1) / 8192.0) * (  UT / 131072.0 - float(t1) / 8192.0)) * float(t3)
    t_fine = int(var1 + var2)
    temp = (var1 + var2) / 5120.0
    return temp

def realHum():
    global h1,h2,h3,h4,h5,h6, t_fine
    realHum = read_raw_hum()
    var_h = t_fine - 76800.0
    if var_h == 0:
        return 0

    var_h = (realHum - (h4 * 64.0 + h5 / 16384.0 * var_h)) * (
        h2 / 65536.0 * (1.0 + h6 / 67108864.0 * var_h * (
            1.0 + h3 / 67108864.0 * var_h)))
    var_h *= (1.0 - h1 * var_h / 524288.0)

    if var_h > 100.0:
        var_h = 100.0
    elif var_h < 0.0:
        var_h = 0.0

    return var_h    

def calibrate():
    global t1,t2,t3,h1,h2,h3,h4,h5,h6

#    to_send = [0x75, ((5 << 5) | (0 << 2) | 0)]
#    spi.xfer2(to_send)

    #lecture du registre 0x88 ==> LSB des data de calibration
    to_send = [0x88,0x00]
    t1_tmp = spi.xfer2(to_send)[1]
    to_send = [0x89,0x00]
    t1_tmp2 = spi.xfer2(to_send)[1]
    t1 = (t1_tmp2<<8 | t1_tmp)
    if t1 & 0x8000:
        t1 = (-t1 ^ 0xFFFF) + 1

    to_send = [0x8A,0x00]
    t2_tmp = spi.xfer2(to_send)[1]
    to_send = [0x8B,0x00]
    t2_tmp2 = spi.xfer2(to_send)[1]
    t2 = (t2_tmp2<<8 | t2_tmp)
#    if t2 & 0x8000:
#        t2 = (-t2 ^ 0xFFFF) + 1

    to_send = [0x8C,0x00]
    t3_tmp = spi.xfer2(to_send)[1]
    to_send = [0x8D,0x00]
    t3_tmp2 = spi.xfer2(to_send)[1]
    t3 = (t3_tmp2 << 8 | t3_tmp)
    
    
    ##humidity
    to_send = [BME280_REGISTER_DIG_H1, 0x00]
    h1 = spi.xfer2(to_send)[1]  #[1] car la 1ere case du tableau est l'octet 0x00
    
    to_send = [BME280_REGISTER_DIG_H2, 0x00]
    h2_tmp =  spi.xfer2(to_send)[1]
    to_send = [BME280_REGISTER_DIG_H3, 0x00]
    h2_tmp2 =  spi.xfer2(to_send)[1]
    h2 = (h2_tmp2<<8 | h2_tmp)
    
    to_send = [BME280_REGISTER_DIG_H4, 0x00]
    h3 =  spi.xfer2(to_send)[1]
    
    to_send = [BME280_REGISTER_DIG_H5, 0x00]
    h4_tmp =  spi.xfer2(to_send)[1]
    to_send = [BME280_REGISTER_DIG_H6, 0x00]
    h4_tmp2 =  spi.xfer2(to_send)[1]
    h4 = ((h4_tmp<<4) | (0x0F & h4_tmp2))
    
    to_send = [BME280_REGISTER_DIG_H7, 0x00]    
    h5_tmp = spi.xfer2(to_send)[1]
    h5 = (h5_tmp << 4) | ((h4_tmp2 >> 4) & 0x0F)
    
    to_send = [BME280_REGISTER_DIG_H8, 0x00]    
    h6 = spi.xfer2(to_send)[1]
#    calibration_h.append(raw_data[24]) h1
#    calibration_h.append((raw_data[26] << 8) | raw_data[25]) h2
#    calibration_h.append(raw_data[27]) h3
    
#    calibration_h.append((raw_data[28] << 4) | (0x0F & raw_data[29]))
#    calibration_h.append((raw_data[30] << 4) | ((raw_data[29] >> 4) & 0x0F))
#    calibration_h.append(raw_data[31])
    
#    if t3 & 0x8000:
#        t3 = (-t3 ^ 0xFFFF) + 1


reset()
time.sleep(2)
setup()
time.sleep(2)
calibrate()
time.sleep(1)
now = datetime.datetime.now()
templog = open("./templog.log", "a")

templog.write("{1} Temp = {0:0.3f} deg C\n".format(realTemp(), now.strftime("%Y-%m-%d %H:%M")))
templog.write("{1} Hum = {0:0.3f} \n".format(realHum(), now.strftime("%Y-%m-%d %H:%M")))
time.sleep(1)

time.sleep(1)
templog.close()
