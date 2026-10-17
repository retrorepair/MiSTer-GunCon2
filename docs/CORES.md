# Cores: what is known, what is set up, what is tested

One calibration (GunCal) serves every core. What changes per core is small and listed here: where the core's picture sits in the
line and frame (measured by the framework, plus the HSync width, which the framework does not measure), how the aim is taken, and
which of the core's buttons the gun's buttons go to.

How to read the columns:

- **Video**: what the framework reports for the running core (`/tmp/guncal_apply.log` on the MiSTer records it).
- **HSync**: the sync pulse width the mapping assumes. It comes from the core's source where there is one, otherwise 4.7 us.
- **Aim**: `flash` = the pointer is set from the game's flash after a trigger pull; `live` = the pointer follows the gun (`LIGHTGUN_CRT_MODE=0`; no core uses it by default).
- **Tested**: "on hardware" means a person shot the real gun at the real game. Everything else is derived and not yet proven.

| Game (core's own name) | Source | Picture (measured) | HSync / VSync | Picture edges, gun raw | Buttons (see below) | Tested |
|---|---|---|---|---|---|---|
| Point Blank (NB1) | `kyledlester/Namco_NB1_MiSTer` | 288x224 progressive | 32 px / 3 lines | x 148..712, y 30..250 | trigger 4, A Start, B Coin, Select Service | **on hardware, "basically perfect"** |
| Virtua Cop (Model2) | `alphanu1/sega-model2-mister` | 496x384 **interlaced**, 15.7 kHz | 64 px / 3 | x 159..729, y 47..235 | trigger, A Reload, B Start, gun Start Coin | map and timing yes; shooting needs the full ROM set |
| Time Crisis (SUPER22) | binary only | 640x480 **interlaced** | **unknown**, 4.7 us / 3 assumed | x 131..724, y 20..256 | trigger, A Pedal, B Start, gun Start Coin | not yet |
| Lethal Enforcers II (KonamiGX) | `ppriest/Arcade-KonamiGX_MiSTer` | 288x224 | 32 px / 8 (estimate) | x 163..731, y 26..246 | trigger, A Reload, B Start, gun Start Coin | not yet |
| Alien3 / Jurassic Park (S32) | `meathax/s32` | 320x224 | 32 px / 3 | x 124..713, y 31..251 | trigger, A (Alien3: second button), B Start, gun Start Coin | not yet |
| Line of Fire (SXB) | `MiSTer-devel/Arcade-SegaXBoard_MiSTer` | 320x224 | 32 px / 4 | x 124..731, y 24..244 | trigger, A Bomb, B Start, gun Start Coin | not yet |
| Point Blank 2 (SYSTEM11) | `XelaNotPu/SYSTEM11_MiSTer` | 352x240 | 4.69 us / 3 | x 115..736, y 21..257 | trigger, A Start, B Coin | **core takes a mouse (P1) / stick velocity (P2), no absolute gun input: expect it not to work** |
| Terminator 2 (A.YUNIT) | closed (blahm1d) | 410x256 | **unknown**, 4.7 us assumed | x 130..737, y 22..273 | trigger, A Bomb, B Start, gun Start Coin | not yet |
| Rambo III (TaitoB) | `Mezzow/Arcade-TaitoB_MiSTer` | 320x224 | **64 px = 9.4 us** / 3 | x 174..732, y 27..247 | trigger, A Button 2, B Start, gun Start Coin | core reads only the stick's X (rotary): gun probably unsupported |
| Laser Ghost (JTS18) | `jotego/jtcores` | 320x224 | unknown, 4.7 us assumed | x 122..753, y 24..244 | trigger, A Special Weapon, B Start, gun Start Coin | not yet |
| Operation Wolf (JTRASTAN) | `jotego/jtcores` | 320x240 | unknown, 4.7 us assumed | x 144..712, y 19..255 | trigger, A Grenade, B Start, gun Start Coin | not yet |

**Scope.** Only games that originally used an optical gun (which flashes the screen for it) can work with the GunCon 2: Point Blank, Time
Crisis, Lethal Enforcers, Virtua Cop (it flashes in play), the NES Zapper, Super Scope, Menacer, Light Phaser, Stunner games. Games that
used analog guns (Alien3, Jurassic Park, Terminator 2, probably Line of Fire, Operation Wolf, Rambo III, Laser Ghost) never flash and are not
a goal; their rows are kept as measurements only. What is per core is only what the framework does not tell us (the sync widths and, for two
console cores, where the gun's coordinates sit in the picture), not per game.

"Picture edges" is what the universal mapping derives for the gun's raw X and Y at the picture's left/right/top/bottom, from the
GunCal calibration of 2026-10-16 plus the timing in `captures/harvest/round3.txt`. **HSync / VSync** come from each core's source and
are what the framework cannot measure; "unknown" falls back to 4.7 us and 3 lines, which can be a few percent of the screen out in
X. A per-core F10 calibration on the MiSTer overrides all of this.

**Buttons.** Every gun game's map is in `config/inputs/<game>_input_0b9a_016a_v3.map` on the card (written by
`tools/mister/make_gun_map.py` from the MRA's own `<buttons>` list). The layout: **trigger -> the first button**, **A -> the game's
second action** (reload, bomb, grenade, pedal), **B -> Start**, the gun's **Start -> Coin**, **Select -> Service**. Games with only
one action (Point Blank, Point Blank 2, Jurassic Park) keep the layout you tested: **A -> Start, B -> Coin**.

**Y beyond 255.** The kernel driver keeps only the low byte of the gun's 16-bit Y (`y = data[4]`; the raw capture shows `data[5]` is 1 in 143
of 1838 reports), so lines past 255 come back as 0, 1, 2... That would put the bottom of Terminator 2 (to line 273), Point Blank 2
(257) and Time Crisis (256) at the top of the screen. The app puts the 256 back for lit reports in the wrapped lines
(`CRTGUN_Y_WRAP`, patch 0010, flagged in the code as a platform limit; checked on the MiSTer with Terminator 2 by
`tools/mister/fakegun_ywrap.py`). The real fix is the one-line kernel patch `patches/kernel/0001-HID-guncon2-report-the-full-16-bit-Y.patch`;
it is **not applied** (it needs a kernel rebuild and a new `zImage` on the SD card, your call). Once it is, the app block can go.

## Sega Model 2 (Virtua Cop)

The core takes a gun as `joystick_l_analog_N` (an absolute position, -127..+127 across the **whole 496x384 game screen**) and the
trigger as joystick button 4. Player 1's buttons are joystick bits 4..9 (Trigger, Reload, Start, Coin, Test, Service); the map is trigger -> Trigger, A -> Reload, B -> Start, gun Start -> Coin, Select -> Service. Reload is by
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

The core's own list (`J1`) is a racing layout (`Gas, Brake, Shift Up, ...`), but the Time Crisis MRA renames the buttons:
`Trigger, Pedal, Start, -, -, Coin, Service, Test, -, Pause`. The map written for `timecris` and `SUPER22` is trigger -> Trigger,
A -> Pedal, B -> Start, gun Start -> Coin, Select -> Service. (An earlier version of this file said the MRA defined no
buttons: that was wrong. I had only read the first and last few KB of the 2.5 MB file.)

Measured on the card's build: 640x480 interlaced; 15.7 kHz lines, so the GunCon 2 can lock. The mapping handles the interlace (the picture
spans 240 gun lines), and puts the picture at raw x 131..724 and y 20..256. The bottom edge sits at the kernel driver's 8-bit
limit for Y (255), so the last row or two cannot be reached until the driver passes the full Y.

