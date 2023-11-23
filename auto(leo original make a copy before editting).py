# %% 
from cProfile import label
import numpy as np
from numpy import log10
import matplotlib.pyplot as plt
import time
from datetime import datetime
from ThorlabsPM100 import ThorlabsPM100, USBTMC  # https://pypi.org/project/ThorlabsPM100/
import serial
import os
%matplotlib qt
plt.close('all')

## sudo chmod a+rw /dev/usbtmc0  ## a (all user)  + (add)  rw (read and write permissions)
## ls -l /dev/ttyUSB*
PM_PORT = '/dev/usbtmc0'
OSA_PORT = '/dev/ttyUSB2'
LASER_PORT = '/dev/ttyUSB0'

os.chdir('/home/edfa/Desktop/student_data')
print('Done! import')



# %% Inilize Power Meter
def inilize_pm():
    ## sudo chmod a+rw /dev/usbtmc0  ## a (all user)  + (add)  rw (read and write permissions)
    set_wavelength_nm = 1550
    inst = USBTMC(device=PM_PORT)
    pm = ThorlabsPM100(inst=inst)
    pm.sense.correction.wavelength = set_wavelength_nm
    pm.sense.average.count = 100
    print('Done! Inilize Power Meter')
    return pm
pm = inilize_pm()


# %% Get Power from Power Meter
def get_pm(pm, set_wavelength_nm, verbose=True):
    pm.sense.correction.wavelength = set_wavelength_nm
    get_wavelength_nm = pm.sense.correction.wavelength
    power_mW = max(1e-6, pm.read*1e3)
    power_dBm = 10*log10(power_mW)
    pm.system.beeper.immediate()
    if verbose:
        print(f'{datetime.now():%Y%m%dt%H%M%S.%f}, p = {power_mW:.6f} mW ({power_dBm:.2f} dBm) @ {get_wavelength_nm:.0f} nm')
    return get_wavelength_nm, power_mW, power_dBm
get_wavelength_nm, power_mW, power_dBm = get_pm(pm, set_wavelength_nm=1550, verbose=True)


# %% Inilize Laser Controller
def give_cmd(cmd, ser, verbose=True):
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
def inilize_laser_controller():
    with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
        give_cmd("*IDN?", ser=ser)
        give_cmd("&DCL", ser=ser)  # Device CLear
        for i in [1,2,3]:
            give_cmd(f":SLOT {i};:SLOT?", ser=ser)
            if i in [1,2]:
                give_cmd(":LIMC:SET 500E-3;:LIMC:SET?", ser=ser)
            elif i in [3]:
                give_cmd(":LIMC:SET 25E-3;:LIMC:SET?", ser=ser)
            give_cmd(":ILD:SET 0.0E-3;:ILD:SET?;:ILD:ACT?", ser=ser)
            give_cmd(":TEMP:SET 25.0E0;:TEMP:SET?;:TEMP:ACT?", ser=ser)
            give_cmd(":TWIN:SET 2.00E0;:TWIN:SET?", ser=ser)
            give_cmd(":TP ON;:TP?", ser=ser)
            give_cmd(":TEC ON;:TEC?", ser=ser)
            give_cmd(":LASER OFF;:LASER?", ser=ser)
        give_cmd(":SLOT 1;&GTL", ser=ser)  # Go To Local
        print('Done! Inilize Laser Controller')
        return None
inilize_laser_controller()


# %% Set Laser current (set mA to -1 means laser off)
def set_laser_mA(slot, mA, laser_ser, verbose=True, gtl=True):
    give_cmd(f":SLOT {slot}", ser=laser_ser, verbose=verbose)
    if mA == -1:
        mA = 0
        give_cmd(":LASER OFF;:LASER?", ser=ser, verbose=verbose)
    else:
        give_cmd(":LASER ON;:LASER?", ser=ser, verbose=verbose)
    # give_cmd(f":SLOT {slot};:SLOT?;:ILD:SET {mA}E-3;:ILD:SET?")
    give_cmd(f":ILD:SET {mA}E-3", ser=laser_ser, verbose=verbose)
    time.sleep(0.001)
    ild_act, = give_cmd(f":ILD:ACT?", ser=laser_ser, verbose=verbose)
    ild_act = ild_act.decode('utf-8').split(' ')[1]
    ild_act = float(ild_act) * 1e3
    if gtl:
        give_cmd(":SLOT 1;&GTL", ser=laser_ser, verbose=verbose)  # Go To Local
    print(f'ild_slot={slot}, ild_set={mA}, ild_act={ild_act}')
    return mA, ild_act
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    ild_set, ild_act = set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    ild_set, ild_act = set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    ild_set, ild_act = set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)


