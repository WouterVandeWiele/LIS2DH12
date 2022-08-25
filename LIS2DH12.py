import ustruct
import time
import machine
from micropython import const


class LIS2DH12:
    SI = const(9.81)

    def __init__(
            self,
            i2c,
            address,
            sensors = 'xyz',
            bit_mode = 10,
            data_rate = '10Hz',
            scale = '2g',
            output_units = 'G',
        ):
        
        self._i2c = i2c
        self._address = address
        self._sensors = sensors
        self._bit_mode = None
        self._data_rate_speed = None
        self._scale_factor = None
        self._scale_divide = 1
        self._output_units = None
        
        # control reg[0] starts at CTRL_REG1 (0x20)
        self._ctrl_reg = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        
        self.modify(
            sensors = sensors,
            bit_mode = bit_mode,
            data_rate = data_rate,
            scale = scale,
            output_units = output_units,
        )


    def modify(
            self,
            sensors = None,
            bit_mode = None,
            data_rate = None,
            scale = None,
            output_units = None,
            verbose = False,
        ):
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

        self.enable_backlight(True)
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


    def enable_backlight(self, enable):
        if enable:
            self._ctrl_reg[5] = const(0xFF)
            self._i2c.writeto_mem(self._address, 0x25, b'\FF')
        else:
            self._ctrl_reg[5] = const(0x00)
            self._i2c.writeto_mem(self._address, 0x25, b'\00')


    @property
    def acceleration(self, verbose: bool=False):
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
        return ord(
            self._i2c.readfrom_mem(self._address, 0x0F, 1)
        )


    # context manager stuff:
    def __enter__(self):
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        pass

