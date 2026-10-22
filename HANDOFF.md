# Handoff

## 2026-10-22: the patched app and GunCal are now ON THE CARD

- After a reboot the RAM-only copies were gone and the card ran the **stock** `MiSTer`, so nothing waited for the flash. Now installed
  persistently over the UART: `/media/fat/MiSTer` = the patched app (patches 0001-0018, md5 f12dff4c...), the stock one kept as
  `/media/fat/MiSTer.stock`; `GunCal.rbf` in `/media/fat/_Utility/`. (`update_all` replaces `MiSTer` with the stock one: copy ours back.)
  The calibration before this was kept as `config/GUNCAL_uni_0b9a_016a_v1.cfg.bak-20261022`.
- The user was running **`_Arcade/cores/Model2C_20261022.rbf`** (the core author's local `model2c` build, House of the Dead; its core name
  reports as `Model2A`). It has no beacon and no OSD flash line, so the app aims from the game's own flash (`LIGHTGUN_CRT_MODE=1`, the default). The author's
  `Gun flash` option is Virtua Cop only (a single white frame the GunCon may be too slow to read: first lit report after darkness has a junk Y). The
  user's report on the stock app: "it flashes but clearly the GunCon 2 can't see it in time". **Not yet tried with the patched app and the gun in
  House of the Dead**; if it still misses, record a `GUNDBG` trace (`build/MiSTer_tracker_debug`) of one shot and decide from the numbers.
- Patch 0018: GunCal starts with the calibration screen (before, a saved calibration put it on the plain monitor page, and the PS1-style
  screen needed a 3 s trigger hold nobody was told about). The sequence is still centre + four corners + check page.
- A `LIGHTGUN_CRT_BEACON=2` override (ask a core for the flash without its OSD line) was written and dropped: Model2C has no beacon, and
  the `[Model2]` section would also have matched the beacon build.
- Pushing files: Git Bash rewrites `/media/...` arguments (`MSYS_NO_PATHCONV=1`), and the SSH key is not authorised on the MiSTer (UART only).

## Where things stand (2026-10-20)

- **Point Blank (Namco NB-1 core, stock)**: works end to end on the user's CRT, "basically perfect" (2026-10-16).
- **Virtua Cop (Sega Model 2 core)**: works on the real gun with the white-flash ("beacon") build: dark enemies are hit, off-screen shots
  reload exactly, and the user's verdict was "seems to work great". The core is the example build in `retrorepair/sega-model2-mister`
  (public), branch `guncon-scan15`: a 15 kHz scan converter (the filled 480-line picture, no smoothing, field order Normal, analog only
  via `MISTER_DEBUG_NOHDMI`) plus the beacon (`docs/scan15.md` and `docs/guncon2/README.md` there).
- **Both were raised with the core's author** as issues on `alphanu1/sega-model2-mister`: #13 (Virtua Cop's I/O board makes no flash; that is
  all it says) and #14 (the 15 kHz **field order** looks reversed on a CRT, which is the important one and costs next to no area; the filled
  480-line picture is a nice-to-have that may not fit). The user decided that the fork **is only an example of the two ideas and is not released**; no Model 2 core is in this repo's
  release. The author is willing to make a 15 kHz-only core based on it.
- **Release**: `retrorepair/MiSTer-GunCon2` (public) has a release with just the patched `MiSTer` and `GunCal.rbf`.
- **Time Crisis (Namco Super System 22 core)**: parked at the user's request. Loads and is mapped; never tried.
- Only optical-gun games are a goal; analog-gun games (Terminator 2, Alien3, Jurassic Park) never flash and are unsupported.
- Everything is in `docs/CORES.md` (per-core facts and status), `docs/DESIGN.md` (evidence and design) and `README.md`.

## Not verified, and what to do about it

- **Field order: what is on the card is the correct one** (the user, 2026-10-20, going by their eyes on the CRT and by the saved OSD setting
  `Field order` = Normal, bit 66 = 0 in `config/vcopa.CFG`, last written 2026-10-18 22:15). The core on the card (seed 1604, md5 9b2584ec...) has
  `swp` = 0 hard-wired: field 0 (aligned vsync, 263 lines) = even output rows, field 1 (vsync half a line early, 262 lines) = odd rows. The user says
  the release's 1:1 mode looks reversed against it; its row parity reads the same in the code, so the cause is unproven (maybe which native
  frame goes in which field). Issue #14 on `alphanu1/sega-model2-mister` reports exactly this. Do NOT flip `swp` (a flip was tried in the source
  on 2026-10-20 and reverted before any build).
