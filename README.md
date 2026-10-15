# MiSTer GunCon 2: saner integration

Goal: make the Namco GunCon 2 on MiSTer usable. Calibration that does not crash or need a keyboard, and a tracker
that follows the game's own trigger flashes instead of a flat 50 ms hold.

Status (2026-10-15): first implementation done and tested in software on a real MiSTer. **Nothing has been tested
with the gun aimed at a lit CRT yet.** Read [docs/DESIGN.md](docs/DESIGN.md) for the evidence, the design and the
test plan.

## Where the real code is

`NolanNicholson/GunCon2-MiSTer` is README-only; the work was merged upstream:

| What | Where |
|---|---|
| Kernel driver | `MiSTer-devel/Linux-Kernel_MiSTer`, `drivers/hid/hid-guncon2.c` (branch `MiSTer-v6.18`) |
| Gun handling, calibration load/save | `MiSTer-devel/Main_MiSTer` `input.cpp` |
| Calibration menu | `Main_MiSTer` `menu.cpp` (`MENU_LGCAL`, `menu_lightgun_cb`) |
| HPS to core transport | `Template_MiSTer` `sys/hps_io.sv` |

`scripts/fetch-refs.sh` re-creates read-only reference copies (untracked), pinned to the commits that were read.

## What is in this repo

- `patches/` changes to Main_MiSTer 13f1de9 (apply in order):
  - `0001` `GUNDBG=1` raw trace of every GunCon event and tracker decision (measurement only)
  - `0002` the tracker (`lightgun_crt.cpp`, host unit tests in `test/`), MiSTer.ini keys, calibration safety fixes
- `scripts/build-main-mister.sh` builds both variants in WSL with ARM's 10.2 toolchain (reproducible: same checksums on rerun).
- `tools/mister/` helpers for the MiSTer's UART console (`console.ps1` to log in yourself, `serial_run.py` to run, push and pull),
  `usbraw.py` (raw USB reports), `gunlog.py` (older evdev logger, useless while MiSTer grabs the gun), `fakegun.py`
  (virtual-gun integration test).
- `tools/analyze_gundbg.py` turns a trace into report timing, valid ranges and the trigger-to-flash lag.
- `captures/dark_usbraw.log` raw reports from the idle gun in the dark.

## New `MiSTer.ini` keys

| Key | Default | Meaning |
|---|---|---|
| `LIGHTGUN_CRT_TRACKER` | 1 | 0 restores the old 50 ms hold |
| `LIGHTGUN_CRT_X_VALID_MIN` | 16 | raw X below this means "no light" |
| `LIGHTGUN_CRT_SHOT_MS` | 200 | window after a trigger pull in which no-light reports are ignored |
| `LIGHTGUN_CRT_DARK_MS` | 500 | longest hold across a dark gap that began inside the screen |
| `LIGHTGUN_CRT_EDGE_PCT` | 12 | width of the "edge" band, percent of each axis span |

## Run it

```
wsl -d Ubuntu -u root -- bash "/mnt/c/Users/joelw/Mister Guncon2/scripts/build-main-mister.sh"
python tools/mister/serial_run.py pushz build/MiSTer_tracker_debug /tmp/dbg/MiSTer
```

Then bind-mount it over `/media/fat/MiSTer` on the MiSTer and restart the app (RAM only; a reboot restores stock). See
`HANDOFF.md` for exactly what is running now.
