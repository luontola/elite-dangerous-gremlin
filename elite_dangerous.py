import gremlin
from gremlin.util import parse_guid
from vjoy.vjoy import AxisName

# GremlinEx plugin script device list

# device WINWING JOYSTICK BASE2 + F18 GRIP - axis count: 7  hat count: 1  button count: 21
JOYSTICK_NAME = "WINWING JOYSTICK BASE2 + F18 GRIP"
JOYSTICK_GUID = "37f05960aae011f08008444553540000"

# device WINWING THROTTLE BASE2 + F18 HANDLE - axis count: 8  hat count: 0  button count: 111
THROTTLE_NAME = "WINWING THROTTLE BASE2 + F18 HANDLE"
THROTTLE_GUID = "386e14e0aae011f08009444553540000"

# device CH PRO PEDALS USB  - axis count: 3  hat count: 0  button count: 0
PEDALS_NAME = "CH PRO PEDALS USB "
PEDALS_GUID = "36ae6380aae011f08001444553540000"

# plugin decorator definitions
## decorators for mode Default
joystick = gremlin.input_devices.JoystickDecorator(JOYSTICK_NAME, JOYSTICK_GUID, "Default")
throttle = gremlin.input_devices.JoystickDecorator(THROTTLE_NAME, THROTTLE_GUID, "Default")
pedals = gremlin.input_devices.JoystickDecorator(PEDALS_NAME, PEDALS_GUID, "Default")

# reading input devices
joy = gremlin.input_devices.JoystickProxy()
pedals_raw = joy[parse_guid(PEDALS_GUID)]
joystick_raw = joy[parse_guid(JOYSTICK_GUID)]
throttle_raw = joy[parse_guid(THROTTLE_GUID)]

@gremlin.input_devices.gremlin_start()
def on_profile_start():
    vjoy = gremlin.joystick_handling.VJoyProxy()
    adjust_throttle(vjoy)

@gremlin.input_devices.gremlin_stop()
def on_profile_stop():
    # stop background threads, if any
    pass

@pedals.axis(1)
def on_left_pedal(event, vjoy):
    adjust_throttle(vjoy)

@pedals.axis(2)
def on_right_pedal(event, vjoy):
    adjust_throttle(vjoy)

def adjust_throttle(vjoy):
    # scale to -1..0 range
    backward = -1 * scaled_0_to_1(pedals_raw.axis(1).value)
    # scale to 0..1 range
    forward = scaled_0_to_1(pedals_raw.axis(2).value)
    # backward takes priority if both pedals are pressed (panic reverse),
    # but filter out light presses near the deadzone
    if backward < -0.25:
        value = backward # strong backward press
    elif forward > 0.25:
        value = forward # strong forward press
    else:
        value = backward + forward # light presses or idle
    vjoy[1].axis(AxisName.RX).value = value

# scales a -1..1 value to 0..1 range
def scaled_0_to_1(value):
    return (value + 1) / 2
