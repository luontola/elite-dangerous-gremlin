# Esko's Gremlin scripts for Elite Dangerous

This is a [GremlinEx](https://github.com/muchimi/JoystickGremlinEx) plugin for my HOTAS setup in [Elite Dangerous](https://www.elitedangerous.com/).
Feel free to copy and adapt to your needs.

## Bindings file

Edit the bindings in `\AppData\Local\Frontier Developments\Elite Dangerous\Options\Bindings` to manually enter the vJoy bindings.
This avoids the need for [HidHide](https://github.com/nefarius/HidHide).
Also some of this plugin's bindings cannot be triggered easily inside menus, because they depend on the game state (e.g. is landing gear down).

vJoy device 1, button 1 as secondary action:

```xml
<Secondary Device="vJoy" DeviceIndex="1" Key="Joy_1" />
```

vJoy device 1, RX-axis (axis 4):

```xml
<Binding Device="vJoy" DeviceIndex="1" Key="Joy_RXAxis" />
```
