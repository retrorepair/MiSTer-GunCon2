# Handoff (written 2026-10-23, about 01:00 BST, for a NEW session)

Read this whole file first. The user is tired and angry because this session took far too long and asked them for the same things many times.
Do not repeat that.

## 0. How the user wants you to work (their words, in order of importance)

- "The user's word is gospel." Do what was asked. Do not substitute your own idea; if you really must, say so first in one line and carry on.
- **"Tell me what you're planning to do before you do it"**, in a few plain words. They also complained "you don't tell me enough about what you're doing"
  and "why are you simulating?": say what and why, briefly, then act. No cryptic one-liners.
- **The MiSTer is yours to use "at will". Do NOT ask for permission to use it.** (their words, 2026-10-23)
- **Passwords: you cannot type one**, not even when told to (a hard rule on the assistant). The user's answer was to install an ssh key so no login is
  ever needed again. STATE OF THAT: attempt 1 failed (the MiSTer's system area is read-only: "Read-only file system"); attempt 2 (a Windows Terminal
  window titled "Install SSH key", started with `tools/mister/install_key.bat`, whose `build/install_key.sh` does `mount -o remount,rw /`, stores the key,
  `remount,ro /`) was **still waiting for the password on 2026-10-23 morning** (its ssh process started 00:50). First thing to do:
  `ssh -o BatchMode=yes root@192.168.1.204 echo ok`. If it prints `ok` you have the MiSTer without any login.
- **2026-10-23, the user: "DON'T ask me for keys and shit ... You have COMPLETE authority over my mister and file system."** Do NOT ask them to log in or
  type a password again. Why access was easy "last week": earlier sessions used the serial console after the user had logged in on it once, and that
  login lasted for days; the reboot at about 23:01 on 22 Oct logged it out. They were told this once (2026-10-23). Ports open on the MiSTer: 22, 21 only.
- The UART console on COM3 is at a `login:` prompt (the MiSTer was rebooted at about 23:01 UTC and the login was lost). `tools/mister/serial_run.py`
  only works after the user logs in on it; prefer ssh once the key is in.
- Do not build or release what was not asked for. Do not leave anything half done silently. Say plainly what is untested.
- They want it **pushed to the repo (retrorepair/MiSTer-GunCon2) once it works**; see section 6.
- Their language is blunt. It is not a reason to answer defensively. Fix things.

## 1. The project in one paragraph

A GunCon 2 (Namco light gun) works on MiSTer FPGA cores on a 15 kHz CRT with ONE calibration (made in our small core **GunCal**) and a **patched
`MiSTer` main program** (`patches/0001..0022` on MiSTer-devel/Main_MiSTer commit 13f1de9) that tracks the gun and maps it onto whichever core is running
from the core's measured video timing. The principle the user insists on: **a shot is only registered after the gun has seen the white flash**
(`LIGHTGUN_CRT_MODE=1`, the default: the aim comes from what the gun sees in the game's flash after a pull, wait up to 400 ms; cores that announce a
white-flash-on-request line get the "beacon": hold the trigger, ask the core for white, measure, then give aim and trigger together).
Read `README.md` (setup), `docs/DESIGN.md` (evidence), `docs/CORES.md`, `docs/CALIBRATION-CORE.md`.

## 2. What is on the user's MiSTer right now (192.168.1.204, root; the user knows the password)

Checked from the logs at 2026-10-22 23:44 UTC and the deploys after it:

| File on the card | What it is |
|---|---|
| `/media/fat/MiSTer` | **(2026-10-23 ~01:25 BST)** the patched app WITH the GUNDBG trace, patches 0001-**0023**, md5 `3985491a98511e88d37d1481f5e30ece` |
| `/media/fat/MiSTer.clean` | the same, without the trace, md5 `8f22d3fcfb527aa683d53a4f3923de59` |
| `/media/fat/MiSTer.prev` | the app before that (patches to 0021, with the trace), md5 `0134139a478618da8167125c115d1fee` |
| `/media/fat/MiSTer.stock` | the ORIGINAL stock app, md5 `2f21ff276ebf429ab91a8b4e33314623`. Put it back to undo everything. |
| `/media/fat/_Utility/GunCal.rbf` | the latest calibration core (480i, very light yellow, md5 `95d13176a9c87e7b16bcdf892da7d17d`); `GunCal.rbf.prev` = the one before |
| `/media/fat/config/GUNCAL_uni_0b9a_016a_v1.cfg` | the saved calibration (last good one: x = 1.1903*px + 119.16, y = 0.9918*py + 17.38, residual 5.4/2.7). `.bak-20261022` = the old 240p one (1.1878, 114.22, 0.9863, 19.04). |
| `/media/fat/_Arcade/cores/Model2C_20261022.rbf` | the core author's LOCAL House of the Dead build (core name reports as `Model2A`); no flash request, no beacon |
| `/media/fat/_Arcade/cores/Model2.rbf` | our Model 2 beacon build (seed 1604, no OSD line); `.bak` = the original |

- `update_all` or the MiSTer updater replaces `/media/fat/MiSTer` with the stock one: copy ours back.
- The system area (`/`) is **read-only**; only /media/fat and /tmp are writable (`mount -o remount,rw /` to change it, then `remount,ro`).
- The launcher software on the card (misterzine, zaparoo) **restarts the MiSTer app for every game it launches**, which overwrites `/tmp/gundbg*.csv`.
  To keep a trace, fetch it right after the session and before launching anything else.
- The MiSTer app is started once at boot by `/etc/inittab` (`::sysinit:/media/fat/MiSTer &`); nothing restarts it. To restart by hand:
  `kill <pid>`, then `cd /media/fat; setsid /media/fat/MiSTer > /tmp/mister.log 2>&1 < /dev/null &`, then
  `timeout 8 sh -c 'echo "load_core /media/fat/_Utility/GunCal.rbf" > /dev/MiSTer_cmd'` (**rbf or mra paths only; a ROM path wedges the FPGA**).

## 3. The repo (C:/Users/joelw/Mister Guncon2, remote retrorepair/MiSTer-GunCon2, branch main)