# %% Inilize Optical Spectrum Analyzer
def inilize_osa():
    with serial.Serial(OSA_PORT, 115200, timeout=0.1, rtscts=True) as ser:
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
        give_cmd("*IDN?")
        give_cmd("*CLS")  # clear status
        give_cmd("*RST")  # reset
        give_cmd("SMID")  # Sensitivity (SNAT,SMID,SHI1,SHI2,SHI3)
        give_cmd("STAWL1450.00")    # start wavelength (600 - 1700nm)
        give_cmd("STPWL1650.00")    # stop wavelength (600- 1700nm)
        give_cmd("RESLN0.10")       # resolution (0.02 - 2.00 nm)
        print('Done! Inilize Optical Spectrum Analyzer')
        return None
inilize_osa()


# %% Get Spectrum from OSA
## range 600-1700nm, resolution 0.02-2.00 nm
def get_osa(start_nm, stop_nm, res_nm, txt=''):
    assert 0.02 <= res_nm <= 2.00, f'OSA says: resolution 0.02-2.00 nm, you give {res_nm}'
    assert 600 <= start_nm < stop_nm <= 1700, f'OSA says: range 600-1700nm, you give {start_nm}-{stop_nm}'
    print(f'OSA measuring {start_nm}-{stop_nm}nm, resolution {res_nm}nm')
    n_point = 1+(stop_nm-start_nm)//res_nm
    assert 101 <= n_point <= 50001, f'OSA says: sampling points range 101-50001, now has {n_point} points'
    etc = n_point*0.007176
    print(f'{n_point:.0f} data points, it may takes {etc} sec')
    with serial.Serial(OSA_PORT, 115200, timeout=0.1, rtscts=True) as ser:
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
        give_cmd(f"STAWL{start_nm:.2f}")   ## start wavelength (600 - 1700nm)
        give_cmd(f"STPWL{stop_nm:.2f}")    ## stop wavelength (600- 1700nm)
        give_cmd(f"RESLN{res_nm:.2f}")     ## resolution (0.02 - 2.00 nm)
        give_cmd(f"SMPL{n_point:.0f}")     ## resolution (0.02 - 2.00 nm)

        trace = 'A'
        give_cmd("SGL")             ## single sweep
        while give_cmd("SWEEP?") == [b'1']:
            time.sleep(1)
        wave, = give_cmd('WDAT'+trace, verbose=False)
        wave_str = wave.decode('utf-8').split(',')[1:]
        value, = give_cmd('LDAT'+trace, verbose=False)
        wavelength_nm = np.asarray([float(x) for x in wave_str])
        value_str = value.decode('utf-8').split(',')[1:]
        level_dBm = np.asarray([float(x) for x in value_str])
        name = f'OSA-{datetime.now():%Y%m%dt%H%M%S}-{txt}'
        plt.figure()
        plt.plot(wavelength_nm, level_dBm, alpha=0.8)
        plt.ylim(-90, 20)
        plt.xlim(wavelength_nm.min(), wavelength_nm.max())
        plt.grid()
        plt.ylabel('Power [dBm]'); plt.xlabel('Wavelength [nm]')
        plt.title(f'{name}')
        plt.savefig(name+'.jpg')
        spectrum = np.stack((wavelength_nm, level_dBm), axis=0)
        np.savetxt(name+'.csv', spectrum.T, delimiter=',', fmt='%f')    
        plt.show()
        return wavelength_nm, level_dBm
wavelength_nm, level_dBm = get_osa(start_nm=1545.00, stop_nm=1555.00, res_nm=0.02, txt='abcd')










# %%
#==================================================
# Task 1: Laser diodes characterization
#==================================================
## Increase current step-by-step and record the power
select_slot = 3
mA_range = np.arange(0, 25, 0.5)
pm_wavelength_nm = 1550
txt = "Leo's demo task 1, signal"  # put some text for the file name

## Start auto measurement
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    measurement = []
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    ## Increase current step-by-step and record the power
    for set_mA in mA_range:
        ild_set, ild_act = set_laser_mA(slot=select_slot, mA=set_mA, laser_ser=ser, verbose=False, gtl=True)
        time.sleep(0.001)
        get_wavelength_nm, power_mW, power_dBm = get_pm(pm, set_wavelength_nm=pm_wavelength_nm, verbose=True)
        measurement.append([select_slot, ild_act, get_wavelength_nm, power_mW, power_dBm])
    ## Turn off the laser
    set_laser_mA(slot=select_slot, mA=-1, laser_ser=ser, verbose=False, gtl=True)
