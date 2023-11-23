# %% 
import numpy as np
from numpy import log10
import matplotlib.pyplot as plt
import time
from datetime import datetime
from ThorlabsPM100 import ThorlabsPM100, USBTMC  # https://pypi.org/project/ThorlabsPM100/
import serial

## sudo ls -l /dev/ttyUSB*
LASER_PORT = '/dev/ttyUSB1'




# %%
def inilize_laser_controller():
    with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
        def give_cmd(cmd, verbose=True):
            ser.write(cmd.encode('ascii') + b'\r\n')
            read_list = []
            while True:
                read = ser.readline()
                if read != b'':
                    read_list.append(read[:-2])
                else:
                    break
            if read_list and verbose:
                print(read_list)
            return read_list
        ##############################
        give_cmd("&DCL")  # Device CLear
        give_cmd("*IDN?")
        for i in [1,2,3]:
            give_cmd(f":SLOT {i};:SLOT?")
            if i in [1,2]:
                give_cmd(":LIMC:SET 500E-3;:LIMC:SET?")
            elif i in [3]:
                give_cmd(":LIMC:SET 25E-3;:LIMC:SET?")
            give_cmd(":ILD:SET 0.0E-3;:ILD:SET?;:ILD:ACT?")
            give_cmd(":TEMP:SET 25.0E0;:TEMP:SET?;:TEMP:ACT?")
            give_cmd(":TWIN:SET 0.03E0;:TWIN:SET?")
            give_cmd(":TP ON;:TP?")
            give_cmd(":TEC ON;:TEC?")
            give_cmd(":LASER OFF;:LASER?")
        give_cmd(":SLOT 1;&GTL")  # Go To Local
        return None
inilize_laser_controller()





# %%
def set_laser_mA(pump1_mA, pump2_mA, signal_mA, verbose=True):
    with serial.Serial(LASER_PORT, 19200, timeout=0.5, rtscts=True) as ser:
        def give_cmd(cmd):
            ser.write(cmd.encode('ascii') + b'\r\n')
            read_list = []
            while True:
                read = ser.readline()
                if read != b'':
                    read_list.append(read[:-2])
                else:
                    break
            if read_list and verbose:
                print(read_list)
            return read_list
        ##############################
        give_cmd("&DCL")  # Device CLear
        give_cmd("*IDN?")
        for i, mA in zip([1,2,3], [pump1_mA, pump2_mA, signal_mA]):
            give_cmd(f":SLOT {i};:SLOT?;:ILD:SET {mA}E-3;:ILD:SET?;:ILD:ACT?")
        give_cmd(":SLOT 1;&GTL")  # Go To Local
        return None
set_laser_mA(1,2,3)




