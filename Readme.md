# Gabecube (Valve Steam Machine) Fanservice

This is a fan controller for the Valve Steam Machine aka Gabecube, made for Debian. (And potentially related Linux distributions.) It uses trailing temperature readings from the CPU and GPU to approximate load on the main heat sink.

The Steam Machine's firmware fan curve runs far too fast on idle. SteamOS apparently takes control of the fan from software. So installing a standard OS like Debian leads to unnecessary noise and potential dust buildup. This little service fixes that.


## 1. Caveats

I consider overheating protection the responsibility of thermal throttling, not of the fan operator service.

 - Some crashes or errors could lock the fan at inappropriate speed.
 - Sensor temperatures on the Steam Machine can be quite volatile.
 - The current configuration ignores the SSD temperature.
 - All of this is a trade-off in the first place.

Since SteamOS appears to also use software fan control by default, none of this should be a problem. But I don't take responsibility for any nonsense Valve may have done, given that they already used an unreasonable firmware fan curve.

If you have any concerns, examine the code and reconfigure it as needed.


## 2. Required Driver

For Debian and related distros, you should be able to just install the included `.deb` driver file. It should fetch the matching `linux-headers-` such as `generic` or `amd64`, then recompile automatically for your system and its future updates.

Terminal: `sudo apt install ./driver/steamdeck-dkms_6.8.12-valve2+2_amd64.deb`

Driver source: https://github.com/firlin123/steamdeck-dkms (Commit 99737c4)

The driver is unchanged and added only for convenience. It is GPL-2-licensed and the source is in the `.deb` file. (Via DKMS.) Refer to the original repo for any driver issues or changes.


## 3. Install the Operator

You need Python 3.

Then run: `sudo python3 gabecube_fanservice_operator.py install`

That should set everything up. Using `uninstall` will remove the operator again. And `console-run` lets you run it from the terminal, but make sure it isn't installed, or else you'll have two instances fighting over the fan.

Note that the fan operator gets copied on install, so if you want to change parameters and then run the changed file as a service, you need to reinstall it.


## Credits

Written by Georg Michna, with research and prototyping by Claude Opus 5.5 (Anthropic AI).

I did type the code and readme by hand, but knew almost nothing about Python syntax and the relevant APIs, so Claude did a lot of the work by finding and explaining details.

License: MIT. Apart from the external driver. See: License.md