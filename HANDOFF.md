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

## The build state (2026-10-18, evening)

The smoothing/pairing/field-order converter now **fits and is on the MiSTer**. It needed room: three fits of the converter alone failed on
"Fitter requires N LABs ... only 4,191" (4,194; 4,203; 4,197 with the 1:1 15 kHz picture retired), so the framework's HDMI scaler was dropped
(`MISTER_DEBUG_NOHDMI` in `Model2.qsf`: about 4,000 ALMs freed, no HDMI picture, no scaler screenshots; the CRT path and `vga_scaler=0` are
untouched). Seed 1604, 36,860 of 41,910 ALMs (88%), 514/553 memory blocks, all clocks pass (tightest setup +0.43 ns on clk_sys, +0.81 ns
clk_mem). `build/Model2_scan15_s1604.rbf`, md5 0a2d705e... (the previous converter is `Model2_scan15_v1_s1604.rbf`).

15 kHz is always the Filled picture now (the 1:1 picture and `15kHz lines/width/picture` are gone). OSD: `Vertical smoothing` On/Off (bit 65),
`Field order` Normal/Swapped (bit 66). Full notes in `forks/sega-model2-mister/docs/scan15.md`; Virtua Cop already runs at the game's own 29 fps.

**On the MiSTer now (RAM only; the 2026-10-18 reboot at 15:22 had wiped the earlier setup):** `/tmp/dbg/Model2_scan15_v2.rbf` bind-mounted over
`_Arcade/cores/Model2.rbf`, `/tmp/dbg/MiSTer21` (patched app, patches 0001-0013, `build/MiSTer_tracker_debug`, md5 1493387b...) over
`/media/fat/MiSTer`; Virtua Cop loaded. Bring-up after a reboot (the user logs in on the console first, `tools/mister/console.ps1`, run with
`powershell -ExecutionPolicy Bypass -File`): push both with `serial_run.py pushz` (the rbf takes about 4 minutes, the app 2: the UART is 115,200 baud),
`mount --bind` each, `kill` the app (nothing restarts it: `/etc/inittab` starts it once), `setsid /media/fat/MiSTer > /tmp/mister21.log 2>&1 < /dev/null &`,
then `echo "load_core <mra>" > /dev/MiSTer_cmd` under `timeout 8`.

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
