# %% 
import numpy as np
from numpy import log10
import matplotlib.pyplot as plt
import time
from datetime import datetime
from ThorlabsPM100 import ThorlabsPM100, USBTMC  # https://pypi.org/project/ThorlabsPM100/
import serial

# !ls -l /dev/ttyUSB*
LASER_PORT = '/dev/ttyUSB1'
OSA_PORT = '/dev/ttyUSB2'



# %%
def inilize_osa():
    with serial.Serial(OSA_PORT, 115200, timeout=1, rtscts=True) as ser:
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
        trace = 'A'
        give_cmd("*IDN?")
        give_cmd("*CLS")  # clear status
        give_cmd("*RST")  # reset
        give_cmd("STAWL600.00")    # start wavelength (600 - 1700nm)
        give_cmd("STPWL1700.00")    # stop wavelength (600- 1700nm)
        give_cmd("SHI1")            # Sensitivity (SNAT,SMID,SHI1,SHI2,SHI3)
        give_cmd("RESLN0.01")       # resolution (0.01 - 2.00 nm)
        give_cmd("SGL")             # single sweep
        while give_cmd("SWEEP?") == [b'1']:
            time.sleep(1)
        wave, = give_cmd('WDAT'+trace, verbose=False)
        value, = give_cmd('LDAT'+trace, verbose=False)
        wave_str = wave.decode('utf-8').split(',')[1:]
        value_str = value.decode('utf-8').split(',')[1:]
        wavelength_nm = [float(x) for x in wave_str]
        level_dBm = [float(x) for x in value_str]
        plt.figure()
        plt.plot(wavelength_nm, level_dBm)
        plt.ylim(-90, 10)
        return None
inilize_osa()




# %%



# %% Setting OSA parameters 
'''Setting OSA parameters'''
'''Setting OSA parameters'''
def setOSA():
    try:
        rm = pyvisa.ResourceManager()
        osa = rm.open_resource('ASRL4')
        osa.Terminator = 'CR/LF'
        osa.InputBufferSize = 10*20001    
        osa.timeout = 10_000  # [ms]
        trace = 'A'   

        ## Sets the measuring sensitivity.
        osa.query('SNAT')
        # osa.query('SMID')
        # osa.query('SHI1')
        # osa.query('SHI2')
        # osa.query('SHI3')

        osa.query('STAWL1000.00')
        osa.query('STPWL1250.00')
        
        ## RESLN*.** : Sets the resolution. (Unit: nm), 0.01 to 2.00
        # osa.query('RESLN2.00')
        # osa.query('RESLN1.00')
        osa.query('RESLN0.50')
        # osa.query('RESLN0.01')

        ## 'SNAT' + 'RESLN2.0' =  5.01 sec
        ## 'SNAT' + 'RESLN1.0' =  8.65 sec
        ## 'SNAT' + 'RESLN0.5' = 12.04 sec
        ## 'SHI1' + 'RESLN2.0' = 17.78 sec
        ## 'SHI1' + 'RESLN0.5' = 51.67 sec

        # osa.query('RPT')  # repeat sweeping
        # osa.query('STP')  # stop sweeping
    
    except Exception as e:
        print(f"An error occurred while using OSA: {e}")
    
    finally:
        osa.close()
        rm.close()
    print('Done setOSA')
    return None
setOSA()




#### Do acquisition from Optical Spectrum Analyzers (OSA)
def acqOSA(save=False, verbose=True):  # spectrum_nm_dBm = acqOSA
    print('\nAcquisition OSA...')
    try:
        rm = pyvisa.ResourceManager()
        osa = rm.open_resource('ASRL4')
        osa.Terminator = 'CR/LF'
        osa.InputBufferSize = 10*20001    
        osa.timeout = 100_000  # [ms]
        trace = 'A'   
        osa.query('SGL')  # single sweeping
        while osa.query('SWEEP?') != '0\r\n':
            time.sleep(1)  # wait until sweep is stop ('0\r\n')
        wave = osa.query_ascii_values('WDAT'+trace )
        wavelength = wave[1:] 
        value = osa.query_ascii_values('LDAT'+trace )
        level = value[1:]  
        osa.query('STP')  # stop sweeping
    
    except Exception as e:
        print(f"An error occurred while using OSA: {e}")
    
    finally:
        osa.close()
        rm.close()
    wavelength = np.asarray(wavelength)
    level = np.asarray(level)
    spectrum = np.stack((wavelength, level), axis=0)

    #%% Plot
    if verbose:
        plt.figure()
        plt.plot(spectrum[0], spectrum[1], alpha=0.8)
        plt.ylim(-90, -10)
        plt.xlim(spectrum[0].min(), spectrum[0].max())
        plt.grid()
        plt.ylabel('Power [dBm]'); plt.xlabel('Wavelength [nm]')
        plt.axvline(1030, color='C1', linestyle='--', alpha=0.7)
        plt.axvline(1083, color='C1', linestyle='--', alpha=0.7)
        fig_name = f'OSA-{datetime.now():%Y%m%dt%H%M%S.%f}'[:-3]
        plt.title(f'{fig_name}\nOSA measurement')
        plt.tight_layout()
        if save:
            plt.savefig(fig_name+'.jpg')
        plt.show()
    if save:
        np.savez(fig_name+'.npz', spectrum)

    return spectrum
