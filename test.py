# timer example

from LIS2DH12 import LIS2DH12
import machine

i2c = BADGE.i2c()
a = LIS2DH12(i2c, 0x18)

timer0 = machine.Timer(0)
timer0.init(period=100, mode=machine.Timer.PERIODIC, callback=lambda t: print(a.acceleration))

#timer0.deinit()

