# MiSTer GunCon 2: saner integration

Goal: make the Namco GunCon 2 on MiSTer usable. One calibration for every core instead of one per core, and an aim that
comes from the game's own trigger flash instead of a continuous guess that wanders.

**Status (2026-10-16):** working on a real CRT. A universal calibration made once with the GunCal core is applied
automatically to the running core from its measured video timing, and the pointer is taken from the game's flash.
Tested in Point Blank (Namco NB-1 core): "basically perfect so far". Everything runs from RAM on the MiSTer; nothing replaces
your stock `MiSTer` binary on the SD card yet.

| Doc | What it holds |
|---|---|
| [docs/CALIBRATION-CORE.md](docs/CALIBRATION-CORE.md) | The GunCal core: the calibration flow, the pages, how it fits together |
| [docs/DESIGN.md](docs/DESIGN.md) | Measured evidence, the design and why, limits, how to test |
| [docs/CORES.md](docs/CORES.md) | Per core: where it came from, its measured video, sync width, buttons, and whether it has been tested |
| [HANDOFF.md](HANDOFF.md) | What is running on the MiSTer now and what is next |

## How it works

1. **GunCal core** (`cores/GunCal`, an FPGA core): draws a PS1-style calibration (a ring and four corner crosses, with a flash on each
   shot), then a check page with a live crosshair. The gun's raw X is a time since the line's sync and Y a line count, so one straight
   line per axis maps the core's pixels to the gun's raw numbers. Saved once for the gun (`config/GUNCAL_uni_<vid>_<pid>_v1.cfg`).
2. **Universal mapping**: for any other core, MiSTer already measures the picture's width, where it starts relative to the sync, and
   how many lines. From that and the calibration, the gun's raw value at the core's picture edges follows. No per-core calibration.
   A per-core calibration file (the old F10 method), if one exists, still wins.
3. **Aim from the game's flash** (`LIGHTGUN_CRT_MODE=1`, the default): between shots the scene wanders (in Point Blank the gun saw
   no light in 82% of its reports). On a trigger pull the pointer is set from the first valid readings that follow, which is the
   game's flash (it arrives 50 to 100 ms after the pull), then it holds until the next pull. A shot with no light and no flash stays
   offscreen, so reload shots work. `LIGHTGUN_CRT_MODE=0` gives the old continuous tracking.

## Where the real code is

`NolanNicholson/GunCon2-MiSTer` is README-only; the work was merged upstream.

| What | Where |
|---|---|
| Kernel driver | `MiSTer-devel/Linux-Kernel_MiSTer`, `drivers/hid/hid-guncon2.c` (it keeps only the low byte of Y) |
| Gun handling, calibration load/save | `MiSTer-devel/Main_MiSTer` `input.cpp` |
| Core video-timing measurement | `Template_MiSTer` `sys/hps_io.sv` (`video_calc`) |

`scripts/fetch-refs.sh` re-creates read-only reference copies (untracked), pinned to the commits that were read.

## What is in this repo

- `patches/` eight patches to Main_MiSTer 13f1de9, in order:
  - `0001` `GUNDBG=1` raw trace of every GunCon event and tracker decision (measurement only)
  - `0002` the continuous tracker (`lightgun_crt.cpp`), `MiSTer.ini` keys, calibration safety fixes (no divide by zero)
  - `0003` GunCal support: the calibration sequence and maths (`guncal.cpp`), the universal mapping onto a core, the core drive code
  - `0004` mode 1: aim from the game's flash
  - `0005` logs the framework's measured video timing of the running core (`/tmp/guncal_apply.log`)
  - `0006` the universal mapping now handles interlaced cores and cores without `frame_clocks` (Super System 22 and Model 2 are 480i/384i)
  - `0007` also logs the core's own `J`/`j` button lists
  - `0008` the Sega Model 2 core's HSync width (64 pixels)
- `cores/GunCal/` the FPGA core (Quartus Lite 17.0, framework `sys/` fetched from Template_MiSTer at build time).
- `scripts/` `build-main-mister.sh` (ARM build in WSL, runs the host tests, reproducible), `build-guncal.sh` (the core).
- `tools/mister/` helpers for the MiSTer's UART console and on-device tests (`serial_run.py`, `console.ps1`, `usbraw.py`, `fakegun*.py`,
  `make_gun_map.py`); `tools/analyze_*.py`, `show_pulls.py` turn traces into numbers.
- `test/` lives in the Main_MiSTer tree (`test/lightgun_crt_test.cpp`, `test/guncal_test.cpp`), exported with the patches.

## `MiSTer.ini` keys (all optional)

| Key | Default | Meaning |
|---|---|---|
| `LIGHTGUN_CRT_TRACKER` | 1 | 0 restores the old 50 ms hold completely |
| `LIGHTGUN_CRT_MODE` | 1 | 1 aim from the game's flash, 0 follow the gun continuously |
| `LIGHTGUN_CRT_SHOT_MS` | 400 | how long after a pull the flash is waited for |
| `LIGHTGUN_CRT_X_VALID_MIN` | 16 | raw X below this means "no light" |
| `LIGHTGUN_CRT_DARK_MS` | 500 | longest hold across a dark gap that began inside the screen |
| `LIGHTGUN_CRT_EDGE_PCT` | 12 | width of the "edge" band, percent of each axis span |
| `GUNCAL_MARGIN` | 12 | how far inside the picture the calibration targets sit, percent |

## Run it

```
wsl -d Ubuntu -u root -- bash "/mnt/c/Users/joelw/Mister Guncon2/scripts/build-main-mister.sh"
bash scripts/build-guncal.sh
python tools/mister/serial_run.py pushz build/MiSTer_tracker_debug /tmp/dbg/MiSTer
python tools/mister/serial_run.py pushz build/GunCal.rbf /tmp/dbg/GunCal.rbf
```

On the MiSTer: bind-mount the app over `/media/fat/MiSTer`, restart it, then
`echo "load_core /tmp/dbg/GunCal.rbf" > /dev/MiSTer_cmd`. `HANDOFF.md` has the exact commands and the current state.
