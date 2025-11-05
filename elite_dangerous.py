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
from unittest.mock import Mock

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
DEFAULT_MODE = "Default"
joystick = gremlin.input_devices.JoystickDecorator(JOYSTICK_NAME, JOYSTICK_GUID, DEFAULT_MODE)
throttle = gremlin.input_devices.JoystickDecorator(THROTTLE_NAME, THROTTLE_GUID, DEFAULT_MODE)
pedals = gremlin.input_devices.JoystickDecorator(PEDALS_NAME, PEDALS_GUID, DEFAULT_MODE)

# alternative to using the above decorators
## converts a JoystickProxy button to a JoystickDecorator button
def on_button(input, mode=DEFAULT_MODE):
    return gremlin.input_devices._button(button_id=input._index, device_guid=input._joystick_guid, mode=mode)

## converts a JoystickProxy axis to a JoystickDecorator axis
def on_axis(input, mode=DEFAULT_MODE):
    return gremlin.input_devices._axis(axis_id=input._index, device_guid=input._joystick_guid, mode=mode)

# device access
vjoy = gremlin.joystick_handling.VJoyProxy()
joy = gremlin.input_devices.JoystickProxy()
joystick_raw = joy[parse_guid(JOYSTICK_GUID)]
throttle_raw = joy[parse_guid(THROTTLE_GUID)]
pedals_raw = joy[parse_guid(PEDALS_GUID)]

# reading game status
status_path = os.path.expanduser(R"~\Saved Games\Frontier Developments\Elite Dangerous\Status.json")
flags = 0
gui_focus = 0

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

GUI_NO_FOCUS = 0
GUI_INTERNAL_PANEL = 1 # right hand side
GUI_EXTERNAL_PANEL = 2 # left hand side
GUI_COMMS_PANEL = 3 # top
GUI_ROLE_PANEL = 4 # bottom
GUI_STATION_SERVICES = 5
GUI_GALAXY_MAP = 6
GUI_SYSTEM_MAP = 7
GUI_ORRERY = 8
GUI_FSS_MODE = 9
GUI_SAA_MODE = 10
GUI_CODEX = 11

def has_flag(flag):
    return (flags & flag) == flag

# The default cooldown is a bit over twice as long as the refresh_status interval.
# This will cause the toggle to be retried on every third refresh.
REFRESH_INTERVAL = 0.5
DEFAULT_COOLDOWN = 1.1

def short_press(button):
    button.is_pressed = True
    def release():
        button.is_pressed = False
    threading.Timer(0.2, release).start()

class ToggleController():
    def __init__(self, is_synced, output, cooldown_seconds=DEFAULT_COOLDOWN):
        self._is_synced = is_synced
        self._output = output
        self._cooldown_seconds = cooldown_seconds
        self._cooldown_end = None

    def periodic_sync(self, now = None):
        if self._is_synced():
            self._cooldown_end = None
            return
        now = now or time.time()
        if self._cooldown_end is None:
            self._cooldown_end = now + self._cooldown_seconds
        elif self._cooldown_end < now:
            self._cooldown_end = None
            short_press(self._output)

    def manual_toggle(self):
        self._cooldown_end = None
        if self._is_synced():
            return
        short_press(self._output)