measurement = np.asarray(measurement)
slot = measurement[0,0]
wavelength_nm = measurement[0,2]
name = f'laser-{datetime.now():%Y%m%dt%H%M%S}-slot{select_slot}-wavelength{wavelength_nm}nm-{txt}'
np.savetxt(name+'.csv', measurement, delimiter=',', fmt='%f')    

## Load csv file and plot it 
arr = np.genfromtxt(name+'.csv', delimiter=",")
x = arr[:,1]  # ild_act
y1 = arr[:,3]  # power_mW
y2 = arr[:,4]  # power_dBm
plt.figure()
plt.plot(x,y1, '.')
plt.grid()
plt.ylabel('Power [mW]'); plt.xlabel('Current [mA]')
plt.title(f'{name}')
plt.tight_layout()
plt.savefig(name+'.jpg')
plt.show()


# %%
## Set current and record the spectrum
select_slot = 3
set_mA = 25  # What current can make power = 50 mW?
osa_para = [1540, 1560, 0.02]  # start_nm, stop_nm, res_nm
txt = f"Leo's demo task 1, pump ,slot{select_slot}, {set_mA}mA"  # put some text for the file name

## Start auto measurement
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    ## Set current and record the spectrum
    ild_set, ild_act = set_laser_mA(slot=select_slot, mA=set_mA, laser_ser=ser, verbose=False, gtl=True)
    time.sleep(0.001)
    wavelength_nm, level_dBm = get_osa(start_nm=osa_para[0], stop_nm=osa_para[1], res_nm=osa_para[2], txt=txt)
    ## Turn off the laser
    set_laser_mA(slot=select_slot, mA=-1, laser_ser=ser, verbose=False, gtl=True)



# %%
## Compare pump 1 and pume 2
csv1 = "laser-20230316t151643-slot1-wavelength980.0nm-Leo's demo task 1.csv"
csv2 = "laser-20230316t152143-slot2-wavelength980.0nm-Leo's demo task 1pump2.csv"
start_point = 20
arr1 = np.genfromtxt(csv1, delimiter=",")
arr2 = np.genfromtxt(csv2, delimiter=",")
x1 = arr1[:,1]  # ild_act
x2 = arr2[:,1]  # ild_act
y1 = arr1[:,3]  # power_mW
y2 = arr2[:,3]  # power_mW
slope1, intercept1 = np.polyfit(x1[start_point:], y1[start_point:], 1)
slope2, intercept2 = np.polyfit(x2[start_point:], y2[start_point:], 1)
plt.close('all')
plt.figure()
plt.plot(x1,y1, '.', label=csv1, alpha=0.6)
plt.plot(x2,y2, '.', label=csv2, alpha=0.6)
plt.plot(x1, slope1*x1 + intercept1, alpha=0.6, label=f'linear fit, y = {slope1} x + {intercept1}')
plt.plot(x2, slope2*x2 + intercept2, alpha=0.6, label=f'linear fit, y = {slope2} x + {intercept2}')
plt.grid()
plt.legend()
plt.ylabel('Power [mW]'); plt.xlabel('Current [mA]')
plt.tight_layout()
plt.show()









# %%
#==================================================
# Task 2: Measurement of the ASE
#==================================================
## Set current and record the spectrum
select_slot = 2
mA_loop =  [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
osa_para = [1400, 1700, 0.10]  # start_nm, stop_nm, res_nm
txt = f"Leo's demo Task 2 P2B, slot{select_slot}, {set_mA}mA"  # put some text for the file name

## Start auto measurement
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    ## Set current and record the spectrum
    for set_mA in mA_loop:
        ild_set, ild_act = set_laser_mA(slot=select_slot, mA=set_mA, laser_ser=ser, verbose=False, gtl=True)
        time.sleep(0.001)
        wavelength_nm, level_dBm = get_osa(start_nm=osa_para[0], stop_nm=osa_para[1], res_nm=osa_para[2], txt=txt)
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)










# %%
#==================================================
# Task 3: Gain and noise characteristics
#==================================================
## Turn on signal laser to 25 mA and turn VOA to get -15 dBm
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    set_laser_mA(slot=3, mA=25, laser_ser=ser, verbose=False, gtl=True)


