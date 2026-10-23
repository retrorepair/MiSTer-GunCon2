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

Measured later, with the gun locked to a CRT (2026-10-16):

| Finding | Source |
|---|---|
| A gun whose yellow RCA plug carries no usable sync reports X = 0/1 for 94% of the time and unrelated numbers the rest (X 16..1988, Y 0..255, jumping by hundreds between frames, runs of 1 to 9 reports). Locked, it reports within a few units frame to frame. | Measured (Duck Hunt trace, then the GunCal monitor page) |
| Locked and swept edge to edge on the user's CRT: raw X about 182..716, Y about 30..237. Reports arrive every 16 to 17 ms (once per frame) when it sees a lit picture. | Measured |
| Calibration fits: raw_x = 1.188*px + 114 (px = 100 ns of the GunCal picture, so about 11.9 raw units per microsecond) and raw_y = 0.97..0.99*py + 19 (py = one line). Every shot within about 4 raw units of the line, which is hand-aiming noise. Y slope over three runs: 0.962, 0.977, 0.986; the true value may be exactly 1.0 (not established). | Measured (GUNCAL_log.txt) |
| MiSTer's measurement of a core's picture timing matches the core's RTL: Namco NB-1 reported active 47 620 ns (RTL 47 606), back porch 6 944 ns (6 942), 288 x 224, 30 lines of vertical back porch (one early reading showed 25 while the core was still settling, so the mapping recomputes when the timing changes). | Measured + From code |
| In Point Blank the gun had no light in 82% of its reports, and in 55% of 120 trigger pulls it had no light at the instant of the pull. In 63 of the 107 pulls where light returned, it came 50 to 100 ms after the pull: the game's flash. | Measured (captures/pb_pulls.txt) |
| The core name MiSTer reports can be the core's own name (NB1) early in a load and the MRA set name (ptblanka) later; per-core settings must recognise both. | Measured |

Still not measured: whether the gun's Y is exactly one count per line (decides whether the slope can be fixed and only an offset solved),
and how accurate the pointer is at the extreme top and bottom in a controlled test (a grid check page was designed but not built).

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

`0001` GUNDBG trace: `make GUNDBG=1` logs every raw GunCon event to `/tmp/gundbg.csv` and every tracker decision (rules and the held aim)
to `/tmp/gundbg_out.csv` (8 MB cap each; line buffered). Not in normal builds.

`0002` Tracker and calibration safety. **Tracker** (`lightgun_crt.cpp`, host unit tests): valid means raw X is at least
`LIGHTGUN_CRT_X_VALID_MIN`. When the light is lost: a trigger pull made while tracking opens a window that ignores dark reports;
otherwise a loss inside the picture is a dark frame and the position is held up to `LIGHTGUN_CRT_DARK_MS` (timed from when the light
went, because the kernel sends no event while values are unchanged); a loss at an edge, or too long, is offscreen. **Calibration
safety:** the GunCon 2 trigger confirms an F10 edge, junk samples no longer reach that menu, edges closer than 16 raw units are refused,
a zero-width saved calibration falls back to the defaults, and the scaler no longer divides by zero on min == max.

`0003` GunCal support (`guncal.cpp`, host unit tests, active only while the GunCal core runs): the five-target sequence (centre, four
corners), the first valid reports during the core's flash as the measurement (median), a least-squares line per axis, a check page,
A or B to end, hold the trigger 3 s to redo, D-pad moves the targets in or out, the fit saved once per gun, every calibration appended
to `config/GUNCAL_log.txt`. **Universal mapping** (`guncal_core_edges`, `guncal_apply_universal` in `input.cpp`): for any other core with
no per-core calibration file, the gun's raw value at the core's picture edges comes from the universal fit and the core's measured
timing (width, active time, end of HSync to first pixel, lines from VSync to first line), plus the sync pulse widths, which the
framework does not measure: a small table (NB-1: HSync 32 px at 6.048 MHz, NES: 25 dots), 4.7 us and 3 lines otherwise.

`0004` Mode 1, aim from the game's flash (default). On a pull the pointer is set to the tracker's estimate at that instant, then to the
median of the first three complete valid reports after it (the flash), and it then holds until the next pull. A pull with no light and
no flash stays offscreen. The core is given the held aim by `crtgun_deliver()` instead of the raw axes.

`0023` (2026-10-23, the user's rule: a shot is registered only where the gun has seen the GAME's flash, in the app, never in a core) replaces
the start of `0004`: on a pull the trigger still goes to the core at once (the game flashes because of it), but the aim goes off the screen,
as a light gun's latch does at the start of a shot, instead of the tracker's estimate from before the pull. The first valid reading after the
pull is the shot and later readings no longer move it; no light within `LIGHTGUN_CRT_SHOT_MS` (400) leaves it off the screen, a reload.
Tried in House of the Dead the same night: the flash is one field, the gun reports it 33..35 ms after the pull, and the game has read the gun by then.

