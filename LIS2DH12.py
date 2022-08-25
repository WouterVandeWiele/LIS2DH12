import ustruct
import time
import machine
from micropython import const


class LIS2DH12:
    SI = const(9.81)
    BACKLIGHT_MIN = const(0)
    BACKLIGHT_MAX = const(10)
    '''
    product page: https://www.st.com/en/mems-and-sensors/lis2dh12.html
    datasheet: https://www.st.com/resource/en/datasheet/lis2dh12.pdf
    '''
    def __init__(
            self,
            i2c,
            address,
            sensors = 'xyz',
            bit_mode = 10,
            data_rate = '10Hz',
            scale = '2g',
            output_units = 'G',
            backlight_duty = 10,
            timer = 0,
        ):
        '''
        Initialize a new class to extract values from an LIS2DH12 accelerometer sensor.
        
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
        # :param backlight: enable INT2 functions and switch to active high signal. (fri3d badge backlight)
        
        ### example fri3d 2022 badge
        >>> from LIS2DH12 import LIS2DH12
        >>> i2c = BADGE.i2c()
        >>> a = LIS2DH12(i2c, 0x18)
        >>> print(a.acceleration)
        
        ### or with a context manager
        >>> from LIS2DH12 import LIS2DH12
        >>> i2c = BADGE.i2c()
        >>> with LIS2DH12(i2c, 0x18) as a:
        >>>     print(a.acceleration)
        '''
        
        self._i2c = i2c
        self._address = address
        self._sensors = sensors
        self._bit_mode = None
        self._data_rate_speed = None
        self._scale_factor = None
        self._scale_divide = 1
        self._output_units = None
        self._backlight_duty = None
        self._timer_value = timer
        self._timer = None
        self._stop_timer = False
        
        # control reg[0] starts at CTRL_REG1 (0x20)
        self._ctrl_reg = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        self.modify(
            sensors = sensors,
            bit_mode = bit_mode,
            data_rate = data_rate,
            scale = scale,
            output_units = output_units,
            backlight_duty = backlight_duty
        )


    def modify(
            self,
            sensors = None,
            bit_mode = None,
            data_rate = None,
            scale = None,
            output_units = None,
            backlight_duty = 10,
            verbose = False,
        ):
        '''
        Modify parameters for the next measurement value readout.
        
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
        :param backlight: enable INT2 functions and switch to active high signal. (fri3d badge backlight)
        :param verbose: show what is going to be writen to ctrl_reg1 - ctrl_reg6
        '''
        if sensors:
            self._enable_sensors(sensors)
        if bit_mode:
            self._measurement_size(bit_mode)
        if data_rate:
            self._data_rate(data_rate)
        if scale:
            self._scale(scale)
        if output_units:
            if output_units in ['SI', 'G']:
                self._output_units = output_units
            else:
                raise RuntimeError(
                    f'unknown output units: {output_units}'
                )

        if backlight_duty:
            self._timer = None
            
            if (self.BACKLIGHT_MIN > backlight_duty):
                self._stop_timer = True
                self._backlight_duty = self.BACKLIGHT_MIN
            elif (backlight_duty > self.BACKLIGHT_MAX):
                self._stop_timer = True
                self._backlight_duty = self.BACKLIGHT_MAX
            else:
                self._backlight_duty = backlight_duty
                self._stop_timer = False
                self._timer = machine.Timer(self._timer_value)
                self._enable_backlight_timer_on(self._backlight_duty)
                
            self._enable_backlight(self._backlight_duty)

        byte_array = b''.join([ustruct.pack('<b', x) for x in self._ctrl_reg])
        if verbose:
            print(f'byte_array: {byte_array}')
        self._i2c.writeto_mem(self._address, 0xA0, byte_array)


    def _enable_sensors(self, sensors):
        # enable sensors
        self._ctrl_reg[0] &= const(0xF8)
        if 'x' in sensors:
            self._ctrl_reg[0] |= const(0x01)
        if 'y' in sensors:
            self._ctrl_reg[0] |= const(0x02)
        if 'z' in sensors:
            self._ctrl_reg[0] |= const(0x04)


    def _measurement_size(self, bit_mode):
        # configure measurement size
        self._ctrl_reg[0] &= const(0xF7)
        self._ctrl_reg[3] &= const(0xF7)
        if bit_mode == 10:
            # normal mode
            self._bit_mode = 10
        elif bit_mode == 8:
            # low power
            self._ctrl_reg[0] |= const(0x08)
            self._bit_mode = 8
        elif bit_mode == 12:
            # high resolution
            self._ctrl_reg[3] |= const(0x08)
            self._bit_mode = 12
        else:
            raise RuntimeError(
                f'Unknow bit mode selected: {bit_mode}'
            )


    def _data_rate(self, data_rate):
        # configure data rate
        self._ctrl_reg[0] &= const(0x0F)
        if data_rate == 'power-down':
            self.data_rate = 'power-down'
        elif data_rate == '1Hz':
            self._ctrl_reg[0] |= const(0x10)
            self.data_rate = '1hz'
        elif data_rate == '10Hz':
            self._ctrl_reg[0] |= const(0x20)
            self.data_rate = '10hz'
        elif data_rate == '25Hz':
            self._ctrl_reg[0] |= const(0x30)
            self.data_rate = '25hz'
        elif data_rate == '50Hz':
            self._ctrl_reg[0] |= const(0x40)
            self.data_rate = '50hz'
        elif data_rate == '100Hz':
            self._ctrl_reg[0] |= const(0x50)
            self.data_rate = '100hz'
        elif data_rate == '200Hz':
            self._ctrl_reg[0] |= const(0x60)
            self.data_rate = '200hz'
        elif data_rate == '400Hz':
            self._ctrl_reg[0] |= const(0x70)
            self.data_rate = '400hz'
        elif data_rate == '1.620kHz':
            if self._bit_mode == 8:
                self._ctrl_reg[0] |= const(0x80)
            else:
                raise RuntimeError(
                    f'1.620kHz data rate not supported in bit_mode: {bit_mode} (only bit_mode 8)'
                )
        elif data_rate == '1.344kHz':
            if self._bit_mode == 8:
                self._ctrl_reg[0] |= const(0x90)
            else:
                raise RuntimeError(
                    f'1.344kHz data rate not supported in bit_mode: {bit_mode} (only bit_mode 8)'
                )
        elif data_rate == '5.376kHz':
            if (self._bit_mode == 10) or (self._bit_mode == 12):
                self._ctrl_reg[0] |= const(0x90)
            else:
                raise RuntimeError(
                    f'1.344kHz data rate not supported in bit_mode: {bit_mode} (only bit_mode 10 or 12)'
                )
        else:
            raise RuntimeError(
                f'Unknow data rate selected: {data_rate}'
            )


    def _scale(self, scale):
        self._ctrl_reg[3] &= const(0x30)
        if scale == '2g':
            self._scale_factor = '2g'
            self._scale_divide = 16384  # 1024*16
        elif scale == '4g':
            self._ctrl_reg[3] |= const(0x10)
            self._scale_factor = '4g'
            self._scale_divide = 8192   # 1024*8
        elif scale == '8g':
            self._ctrl_reg[3] |= const(0x20)
            self._scale_factor = '8g'
            self._scale_divide = 4096   # 1024*4
        elif scale == '16g':
            self._ctrl_reg[3] |= const(0x30)
            self._scale_factor = '16g'
            self._scale_divide = 1024   # 1024*1
        else:
            raise RuntimeError(
                f'Unknow scale: {scale}'
            )


    def _enable_backlight(self, enable):
        if enable:
            self._ctrl_reg[5] = const(0xFF)
            self._i2c.writeto_mem(self._address, 0x25, b'\FF')
        else:
            self._ctrl_reg[5] = const(0x00)
            self._i2c.writeto_mem(self._address, 0x25, b'\00')


    def _enable_backlight_timer_on(self, event):
        self._enable_backlight(False)
        
        # self._timer.deinit()
        if not(self._stop_timer): # and (self._backlight_duty == self.BACKLIGHT_MIN)):
            self._timer.init(
                period=self.BACKLIGHT_MAX-self._backlight_duty,
                mode=machine.Timer.ONE_SHOT,
                callback=self._enable_backlight_timer_off
            )
        

    def _enable_backlight_timer_off(self, event):
        self._enable_backlight(True)
        
        # self._timer.deinit()
        if not(self._stop_timer): # and (self._backlight_duty == self.BACKLIGHT_MAX)):
            self._timer.init(
                period=self._backlight_duty,
                mode=machine.Timer.ONE_SHOT,
                callback=self._enable_backlight_timer_on
            )
        
    
    @property
    def acceleration(self, verbose: bool=False):
        '''
        Get a measurement value.
        
        :param verbose: show the raw values from the LSB and MSB from the x, y and z registers.
            Next show the decoded and scaled measurement values.
        :return: list with the parsed x, y and z measurements.
        '''
        xyz = [0, 0, 0]
        lsb_buffer = 0
        value_raw = self._i2c.readfrom_mem(self._address, 0xA8, 6)
        
        if verbose:
        	print(value_raw)
        
        for index in range(3):
            value = value_raw[index*2:index*2+2]
            xyz[index] = ustruct.unpack('<h', value)[0] / self._scale_divide

            if self._output_units == 'SI':
                xyz[index] *= self.SI

            if verbose:
                print(f'index {index}, {value}')

        return xyz

  
    @property
    def whoami(self):
        '''
        Read LIS2DH12 accelerometer ID.
        :return: should be int: 51.
        '''
        return ord(
            self._i2c.readfrom_mem(self._address, 0x0F, 1)
        )


    # context manager stuff:
    def __enter__(self):
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        pass