- The released `MiSTer` finds the flash by an OSD line (`-,GunCon flash on request;`, any dash line containing "GunCon flash") that the
  **core** announces. Host unit tests pass, but it has **not been run on the MiSTer with a core that has the line**: the last core build
  (the one with the line) was stopped on purpose. The Model 2 `.rbf` files in the fork's `releases/` predate the line, so with the released
  `MiSTer` they get no flash. What was played on the hardware is the previous app (it knew the core by name) with
  `Model2_scan15_s1604.rbf` (md5 9b2584ec..., misses the i960 clock by 1.688 ns, works).
- To close it: build the fork with `scripts/scan15_sweep.ps1` (it continues over seeds until setup timing is met on every clock; about
  27 min a fit, one at a time, a fit peaks near 5 GB; seeds 1606, 1607, ...), put the result on the card as `Model2.rbf`, run the released
  `MiSTer`, and check that a shot flashes white and that a core without the line (Point Blank) does not.

## What is on the MiSTer (192.168.1.204, UART on COM3; the user logs in on the console)

On the SD card: `_Arcade/cores/Model2.rbf` = the beacon build (seed 1604, md5 9b2584ec...), `Model2.rbf.bak` = the original; the user's
calibration `config/GUNCAL_uni_0b9a_016a_v1.cfg`; `config/inputs/*_input_0b9a_016a_v3.map` (the gun's buttons, one per gun game, made by
`tools/mister/make_gun_map.py`, which refuses to overwrite); `config/vcopa.CFG`; `_Arcade/_gun_test/` (two MRAs; `load_core` only takes
MRAs under `/media/fat`). `MiSTer.ini` is the original. Since 2026-10-22 `/media/fat/MiSTer` is the patched app (stock: `MiSTer.stock`).

To replace the app: `pushz` it to `/media/fat/MiSTer.new` (UART 115,200 baud, about 11 KB/s, md5 checked), `mv -f` it over `MiSTer`, `kill` the
running app (nothing restarts it: `/etc/inittab` starts it once, and launchers such as misterzine start it with arguments),
`setsid /media/fat/MiSTer > /tmp/mister.log 2>&1 < /dev/null &`, then `echo "load_core <rbf or mra>" > /dev/MiSTer_cmd` under `timeout 8`.

## Build

- App: `MSYS_NO_PATHCONV=1 wsl -d Ubuntu -u root -- bash "/mnt/c/Users/joelw/Mister Guncon2/scripts/build-main-mister.sh"` (runs the host
  tests; writes `build/MiSTer_tracker` and `build/MiSTer_tracker_debug`, the latter records every raw report with `GUNDBG=1`).
  The development clone `Main_MiSTer/` is git-ignored; its commits are exported with `git format-patch` into `patches/` (rename to
  `00NN-...` and fix the `[PATCH n/17]` subject).
- GunCal: `scripts/build-guncal.sh` -> `build/GunCal.rbf`.
- The Model 2 core: `scripts/scan15_sweep.ps1` (see above). `forks/sega-model2-mister` has remote `mine` (retrorepair, public) and `origin`
  (alphanu1, read only).

## Waiting on the user / open

1. Decide whether to build a core with the OSD line (above), so the released app and a core agree on the hardware.
2. An HDMI-on fit of the converter (remove `MISTER_DEBUG_NOHDMI`) was never tried since the smoothing was dropped.
3. **Kernel Y fix** (optional): `patches/kernel/` is a one-line driver patch (the driver keeps only the low byte of Y; the app compensates).
4. Cores other than Point Blank and Virtua Cop are mapped from their measured video and have not been tried with the gun.

## Lessons for whoever continues

- **`load_core` takes a core `.rbf` or an arcade `.mra` only.** A ROM path left the FPGA unconfigured and hung the console for an hour
  (2026-10-17). `harvest_cores.py` refuses anything else.
- The CD cores (PSX, Saturn, Mega-CD, TG16) run `MiSTer_Physical-CD` (MiSTer.ini `main=`): the patches do not apply there.
- The user wants no ambiguity and no timer-based asks: self-paced tools, exact steps. Their word is final: do not build or release what they
  did not ask for.
- Never type credentials into a login prompt; the user logs in on the console (`tools/mister/console.ps1`), then use `serial_run.py`.
- **Never `cat` a big file over the serial console**; `head -c` it or `pull` it. Ctrl+C drains it.
- Verify with a trace before designing, and never decide a game's behaviour from attract mode or a core's source: see the flash
  correction (`docs/CORES.md`, Model 2). A CRT gun sees nothing below about a third of full brightness.
- Games flash only in gameplay; default every core to flash mode (`LIGHTGUN_CRT_MODE=1`).
- `user_io_get_confstr(n)` returns NULL for an empty field as well as past the end.
- Fits near 99% area are chaotic (about +-10 LABs for small changes) and seeds change timing, not the LAB count.
