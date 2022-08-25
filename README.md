# LIS2DH12

Based on ![LIS2HH12](https://github.com/tuupola/micropython-lis2hh12/blob/ffba6ab86ede3a517d68d9fcb8a1b8898c69b7d3/lis2hh12.py) driver from tuupola.


## Resources
![Product page](https://www.st.com/en/mems-and-sensors/lis2dh12.html#documentation)
![Datasheet](https://www.st.com/resource/en/datasheet/lis2dh12.pdf)

## Method and atribute description

### (method) __init__

Initialize a new class to extract values from an LIS2DH12 accelerometer sensor.

```
:param i2c: machine.SoftI2C instance, connected to the accelerometer.
:param address: I2C bus address of the accelerometer.
:param sensors: String containing the senor axis to enable. Can contain 'x', 'y' and/or 'z'.
:param bit_mode: Measurement size on the sensor. Either 8, 10 or 12.
:param data_rate: Speed at which the sensor collects the measurement values.
    Can be: '1Hz', '10Hz', '25Hz', '50Hz', '100Hz', '200Hz', '400Hz' or
    - In 8 bit_mode: '1.344kHz' or '1.620kHz'
    - In 10 or 12 bit_mode: '5.376kHz'
:param scale: Sensitivity at which the sensor takes measurements. 
    Will be scaled automatically by this library to SI m/s² or G-factor.
    Can be: '2g', '4g', '8g' or '16g'
:param output_units: output values in SI-units (m/s²) or G's. Can be either: 'SI' or 'G'
```


```python
### example fri3d 2022 badge
from LIS2DH12 import LIS2DH12
i2c = BADGE.i2c()
a = LIS2DH12(i2c, 0x18)
print(a.acceleration)
```
```python
### or with a context manager
from LIS2DH12 import LIS2DH12
i2c = BADGE.i2c()
with LIS2DH12(i2c, 0x18) as a:
    print(a.acceleration)
```

### (method) modify

Modify parameters for the next measurement value readout.

```
:param i2c: Machine.SoftI2C instance, connected to the accelerometer.
:param address: I2C bus address of the accelerometer.
:param sensors: String containing the senor axis to enable. Can contain 'x', 'y' and/or 'z'.
:param bit_mode: Measurement size on the sensor. Either 8, 10 or 12.
:param data_rate: Speed at which the sensor collects the measurement values.
    Can be: '1Hz', '10Hz', '25Hz', '50Hz', '100Hz', '200Hz', '400Hz' or
    - In 8 bit_mode: '1.344kHz' or '1.620kHz'
    - In 10 or 12 bit_mode: '5.376kHz'
:param scale: Sensitivity at which the sensor takes measurements. 
    Will be scaled automatically by this library to SI m/s² or G-factor.
    Can be: '2g', '4g', '8g' or '16g'
:param output_units: output values in SI-units (m/s²) or G's. Can be either: 'SI' or 'G'
:param verbose: show what is going to be writen to ctrl_reg1 - ctrl_reg6
```

### (method) enable_backlight

Enable or disable the backlight on the fri3d 2022 badge.
The line that controls the backlight is connected to the INT2 pin of the accelerometer.

```
:param enable: boolean: True to turn on the backlight, false to turn off.
```

### (attribute - read only)

Get a measurement value.

```        
:param verbose: show the raw values from the LSB and MSB from the x, y and z registers.
    Next show the decoded and scaled measurement values.
:return: list with the parsed x, y and z measurements.
```

### (attribute - read only) whoami

Read LIS2DH12 accelerometer ID.
```
:return: should be int: 51.
```
