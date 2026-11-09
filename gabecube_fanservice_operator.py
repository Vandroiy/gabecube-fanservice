#!/usr/bin/env python3
"""Fan control for the Valve Steam Machine aka Gabecube.

Takes one argument, to select mode. Modes are:

  install       Copies this program to /usr/local/sbin and sets it up as a service.
  uninstall     Removes this program from /usr/local/sbin and removes the service.
  console-run   Runs in console mode: prints updates to the console.
  service-run   Runs in service mode: normal operation.
  use-firmware  Sets to firmware control and exits.

For normal use, all you need to do is ensure the driver is installed,
then run the operator once in install mode. The rest should be automatic.
"""
import os, signal, socket, sys, shutil, subprocess, time, glob
from datetime import datetime

# == CONSTANTS =====================================================================
HALFLIFE_S  =   36     # Time until half effect after a temperature change
INTERVAL_S  =    3.0   # Sleep time between updates
LOW_RPM     =  400     # Target RPM should not go below this
MID_RPM     =  800     # Target RPM under low to moderate load
MAX_RPM     = 1600     # Target RPM under maximum load

# driver name, sensor label, TLow, TMid, TMax
SENSORS = [
    ("k10temp", "Tctl",     35, 60, 90),
    ("amdgpu",  "edge",     35, 55, 80),
    ("amdgpu",  "junction", 35, 60, 90),
    ("amdgpu",  "mem",      35, 70, 90),
]

HWMON_PATH             = "/sys/class/hwmon"
FAN_DRIVER_NAME        = "steamdeck_hwmon"
SERVICE_NAME           = "gabecube_fan"
SERVICE_FILEPATH       = f"/etc/systemd/system/{SERVICE_NAME}.service"
OPERATOR_SBIN_FILEPATH = "/usr/local/sbin/gabecube-fanservice-operator"

TRAILING_FACTOR = 0.5**(INTERVAL_S/HALFLIFE_S)
# ==================================================================================


class OperatorError(Exception):
    """Irrecoverable error. Reset fan speed to 0 to restore firmware control."""


def text_of_path(path):
    with open(path) as f:
        return f.read().strip()

def find_hwmon(name):
    """Return hwmon* folder with this driver name. (Numbers may change at boot.)"""
    for path in sorted(glob.glob(os.path.join(HWMON_PATH, "hwmon*"))):
        try:
            if text_of_path(os.path.join(path, "name")) == name:
                return path
        except OSError:
            pass
    raise OperatorError(f"Hwmon path for {name} not found; is the driver installed?")


def apply_raw_target_rpm(fan_path, value):
    with open(os.path.join(fan_path, "fan1_target"), "w") as f:
        f.write(str(int(value)))

def apply_firmware_control():
    apply_raw_target_rpm(find_hwmon(FAN_DRIVER_NAME), 0)

