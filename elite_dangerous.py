import gremlin
from gremlin.util import parse_guid, log
from vjoy.vjoy import AxisName
import io
import json
import os
import threading
import time
import traceback
import unittest

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

# device access
vjoy = gremlin.joystick_handling.VJoyProxy()
joy = gremlin.input_devices.JoystickProxy()
pedals_raw = joy[parse_guid(PEDALS_GUID)]
joystick_raw = joy[parse_guid(JOYSTICK_GUID)]
throttle_raw = joy[parse_guid(THROTTLE_GUID)]

# reading game status
status_path = os.path.expanduser(R"~\Saved Games\Frontier Developments\Elite Dangerous\Status.json")
flags = 0

DOCKED_FLAG = 0x00000001
LANDED_FLAG = 0x00000002
LANDING_GEAR_DOWN_FLAG = 0x00000004
SHIELDS_UP_FLAG = 0x00000008
SUPERCRUISE_FLAG = 0x00000010
FLIGHT_ASSIST_OFF_FLAG = 0x00000020
HARDPOINTS_DEPLOYED_FLAG = 0x00000040
IN_WING_FLAG = 0x00000080
LIGHTS_ON_FLAG = 0x00000100
CARGO_SCOOP_DEPLOYED_FLAG = 0x00000200
SILENT_RUNNING_FLAG = 0x00000400
SCOOPING_FUEL_FLAG = 0x00000800
SRV_HANDBRAKE_FLAG = 0x00001000
SRV_TURRET_VIEW_FLAG = 0x00002000
SRV_TURRET_RETRACTED_FLAG = 0x00004000
SRV_DRIVE_ASSIST_FLAG = 0x00008000
FSD_MASS_LOCKED_FLAG = 0x00010000
FSD_CHARGING_FLAG = 0x00020000
FSD_COOLDOWN_FLAG = 0x00040000
FUEL_LOW_FLAG = 0x00080000
OVERHEATING_FLAG = 0x00100000
HAS_LAT_LON_FLAG = 0x00200000
IS_IN_DANGER_FLAG = 0x00400000
BEING_INTERDICTED_FLAG = 0x00800000
IN_MAIN_SHIP_FLAG = 0x01000000
IN_FIGHTER_FLAG = 0x02000000
IN_SRV_FLAG = 0x04000000
ANALYSIS_MODE_FLAG = 0x08000000
NIGHT_VISION_FLAG = 0x10000000
ALTITUDE_AVG_RADIUS_FLAG = 0x20000000
FSD_JUMP_FLAG = 0x40000000
SRV_HIGH_BEAM_FLAG = 0x80000000

def on(flag):
    return (flags & flag) == flag

def off(flag):
    return not on(flag)

cooldowns = {}

# The default cooldown is a bit over twice as long as the refresh_status interval.
# This will cause the toggle to be retried on every third refresh.
def toggle_with_cooldown(scope, button, cooldown_seconds=1.1):
    now = time.time()
    cooldown_end = cooldowns.get(scope, 0)
    if cooldown_end < now:
        log(f"Toggling {scope}!")
        cooldowns[scope] = now + cooldown_seconds
        short_press(button)
    else:
        log(f"Cooldown active for {scope}, skipping toggle.")

def short_press(button):
    button.is_pressed = True
    def release():
        button.is_pressed = False
    threading.Timer(0.2, release).start()


# Main

@gremlin.input_devices.gremlin_start()
def on_profile_start():
    log("on_profile_start")
    adjust_throttle()

@gremlin.input_devices.gremlin_stop()
def on_profile_stop():
    log("on_profile_stop")

@gremlin.input_devices.periodic(0.5)
def refresh_status():
    try:
        #log("---")
        with open(status_path) as f:
            data = json.load(f)
        global flags
        new_flags = data['Flags']
        if new_flags != flags:
            log(f"flags {flags}")
        flags = new_flags
        sync_lights()
        sync_night_vision()
        sync_landing_gear()
        sync_hardpoints()
    except Exception as e:
        # Reading the file may fail if we read it at a bad time.
        # For example the file may be empty, so parsing the JSON fails.
        # If the exception is not caught, gremlin stops the periodic calls.
        log(f"refresh_status failed:\n{traceback.format_exc()}")


# Ship lights

input = 65
output = 1
lights_input = throttle_raw.button(input)
lights_output = vjoy[1].button(output)