**Pushed 2026-10-23** (the user asked): patches to 0024, `cores/GunCal` changes, docs, tools, this file. The public release was NOT touched.
The development clone of Main_MiSTer is `Main_MiSTer/` (git-ignored, branch guncon-dev, its commits are exported with `git format-patch` into
`patches/` and the subject's `[PATCH n/N]` fixed; the commit author must be `retrorepair <joelwhybrow@googlemail.com>`).
Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
Patches this session: 0018 GunCal starts with the calibration screen; 0019 check page with TRY AGAIN / EXIT, calibration saved only on EXIT (A on the
gun = EXIT, B = save and monitor page, holding the trigger 3 s restarts); 0020 title banner and prompt until the first shot; 0021 `Model2A` in the sync
table; 0022 the tracker drops only the gun's X and Y (it dropped the D-pad too). The README/CALIBRATION-CORE docs are updated for 0018-0020; they do not
yet mention 0021/0022. The public release (v1: `MiSTer` cd063fc3 + `GunCal.rbf` 522a413e) is OLD; do not republish without the user asking.

Build outputs on the PC (all verified): `build/GunCal.rbf` (95d13176...), `build/MiSTer_tracker` (clean, patches to **0023**, md5 `8f22d3fcfb527aa683d53a4f3923de59`),
`build/MiSTer_tracker_debug` (with the trace, md5 `3985491a98511e88d37d1481f5e30ece`). **0022 and 0023 are built but not on the MiSTer.**

**Patch 0023 (2026-10-23), the user's spec, verbatim:** "I want the guncon2 to pull the trigger and once it sees the GAME generated white flash for the
lightgun, THEN register where it's seen on the screen. It won't work otherwise. This has to be in main, not in the cores. Also, the calibration core has
to then map to each core's resolution. Often current res. This HAS to happen without modifying the core." What 0023 does: on a pull the trigger goes to the core at once,
the aim goes OFF the screen (nothing seen for this shot yet: no estimate from before the pull any more), the first valid reading after the pull is the
shot and is held (no median with later readings), no light in 400 ms = off the screen (reload). Host tests pass (two new ones). Untested on the MiSTer.
The mapping part was already in main (`guncal_apply_universal`, recomputed whenever the core's measured timing changes); nothing changed there.
Install with `tools/mister/deploy_app.sh` (app only; restarts the app into the same core and game it was running; command in its header).

## 4. Open problems, in the order to work on them

1. **Get access, then install the 0023 app** (it has 0022, the D-pad fix, too). With the key working, from the repo root in Git Bash:
   `cp build/MiSTer_tracker_debug build/MiSTer.app && cp build/MiSTer_tracker build/MiSTer.clean`, then
   `tar cf - -C build MiSTer.app MiSTer.clean -C ../tools/mister deploy_app.sh | ssh root@192.168.1.204 "cd /tmp && tar xf - && tr -d '\r' < deploy_app.sh > d.sh && sh d.sh 3985491a98511e88d37d1481f5e30ece 8f22d3fcfb527aa683d53a4f3923de59"`
   (check the `\r` survived). It restarts the app into the same game. Tell the user the screen will drop out first, in one line.
   Then the HotD trace (item 2) decides whether 0023 is enough: per pull, the time from the pull to the first valid lit report (the flash) and whether
   the game counted the shot. If shots became reloads, HotD reads the gun before the gun's report of the flash arrives.
2. **HotD MEASURED 2026-10-23 with 0023 (trace in `build/hotd_0023/`, 47 pulls, 15 kHz MRA):** in a dark scene the gun reports nothing at 0 and
   17 ms after the pull and ONE lit report with a good X/Y at 33-35 ms (the game's flash is a single field, the field right after the pull), then dark
   again. The app gave the core that aim at 34-36 ms (28 pulls); 10 pulls were in lit scenes (aim at the pull), 9 saw no light (reloads). The user:
   "it's not seeing the flash. It's reading too early": HotD reads the gun before the gun's report of its flash field reaches the app. The driver
   already asks for 1 ms polling (`usb_fill_int_urb(..., 1)`) and reports still come once per field, so the GunCon 2 reports a field after it ends;
   the app cannot make that earlier. Point Blank works because its flash lasts several frames (light 50-100 ms after the pull). Options put to the
   user: (a) main only: on a pull, give the core a trigger with the aim off the screen (the game flashes and reloads), take the aim from that flash,
   then give the real trigger with it (costs: a reload every shot = never out of ammo, two flashes, ~35 ms more; HotD may ignore a trigger right
   after a reload); (b) the core flashes on request (the beacon, as Virtua Cop), a core change by its author. **The user chose (a): patch 0024,
   the probe** (`crtgun_probe_*` in lightgun_crt.cpp, on for core name `Model2A`, `LIGHTGUN_CRT_PROBE=0` turns it off; 5 host tests). Installed
   2026-10-23 ~01:43 BST: `/media/fat/MiSTer` = trace build md5 `f7b7bf66df250a92c9530b0495767455`, `MiSTer.clean` = `b1b17f3e5a53112fd7785ce4c4446cbd`,
   `MiSTer.prev` = the 0023 app. The out trace has `pb_phase,pb_pressed` columns (ticks of a probe sequence logged every 2 ms).
   **The user, after playing: "Yeah works"** (2026-10-23 ~01:48 BST). Trace `build/hotd_0024/`: 41 pulls, 32 shots given (probe press 3..8 ms,
   aim from the probe's flash 47..52 ms, real press 79..84 ms after the pull), 9 with no light (the probe was the reload). The user asked for it to
   stay the default on the MiSTer (it is: `/media/fat/MiSTer`, started by inittab and by the launchers; MiSTer.ini has no LIGHTGUN keys) and for
   the repo to be pushed (done with this file).
   Older notes: **House of the Dead was a "random mess"** (user, after a good calibration): very low hit rate, flash "not seen properly", off-screen shots mostly do not
   reload. NOT explained. What is known and fixed: the core name `Model2A` was missing from the sync table (0021: a 4.7 us HSync was used instead of 6.2 us,
   about 3% of the width off). What to do: have the user play HotD a few minutes (shots on screen, at the flash, clearly off screen), then immediately fetch
   `/tmp/gundbg.csv` and `/tmp/gundbg_out.csv` (raw events and tracker decisions: `dev,t_ms,raw_x,raw_y,trig,shot,out_x,out_y,offscreen,pub_x,pub_y,pub_off,bc_phase,bc_req`)
   and `/tmp/guncal_apply.log` (the mapping used), with `tools/mister/collect_logs.sh` (read-only, one gzip'd tar on stdout:
   `ssh root@192.168.1.204 "tr -d '\r' | sh" < tools/mister/collect_logs.sh > build/mister_logs.tgz`). Analyse with `tools/mister/gunlog.py`, `flash_probe.py`,
   `flash_shape.py`, `light_edges.py`. Hypotheses to test against the trace, not to assume:
   - HotD's flash is the GAME's single white frame (the author's notes: the game reads the aim at the vblank ending it, 35-52 ms after the pull); a GunCon needs
     a few fields of light after darkness (the first lit report has a junk Y, which `crtgun_valid` rejects), so the flash may be over before the gun reports.
     Mode 1 then keeps the aim estimated at the pull, which is only good if the gun saw light before the pull.
   - Junk lit readings (a gun with no sync lock reports unrelated X/Y every frame; ~25% fall inside the picture) may be taken as an aim during the 400 ms
     window and turn an off-screen shot into an on-screen miss: there is no steadiness test in the flash window (GunCal's monitor page has one).
   - The Model 2 I/O treats the outer ~5% of the stick range as off-screen (patch 0014 insets aims for core name `Model2`; `Model2A` does not get the inset
     because only `board == "Model2"` is checked in `guncal_apply_universal` in input.cpp). Whether the author's HotD gun logic does the same is unknown.
   - The HotD picture is 496x480 interlaced; the mapping halves the rows for interlaced cores. See item 3 about the GunCal constants.
   - The user's HotD core is the author's local build; the author (alphanu1) is friendly and answered issue #13 (2026-10-22: a `Gun flash` OSD option,
     Arcade or Off, Virtua Cop only) and #14. Ask him what HotD's gun I/O does, if the trace points there.
3. **GunCal constants for the 480i picture.** `GUNCAL_CAL_VS_TO_PIC_LINES` (17) and `GUNCAL_CAL_HS_TO_PIC_PX` (94) in `Main_MiSTer/guncal.h` say where the GunCal picture
   sits after the sync pulses; they were measured for the old 240p core. The new 480i core has a half-line different VSync in field 1 and the fit's vertical offset moved
   by about -1.7 lines (17.38 vs 19.04): compute the real offsets from a few GOOD calibrations (`config/GUNCAL_log.txt` has every attempt; reject the ones
   where the user did not move the gun) and correct the constants, or the Y of every core is a line or two off.
4. **Check Point Blank again** (NB-1 core, was "basically perfect" on 16 Oct). It was broken tonight because a bad calibration (vertical offset 36, not 18) had been saved
   automatically; the save-on-EXIT change (0019) removes that. Re-test with the good calibration and the 0022 app.
5. **Prove the GunCal output is really interlaced.** The framework reports `interlaced` from `VGA_F1` (hps_io `video_calc`); `guncal_apply_universal` deliberately skips the core
   named GUNCAL, so `/tmp/guncal_apply.log` has no GunCal line. Log GunCal's `current_video_info` once (e.g. from `guncal_service`) and read it. The user judged the earlier
   (line-doubled 240p) build "not interlaced" and the latest one "looks good".
6. Smaller: the GunCal quality gate accepts residuals up to ~10 raw units (several poor fits were accepted tonight); consider refusing worse than ~6 so the user
   is sent round again. The PS1 GunCon calibration's exact sequence is unknown (ours: centre, four corners, check page); do not claim it matches.

## 5. Tools, access and traps

- ssh: `ssh root@192.168.1.204` (password only until the key is in). The system area is read-only. `scp` works too. Port 21 (ftp) is open.
- UART: `tools/mister/console.ps1` (the user logs in, then Ctrl+]), `tools/mister/serial_run.py run|push|pushz|pull` (115,200 baud, about 11 KB/s: a 1.3 MB app takes 100 s).
  `pushz` is gzip+base64 with md5 checks. **Never `cat` a big file over serial.**
- Git Bash rewrites arguments that start with `/` (`/media/fat/x` became `C:/Program Files/Git/media/fat/x`): run with `MSYS_NO_PATHCONV=1`.
- The Write tool and heredocs can collapse backslashes (`\r`, `\n`, `\b`): check generated scripts with `cat -A` / `repr`.
- `.ps1` files are blocked by the execution policy on this PC: use `.bat`, or `powershell -ExecutionPolicy Bypass -File`.
- The terminal panel tool allows only 6 tabs and cannot close a tab the user has typed in: use `Start-Process cmd.exe -ArgumentList '/c','title X && <bat>'` for something
  the user must type into (it opens a normal window), and tell them which window.
- The user's shell for a password prompt must have FOCUS and the password goes in the window, not into the chat (they typed `1` into the chat once).
- Build the app (WSL, runs the host tests, applies all patches to the pinned base):
  `MSYS_NO_PATHCONV=1 wsl -d Ubuntu -u root -- bash "/mnt/c/Users/joelw/Mister Guncon2/scripts/build-main-mister.sh"` -> `build/MiSTer_tracker`, `build/MiSTer_tracker_debug`.
- Build the GunCal core: `bash scripts/build-guncal.sh` from Git Bash (Quartus Lite 17.0 at C:/intelFPGA_lite/17.0, about 7 minutes, output `build/GunCal.rbf`; check
  `build/GunCal/output_files/GunCal.sta.summary` for slack >= 0). Draw every GunCal screen from the RTL in simulation (about 80 s):
  `MSYS_NO_PATHCONV=1 wsl -d Ubuntu -u root -- bash -c 'cd "/mnt/c/Users/joelw/Mister Guncon2" && python3 cores/GunCal/tools/render_frames.py build/sim'`
  (iverilog; `cores/GunCal/tools/tb_frame.v` is its testbench; the core's `ce_pix` has no reset, the testbench zeroes it).
- Text on the GunCal screen is generated: edit `cores/GunCal/tools/gen_text.py` (layout), run it; `font5x7.v` is generated by `gen_font.py`.
- Background tasks started with `&` inside a Bash call report "completed" at once; wait with `until grep -q '^exit' <log>; do sleep 10; done` run in the background.

## 6. Pushing and the release (the user asked for it "once decided")

Nothing is pushed. When the user is happy: commit the working tree (the new patches, `cores/GunCal`, docs, tools, this file), update README/CALIBRATION-CORE for 0021/0022, push to
`origin main`. Do NOT replace the public release files without being asked (the old `MiSTer` there has neither the GunCal changes nor the D-pad fix, and the release README says
which build it is). `build/` is git-ignored.

## 7. Background kept from earlier (still true)

- Point Blank (NB-1 stock): "basically perfect" on 16 Oct. Virtua Cop (Sega Model 2, our beacon build `retrorepair/sega-model2-mister` branch `guncon-scan15`): "seems to work
  great" with the earlier by-name build of the app; the released app finds the flash by an OSD line the core announces (`-,GunCon flash on request;`), no shipped core has it yet.
  Issues #13/#14 are on `alphanu1/sega-model2-mister`; the fork is an example only, not released. The author is willing to make a 15 kHz-only core.
- Games flash only in real gameplay (coin + start), never decide a game's flash from attract mode or a core's source; default every core to `LIGHTGUN_CRT_MODE=1`.
- Analog-gun games (Terminator 2, Alien3, Jurassic Park) never flash and are not supported. Time Crisis (System 22 core) is parked. CD cores run `MiSTer_Physical-CD`,
  which the patches do not touch.
- The kernel driver keeps only the low byte of the gun's Y (the app compensates; `patches/kernel/` is an optional one-line fix).
- Fits near 99% area are chaotic; seeds change timing, not the LAB count (Model 2 core builds: `scripts/scan15_sweep.ps1`, not needed for GunCal).
- Memory files for this project are in `C:/Users/joelw/.claude/projects/C--Users-joelw-Mister-Guncon2/memory/` (read `MEMORY.md`).

## 2026-10-23 night (02:30 BST): PS1 and "all cores" (the user asleep; read this first)

- **Why PS1 "couldn't see the flash":** MiSTer.ini has `main=MiSTer_Physical-CD` for [PSX], [Saturn], [MegaCD], [TurboGrafx16], so those cores ran the
  physical-disc app (Anime0t4ku/Main_MiSTer_Physical_Disc) with NONE of our patches. Fixed: all our commits carried onto that fork at tag v2.10.0
  (plus only the frame_clocks read of upstream d8c88df, not its YC change) = `patches-physical-cd/0001..0027` (git am onto v2.10.0; WSL tree
  /root/build/physdisc, branch guncon-physdisc). The card's own copy is kept as `/media/fat/MiSTer_Physical-CD.orig` (md5 87973185...) to roll back.
- **Patch 0025:** the probe for EVERY core (not GunCal, not the menu); only light of a field that began after the probe press counts; give-up 160 ms;
  PSX gets the System 11 sync sizes. **0026:** a still gun on a lit spot (no reports: the kernel drops unchanged values) is taken 2 fields + 8 ms after
  the probe press; the trace logs the step that ends a sequence. `LIGHTGUN_CRT_PROBE=0` (globally or in a core's ini section) turns the probe off.
- **On the card now:** `MiSTer` = trace build 00d07278..., `MiSTer.clean` cac81424...; `MiSTer_Physical-CD` = trace build ad6f51c2...,
  `.clean` abdf7cbc...; PSX loaded. Calibration untouched (44b5b3a5...).
- **Verified on the MiSTer with a virtual gun** (`tools/mister/fakegun_probe.py`, `fakegun_noprobe.py`): PSX under the patched Physical-CD app and HotD
  under the main app: probe press 3..8 ms, 40 ms long, aim from the flash after it, real press 35 ms later with the aim in place, released 40 ms later;
  off-screen = probe only; menu and GunCal untouched. PSX is mapped (`guncal_apply.log`: 704x478i, hs 4690 ns).
- **NOT verified with the real gun:** PS1 games, Point Blank (now gets the probe: an extra off-screen shot each pull; `[NB1] LIGHTGUN_CRT_PROBE=0` to
  compare), NES (Duck Hunt counts the probe press as a missed shot), Saturn. A PS1 GunCon game must have the PSX OSD pad set to GunCon.
- **Left to do:** `scripts/build-physical-cd.sh` (fetch fork v2.10.0, `git am patches-physical-cd/*`, tests, build); README/CORES.md for 0025/0026
  and the Physical-CD app.
