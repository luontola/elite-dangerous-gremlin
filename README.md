# Esko's Joystick Gremlin scripts for Elite Dangerous

This is a [GremlinEx](https://github.com/muchimi/JoystickGremlinEx) plugin for my HOTAS setup in [Elite Dangerous](https://www.elitedangerous.com/).
Feel free to copy and adapt to your needs.

I fly in VR using the WinWing Orion HOTAS and CH Products Pro Pedals.
[These are my bindings](https://imgur.com/a/elite-dangerous-bindings-winwing-orion-hotas-7iuRdSV) as of writing.


## Features

### Binding 2-way switches to toggle buttons

The average HOTAS setup has lots of 2-way and 3-way switches, but Elite Dangerous doesn't support them properly; it uses toggle buttons for nearly everything.

This plugin will sync the game state with the physical switch's state.
It will periodically check if the game state (e.g. landing gear down) differs from the physical switch's state (e.g. landing gear up), and then press the toggle button shortly.
The following controls are managed by this mechanism:

- Landing gear
- Cargo scoop <sup>[1]</sup> <sup>[2]</sup>
- Hardpoints
- Ship lights
- Night vision

<sup>[1]</sup>
Though the game has a hold mode for the cargo scoop binding, I find it fails when the game loses focus.
Toggle mode together with this plugin is more reliable.

<sup>[2]</sup>
The game closes the cargo scoop temporarily when launching limpets, so this plugin has a longer sync delay for cargo scoop than the others.
That should avoid some voice announcement spam during mining.


### Combining two throttle axes into one

I use the throttle handle on my HOTAS for forward thrust, and the left break pedal for backward thrust.
(The right break pedal is boost.)
This plugin combines those two axes into a single throttle axis.

Breaking and going reverse doesn't require reducing the forward thrust.
Regardless of how much forward thrust there is, pressing the break pedal to the bottom will go full reverse.
The amount of break pedal that is needed to reach a standstill depends linearly on how much forward thrust there is; with full forward thrust you'll need to press the break pedal halfway.

I use a 3-way switch to adjust the throttle handle movement range and deploying hardpoints.
When cruising or landing, I want to use the full movement range of the HOTAS throttle for better accuracy.
But in combat that would hinder quick throttle adjustments, so I'm adding deadzones to the max and min ranges.
The throttle mode and hardpoints are controlled by a 3-way switch:

1. Travel mode: full throttle range, hardpoints retracted
2. Maneuver mode: compressed throttle range, hardpoints retracted
3. Combat mode: compressed throttle range, hardpoints deployed


### Galaxy and system maps on a 3-way switch

I use a 3-way switch to quickly open and close the galaxy and system maps.
Flipping it to one end opens the galaxy map, the other end opens the system map, and the middle position closes both maps.

The game has multiple ways of opening and closing the maps, so this switch must peacefully coexist with all of them.
The switch opens or closes maps only when it is moved.
That means the switch may sometimes be out of sync with the game state, but moving the switch once back and forth will resolve it.


### Auto fire for laser mining

Holding down the trigger for long times is tiring (especially since my flight stick has a heavy trigger).
To make laser mining more relaxing, I use a toggle switch as an alternative key binding for the primary fire.
But as a safety measure, that switch works only in analysis mode.


## Configuring the bindings

I'm not using [HidHide](https://github.com/nefarius/HidHide).
That means I can't easily bind virtual buttons that are triggered by a physical button press.

The toggle button switches can typically be bound in-game by relying on this plugin pressing the vJoy buttons every few seconds when the switch is in the other position.
For the other key bindings, it's necessary to edit the key bindings file manually.

Edit the bindings file in `\AppData\Local\Frontier Developments\Elite Dangerous\Options\Bindings` to manually bind vJoy buttons and axes. Below are some examples.

vJoy device 1, button 1 as secondary action:

```xml
<Secondary Device="vJoy" DeviceIndex="1" Key="Joy_1" />
```

vJoy device 1, RX-axis (axis 4):

```xml
<Binding Device="vJoy" DeviceIndex="1" Key="Joy_RXAxis" />
```