## Console cores (core file loaded alone, no game)

Measured with `tools/mister/harvest_cores.py` (`captures/harvest/consoles1.txt`). A console core's picture size depends on the game
(and for the NES on its overscan option); the mapping is recomputed whenever it changes. The MiSTer cannot load a game from the command
FIFO, so these are the cores' idle pictures.

| Core | Idle picture | HSync / VSync | Gun space | Buttons (core's `J1`) |
|---|---|---|---|---|
| NES (`NES`) | 284x242 (wide overscan) | 4.65 us / 3 | **its own PPU dots 0..255 and scanlines 0..239**, a window inside the picture: raw x 142..706, y 21..257 in this mode | A, B, Select, Start, FDS, Mic, **Zapper/Vaus Btn (bit 10)** |
| SNES (`SNES`) | 512x224 | 4.7 us (assumed) / 3 | the visible picture (it scales to its own `vtotal`), so the default | `A(SS Fire), B(SS Cursor), X(SS TurboSw), Y(SS Pause), LT(SS Cursor), RT(SS Fire)`, Select, Start |
| Mega Drive / Mega-CD (`MegaDrive`, `MegaCD`) | 256x192 idle (games 256/320 x 224) | 4.7 us (assumed) / 3 | X over the picture width, **Y as a screen line (stick minus 8)**, so the stick spans lines -8..247: raw y 37..288 at 192 lines | A, B, C, Start, Mode, X, Y, Z |
| Master System (`SMS`) | 256x192 | 4.7 us (assumed) / 3 | the visible picture (X = stick, Y scaled to the visible lines), so the default | Fire 1, Fire 2, Pause, ... |
| Atari 7800 | 372x224 | 4.7 us (assumed) / 3 | not read | Fire1, Fire2, Pause/B&W, Select, Reset(Start), ... |
| PlayStation, Mega-CD | not harvested | | | the card launches `/media/fat/MiSTer_Physical-CD` for CD cores, a separate build the patches do not cover |

The NES window follows the core's overscan option (detected from the measured picture size): 256x224 and 256x240 (narrow), 283/284 x 242
(wide). It is derived from `NES_video.sv`/`NES_zapper.sv` to about a pixel and has **not** been tried with the gun. The Zapper needs
`Peripheral: Zapper(Joy1)` and `Zapper Trigger: Joystick` set in the core's OSD, and the gun's map at `config/inputs/NES_input_0b9a_016a_v3.map`
(trigger -> bit 10).

**Lesson (cost an hour):** `load_core` takes a core `.rbf` or an arcade `.mra` only. Given a ROM (`.nes`) it programs the FPGA with the ROM
as if it were a bitstream, the FPGA is left unconfigured, the app then refuses to start, and a write to `/dev/MiSTer_cmd` blocks the console
for good. Recovery without a reboot (a reboot would put the console back at its login prompt): run a build of the app that programs the
FPGA from the command line when it is unconfigured (a one-off; `MiSTer /media/fat/menu.rbf`).

## Cores run by the physical-disc build (PlayStation, Saturn, Mega-CD, TurboGrafx-16)

`MiSTer.ini` on the card has `main=MiSTer_Physical-CD` in the `[PSX]`, `[Saturn]`, `[MegaCD]` and `[TurboGrafx16]` sections (the card's own
physical-disc setup). When one of those cores loads, the app relaunches itself as that other executable, so **the patches in this repo do not
apply to those cores**: no universal mapping, no flash aim, no timing log. Applying them means building the same patches onto whatever
`MiSTer_Physical-CD` is built from (I do not know its source), or switching `main=` for a section back to `MiSTer` (which drops the disc-drive
support for that core): your call.

This is where the Saturn **Virtua Cop** (and Virtua Cop 2: `Saturn/Virtua Cop (USA) (6S).chd` etc. are on the share) lives. The Saturn core has the
option `Pad 1 = Virt LGun`, with `LGun P1 XY Ctrl = Joy 1 / Mouse` and `LGun P1 Buttons = Joy 1 / Mouse` (`Saturn.sv`), and a lightgun module
derived from the Mega Drive's. So it takes an absolute joystick-analog position, the same shape as the cores above, once the mapping applies.
