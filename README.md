# GunCon 2 on MiSTer: one calibration, every core

Use a Namco **GunCon 2** on a **15 kHz CRT** with MiSTer cores, without calibrating each core separately. You calibrate once, in a small
core, and from then on every core's picture position is worked out from its measured video timing. The pointer is taken from the game's
own flash on a trigger pull, so it does not wander between shots.

**The aim is that any MiSTer core with a light-gun game works this way**, with no per-core calibration and no per-core changes: the program
reads the game's flash on whatever core you load. Where a game's own flash is unusable (Virtua Cop's is a black frame), a core can supply a
white one on request, see [below](#what-you-need-and-what-is-custom).

**CRT only.** A light gun reads the beam of a tube; it cannot work on an LCD or on HDMI.

## What you need, and what is custom

| Piece | Stock or custom | Needed for |
|---|---|---|
| Cores for the games you play (NES, SNES, Mega Drive, Namco NB-1, System 32, ...) | **stock, unmodified** | everything |
| `MiSTer` (the main program) | **patched**, built from `MiSTer-devel/Main_MiSTer` | everything: this is where the gun handling lives |
| `GunCal.rbf` (calibration core) | **custom**, tiny, our own | calibrating, once. It is not a game core. |

**Nothing else is custom: no game core is replaced.** Both files are in the [release](https://github.com/retrorepair/MiSTer-GunCon2/releases/latest).

One thing a core *can* add, and none ships it yet: the **white flash**. A CRT gun cannot see anything dark (it needs about a third of full
brightness), and some games' own flash is a black frame (Virtua Cop's is), so a dark enemy gives it nothing to measure. A core that can show
the whole picture white for a moment on a shot, when the patched `MiSTer` asks, fixes that. The core announces it with a line in its OSD
(`GunCon flash on request`); a core without the line is never asked, so every stock core works as before, only not in dark areas.
Sega Model 2 (Virtua Cop) is the worked example, see [below](#virtua-cop-and-the-white-flash-an-example-not-shipped); it has been proposed to
the core's author as [alphanu1/sega-model2-mister#13](https://github.com/alphanu1/sega-model2-mister/issues/13) (the game's I/O board makes no flash) and
[#14](https://github.com/alphanu1/sega-model2-mister/issues/14) (the 15 kHz field order, and a picture that fills the screen).

## Status: be honest about what has been tried

- Tested on a real CRT with a real GunCon 2: **Point Blank (Namco NB-1 core, stock)** and **Virtua Cop (the example Model 2 core with the white
  flash)**. Virtua Cop was played with an earlier build of this program that knew the Model 2 core by name. The program in this release finds
  the flash by the core's OSD line instead; it passes the host tests, but **it has not been run on the MiSTer with a core that has the line**,
  because no such core has been built yet. Cores without the line behave exactly as before.
- **House of the Dead** (the Model 2A core, a build from the core's author, the `[15kHz CRT]` MRA; core unmodified): works with the probe
  (patch 0024, below), "works" on 2026-10-23. Its flash is one field and the game reads the gun at the end of it, before the GunCon 2 can report
  that field (the report arrives 33..35 ms after the pull), so the plain flash mode cannot give it the aim in time.
- Every other core's mapping is derived from its measured video and its source, and **has not been tried with the gun**. See
  [docs/CORES.md](docs/CORES.md) for what is known per core and [docs/TESTING.md](docs/TESTING.md) for what to try first.
- Games whose original gun was analog (Terminator 2, Jurassic Park, Alien3) never flash, so a CRT gun cannot work on them.

## Install (about ten minutes)

1. **Back up** `/media/fat/MiSTer` on the SD card, then copy the release's `MiSTer` over it (SD card reader, or the MiSTer's Samba share).
   Reboot the MiSTer. (Running `update_all` or the MiSTer updater later replaces it with the stock program: copy this one back.)
2. Copy `GunCal.rbf` to `/media/fat/_Utility/`.
3. Plug the GunCon 2 into the MiSTer's USB. Its video plug goes to the picture's **sync** (the yellow RCA plug must carry the picture's sync,
   as for any GunCon 2 on a CRT); the MiSTer must output 15 kHz video with composite sync (`MiSTer.ini`: `vga_scaler=0`, `composite_sync=1`).
4. **Calibrate once.** Menu, Utility, **GunCal**. The calibration screen comes up at once and shows only the target: shoot the centre ring,
   then the four corner crosses (the screen flashes white on each shot; the D-pad on the gun moves the targets in or out if your set hides the
   edges). A shot with no light is refused ("MISSED - AGAIN"); shots that do not lie on a line are refused ("BAD SHOTS: REDO"). After the fifth a
   check page shows a live crosshair and two boxes: shoot **EXIT** to save the calibration
   (`/media/fat/config/GUNCAL_uni_<vid>_<pid>_v1.cfg`, once for the gun) and return to the menu, or **TRY AGAIN** to start over. Nothing is saved
   before EXIT. Holding the trigger for 3 seconds also starts over.
5. **Play.** Load any core and game. The first time, map the gun's buttons as you would a gamepad (OSD, Define joystick buttons): the trigger
   is the game's first button, for example. [docs/CORES.md](docs/CORES.md) lists a layout per core.

## Virtua Cop and the white flash (an example, not shipped)

The Sega Model 2 core was changed to show the white flash, and to give a 15 kHz picture that fills the screen (a scan converter), as a
worked example for core authors. The source is the `guncon-scan15` branch of
[retrorepair/sega-model2-mister](https://github.com/retrorepair/sega-model2-mister) (a copy of `alphanu1/sega-model2-mister`). **No Model 2 core
is part of this release**; the changes are proposed to the author in the two issues above. What it does, with the evidence:

- Each shot is held back about 55 ms while the picture flashes white; the gun measures the white and the aim goes to the game with the trigger.
  Shooting off the screen reloads exactly, because no light during a white picture means the gun is not pointing at it.
- The contract, for any core: `joystick_3` bit 0 is a level from `MiSTer`; while it is high, show the whole picture white in whole fields, six at
  most; announce it with an OSD line containing `GunCon flash`. The details are in
  [docs/guncon2/README.md](https://github.com/retrorepair/sega-model2-mister/blob/guncon-scan15/docs/guncon2/README.md) and
  [docs/scan15.md](https://github.com/retrorepair/sega-model2-mister/blob/guncon-scan15/docs/scan15.md) there.
- To try it you build the core from that branch (Quartus Lite 17.0, the chip is 99% full, and a fit can need several fitter seeds; the CRT build
  has no HDMI). The `.rbf` files in that repository's `releases/` predate the OSD line, so this release's `MiSTer` will not ask them for the flash.
- `LIGHTGUN_CRT_BEACON=0` in `MiSTer.ini` (for example in a `[Model2]` section) stops the program from ever asking.

## How it works

1. **GunCal core** draws a calibration like the PS1 GunCon screen. The gun's raw X is the time since the line's sync pulse and Y a line count
   since the frame's sync, so one straight line per axis maps picture positions to the gun's raw numbers.
2. **Universal mapping.** For any other core MiSTer already measures the picture's width, where it starts after the sync pulse and how many
   lines it has; with the calibration that gives the gun's raw value at the core's picture edges. No per-core calibration. A per-core
   calibration file (the old F10 method), if one exists, still wins. A small table supplies each core's sync pulse widths.
3. **Aim from the game's flash** (`LIGHTGUN_CRT_MODE=1`, the default). A shot is registered only where the gun has seen the game's flash: on a
   pull the aim goes off the screen (nothing seen yet), the first valid reading after the pull is the shot, and it holds until the next pull.
   No light within 400 ms leaves it off the screen, so reload shots work. Nothing the gun saw before the pull is used.
4. **Beacon** (cores that announce it): the app holds the trigger back on a pull, asks the core for a white picture, measures, then gives the
   core the aim and the trigger together. [docs/DESIGN.md](docs/DESIGN.md) and the notes in the Model 2 repository's `docs/guncon2/` have the
   evidence and the contract for core authors.
5. **Probe** (games that read their one-field flash before the gun can report it; House of the Dead, by the core's name `Model2A`): the app
   holds the trigger back, sets the aim off the screen and gives the core a short probe press, so the game flashes (and counts a reload). Where
   the gun sees that flash is the aim; the probe press goes up, the aim is set, and the real press follows with it in place. No light means the
   gun is off the screen and the probe was the reload. You see two flashes and a reload with every shot, and the shot reaches the game about
   80 ms after the pull (measured: probe press 3..8 ms, aim 47..52 ms, real press 79..84 ms after the pull).

## `MiSTer.ini` keys (all optional)

| Key | Default | Meaning |
|---|---|---|
| `LIGHTGUN_CRT_TRACKER` | 1 | 0 restores the old 50 ms hold completely |
| `LIGHTGUN_CRT_MODE` | 1 | 1 aim from the game's flash, 0 follow the gun continuously |
| `LIGHTGUN_CRT_BEACON` | 1 | 0: never ask a core for the white flash |
| `LIGHTGUN_CRT_PROBE` | 1 | 0: no probe press, even for the cores that get it (House of the Dead) |
| `LIGHTGUN_CRT_SHOT_MS` | 400 | how long after a pull the flash is waited for |
| `LIGHTGUN_CRT_X_VALID_MIN` | 16 | raw X below this means "no light" |
| `LIGHTGUN_CRT_DARK_MS` | 500 | longest hold across a dark gap that began inside the screen |
| `LIGHTGUN_CRT_EDGE_PCT` | 12 | width of the "edge" band, percent of each axis span |
| `GUNCAL_MARGIN` | 12 | how far inside the picture the calibration targets sit, percent |

Settings can go in a section named for a core or an MRA set (for example `[Model2]`), as for any MiSTer.ini key.

## What is in this repo

- `patches/` twenty-four patches to `Main_MiSTer` commit 13f1de9, in order (`0001` trace, `0002` the tracker, `0003` GunCal support and the
  universal mapping, `0004` aim from the flash, `0005`..`0013` timing log, interlaced cores, per-core sync table, gun windows, ... , `0014`
  tracker edges and the Model 2 inset, `0015` junk readings after a black frame, `0016` the tracker's decisions delivered on time, `0017` the
  beacon, `0018` GunCal starts with the calibration screen, `0019` its TRY AGAIN / EXIT boxes, `0020` its title until the first shot, `0021` the
  Model 2A core's sync sizes, `0022` the gun's D-pad works with the tracker, `0023` a shot only where the gun saw the flash, `0024` the probe). `patches/kernel/` is a one-line fix for the Linux driver (it keeps only the low byte of Y; the app compensates without it).
- `cores/GunCal/` the calibration core (Quartus Lite 17.0; the framework `sys/` is fetched from Template_MiSTer at build time).
- `scripts/` `build-main-mister.sh` (ARM build in WSL, runs the host unit tests, reproducible), `build-guncal.sh`, and the Quartus helpers.
- `tools/mister/` helpers for the MiSTer's UART console and the analysis of gun traces (`GUNDBG=1` builds record every raw report).
- `docs/` the calibration core, the design and its evidence, per-core notes, what to test. `HANDOFF.md` is the working log.
- The [release](https://github.com/retrorepair/MiSTer-GunCon2/releases/latest) has just the two files you need: `MiSTer` (built by
  `scripts/build-main-mister.sh` from the patches here) and `GunCal.rbf`. **The release is older than patches 0018..0024** (GunCal's new screens,
  the D-pad fix, the flash-only shot, the probe): build from this repository for those.

## Build it yourself

```
wsl -d Ubuntu -u root -- bash scripts/build-main-mister.sh     # patched MiSTer for the ARM CPU: build/MiSTer_tracker (and a trace build)
bash scripts/build-guncal.sh                                   # the calibration core: build/GunCal.rbf
```

## Licence and credits

GPL-3.0, like the programs it patches. `Main_MiSTer`, `Template_MiSTer` and the Linux driver are MiSTer-devel's; the Sega Model 2 core is
`alphanu1`'s. The GunCon 2 driver is in MiSTer's Linux kernel; this adds the calibration, the mapping and the tracker on top of it.
