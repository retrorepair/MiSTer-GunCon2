# What to test, in order, with exact steps

Written 2026-10-17 for the first morning. Everything here is set up on the MiSTer already (see `HANDOFF.md`) and **none of it has been tried
with the gun in a game** except Point Blank (NB-1). Each entry says what I derived from the core's source and what could still be wrong,
so a failure tells you where to look.

Before anything: the MiSTer is running the patched app from RAM, the GunCon 2 is plugged in, and the universal calibration
(`config/GUNCAL_uni_0b9a_016a_v1.cfg`) is in place. If the MiSTer was power-cycled, the RAM-only parts are gone: say so and I will bring them
back (or follow `HANDOFF.md`).

Every game's gun buttons are already mapped: **trigger = the game's first button, A = its second action (reload / bomb / grenade / pedal),
B = Start, gun Start = Coin, Select = Service** (Point Blank, Point Blank 2, Jurassic Park: A = Start, B = Coin, as you tested).
To change one, press F12 > Define joystick buttons while that game is loaded, or tell me.

How to judge a result: after a trigger pull the game flashes, and the shot should land where the gun points. Report (a) does it land, (b)
which way it is off at the left/right/top/bottom edges, (c) does shooting off the screen reload.

## 1. Virtua Cop (Sega Model 2) — you asked for this first

**Blocked on ROMs.** `Y:\MiSTer\mame\vcopa.zip` holds 2 of the 23 files. Needed in the same folder: the parent `vcop.zip` and
`model1io2.zip` (the full list is in `docs/CORES.md`). I did not look for them.

Then: load `_Arcade/_gun_test/Virtua Cop (Revision A) [15kHz CRT].mra`. In the core's OSD set **Crosshair = Off** (a real gun does not need it).
Insert a coin, press Start, and shoot: **the game only flashes in play**, not in the attract demo. Everything else is already derived:
15.7 kHz interlaced, picture edges raw x 159..729 / y 47..235, sync 6.2 us / 3 lines.
Could be wrong: the core's `Gun reload` option (leave `Shoot off-screen`); the flash itself (first time measured in this game).

## 2. Time Crisis (Namco Super System 22 core on the card)

Load `_Arcade/Time Crisis (World, TS2 Ver.B).mra`. 640x480 interlaced at 15.7 kHz, so the gun can lock. Mapped: trigger, **A = pedal**, B = Start,
gun Start = Coin.
Could be wrong: the core is a bring-up build (its MRA says the gun reaches the game through an ADC path) and may not accept a gun at all; the
HSync width is unknown (closed core) so X may sit a few percent off; the bottom row or two of the picture is at the edge of what the app can
reach (raw Y 256).

## 3. Lethal Enforcers II (Konami GX core)

Load `_Arcade/Lethal Enforcers II - Gun Fighters (ver EAA).mra`. OSD: **Crosshair = Off**, **P1 stick = Aim** (the core's "Auto" may pick d-pad),
**Mouse aims = Off**. Mapped: trigger, A = reload, B = Start, gun Start = Coin.
Could be wrong: the GX sync width is the game-programmed value I estimated (32 px / 8 lines); a visible left/right or up/down offset that is the
same everywhere points there.

## 4. Alien3 and Jurassic Park (Sega System 32 core)

Load the MRA from `_Arcade/`. OSD: **P1 Gun Input = Stick/USB Gun/Sinden** (the default), **Gun Crosshair = Off**, Gun Sensitivity does not matter
for an absolute gun. Mapped: trigger, Alien3 A = second button, B = Start (Jurassic Park: A = Start, B = Coin). Derived: 32 px / 3 lines.

## 5. Line of Fire (Sega X Board core)

OSD: **Gun control = Lightgun** (not Gamepad). Mapped: trigger, A = bomb, B = Start. Derived: 32 px / 4 lines.

## 6. Terminator 2 (Midway Y unit core, closed)

Mapped: trigger, A = bomb, B = Start, gun Start = Coin. 410x256 with the picture reaching raw Y 273: the app now puts back the lines
the kernel driver drops (checked with a virtual gun, not a real one). HSync width unknown (4.7 us assumed).

## 7. Point Blank 2 (Namco System 11 core): expect it NOT to work with the GunCon 2 as is

Read from the core's source (`SYSTEM11.sv`): player 1's aim comes from a **PS/2 mouse** (relative movements accumulated into a pointer), and
player 2's from the second pad's stick used as a **velocity**. It has no absolute-position input, so the GunCon 2's absolute aim has nothing
to attach to (the trigger would still work). The author's fork `misteraddons/SYSTEM11_MiSTer` adds a GunCon on the PlayStation SNAC port, which
is a different gun. To make this work the app would have to present the GunCon 2 as a mouse (turning its absolute position into movements
that drive the core's pointer); that is new work, not done, and it is your call whether it is wanted.

## 8. Rambo III, Laser Ghost, Operation Wolf

Mapped from their MRAs (trigger + second weapon; Start/Coin). Sync widths: Taito B is 64 px (9.4 us, from its source); the two jotego cores
(Laser Ghost, Operation Wolf) are assumed 4.7 us. **Rambo III** is probably unsupported: the Taito B core reads only the stick's X axis (as a
rotary/paddle input); its README lists Rambo III as playable with a joystick and says nothing of a gun.

## 9. NES Duck Hunt

Load the NES core and the game from the menu. OSD: **Peripheral = Zapper(Joy1)**, **Zapper Trigger = Joystick**. Map: trigger -> `Zapper/Vaus Btn`.
The Zapper reads the PPU's own coordinates, which sit at an offset inside the output; the app places them for the three overscan options
(derived from the source to about a pixel). Duck Hunt's flash boxes are big, so a pixel or two does not matter; a few tens of pixels would.

## What I cannot test without you, and why

I cannot see the screen and cannot move the gun. What I checked: the numbers each core's video reports, that the app derives sensible edges
from them (logs in `captures/harvest/`), the unit tests, and the app's behaviour with a virtual gun. Everything in the "Tested" column of
`docs/CORES.md` that says "not yet" needs your eyes.
