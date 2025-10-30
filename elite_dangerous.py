import gremlin
from gremlin.spline import CubicSpline
from gremlin.input_devices import keyboard
from vjoy.vjoy import AxisName

# GremlinEx plugin script device list


# device CH PRO PEDALS USB  - axis count: 3  hat count: 0  button count: 0
PEDALS_NAME = "CH PRO PEDALS USB "
PEDALS_GUID = "36ae6380aae011f08001444553540000"

# device WINWING JOYSTICK BASE2 + F18 GRIP - axis count: 7  hat count: 1  button count: 21
JOYSTICK_NAME = "WINWING JOYSTICK BASE2 + F18 GRIP"
JOYSTICK_GUID = "37f05960aae011f08008444553540000"

# device WINWING THROTTLE BASE2 + F18 HANDLE - axis count: 8  hat count: 0  button count: 111
THROTTLE_NAME = "WINWING THROTTLE BASE2 + F18 HANDLE"
THROTTLE_GUID = "386e14e0aae011f08009444553540000"

# plugin decorator definitions

# decorators for mode Default
joystick = gremlin.input_devices.JoystickDecorator(JOYSTICK_NAME, JOYSTICK_GUID, "Default")
pedals = gremlin.input_devices.JoystickDecorator(PEDALS_NAME, PEDALS_GUID, "Default")
throttle = gremlin.input_devices.JoystickDecorator(THROTTLE_NAME, THROTTLE_GUID, "Default")

@pedals.axis(1)
def on_left_pedal(event, vjoy):
    vjoy[1].axis(AxisName.RX).value = (event.value + 1) / 2 * -1

@pedals.axis(2)
def on_right_pedal(event, vjoy):
    vjoy[1].axis(AxisName.RX).value = (event.value + 1) / 2