class test_ToggleController(unittest.TestCase):
    class FakeButton():
        def __init__(self):
            self.is_pressed = None

    def setUp(self):
        self.output = self.FakeButton()
        self.aligned = lambda: True
        self.deviating = lambda: False

    def test_periodic_sync__when_aligned__does_nothing(self):
        ctrl = ToggleController(self.aligned, self.output, cooldown_seconds=4)
        now = 1000
        
        ctrl.periodic_sync(now)

        self.assertEqual(self.output.is_pressed, None)
        self.assertEqual(ctrl._cooldown_end, None)

    def test_periodic_sync__when_deviating__starts_a_cooldown(self):
        ctrl = ToggleController(self.deviating, self.output, cooldown_seconds=4)
        now = 1000
        
        ctrl.periodic_sync(now)

        self.assertEqual(self.output.is_pressed, None)
        self.assertEqual(ctrl._cooldown_end, 1004)

    def test_periodic_sync__when_deviating_and_in_cooldown__does_nothing(self):
        ctrl = ToggleController(self.deviating, self.output, cooldown_seconds=4)
        now = 1000
        ctrl.periodic_sync(now)

        now = 1003.9
        ctrl.periodic_sync(now)

        self.assertEqual(self.output.is_pressed, None)
        self.assertEqual(ctrl._cooldown_end, 1004)

    def test_periodic_sync__when_deviating_and_after_cooldown__presses_the_button_and_clears_the_cooldown(self):
        ctrl = ToggleController(self.deviating, self.output, cooldown_seconds=4)
        now = 1000
        ctrl.periodic_sync(now)

        now = 1004.1
        ctrl.periodic_sync(now)

        self.assertEqual(self.output.is_pressed, True)
        self.assertEqual(ctrl._cooldown_end, None)

    def test_periodic_sync__when_aligned_and_in_cooldown__only_clears_the_cooldown(self):
        is_synced = False
        ctrl = ToggleController(lambda: is_synced, self.output, cooldown_seconds=4)
        now = 1000
        ctrl.periodic_sync(now)

        is_synced = True
        ctrl.periodic_sync(now)

        self.assertEqual(self.output.is_pressed, None)
        self.assertEqual(ctrl._cooldown_end, None)

    def test_the_cooldown_uses_the_current_time_and_a_default_delay(self):
        ctrl = ToggleController(self.deviating, self.output)

        t1 = time.time()
        ctrl.periodic_sync()
        t2 = time.time()

        self.assertGreaterEqual(ctrl._cooldown_end, t1 + DEFAULT_COOLDOWN)
        self.assertLessEqual(ctrl._cooldown_end, t2 + DEFAULT_COOLDOWN)

    def test_manual_toggle__when_aligned__does_nothing(self):
        ctrl = ToggleController(self.aligned, self.output)

        ctrl.manual_toggle()

        self.assertEqual(self.output.is_pressed, None)

    def test_manual_toggle__when_deviating__presses_the_button(self):
        ctrl = ToggleController(self.deviating, self.output)

        ctrl.manual_toggle()

        self.assertEqual(self.output.is_pressed, True)

    def test_manual_toggle__when_deviating_and_in_cooldown__presses_the_button_and_clears_the_cooldown(self):
        ctrl = ToggleController(self.deviating, self.output)
        ctrl.periodic_sync()

        ctrl.manual_toggle()

        self.assertEqual(ctrl._cooldown_end, None)
        self.assertEqual(self.output.is_pressed, True)

    def test_manual_toggle__when_aligned_and_in_cooldown__only_clears_the_cooldown(self):
        is_synced = False
        ctrl = ToggleController(lambda: is_synced, self.output)
        ctrl.periodic_sync()

        is_synced = True
        ctrl.manual_toggle()

        self.assertEqual(ctrl._cooldown_end, None)
        self.assertEqual(self.output.is_pressed, None)



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
        with open(status_path) as f:
            data = json.load(f)
        global flags
        flags = data.get('Flags', 0)
        global gui_focus
        gui_focus = data.get('GuiFocus', 0)

        lights.periodic_sync()
        night_vision.periodic_sync()
        landing_gear.periodic_sync()
        cargo_scoop.periodic_sync()
        hardpoints.periodic_sync()
        sync_auto_miner()
    except Exception as e:
        # Reading the file may fail if we read it at a bad time.
        # For example the file may be empty, so parsing the JSON fails.
        # If the exception is not caught, gremlin stops the periodic calls.
        log(f"refresh_status failed:\n{traceback.format_exc()}")


# Ship lights

lights_input = throttle_raw.button(65)
lights_output = vjoy[1].button(1)

lights = ToggleController(
    is_synced=lambda: has_flag(LIGHTS_ON_FLAG) == lights_input.is_pressed,
    output=lights_output,
)

@on_button(lights_input)
def on_lights(event):
    lights.manual_toggle()


# Night vision

night_vision_input = throttle_raw.button(67)
night_vision_output = vjoy[1].button(2)

