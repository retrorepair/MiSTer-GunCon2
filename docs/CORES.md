# Cores: what is known, what is set up, what is tested

One calibration (GunCal) serves every core. What changes per core is small and listed here: where the core's picture sits in the
line and frame (measured by the framework, plus the HSync width, which the framework does not measure), how the aim is taken, and
which of the core's buttons the gun's buttons go to.

How to read the columns:

- **Video**: what the framework reports for the running core (`/tmp/guncal_apply.log` on the MiSTer records it).
- **HSync**: the sync pulse width the mapping assumes. It comes from the core's source where there is one, otherwise 4.7 us.
- **Aim**: `flash` = the pointer is set from the game's flash after a trigger pull; `live` = the pointer follows the gun (`LIGHTGUN_CRT_MODE=0`; no core uses it by default).
- **Tested**: "on hardware" means a person shot the real gun at the real game. Everything else is derived and not yet proven.

| Core | Source | Video (measured) | HSync | Aim | Buttons | Tested |
|---|---|---|---|---|---|---|
| Namco NB-1 (Point Blank) | `kyledlester/Namco_NB1_MiSTer` | 288x224, 15 kHz progressive | 32 px at 6.048 MHz | flash | trigger 4, A start, B coin, Select service | **on hardware, "basically perfect"** |
| Sega Model 2 (Virtua Cop) | `alphanu1/sega-model2-mister` (release `Model2_20261016`) | 496x384 **interlaced**, 63.55 us lines, 48.06 us picture | 64 px (6.2 us) | flash | trigger 4, gun Start = Reload 5, A = Start 6, B = Coin 7, Select = Service 9 | map and timing: yes. Aiming at the game: not yet, needs the full ROM set and a played game |
| Namco Super System 22 (Time Crisis) | binary only (see below) | 640x480 **interlaced**, 63.58 us lines, 50 us picture | unknown, 4.7 us assumed | flash | **no map written**: see below | not yet |

## Sega Model 2 (Virtua Cop)

The core takes a gun as `joystick_l_analog_N` (an absolute position, -127..+127 across the **whole 496x384 game screen**) and the
trigger as joystick button 4. Player 1's buttons are joystick bits 4..9 (Trigger, Reload, Start, Coin, Test, Service). Reload is by
shooting off-screen (the outer 5% of the range), or the Reload button. Set the core's OSD `Crosshair` to `Off` with a real gun.

The aim is taken from the game's flash, as for Point Blank. Virtua Cop flashes in gameplay (not in the attract demo), so the flash
can only be seen and measured by inserting a coin and starting a game. I first guessed the game does not flash and wrote a per-core
"live" mode; the owner corrected that and the mode was withdrawn before it ran anywhere. Not yet shown on hardware.

Measured on the card with Daytona (`Daytona USA (Revision A) [15kHz CRT]`, the same video generator as Virtua Cop's): 496x384
interlaced, `htime` 6355, `ptime` 4806, `de_h` 698 clocks (6.98 us), `de_v` 42 lines, derived HSync 6.2 us (= 64 pixels,
`m2_video_timing.sv`). The universal mapping puts the picture at raw x 159..729, y 47..235, comfortably inside the driver's
8-bit Y. The core's own button list is `Coin, Start, Test, Service, VR1 Red, VR4 Green, Accel, Brake, Gear Up, Gear Down,
VR2 Blue, VR3 Yellow`; the Virtua Cop MRA renames bits 4..9 to `Trigger, Reload, Start, Coin, Test, Service`.

To try it (the files are on the card in `_Arcade/_gun_test/`, the core file is the friend's release `Model2_20261016.rbf`, md5
`644e28fa0dee02c90d4b2d93c2d99fbd`): put the full `vcopa.zip` + `vcop.zip` (+ `model1io2.zip`) in `games/mame`, load the Virtua Cop
MRA, set the core's OSD `Crosshair` to `Off`, insert a coin, start, and shoot.

ROMs: the MRA needs `vcopa.zip`, the parent `vcop.zip`, and the I/O board's `epr-17181.6` (in either, or in `model1io2.zip`).
On 2026-10-17 `Y:\MiSTer\mame\vcopa.zip` held only 2 of the 23 files the MRA names (the two i960 program ROMs
`epr-17166a.12`, `epr-17167a.13`); the other 21 are in the parent set and the BIOS zip.

## Namco Super System 22 (Time Crisis)

The card has `XNSUPER22_20260913.rbf` and `Time Crisis (World, TS2 Ver.B).mra` (the MRA says the gun reaches the game through the
M37710 ADC path, a bring-up state). There is no public source for that build (Patreon). `spacestate1/Arcade_namco22_MiSTer` is a
related public GPL-3.0 research core for the same hardware: Prop Cycle runs, Time Crisis is not loadable there, no sound, ~6 fps.

The card's build lists these buttons (`J1`): `Gas, Brake, Shift Up, Shift Down, View, Coin, Service, Test, Motion Stop, Pause` (bits 4..13),
and `jn,A,B,R,L,X,Select`: a racing layout, and the Time Crisis MRA defines no `<buttons>`. MAME has the gun trigger on BUTTON1 and the
foot pedal on BUTTON2, but which of these two the build wires them to is not in anything I can read, so **no map was written**. Once
known, one command on the MiSTer writes it: `python3 /tmp/make_gun_map.py timecris <trigger bit> <A> <B> <Select> <Start>` (and the same for
`SUPER22`, the name the core reports early).

Measured on the card's build: 640x480 interlaced; 15.7 kHz lines, so the GunCon 2 can lock. The mapping handles the interlace (the picture
spans 240 gun lines), and puts the picture at raw x 131..724 and y 20..256. The bottom edge sits at the kernel driver's 8-bit
limit for Y (255), so the last row or two cannot be reached until the driver passes the full Y.
