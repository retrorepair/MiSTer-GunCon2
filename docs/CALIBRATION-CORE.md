# GunCal: the GunCon 2 calibration and monitor core

A MiSTer FPGA core (`cores/GunCal`) that gives the gun a clean 15 kHz picture and walks you through a PS1-style calibration (and has a
monitor page that shows live where the gun thinks it is pointing). The calibration it produces is made once, for the gun and your display, and is applied
to every other core automatically from that core's measured video timing.

## Why a core, and why one calibration can serve every core

The gun does not measure a position on the glass. It measures **time**: X is the time since the line's sync pulse began, Y is the number
of lines since the frame's sync. Both are linear in where the beam is, so one straight line per axis maps any picture position to the
gun's raw numbers (about 1.19 raw units per 100 ns, about 1 per line, measured). What differs between cores is only *when* their picture
sits inside the line and frame. MiSTer measures that for the running core (`video_calc` in `hps_io.sv`: picture width and duration, end of
HSync to the first pixel, lines from the end of VSync to the first line; checked against the NB-1 core's RTL to the nanosecond), so
one calibration gives the picture edges of any core.

A CRT shows only part of what a core draws (overscan, bezel). Nothing here assumes the whole picture is visible: the targets sit well
inside (12% in from the edges by default, `GUNCAL_MARGIN`; the gun's D-pad moves them in or out while you calibrate) and the fit uses
only where you actually shot. Hidden edges are reached by extrapolating the line.

## The calibration (the PS1 GunCon screen's look)

Loading the core starts the calibration at once, as a console game's own GunCon calibration does (an earlier version came up on the monitor page
when a calibration was already saved, and the calibration was only reached by holding the trigger for 3 seconds).

A bright yellow screen (so the gun always has light) and one blue ring with a plus and ticks, round on a 4:3 tube. **While a target is asked for
there is nothing else on the screen**, so a target is never covered. Five targets are shot in turn: the centre, then the four corners. On each
trigger pull the screen flashes white for about 100 ms and the first valid reports of the flash are the measurement (median of the reports in
the next 300 ms): the shot counts only once the gun has seen the flash. A shot with no light is refused (a navy strip at the top says
"MISSED - AGAIN"; no target can reach that strip); shots that do not lie on a line are refused ("BAD SHOTS: REDO") and the sequence starts again.
Every shot is logged in `config/GUNCAL_log.txt` (target, raw reading, residual) when the calibration is kept.

Then the **check page**: a ring in the middle and a black crosshair that follows the gun, and two white boxes, **TRY AGAIN** and **EXIT**.
Shoot a box: the screen flashes white and the gun's readings in the flash are tested against the boxes, as for a calibration shot (the box under
the crosshair turns green). **EXIT saves the calibration** (`/media/fat/config/GUNCAL_uni_<vid>_<pid>_v1.cfg`, once for the gun) **and leaves
GunCal for the menu**; TRY AGAIN starts over; nothing is saved before EXIT, so a calibration you walk away from does not replace the old one.
On the gun, A does what EXIT does; B saves and shows the monitor page. Holding the trigger for 3 seconds redoes the calibration at any time.

The picture is 480i: two fields of 240 lines (the second field's VSync half a line early), both showing the same 529 x 240 picture, so every
line is drawn twice, a row apart, and the CRT shows a filled picture. The gun counts lines per field, so its Y is as in a 240 line picture.

## The monitor page

```
GUNCON2 CALIBRATION CORE
NOW  X:0287  Y:0123       the gun's latest raw report
LAST X:0287  Y:0123       the last report that had light
PICTURE X:0264  Y:0120    the calibrated position in this core's pixels (x 0..528, y 0..239)
LIGHT:YES                 X >= 16
LOCK :STEADY              STEADY, JUMPY or NO LIGHT
EVENTS/S:0060             new gun reports per second
TRIGGER:UP    PULLS:0003
X RANGE:0182-0716         min/max with light since the last clear
Y RANGE:0030-0237
```

STEADY means the gun is locked to the picture's sync; JUMPY means it sees light but the numbers are unrelated from one report to the
next, which is a wiring problem (the yellow RCA plug must carry the picture's sync).

## Using the calibration in a real core

When any other core runs, `guncal_apply_universal` (in `input.cpp`) reads the core's measured timing and derives the gun's raw values at
the core's left, right, top and bottom picture edges: the same four numbers the old per-core F10 calibration stored, so the rest of
MiSTer's gun path is unchanged. A per-core calibration file, if one exists, wins. The sync pulse widths are not measured by the
framework; a small per-core table supplies them (NB-1: HSync 32 px at 6.048 MHz; NES: 25 dots; otherwise 4.7 us and 3 lines).

On top of that, the pointer follows the game's flash (`LIGHTGUN_CRT_MODE=1`): see `docs/DESIGN.md`.

Tested in Point Blank on the NB-1 core. It also needs the gun's button map for the core (the trigger onto the core's first button); the
OSD wizard does that, or `tools/mister/make_gun_map.py` writes it directly (for NB-1: `make_gun_map.py NB1 4 7 8 9 5`, and the same
for the set name `ptblanka`, because MiSTer reports either).

## How it fits together

- **FPGA core** (`cores/GunCal`): draws the pages, the target, the flash, the readouts. No maths.
- **MiSTer app** (`guncal.cpp`, driven from `input.cpp`, active only while this core runs): counts the pulls, collects the reports, fits the
  lines, saves them, sends the corrected pointer back. Host unit tests in `test/guncal_test.cpp`.
- Words to the core: `joystick_3` target position and count, `joystick_4` page / target number / flash sequence / message / pointer,
  `joystick_5` the gun's raw report. Only sent while the running core is named `GUNCAL`.
- The kernel driver keeps only the low byte of the gun's Y, so Y here is 0..255.

## Build and run

```
bash scripts/build-guncal.sh --map     synthesis only, a few minutes
bash scripts/build-guncal.sh           full compile (Quartus Lite 17.0), output build/GunCal.rbf
python tools/mister/serial_run.py pushz build/GunCal.rbf /tmp/dbg/GunCal.rbf
```

On the MiSTer, with the matching app running: `echo "load_core /tmp/dbg/GunCal.rbf" > /dev/MiSTer_cmd`. Nothing is written to the SD
card except the calibration file and its log.
