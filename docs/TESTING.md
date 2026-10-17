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

The ROM set is complete now (`vcopa.zip` + `vcop.zip` + `model1io2.zip`; all 23 files the MRA names are present with the right CRCs) and the game
is **loaded on the MiSTer**: `_Arcade/_gun_test/Virtua Cop (Revision A) [15kHz CRT].mra`. The core reports 496x384 at 15.7 kHz and the app has the
picture at raw x 159..729, y 47..235. In the core's OSD set **Crosshair = Off** (a real gun does not need it). Then insert a coin, press Start and
shoot: **the game only flashes in play**, not in the attract demo. Buttons: trigger, A = Reload, B = Start, gun Start = Coin.
Could be wrong: the `Gun reload` option (leave `Shoot off-screen`); the flash itself (first time measured in this game).
What to report: do shots land, which way they are off at the left/right/top/bottom edges, does shooting off the screen reload.

## 2. Time Crisis — PARKED (the core is not mature enough yet; your call, 2026-10-17)

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

## 4. Point Blank 2 (Namco System 11 core): expect it NOT to work with the GunCon 2 as is

Read from the core's source (`SYSTEM11.sv`): player 1's aim comes from a **PS/2 mouse** (relative movements accumulated into a pointer), and
player 2's from the second pad's stick used as a **velocity**. It has no absolute-position input, so the GunCon 2's absolute aim has nothing
to attach to (the trigger would still work). The author's fork `misteraddons/SYSTEM11_MiSTer` adds a GunCon on the PlayStation SNAC port, which
is a different gun. To make this work the app would have to present the GunCon 2 as a mouse (turning its absolute position into movements
that drive the core's pointer); that is new work, not done, and it is your call whether it is wanted.

## 5. NES Duck Hunt

Load the NES core and the game from the menu. OSD: **Peripheral = Zapper(Joy1)**, **Zapper Trigger = Joystick**. Map: trigger -> `Zapper/Vaus Btn`.
The Zapper reads the PPU's own coordinates, which sit at an offset inside the output; the app places them for the three overscan options
(derived from the source to about a pixel). Duck Hunt's flash boxes are big, so a pixel or two does not matter; a few tens of pixels would.

## Not a goal: games whose original gun was analog, so they never flash

The GunCon 2 only gives a position when the game flashes the screen for it. Alien3, Jurassic Park and Terminator 2 (your call, and it
matches the hardware: their guns were mounted on potentiometers) never flash, so a CRT gun cannot work on them and that is accepted. I
believe the same of Line of Fire, Operation Wolf, Rambo III and Laser Ghost, but you named only the first three: tell me if any of the others
did flash. Their maps, timings and the app's handling are in place and harmless, but nothing here should be expected to work, so none of it is
on the list above. (Rambo III's core also reads only the stick's X.)

## What I cannot test without you, and why

I cannot see the screen and cannot move the gun. What I checked: the numbers each core's video reports, that the app derives sensible edges
from them (logs in `captures/harvest/`), the unit tests, and the app's behaviour with a virtual gun. Everything in the "Tested" column of
`docs/CORES.md` that says "not yet" needs your eyes.