def notify_system(message):
    address = os.environ.get("NOTIFY_SOCKET")
    if not address: return
    if address.startswith('@'): address = '\0' + address[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
        s.sendto(message.encode(), address)


class Operator:
    """Stores state and updates fan target accordingly."""

    def __init__(self):
        self.fan_path = find_hwmon(FAN_DRIVER_NAME)
        self.sensors = []
        self.current_temps = {}
        self.trailing_temps = {}
        self.stall_counter = 0
        self.target_rpm = MAX_RPM
        
        # Set self.sensors by matching the SENSORS table to input files.
        for name, label, t_low, t_mid, t_max in SENSORS:
            sensor_id = f"{name}/{label}"
            label_files = sorted(glob.glob(os.path.join(find_hwmon(name), "temp*_label")))
            found = False
            for file in label_files:
                try:
                    if text_of_path(file) == label:
                        path = f"{file[: -len("_label")]}_input"
                        self.sensors.append({"id": sensor_id, "path": path,
                                             "tLow" : t_low, "tMid" : t_mid, "tMax" : t_max})
                        found = True
                        break
                except OSError:
                    pass
            if not found:
                raise OperatorError(f"Sensor {sensor_id} not found. Missing drivers or not on a Steam Machine?")

        self.update_current_temps()
        self.trailing_temps = dict(self.current_temps)
    

    def apply_target(self):
        if not (LOW_RPM <= self.target_rpm <= MAX_RPM):
            raise OperatorError("Internal error: attempted to set out-of-bounds RPM")
        apply_raw_target_rpm(self.fan_path, self.target_rpm)

    def interpolate_raise_target(self, t, t0, t1, r0, r1):
        req = r0 + (r1 - r0) * (t - t0) / (t1 - t0)
        self.target_rpm = max(self.target_rpm, req)

    def run(self, print_info):
        notify_system("READY=1")  # Confirm to system that the service starts operating
        while True:
            self.update_current_temps()
            self.update_trailing_temps()
            actual_rpm = int(text_of_path(os.path.join(self.fan_path, 'fan1_input')))

            if (actual_rpm < 100):
                self.stall_counter += 1
                if self.stall_counter > 5:
                    raise OperatorError("Fan reported stalled!")
            else:
                self.stall_counter = 0
            
            self.target_rpm = LOW_RPM
            for sensor in self.sensors:
                t = self.trailing_temps[sensor['id']]
                if t <= sensor['tLow']:
                    pass
                elif t >= sensor['tMax']:
                    self.target_rpm = MAX_RPM
                elif t <= sensor['tMid']:
                    self.interpolate_raise_target(t, sensor['tLow'], sensor['tMid'], LOW_RPM, MID_RPM)
                else:
                    self.interpolate_raise_target(t, sensor['tMid'], sensor['tMax'], MID_RPM, MAX_RPM)

            # Don't bother setting micro-changes, just steps of 50 rpm
            self.target_rpm = round(self.target_rpm / 50) * 50
            self.apply_target()
            
            if print_info:
                print(f"# -- Thermal update -- {datetime.now():%H:%M:%S} -- target = {self.target_rpm} rpm -- actual = {actual_rpm} rpm")
                print("| Current    " + "   ".join(f"{k} = {v:.1f}" for k, v in self.current_temps.items()))
                print("| Trailing   " + "   ".join(f"{k} = {v:.1f}" for k, v in self.trailing_temps.items()))

            notify_system(f"STATUS=target{self.target_rpm} rpm -- actual {actual_rpm} rpm")
            time.sleep(INTERVAL_S)
            notify_system("WATCHDOG=1")  # Reassure system that we are still operating

    def update_current_temps(self):
        for sensor in self.sensors:
            t = int(text_of_path(sensor['path'])) / 1000
            if not (-25 <= t <= 125):
                raise OperatorError(f"Implausible temperature {t:.1f} on sensor id {sensor['id']}")
            self.current_temps[sensor['id']] = t
    
    def update_trailing_temps(self):
        """Approaches trailing_temps toward current_temps for one interval step."""
        for sensor in self.sensors:
            tOld = self.trailing_temps[sensor['id']]
            tCur = self.current_temps[sensor['id']]
            self.trailing_temps[sensor['id']] = TRAILING_FACTOR * tOld + (1 - TRAILING_FACTOR) * tCur


def main():
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))
    if not (os.geteuid() == 0): sys.exit("Must be run by root / use sudo.")

    mode = sys.argv[1] if len(sys.argv) >= 2 else "arg-missing"
    match mode:
        case "service-run" | "console-run":
            if mode == "service-run": time.sleep(5) # Give the system time to boot and load everything
            operator = Operator()
            try:
                operator.run(mode == "console-run")
            except KeyboardInterrupt:
                pass
            finally:
                apply_firmware_control()
        case "use-firmware":
            apply_firmware_control()
        case "install":
            this_file_path = os.path.abspath(__file__)
            shutil.copy(this_file_path, OPERATOR_SBIN_FILEPATH)
            os.chmod(OPERATOR_SBIN_FILEPATH, 0o755)
            with open(SERVICE_FILEPATH, "w") as f:
                f.write(SERVICE_TEXTCONTENT)
            os.chmod(SERVICE_FILEPATH, 0o644)
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", SERVICE_NAME], check=True)
            subprocess.run(["systemctl", "reset-failed", SERVICE_NAME], check=False)
            subprocess.run(["systemctl", "restart", SERVICE_NAME], check=True)
        case "uninstall":
            subprocess.run(["systemctl", "disable", "--now", SERVICE_NAME], check=False)
            for p in [SERVICE_FILEPATH, OPERATOR_SBIN_FILEPATH]:
                if os.path.exists(p): os.remove(p)
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            apply_firmware_control()
        case _:
            sys.exit(__doc__)


SERVICE_TEXTCONTENT = f"""\
[Unit]
Description=Steam Machine fan controller
After=systemd-modules-load.service
StartLimitIntervalSec=300
StartLimitBurst=4

[Service]
Type=notify
WatchdogSec=15
TimeoutStopSec=15
ExecStartPre={OPERATOR_SBIN_FILEPATH} use-firmware
ExecStart={OPERATOR_SBIN_FILEPATH} service-run
ExecStopPost={OPERATOR_SBIN_FILEPATH} use-firmware
Restart=always
RestartSec=15
NoNewPrivileges=yes
ProtectHome=yes

[Install]
WantedBy=multi-user.target
"""


if __name__ == "__main__": main()