`0024` the probe (the user's choice, for games like that; core name `Model2A`, `LIGHTGUN_CRT_PROBE=0` turns it off): on a pull the physical trigger
is held back and the aim goes off the screen; a probe press makes the game flash (and count a reload); the first valid reading after it is where the
gun saw that flash; the probe press goes up, the aim is set, and after 35 ms of trigger-up the real press is given with the aim in place. No light
within 100 ms is the reload, and nothing more is sent. Costs: a reload every shot, two flashes, about 80 ms from the pull to the real press.

**The GunCal core** (`cores/GunCal`, see `docs/CALIBRATION-CORE.md`): colour UI like the PS1 GunCon calibration screen (bright background,
boxed prompts, blue ring target), the white flash, a check page with a live crosshair, and a monitor page with the raw readouts.

**Tested.** Host unit tests: tracker (16 tests) and calibration (12 tests). On the MiSTer: virtual-gun
integration runs of the tracker rules (10/10), of the whole five-shot calibration (the saved fit equals the one fed in), and of the flash
mode (7/7); a degenerate calibration file is rejected without a crash. With the real gun: the GunCal calibration, the monitor page's live
lock readout, and Point Blank on the NB-1 core ("basically perfect so far" after the HSync-width table was made to recognise both of that
core's names).

## 4. Why the core's own logic is not changed

The idea "cores use the gun's real light-seen signal" runs into timing: the gun reports light it already saw, so a report reaches the
core at least one frame after the flash. Pulse-style cores need the light during the flash frame. Delivering the held, flash-derived aim
from the HPS gives every core the benefit with no FPGA change, and it worked for NB-1 without touching that core. A flag in
`joystick_r_analog_N` or an unused button bit remains available if a core ever needs "no light" as its own signal.

## 5. Open work

- **Persistent install.** Everything runs from RAM through a bind mount over `/media/fat/MiSTer`; a reboot returns to stock. A permanent
  install (our binary and `GunCal.rbf` on the SD card, plus a Scripts-menu entry to enable it) is not done.
- **Other cores.** NES (Duck Hunt), PSX and the System 11 core have the same path in principle (their per-core sync widths need checking;
  NES is in the table, others use 4.7 us / 3 lines). Not tested.
- **Edge accuracy.** The user reported the very top and bottom as weaker on an earlier build; the latest build is "basically perfect so
  far". A grid check page (small rings over the whole screen, live crosshair) was designed to answer this objectively; not built.
- **Gun constants.** If raw Y is exactly one count per line and raw X exactly 11.9 per microsecond, the slopes could be fixed and only the
  offsets solved, removing aiming noise from the slopes. Needs more shots (`GUNCAL_log.txt` accumulates them).
- **Kernel truncation.** The driver keeps only the low byte of Y, so a core whose picture extends beyond raw Y 255 cannot reach its last
  lines (NB-1's last line is at about 255; its visible part is below that). 480p is out of reach for the same reason.
- **Two guns.** The calibration state and the tracker are per device, but the GunCal sequence assumes one gun.

## 6. Known limitations and risks

- The tracker's continuous rules are event driven: a gun perfectly still in a dark interior stays "held" forever (nothing arrives to expire it).
  Mode 1 does not depend on it.
- Mode 1 gives a stationary pointer between shots, so the core's own crosshair jumps at each shot. Games that track the gun continuously with
  their own flashes (every frame) would need `LIGHTGUN_CRT_MODE=0`.
- Thresholds (valid X 16, edge 12%, dark 500 ms, flash window 400 ms) are educated guesses that worked on the one CRT tested.
- The sync pulse widths of a core must be known to map it; an unknown core uses 4.7 us / 3 lines, which can shift the aim sideways by a few pixels.

## 7. Testing

With the GUNDBG app build running (`HANDOFF.md`):

1. Raw look at a lit screen: `tools/mister/usbraw.py`, then `tools/analyze_usbraw.py`.
2. Trace a play session: `serial_run.py pull /tmp/gundbg.csv`, then `tools/analyze_gundbg.py`, `tools/show_pulls.py`.
3. Calibration quality: `tools/analyze_cal.py` on a trace plus the saved file, and `config/GUNCAL_log.txt` (per-point residuals).
4. Software wiring with no gun: `fakegun.py` (rules), `fakegun_cal.py` (whole calibration), `fakegun_flash.py` (flash mode), with the real
   gun unbound (`echo 1-1.2:1.0 > /sys/bus/usb/drivers/guncon2/unbind`) and rebound afterwards.
