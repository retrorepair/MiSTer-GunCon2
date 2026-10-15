# GunCon 2 on MiSTer: evidence, design, status

Written 2026-10-15 (overnight session, no hardware testing with a lit CRT yet). Facts and guesses are
kept apart: **Measured** means seen on this MiSTer tonight, **From code** means read in a pinned
upstream source, **Hypothesis** means not yet confirmed.

## 1. What was measured

Setup: MiSTer, Linux 6.18.38, MiSTer binary of 2026-09-28, GunCon 2 `0b9a:016a` on hub port 1-1.2.

| Finding | Source |
|---|---|
| The gun is a **low-speed USB** device, interrupt endpoint 0x81, `bInterval` 8 ms, max packet 8. | Measured (sysfs) |
| A report is 6 bytes: buttons (u16, active low), X (u16 LE), Y (u16 LE). The kernel driver keeps only the low byte of Y. | Measured (raw usbfs read) + From code (`hid-guncon2.c` reads `data[4]` only; psakhis' Windows daemon reads Y as 16 bit) |
| Gun at rest in the dark: constant `ff ff 00 00 05 00`, one report about every **87 ms** (231 in 20 s, gaps 63 to 89 ms). | Measured (`captures/dark_usbraw.log`) |
| "No light" is **X = 0** (X = 1 also appears) and a **meaningless Y (5)**. It is not (0, 0) as PCSX2's emulation suggests, so validity must be judged on X. This agrees with the existing Main_MiSTer comment that X is the reliable axis. | Measured |
| Handled in a lit room the gun produced reports 3 to 60 ms apart: X flipping 0/1 about 18 times a second, Y settling at 5. So reports are event-driven when the photodiode fires, with a slow heartbeat otherwise. | Measured (evdev trace, 153 s, about 11 300 lines; the file was overwritten when the build was replaced, so the numbers are kept here) |
| The kernel only emits an input event when a value **changed**. A gun held perfectly still emits nothing. | From code (input core) + Measured |
| MiSTer **grabs every input device exclusively** (`grabbed = 1`), so no side process can read the gun while MiSTer runs. The kernel has no usbmon, kprobes or BPF. Measuring means building a logging MiSTer (`GUNDBG=1`). | From code + Measured |
| MiSTer reads an event about **0.1 ms** after the kernel stamps it (median; 8 ms worst case). | Measured (virtual-gun run) |
| The kernel driver sets mode byte 5 = 1 (word 0x0100). PCSX2 calls bit 0x0100 `PROGRESSIVE`; psakhis' daemon comments the same value "60 Hz interlaced". Which is right is unresolved and matters only for 480p. | From code, **unresolved** |
| Real PS2 games calibrate with the game's own flash: Time Crisis shows a black frame, waits for the gun to report "no light", then derives an offset from the first valid report. | From code (PCSX2 comment) |

Not measured yet (needs a lit CRT and a flashing game): the report rate when the gun sees a screen, the
valid X/Y range, and the **lag between a game flash and the report that carries it**.

## 2. How stock Main_MiSTer treats the gun, and what is wrong

- The gun is a continuous analog pointer (ABS_X/ABS_Y scaled by a four-number calibration to -127..127).
  Cores fake the light sensor: NES checks the colour of the pixel under the pointer, SNES emits its latch
  pulse at the pointer's beam position every frame, PSX treats an extreme stick value as "offscreen".
- When the gun loses light, a flat 50 ms hold of the last coordinate was added (commit 8f80dba). It cannot
  tell a dark frame from the gun leaving the screen, and 50 ms is arbitrary. Because the kernel sends no
  event while values are unchanged, what the core actually keeps is whatever was last sent.
- Calibration: four numbers per core per gun, one live sample each, needs a full-white screen. The menu
  asks for the trigger but only accepts A/B. `min == max` on an axis divides by zero and crashes MiSTer
  until the file in `/config` is deleted.

## 3. What was built (patch series in `patches/`, on Main_MiSTer 13f1de9)

`0001` GUNDBG trace: `make GUNDBG=1` logs every raw GunCon event to `/tmp/gundbg.csv` and every tracker
decision to `/tmp/gundbg_out.csv` (8 MB cap each; line buffered). Not in normal builds.

`0002` Tracker and calibration safety.

**Tracker** (`lightgun_crt.cpp`, unit-tested on the host, 10 tests). Valid means raw X is at least
`LIGHTGUN_CRT_X_VALID_MIN` (16). Valid reports pass straight through. When the light is lost:

1. A trigger pull made **while the gun was tracking** opens a window (`LIGHTGUN_CRT_SHOT_MS`, 200).
   Inside it, no-light reports are ignored (the game's flash blanks the screen) and a valid report is
   taken as the position (the flash is when real hardware measures it).
2. Otherwise, if the last valid position was **in the interior** (further than `LIGHTGUN_CRT_EDGE_PCT`,
   12 %, of the span from every edge) it is a dark frame and the position is held for up to
   `LIGHTGUN_CRT_DARK_MS` (500) from the moment the light went.
3. Otherwise (lost at an edge, or held too long, or never seen light) the gun is **offscreen** now.

A pull made with no light stays offscreen, so a reload shot is not turned into an on-screen shot. The dark-gap
timer starts at the transition to "no light", not at the last valid event, because a still gun is silent
(found by the integration test; there is a regression unit test).

`LIGHTGUN_CRT_TRACKER=0` in `MiSTer.ini` restores the old 50 ms behaviour for A/B comparison.

**Calibration safety:** the GunCon 2 trigger (BTN_X) confirms an edge; junk samples (no light) no longer reach
the menu; opposite edges closer than 16 raw units are refused and the run restarts; a saved calibration of
zero width falls back to the device defaults; the scaler no longer divides by zero on `min == max`.

**Tested:** host unit tests; on the MiSTer an integration run (`tools/mister/fakegun.py`) creates a virtual
GunCon 2 and plays scripted situations through MiSTer's real input path (dark frame, expiry, edge exit,
shot with flash, reload shot): 10/10 pass. A degenerate calibration file was loaded and rejected, with no
crash. **Not tested:** anything with the real gun and a lit CRT, the calibration menu UI, any core.

## 4. Why the cores are not changed yet

The idea "cores use the gun's real light-seen signal" runs into timing. The gun reports light it **already
saw**, so a report reaches the core at least one frame after the flash that caused it. NES, SNES, SMS and
MegaDrive games read the light during the flash frame, so the report cannot be that signal. What a core can
use is a validity flag (exact offscreen, no phantom hits) and a latched position. That is what the tracker
now provides on the HPS side for every core without touching FPGA code. A core-side flag would travel in
`joystick_r_analog_N` or an unused button bit (no `hps_io.sv` change), and the clean first targets are SNES
`lightgun.sv` and the PSX `Gun*AimOffscreen` logic. Decide after the lag is measured.

## 5. Calibration plan (not started)

- **Idea:** draw the calibration targets with MiSTer's own framebuffer over any running core, so the 240p Test
  Suite and a keyboard are not needed. The machinery exists (`video_fb_enable`, Imlib2 drawing, the `MiSTer_fb`
  module). Open: whether the framebuffer can be shown with transparency over a core, and how to relate its
  coordinates to the core's picture rectangle (scaler aspect/crop settings).
- **Idea:** the gun's X is a time since hsync and Y a line count, so the mapping to a core's pixels is fixed by
  the video timing MiSTer outputs. One calibration per gun and display might then serve every core.
  **Hypothesis**, needs lit-CRT data to check the units.

## 6. Known limitations and risks

- The tracker is driven by events. A gun that is perfectly still in a dark interior stays "held" forever,
  because nothing arrives to expire it. A periodic tick would fix it; wait for real data first.
- All thresholds (valid X 16, edge 12 %, dark 500 ms, shot 200 ms) are educated guesses to tune with the real
  gun. They are `MiSTer.ini` keys on purpose.
- Y is truncated to 8 bits by the kernel driver, so 480p cannot work without a kernel change. Not attempted:
  custom kernels have broken other devices (per the GunCon2-MiSTer README).
- Y has no validity information of its own.
- Shooting a game that is dark before the flash (a black menu) cannot be fixed on the HPS side: no light, no position.

## 7. Tomorrow's session (about 30 minutes)

State left on the MiSTer: the debug build runs from RAM through a bind mount over `/media/fat/MiSTer`
(SD card untouched; a reboot returns to stock). `MiSTer.ini` is unchanged, so the tracker is on.

1. Check the wiring: CRT on, the gun's yellow RCA on composite sync, gun straight into the MiSTer USB hub
   (the extender gave trouble).
2. Raw look at a lit screen: `tools/mister/usbraw.py` while sweeping the gun edge to edge over a white screen.
   Gives the lit X/Y range, report cadence, and confirms the valid threshold.
3. Flash game with the debug build (NES Duck Hunt or PSX Point Blank): shoot bright areas, dark areas, off the
   screen; then `serial_run.py pull /tmp/gundbg.csv` and `/tmp/gundbg_out.csv` and run `tools/analyze_gundbg.py`.
   The "first no-light after / light again after" columns are the flash lag.
4. A/B: set `LIGHTGUN_CRT_TRACKER=0` for the old behaviour and compare in the same game.
5. Calibration menu (F10 in the OSD): confirm the trigger works and that a bad calibration is refused.