night_vision = ToggleController(
    is_synced=lambda: has_flag(NIGHT_VISION_FLAG) == night_vision_input.is_pressed,
    output=night_vision_output,
)

@on_button(night_vision_input)
def on_night_vision(event):
    night_vision.manual_toggle()


# Landing gear

landing_gear_input = throttle_raw.button(74)
landing_gear_output = vjoy[1].button(3)

landing_gear = ToggleController(
    is_synced=lambda: has_flag(LANDING_GEAR_DOWN_FLAG) == landing_gear_input.is_pressed,
    output=landing_gear_output,
)

@on_button(landing_gear_input)
def on_landing_gear(event):
    landing_gear.manual_toggle()


# Cargo scoop

cargo_scoop_input = throttle_raw.button(76)
cargo_scoop_output = vjoy[1].button(4)

cargo_scoop = ToggleController(
    is_synced=lambda: has_flag(CARGO_SCOOP_DEPLOYED_FLAG) == cargo_scoop_input.is_pressed,
    output=cargo_scoop_output,
    # the cargo scoop closes temporarily for nearly 5 seconds when launching prospectors or abandoning limpets
    cooldown_seconds=5,
)

@on_button(cargo_scoop_input)
def on_cargo_scoop(event):
    cargo_scoop.manual_toggle()



# Hardpoints

hardpoints_input = throttle_raw.button(93)
hardpoints_output = vjoy[1].button(5)

hardpoints = ToggleController(
    is_synced=lambda: has_flag(HARDPOINTS_DEPLOYED_FLAG) == hardpoints_input.is_pressed,
    output=hardpoints_output,
)

@on_button(hardpoints_input)
def on_hardpoints(event):
    hardpoints.manual_toggle()


# Auto miner

auto_miner_input = throttle_raw.button(86)
auto_miner_output = vjoy[1].button(6) # primary fire

@on_button(auto_miner_input)
def sync_auto_miner(event = None):
    auto_miner_output.is_pressed = auto_miner_input.is_pressed and has_flag(ANALYSIS_MODE_FLAG)


# Galaxy map

galaxy_map_input = throttle_raw.button(3)
galaxy_map_output = vjoy[1].button(11)

@on_button(galaxy_map_input)
def on_galaxy_map(event):
    actual = gui_focus == GUI_GALAXY_MAP
    desired = event.is_pressed
    if actual == desired:
        return
    short_press(galaxy_map_output)


# System map

system_map_input = throttle_raw.button(5)
system_map_output = vjoy[1].button(12)

@on_button(system_map_input)
def on_system_map(event):
    actual = gui_focus == GUI_SYSTEM_MAP
    desired = event.is_pressed
    if actual == desired:
        return
    short_press(system_map_output)


# Throttle

right_throttle_input = throttle_raw.axis(4)
left_pedal_input = pedals_raw.axis(1)
travel_mode_input = throttle_raw.button(95)
throttle_output = vjoy[1].axis(AxisName.RX)

@on_axis(right_throttle_input)
def on_right_throttle(event):
    adjust_throttle()

@on_axis(left_pedal_input)
def on_left_pedal(event):
    adjust_throttle()

@on_button(travel_mode_input)
def on_travel_mode(event):
    adjust_throttle()

def adjust_throttle():
    forward = right_throttle_input.value * -1
    backward = left_pedal_input.value
    if not travel_mode_input.is_pressed:
        forward = gremlin.input_devices.deadzone(forward, -0.8, 0, 0, 0.5)
    throttle_output.value = calculate_throttle(forward, backward)

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

    def test_full_backward_exactly_overshadows_full_forward(self):
        self.assertEqual(calculate_throttle(forward=1, backward=1), -1)

    def test_full_backward_exactly_overshadows_half_forward(self):
        self.assertEqual(calculate_throttle(forward=0, backward=1), -1)

    def test_half_backward_is_needed_to_standstill_full_forward(self):
        self.assertEqual(calculate_throttle(forward=1, backward=0), 0)

    def test_third_backward_is_needed_to_standstill_half_forward(self):
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
        loader.loadTestsFromTestCase(test_ToggleController),
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
