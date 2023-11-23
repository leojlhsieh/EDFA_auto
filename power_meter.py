# %% 
import numpy as np
from numpy import log10
import matplotlib.pyplot as plt
import time
from datetime import datetime
from ThorlabsPM100 import ThorlabsPM100, USBTMC  # https://pypi.org/project/ThorlabsPM100/


# %%
## sudo chmod a+rw /dev/usbtmc0  ## a (all user)  + (add)  rw (read and write permissions)
inst = USBTMC(device="/dev/usbtmc0")
pm = ThorlabsPM100(inst=inst)
print('Done connecting to power meter')


# %%
set_wavelength_nm = 1550
pm.sense.correction.wavelength = set_wavelength_nm
pm.sense.average.count = 100
# for _ in range(20):
while True:
    time.sleep(1)
    get_wavelength_nm = pm.sense.correction.wavelength
    power_mW = max(1e-6, pm.read*1e3)
    power_dBm = 10*log10(power_mW)
    pm.system.beeper.immediate()
    print(f'{datetime.now():%Y%m%dt%H%M%S.%f} p = {power_mW:.6f} mW ({power_dBm:.2f} dBm) @ {get_wavelength_nm:.0f} nm')