# %%
## Set current and record the spectrum
select_slot = 2
mA_loop =  np.arange(0, 500, 25)
osa_para = [1540, 1560, 0.02]  # start_nm, stop_nm, res_nm
txt = f"Leo's demo Task 3 P2B, slot{select_slot}, {set_mA}mA"  # put some text for the file name

## Start auto measurement
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    ## Turn off pump lasers and set signal to 25 mA
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=25, laser_ser=ser, verbose=False, gtl=True)
    ## Set current and record the spectrum
    for set_mA in mA_loop:
        ild_set, ild_act = set_laser_mA(slot=select_slot, mA=set_mA, laser_ser=ser, verbose=False, gtl=True)
        time.sleep(0.001)
        wavelength_nm, level_dBm = get_osa(start_nm=osa_para[0], stop_nm=osa_para[1], res_nm=osa_para[2], txt=txt)
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)








# %%
#==================================================
# Task 4: Gan saturation
#==================================================
## Turn on signal laser to 25 mA and vary the VOA
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    set_laser_mA(slot=3, mA=25, laser_ser=ser, verbose=False, gtl=True)


# %%
## Take one spectrum measurement
txt = f"Leo's demo Task 4, slot{select_slot}, {set_mA}mA"  # put some text for the file name
osa_para = [1540, 1560, 0.02]  # start_nm, stop_nm, res_nm
wavelength_nm, level_dBm = get_osa(start_nm=osa_para[0], stop_nm=osa_para[1], res_nm=osa_para[2], txt=txt)


# %%
## Turn off all 3 lasers
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)






























# %%
#==================================================
# Task 5: Fiber laser (Optional
#==================================================
## Increase current step-by-step on both pump and record the power
mA_range = np.arange(0, 500, 5)
pm_wavelength_nm = 1550
txt = "Leo's demo task 5"  # put some text for the file name

## Start auto measurement
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    measurement = []
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    ## Increase current step-by-step and record the power
    for set_mA in mA_range:
        ild_set, ild_act = set_laser_mA(slot=1, mA=set_mA, laser_ser=ser, verbose=False, gtl=True)
        ild_set, ild_act = set_laser_mA(slot=2, mA=set_mA, laser_ser=ser, verbose=False, gtl=True)
        time.sleep(0.001)
        get_wavelength_nm, power_mW, power_dBm = get_pm(pm, set_wavelength_nm=pm_wavelength_nm, verbose=True)
        measurement.append([ild_act, get_wavelength_nm, power_mW, power_dBm])
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)
measurement = np.asarray(measurement)
slot = measurement[0,0]
wavelength_nm = measurement[0,2]
name = f'laser-{datetime.now():%Y%m%dt%H%M%S}-slot1and2-wavelength{wavelength_nm}nm-{txt}'
np.savetxt(name+'.csv', measurement, delimiter=',', fmt='%f')    

## Load csv file and plot it 
arr = np.genfromtxt(name+'.csv', delimiter=",")
x = arr[:,1]  # ild_act
y1 = arr[:,3]  # power_mW
y2 = arr[:,4]  # power_dBm
plt.figure()
plt.plot(x,y1, '.')
plt.grid()
plt.ylabel('Power [mW]'); plt.xlabel('Current [mA]')
plt.title(f'{name}')
plt.tight_layout()
plt.savefig(name+'.jpg')
plt.show()


# %%
## Set current and record the spectrum
mA_loop =  [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
osa_para = [1400, 1700, 0.10]  # start_nm, stop_nm, res_nm
txt = f"Leo's demo Task 5, slot1and2, {set_mA}mA"  # put some text for the file name

## Start auto measurement
with serial.Serial(LASER_PORT, 19200, timeout=0.1, rtscts=True) as ser:
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    ## Set current and record the spectrum
    for set_mA in mA_loop:
        ild_set, ild_act = set_laser_mA(slot=1, mA=set_mA, laser_ser=ser, verbose=False, gtl=True)
        ild_set, ild_act = set_laser_mA(slot=2, mA=set_mA, laser_ser=ser, verbose=False, gtl=True)
        time.sleep(0.001)
        wavelength_nm, level_dBm = get_osa(start_nm=osa_para[0], stop_nm=osa_para[1], res_nm=osa_para[2], txt=txt)
    ## Turn off all 3 lasers
    set_laser_mA(slot=1, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=2, mA=-1, laser_ser=ser, verbose=False, gtl=True)
    set_laser_mA(slot=3, mA=-1, laser_ser=ser, verbose=False, gtl=True)




