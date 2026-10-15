# Handoff

## Done (2026-10-15)
- Located the real GunCon 2 code (Main_MiSTer, kernel `hid-guncon2.c`) and read the calibration and CRT-gun paths.
- Read how NES, SNES, MegaDrive and PSX cores consume the gun.
- Established the report format and the (0, 0) = no-light convention from PCSX2's device emulation.

## Open / blockers
- User asked what core-side (FPGA) changes involve; the answer is in README.md "Open design constraint".
- Report lag behind the flash is unmeasured; it decides how much the cores can use the real signal.
- No code written. Nothing tested on hardware.

## Next
1. Agree scope with the user (HPS-side first, which cores after).
2. Write an SSH + python3 logger for raw gun reports (MiSTer has python3, no gcc).
3. Set up the ARM toolchain (Main_MiSTer `setup_default_toolchain.sh`, via WSL).
