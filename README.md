# GunCon 2 on MiSTer: one calibration, every core

Use a Namco **GunCon 2** on a **15 kHz CRT** with MiSTer cores, without calibrating each core separately. You calibrate once, in a small
core, and from then on every core's picture position is worked out from its measured video timing. The pointer is taken from the game's
own flash on a trigger pull, so it does not wander between shots.

**CRT only.** A light gun reads the beam of a tube; it cannot work on an LCD or on HDMI.

## What you need, and what is custom

| Piece | Stock or custom | Needed for |
|---|---|---|
| Cores for the games you play (NES, SNES, Mega Drive, Namco NB-1, System 32, ...) | **stock, unmodified** | everything except the Virtua Cop row below |
| `MiSTer` (the main program) | **patched**, built from `MiSTer-devel/Main_MiSTer` | everything: this is where the gun handling lives |
| `GunCal.rbf` (calibration core) | **custom**, tiny, our own | calibrating, once. It is not a game core. |
| `Model2_GunCon.rbf` (Sega Model 2 core) | **custom build** of `alphanu1/sega-model2-mister` | Virtua Cop only (see below) |

So: only **Virtua Cop** needs a custom game core. For everything else the game cores stay stock; you replace the main program and run the
calibration core once.

Why Virtua Cop is different: its own "flash" after a shot is a black frame, and a CRT gun cannot see anything dark (it needs about a third of
full brightness), so a dark enemy gives it nothing to measure. The custom Model 2 core can show the whole picture white for a moment on a
shot, which the patched `MiSTer` asks for (the arcade cabinet's gun board did the same in the video path). The core announces that it can
with a line in its OSD ("GunCon flash on request"); a core without the line is never asked, so the stock Model 2 core still works with the
patched `MiSTer`, just not in dark areas.

## Status: be honest about what has been tried

- Tested on a real CRT with a real GunCon 2: **Point Blank (Namco NB-1 core)** and **Virtua Cop (custom Model 2 core)**.
- Every other core's mapping is derived from its measured video and its source, and **has not been tried with the gun**. See
  [docs/CORES.md](docs/CORES.md) for what is known per core and [docs/TESTING.md](docs/TESTING.md) for what to try first.
- Games whose original gun was analog (Terminator 2, Jurassic Park, Alien3) never flash, so a CRT gun cannot work on them.

## Install (about ten minutes)

1. **Back up** `/media/fat/MiSTer` on the SD card, then copy the release's `MiSTer` over it (SD card reader, or the MiSTer's Samba share).
   Reboot the MiSTer. (Running `update_all` or the MiSTer updater later replaces it with the stock program: copy this one back.)
2. Copy `GunCal.rbf` to `/media/fat/_Utility/`.
3. Plug the GunCon 2 into the MiSTer's USB. Its video plug goes to the picture's **sync** (the yellow RCA plug must carry the picture's sync,
   as for any GunCon 2 on a CRT); the MiSTer must output 15 kHz video with composite sync (`MiSTer.ini`: `vga_scaler=0`, `composite_sync=1`).
4. **Calibrate once.** Menu, Utility, **GunCal**. Shoot the centre ring, then the four corner crosses (the screen flashes white on each shot;
   the D-pad on the gun moves the targets in or out if your set hides the edges). A shot with no light is refused ("MISSED"); shots that do
   not lie on a line are refused ("BAD SHOTS"). After the fifth the fit is saved to `/media/fat/config/GUNCAL_uni_<vid>_<pid>_v1.cfg` and a
   check page shows a live crosshair: press **A or B** on the gun to finish. Holding the trigger for 3 seconds redoes it.
5. **Play.** Load any core and game. The first time, map the gun's buttons as you would a gamepad (OSD, Define joystick buttons): the trigger
   is the game's first button, for example. [docs/CORES.md](docs/CORES.md) lists a layout per core.

## Virtua Cop (custom Model 2 core)

1. Copy `Model2_GunCon.rbf` to `/media/fat/_Arcade/cores/Model2.rbf` (keep the original as `Model2.rbf.bak`), and
   `Virtua Cop (Revision A) [15kHz CRT].mra` to `/media/fat/_Arcade/`.
