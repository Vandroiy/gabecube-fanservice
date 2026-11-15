# Gabecube (Valve Steam Machine) Fanservice

This is a fan controller for the Valve Steam Machine aka Gabecube, made for Debian. (And potentially related Linux ditributions.) It uses trailing temperature readings from the CPU and GPU to approximate load on the main heat sink.

The Steam Machine's firmware fan curve runs far too fast on idle. Steam OS apparently takes control of the fan from software. So installing a standard OS like Debian leads to unnecessary noise and potential dust buildup. This little service fixes that.


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

Driver source: https://github.com/firlin123/steamdeck-dkms (Commit 99737c4)

The driver is unchanged and added only for convenience. It is GPL-2-licensed and the source is in the `.deb` file. (Via DKMS.) Refer to the original repo for any driver issues or changes.


## 3. Install the Operator

You need Python 3.

Then run: `python3 gabecube_fanservice_operator.py install`

That should set everything up. Using `uninstall` will remove it again. And `console-run` lets you run it from the terminal, but make sure it isn't installed, or else you'll have two instances fighting over the fan.

Note that the fan operator gets copied on install, so if you want to change parameters and then run the changed file as a service, you need to reinstall it.


## Credits

Written by Georg Michna, with research and prototyping by Claude Opus 5.5 (Anthropic AI).

I did type the code and readme by hand, but knew almost nothing about Python syntax and the relevant APIs, so Claude did a lot of the work by finding and explaining details.


## License (MIT)

Copyright 2026 Georg R.K. Michna

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
