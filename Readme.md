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

**Various parameters are configuable near the top of the python file.**

The fan operator gets copied on install, so if you want to change parameters and then run the changed file as a service, you need to reinstall it.


## Credits

Written by Georg Michna, with research and prototyping by Claude Opus 5.5 (Anthropic AI).


**Update, before more herp derp AI speculations are raised:**

I made the foolish error of posting about this on Reddit. Thus, I encountered *the typical Redditors*, who aren't interested in using this, but entertain themselves by throwing around baseless accusations. For example, how undisclosed parts of this could have been written by AI, maybe my messages too, or how I'm not attributing correctly by saying "I wrote" this. To hopefully end this noise, I'm expanding on the earlier elaboration how AI was used.

 - *Written by* means I physically typed everything with a keyboard, including documentation. I may have used single-word IDE autocomplete, but as of 2026-11-16, no AI IDE integration, nor any pasting of generated or otherwise external code or documentation. (Apart from the driver and licenses.)
 - *Research* means that Claude searched and presented relevant information. This enabled me to identify the driver and relevant APIs quickly.
 - *Prototyping* means that Claude generated example code that I looked at as I implemented this.
 - I am not a Python programmer and so asked Claude syntax questions.
 - I also showed Claude my work in progress and it offered some suggestions.

So is this *written by AI*? Technically no. Philosophically, that's your interpretation. Of course a program that has large parts for wiring specific APIs will have structural similarities to an AI-written prototype for it. And Claude was very helpful with this, which is why I credited it here.

In practice, this comes down to a simple question: why do you care?

 - If you care whether a human has intentionally considered and written every element, then this is the case.
 - If you care whether AI has had substantial input into the process of making it, then this is also the case.

Beyond this point, we'd be debating philosophy and definitions, not fixing hardware control issues. Please only contact me with constructive and relevant feedback, not unsubstantiated slander.