2. ROMs go in `/media/fat/games/mame/`, which you supply: `vcopa.zip`, `vcop.zip` and `model1io2.zip` (MAME's sets).
3. Load the MRA. In the core's OSD set **Crosshair = Off** (or leave it on to see where the game thinks you are aiming), and map the gun:
   trigger = Trigger, A = Reload, B = Start, gun Start = Coin.
4. Insert a coin, press Start. **Each shot flashes the whole picture white for a moment; that is the gun finding its aim**, and the trigger
   reaches the game about 55 ms after you pull it. Shooting off the screen reloads, exactly, because no light during the flash means the gun
   is not pointing at the picture.
5. The custom core is analog only (no HDMI picture, `vga_scaler=0`) and always shows 15 kHz as the 480-line filled picture it was built for;
   24 kHz is unchanged. Details and the design: `forks/sega-model2-mister` and its `docs/scan15.md`.
6. To turn the flash off: `LIGHTGUN_CRT_BEACON=0` in the `[Model2]` section of `MiSTer.ini` (the gun then follows the light only).

## How it works

1. **GunCal core** draws a calibration like the PS1 GunCon screen. The gun's raw X is the time since the line's sync pulse and Y a line count
   since the frame's sync, so one straight line per axis maps picture positions to the gun's raw numbers.
2. **Universal mapping.** For any other core MiSTer already measures the picture's width, where it starts after the sync pulse and how many
   lines it has; with the calibration that gives the gun's raw value at the core's picture edges. No per-core calibration. A per-core
   calibration file (the old F10 method), if one exists, still wins. A small table supplies each core's sync pulse widths.
3. **Aim from the game's flash** (`LIGHTGUN_CRT_MODE=1`, the default). On a pull the pointer is set from the first valid readings that follow,
   which is the game's flash, and it holds until the next pull. A shot with no light and no flash stays offscreen, so reload shots work.
4. **Beacon** (cores that announce it): the app holds the trigger back on a pull, asks the core for a white picture, measures, then gives the
   core the aim and the trigger together. [docs/DESIGN.md](docs/DESIGN.md) and the notes in `forks/sega-model2-mister/docs/guncon2/` have the
   evidence and the contract for core authors.

## `MiSTer.ini` keys (all optional)

| Key | Default | Meaning |
|---|---|---|
| `LIGHTGUN_CRT_TRACKER` | 1 | 0 restores the old 50 ms hold completely |
| `LIGHTGUN_CRT_MODE` | 1 | 1 aim from the game's flash, 0 follow the gun continuously |
| `LIGHTGUN_CRT_BEACON` | 1 | 0: never ask a core for the white flash |
| `LIGHTGUN_CRT_SHOT_MS` | 400 | how long after a pull the flash is waited for |
| `LIGHTGUN_CRT_X_VALID_MIN` | 16 | raw X below this means "no light" |
| `LIGHTGUN_CRT_DARK_MS` | 500 | longest hold across a dark gap that began inside the screen |
| `LIGHTGUN_CRT_EDGE_PCT` | 12 | width of the "edge" band, percent of each axis span |
| `GUNCAL_MARGIN` | 12 | how far inside the picture the calibration targets sit, percent |

Settings can go in a section named for a core or an MRA set (for example `[Model2]`), as for any MiSTer.ini key.

## What is in this repo

- `patches/` seventeen patches to `Main_MiSTer` commit 13f1de9, in order (`0001` trace, `0002` the tracker, `0003` GunCal support and the
  universal mapping, `0004` aim from the flash, `0005`..`0013` timing log, interlaced cores, per-core sync table, gun windows, ... , `0014`
  tracker edges and the Model 2 inset, `0015` junk readings after a black frame, `0016` the tracker's decisions delivered on time, `0017` the
  beacon). `patches/kernel/` is a one-line fix for the Linux driver (it keeps only the low byte of Y; the app compensates without it).
- `cores/GunCal/` the calibration core (Quartus Lite 17.0; the framework `sys/` is fetched from Template_MiSTer at build time).
- `scripts/` `build-main-mister.sh` (ARM build in WSL, runs the host unit tests, reproducible), `build-guncal.sh`, and the Quartus helpers.
- `tools/mister/` helpers for the MiSTer's UART console and the analysis of gun traces (`GUNDBG=1` builds record every raw report).
- `docs/` the calibration core, the design and its evidence, per-core notes, what to test. `HANDOFF.md` is the working log.

## Build it yourself

```
wsl -d Ubuntu -u root -- bash scripts/build-main-mister.sh     # patched MiSTer for the ARM CPU: build/MiSTer_tracker (and a trace build)
bash scripts/build-guncal.sh                                   # the calibration core: build/GunCal.rbf
```

## Licence and credits

GPL-3.0, like the programs it patches. `Main_MiSTer`, `Template_MiSTer` and the Linux driver are MiSTer-devel's; the Sega Model 2 core is
`alphanu1`'s. The GunCon 2 driver is in MiSTer's Linux kernel; this adds the calibration, the mapping and the tracker on top of it.
