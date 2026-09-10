====================================================================
 ArtilleryProject -- IOE Tactical HUD
 Assembly & Operation Notes (current as of: GPS + LRF + Compass wired)
====================================================================

This file covers physical assembly and how to run the system as it
stands today. It will be updated as more of the backend (ballistics /
deflection engine, additional sensors) gets built out.

--------------------------------------------------------------------
1. PROJECT LAYOUT
--------------------------------------------------------------------

Main Project/
  requirements.txt              <- install this ONCE, covers everything
  ArtilleryProject_Frontend/     PySide6 GUI (the HUD you look at)
  ArtilleryProject_Backend/      Headless daemon (reads sensors, talks
                                  to the frontend over a TCP socket)

Frontend and backend both run on the same Raspberry Pi 5, in the same
Python virtual environment. The backend listens on port 5555; the
frontend connects to it as a client.

--------------------------------------------------------------------
2. HARDWARE ASSEMBLY
--------------------------------------------------------------------

2.1 GPS module
--------------
Connects over a serial UART to the Pi (e.g. /dev/serial0). Requires
gpsd running and pointed at that device -- see section 3.2.

2.2 Laser Rangefinder (LRF)
----------------------------
Connects over a serial UART at 115200 baud, 8N1. Currently configured
for /dev/ttyAMA2 (see LRF_PORT in ArtilleryProject_Backend/main.py).

Because the LRF and the GPS each need their own UART, you will likely
need to enable an extra UART on the Pi 5 via a device-tree overlay in
/boot/firmware/config.txt (e.g. dtoverlay=uart2), since only one UART
(serial0) is enabled by default. Confirm which /dev/ttyAMAx or
/dev/ttySx each device lands on with `ls /dev/tty*` before and after
plugging each one in, and update LRF_PORT / your gpsd device path to
match.

2.3 Compass (CMPS12, I2C)
---------------------------
Wiring (per CMPS12 datasheet pin order):
    Pin 1 (3.3v-5v)   -> Pi 3.3V   (physical pin 1)
    Pin 2 (SDA/TX)    -> Pi GPIO2 / SDA1 (physical pin 3)
    Pin 3 (SCL/RX)    -> Pi GPIO3 / SCL1 (physical pin 5)
    Pin 4 (Mode)      -> leave open (I2C mode; only ground this for serial mode)
    Pin 5 (Factory)   -> leave open
    Pin 6 (0v ground) -> Pi GND    (physical pin 6)

Default I2C address 0x60 (7-bit). Enable I2C on the Pi via
`sudo raspi-config` (Interface Options -> I2C) if not already on, then
confirm the module is visible with `i2cdetect -y 1` (should show a
device at address 0x60).

2.4 Display
------------
The frontend opens a real GUI window (PySide6/Qt). The Pi needs either
a monitor attached (HDMI, with a desktop environment installed) or a
remote desktop/VNC session -- plain SSH is not enough to see it.

--------------------------------------------------------------------
3. SOFTWARE SETUP (on the Raspberry Pi 5)
--------------------------------------------------------------------

3.1 System packages
---------------------
    sudo apt update
    sudo apt install gpsd gpsd-clients python3-gps

3.2 Start/point gpsd at the GPS device
-----------------------------------------
    sudo systemctl stop gpsd.socket gpsd
    sudo gpsd /dev/serial0 -F /var/run/gpsd.sock

Verify the GPS hardware + gpsd independently of our code before going
further:
    cgps -s
(should show a real, moving 2D/3D fix)

3.3 Python virtual environment
----------------------------------
    python3 -m venv ArtyProject_venv
    source ArtyProject_venv/bin/activate
    pip install -r requirements.txt

If `import gps` fails inside the venv (it can't see the apt-installed
python3-gps package), either recreate the venv with
--system-site-packages, or add a .pth file inside the venv's
site-packages pointing at /usr/lib/python3/dist-packages. Both are
covered in requirements.txt's comments.

--------------------------------------------------------------------
4. RUNNING IT
--------------------------------------------------------------------

Two terminals, same Pi, same activated venv:

    Terminal 1:
        cd ArtilleryProject_Backend
        python3 main.py

    Terminal 2:
        cd ArtilleryProject_Frontend
        python3 main.py

What to expect: the HUD's top bar should flip from CONNECTING... to
CONNECTED, and the Observation Post Telemetry panel should start
showing live GPS lat/lon/alt, azimuth/pitch/roll from the compass, and
laser distance -- as each sensor reports in.

--------------------------------------------------------------------
5. TESTING WITHOUT HARDWARE
--------------------------------------------------------------------

To sanity-check the frontend/backend wiring alone, without any sensor
plugged in (useful on a dev machine too, not just the Pi):

    Terminal 1: python3 ArtilleryProject_Backend/tools/mock_gps_broadcast.py
    Terminal 2: python3 ArtilleryProject_Frontend/main.py

This feeds the real GUI a fake, slowly-drifting GPS fix once a second
so you can visually confirm the socket link works.

--------------------------------------------------------------------
6. STATUS AS OF NOW
--------------------------------------------------------------------

Done:
    - Frontend HUD layout (telemetry / target / fire-correction panels,
      equal-width 3-column layout, side nav removed)
    - Backend socket server + JSON protocol (protocol.py)
    - GPS sensor wired end-to-end (sensors/gps_reader.py)
    - Laser rangefinder wired end-to-end (sensors/lrf_reader.py)
    - Compass (CMPS12) wired end-to-end (sensors/compass_reader.py)
    - All three sensors merge into one telemetry snapshot per broadcast,
      so one sensor updating doesn't blank out another's last reading

Not done yet:
    - The frontend's "SET TARGET & ACQUIRE" button sends target grid
      coordinates to the backend, but the backend currently only logs
      them -- there is no ballistics/deflection calculation engine yet,
      so the Fire Correction panel will show "DEFLECTION UNAVAILABLE"
      until that's built.
    - Manual deflection/range adjustment buttons and the fine-tune
      slider in the Fire Correction panel are UI-only right now; they
      don't send anything to the backend.