@throttle.button(input)
def sync_lights(event = None):
    actual = on(LIGHTS_ON_FLAG)
    desired = lights_input.is_pressed
    #log(f"sync_lights status={actual} desired={desired}")
    if actual == desired:
        return
    toggle_with_cooldown("lights", lights_output)


# Night vision

input = 67
output = 2
night_vision_input = throttle_raw.button(input)
night_vision_output = vjoy[1].button(output)

@throttle.button(input)
def sync_night_vision(event = None):
    actual = on(NIGHT_VISION_FLAG)
    desired = night_vision_input.is_pressed
    #log(f"sync_night_vision actual={actual} desired={desired}")
    if actual == desired:
        return
    toggle_with_cooldown("night vision", night_vision_output)


# Landing gear

input = 74
output = 3
landing_gear_input = throttle_raw.button(input)
landing_gear_output = vjoy[1].button(output)

@throttle.button(input)
def sync_landing_gear(event = None):
    actual = on(LANDING_GEAR_DOWN_FLAG)
    desired = landing_gear_input.is_pressed
    #log(f"sync_landing_gear actual={actual} desired={desired}")
    if actual == desired:
        return
    toggle_with_cooldown("landing gear", landing_gear_output)


# Hardpoints

input = 93
output = 4
hardpoints_input = throttle_raw.button(input)
hardpoints_output = vjoy[1].button(output)

@throttle.button(input)
def sync_hardpoints(event = None):
    actual = on(HARDPOINTS_DEPLOYED_FLAG)
    desired = hardpoints_input.is_pressed
    #log(f"sync_hardpoints actual={actual} desired={desired}")
    if actual == desired:
        return
    toggle_with_cooldown("hardpoints", hardpoints_output)


# Throttle

right_throttle = throttle_raw.axis(4)
left_pedal = pedals_raw.axis(1)

@throttle.axis(right_throttle._index)
def on_left_pedal(event):
    adjust_throttle()

@pedals.axis(left_pedal._index)
def on_right_pedal(event):
    adjust_throttle()

def adjust_throttle():
    vjoy[1].axis(AxisName.RX).value = calculate_throttle(
        forward = right_throttle.value * -1,
        backward = left_pedal.value,
    )

def calculate_throttle(forward, backward):
    forward = scaled_0_to_1(forward)            #  0..1 range
    backward = scaled_0_to_1(backward) * -1     # -1..0 range
    backward = backward * (1 + forward)         # up to -2..0 range, to linearly counter forward and reach exactly -1 when summed
    return forward + backward                   # -1..1 range

class test_calculate_throttle(unittest.TestCase):
    def test_no_throttle(self):
        self.assertEqual(calculate_throttle(forward=-1, backward=-1), 0)

    def test_full_forward(self):
        self.assertEqual(calculate_throttle(forward=1, backward=-1), 1)

    def test_full_backward(self):
        self.assertEqual(calculate_throttle(forward=-1, backward=1), -1)

    def test_full_backward_completely_overshadows_full_forward(self):
        self.assertEqual(calculate_throttle(forward=1, backward=1), -1)

    def test_half_backward_is_needed_to_counter_full_forward(self):
        self.assertEqual(calculate_throttle(forward=1, backward=0), 0)

    def test_third_backward_is_needed_to_counter_half_forward(self):
        self.assertAlmostEqual(calculate_throttle(forward=0, backward=-0.333), 0, places=3)


# scales a -1..1 axis value to 0..1 range
def scaled_0_to_1(value):
    return (value + 1) / 2

class test_scaled_0_to_1(unittest.TestCase):
    def test_scales_an_axis_to_range_0_to_1(self):
        for input, expected in [
                (-1, 0),
                ( 0, 0.5),
                ( 1, 1)
            ]:
            with self.subTest(input=input, expected=expected):
                self.assertEqual(scaled_0_to_1(input), expected)


def run_unit_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite([
        loader.loadTestsFromTestCase(test_calculate_throttle),
        loader.loadTestsFromTestCase(test_scaled_0_to_1),
    ])

    with io.StringIO() as buffer:
        runner = unittest.TextTestRunner(stream=buffer, verbosity=2)
        result = runner.run(suite)
        output = buffer.getvalue()

    log(f"Unit test results:\n\n{output}")
    if not result.wasSuccessful():
        raise RuntimeError("Unit tests failed")

run_unit_tests()
