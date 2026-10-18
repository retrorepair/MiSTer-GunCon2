# Handoff

## Where things stand (2026-10-17, afternoon)

- **Point Blank (NB-1 core)**: working end to end on the user's CRT, "basically perfect" (tested 2026-10-16).
- **Virtua Cop (Sega Model 2 core, alphanu1's, ROM set complete)**: the gun works, off-screen reload works. Dead zones at the edges were
  the core's symmetric off-screen band (patch 0013 moves it outside the picture). The user's remaining complaint is the 15 kHz
  picture (borders, interlace flicker, small text), which is a video problem, not a gun one. Work on it lives in the private fork
  `retrorepair/sega-model2-mister`, branch `guncon-scan15` (see `docs/scan15.md` there): an in-core scan converter that turns the
  native 24 kHz picture into 480 interlaced 15.1 kHz lines, a 4:5 vertical scale, now with a vertical flicker filter, a 12-line ring,
  an automatic pairing of the two fields of a frame to the game's image changes, and a field-order switch. Bit-exact in simulation.
- **Time Crisis (Namco Super System 22 core)**: parked at the user's request ("forget time crisis for now"). Loads and is mapped; never tried.
- Only optical-gun games are a goal; analog-gun games (Terminator 2, Alien3) never flash and are accepted as unsupported.
- Everything is in `docs/CORES.md` (per-core facts and status), `docs/DESIGN.md` (evidence and design) and `README.md`.

## The build state (2026-10-18)

The smoothing/pairing/field-order build does **not fit yet**; nothing is running. Three fits, all "Fitter requires N LABs ... device contains
only 4,191": 4,194 (first), 4,203 (converter trimmed to 174 ALUTs: the fitter's own speed optimisation moves the count by about 10 LABs
for small changes, so smaller RTL did not mean fewer LABs), 4,197 (with the 1:1 15 kHz picture retired and its interlace path tied off,
which synthesis says frees only 76 ALMs). Packing is the same for every seed, so more seeds do not help. Logs: `build/scan15_sweep_run*.txt`,
`build/map_trimmed_failed.rpt`, `build/fit_trimmed_failed.summary`.

The converter RTL is final and bit-exact in simulation (`forks/sega-model2-mister`, branch `guncon-scan15`, `docs/scan15.md`). To make it fit
the options, none taken without the user's say, are: (1) a CRT-only build with the framework's `MISTER_DEBUG_NOHDMI` (about 2,000 ALMs: no HDMI
output, no scaler screenshots; needs `direct_video=1` in MiSTer.ini), (2) drop the Virtua Cop crosshair overlay (about 70-100 ALMs),
(3) renderer speed/area dials (needs a measurement build; could slow Daytona). Virtua Cop already runs at the game's own 29 fps.
Scripts: `scripts/launch_scan15_sweep.ps1` (-MapOnly, -Seeds N -SkipMap), `scripts/scan15_finish.ps1` (finish-or-hold watcher).

What the MiSTer runs now: the previous converter (plain 4:5 blend, `build/Model2_scan15_v1_s1604.rbf`), as `/tmp/dbg/Model2_scan15.rbf`
bind-mounted over the card's Model2.rbf. The OSD there has `15kHz picture` (Filled is set in `config/vcopa.CFG`).

## Waiting on the user

1. Look at the new build on the CRT when it exists (see above): is the flicker gone with `Vertical smoothing` On; if the picture still
   looks doubled or its line pairs look swapped, `Field order` = Swapped.
2. Report aiming accuracy in Filled mode (the gun mapping is measured from the video, so it should follow the new picture, but it was
   not tried), and the left/top dead-zone asymmetry if it is still there.
3. **Kernel Y fix** (optional): `patches/kernel/` is a one-line driver patch. It needs a kernel rebuild and a new kernel image on the SD card.

## What is on the MiSTer (192.168.1.204, UART on COM3)

RAM only, a reboot returns to stock:
- `/tmp/dbg/MiSTer21` = patched app, patches 0001..0013, bind-mounted over `/media/fat/MiSTer`.
- `/tmp/dbg/Model2_scan15.rbf` (the v1 converter) bind-mounted over `/media/fat/_Arcade/cores/Model2.rbf`, so MRAs that name `Model2` get
  it. The original `Model2.rbf` on the card is untouched underneath.
- `/tmp/archive/*` earlier logs (Point Blank, Time Crisis probes, Model 2 probes). `/tmp/guncal_apply.log` is the live timing log.

Written to the SD card (the only persistent changes; the stock `MiSTer` binary is untouched):
- `config/GUNCAL_uni_0b9a_016a_v1.cfg` (+ `.3pt.bak`, `GUNCAL_log.txt`): the user's universal calibration.
- `config/inputs/<game>_input_0b9a_016a_v3.map` (one per gun game found on the card: vcopa, vcop, Model2, le2, alien3, jpark, loffire,
  ptblank2a, term2, rambo3, lghost, opwolf, timecris, plus ptblanka/NB1/NES): the GunCon 2's buttons onto the game's own button list.
  Layout and rationale in `docs/CORES.md`. Written by `tools/mister/make_gun_map.py`, which refuses to overwrite.
- `config/vcopa.CFG`: OSD settings for Virtua Cop (Crosshair Off, 262/263 lines, Filled).
- `_Arcade/_gun_test/` with two MRAs from the Model 2 release. Delete the folder to undo. (`load_core` only takes MRAs under `/media/fat`.)

Bring it back up after a reboot (console logged in by the user, never by this tooling): see the commands in README.md, then
`mount --bind /tmp/dbg/Model2_scan15.rbf /media/fat/_Arcade/cores/Model2.rbf` (push the rbf with `serial_run.py pushz`, ~9 minutes).

## Repos

- This repo: `retrorepair/MiSTer-GunCon2` (private). (`MiSTer-GunCal` is an older duplicate, unused.)
- `retrorepair/sega-model2-mister` (private working copy of `alphanu1/sega-model2-mister`, GPL-3.0), branch `guncon-scan15`: the 15 kHz
  scan converter. Local clone in `forks/` (git-ignored; its `mine` remote is the private copy, `origin` is alphanu1's public repo, read
  only). `forks/Arcade_namco22_MiSTer` is a read-only clone of `spacestate1`'s Namco System 22 core.
- Never push to a public fork; the user wants private copies.

## Lessons for whoever continues

- **`load_core` takes a core `.rbf` or an arcade `.mra` only.** A ROM path left the FPGA unconfigured and hung the console for an hour on
  2026-10-17 (recovered without a reboot with a one-off app build; see `docs/CORES.md`). `harvest_cores.py` now refuses anything else.
- The CD cores (PSX, Saturn, Mega-CD, TG16) run `MiSTer_Physical-CD` (MiSTer.ini `main=`): the patches do not apply there.
- The MiSTer is currently left running Virtua Cop (Filled mode) under the patched app.

- The user wants no ambiguity and no timer-based asks: self-paced tools, exact steps.
- Never type credentials into a login prompt; the user logs in on the console (`tools/mister/console.ps1`), then use `serial_run.py`.
- **Never `cat` a big file over the serial console** (a 2.5 MB MRA jammed it); `head -c` it or `pull` it. Ctrl+C drains it.
- Verify with a trace before designing, and never decide a game's behaviour from attract mode or a core's source: see the flash
  correction (`docs/CORES.md`, Model 2).
- `user_io_get_confstr(n)` returns NULL for an empty field as well as past the end.
