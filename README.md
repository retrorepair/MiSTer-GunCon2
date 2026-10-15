# MiSTer GunCon 2 — saner integration

Goal: make the Namco GunCon 2 on MiSTer more usable. Better calibration, and
use the game's own trigger flashes instead of continuous tracking plus a hold
timer.

Status: research only. No code has been written or tested yet.

## Where the real code is

`NolanNicholson/GunCon2-MiSTer` is README-only now; the work was merged upstream.

| What | Where |
|---|---|
| Kernel driver | `MiSTer-devel/Linux-Kernel_MiSTer`, `drivers/hid/hid-guncon2.c` (branch `MiSTer-v6.18`) |
| Gun handling | `MiSTer-devel/Main_MiSTer` `input.cpp` (`QUIRK_LIGHTGUN_CRT`, 50 ms grace hold, per-core cal files) |
| Calibration UI | `Main_MiSTer` `menu.cpp` (`MENU_LGCAL`, `MENU_LGCAL1`, `menu_lightgun_cb`) |
| HPS to core transport | `Template_MiSTer` `sys/hps_io.sv` (`joystick_N`, `joystick_l_analog_N`, `joystick_r_analog_N`) |

Reference copies are not tracked here. Run `scripts/fetch-refs.sh` to recreate them,
pinned to the commits the notes below were written against.

## How it works today

- The gun is a continuous analog pointer: kernel `ABS_X/ABS_Y` become the core's
  joystick analog X/Y (8 bit each, -127..127).
- Cores mostly fake the light sensor themselves.
  - NES `zapper.sv`: checks the colour of the pixel it rendered at the pointer.
  - SNES `lightgun.sv`: emits a latch pulse at the pointer's beam position every frame, no colour check.
  - PSX: offscreen is "analog X or Y is at an extreme (0x00/0xFF)".
- The gun only updates while it sees light, so dark scenes give junk. The fix
  (Main_MiSTer commit 8f80dba) holds the last good X/Y for 50 ms.
- Calibration: four numbers (Y min/max, X min/max) per core per gun, each a single
  live sample, confirmed with A (the prompt says Trigger). It needs a full-white screen.
  If min equals max, `input.cpp` divides by zero and MiSTer crashes until the file in
  `/config` is deleted.

## Findings about the GunCon 2 itself

From PCSX2's emulation of the device (`pcsx2/USB/usb-lightgun/guncon2.cpp`):

- The report is 6 bytes: buttons (u16), x (s16), y (s16). The MiSTer driver reads
  y as one byte (`data[4]`) and drops the high byte. Fine for ~25..245 lines,
  wrong for 480p.
- (0, 0) is reserved to mean "no light seen". So a light-seen flag already exists in
  the stream; the driver passes it through as `ABS_X=0, ABS_Y=0`.
- Real PS2 games use flashes themselves: Time Crisis shows a black frame, waits for the
  gun to report (0, 0), then computes an offset from the first non-zero report.
- The host sends the gun parameters (x offset, y offset, mode) with a control request;
  the MiSTer driver sends zero offsets and sets byte 5 to 1 (mode word 0x0100; what that
  mode selects is not verified).

## Open design constraint (not yet measured)

The gun reports light it saw earlier, so the report reaches the core at least one frame
after the flash. Pulse-style cores (NES, SNES, SMS, MD) need the pulse during the flash
frame. A real "light seen" signal therefore cannot replace their in-frame pulse; it can
validate and latch the pointer, and give an exact offscreen. How many frames the report
lags needs to be measured on real hardware.

## Plan

1. Measure: log raw reports on the MiSTer against a flashing game (rate, lag, (0, 0) behaviour).
2. Main_MiSTer fork: a validity state machine on (0, 0), a trigger-latched flash policy in
   place of the flat 50 ms hold, a calibration redo (no crash on min == max, trigger-confirmed,
   averaged samples, geometry from the core's video timing).
3. Core-side, selectively: pass a valid flag and latched position through spare transport
   (`joystick_r_analog_N` / unused button bits), then change one core with a clean seam first
   (SNES or PSX).

Toolchains seen on the dev machine: Quartus Lite 17.0 (with Cyclone V support); WSL Ubuntu (stopped);
no ARM cross-compiler on PATH.
