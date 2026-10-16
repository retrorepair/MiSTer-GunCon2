# Handoff

## Where things stand (2026-10-16)

Working end to end on the user's CRT: GunCal calibration, the universal mapping onto a running core, and the game-flash aim.
Point Blank (Namco NB-1 core) is "basically perfect so far". See `README.md` for what it is and `docs/DESIGN.md` for the evidence.

## What is on the MiSTer (192.168.1.204, UART on COM3)

RAM only (a reboot returns the MiSTer to its stock state):
- `/tmp/dbg/MiSTer10` is the patched app (build/MiSTer_tracker_debug, md5 31421c4d...), bind-mounted over `/media/fat/MiSTer`.
  `/tmp/dbg/GunCal.rbf` is the calibration core. Test scripts and analysers are in `/tmp`.
- Logs in `/tmp`: `gundbg.csv`, `gundbg_out.csv` (8 MB cap each), `guncal_apply.log` (the edges derived for each core). **Restarting the app
  deletes them in my procedure below: copy them off first.**

On the SD card (written during this work; the stock `MiSTer` binary is untouched):
- `config/GUNCAL_uni_0b9a_016a_v1.cfg`: the user's universal calibration (five-point, made 2026-10-16). `GUNCAL_log.txt`: its shots.
  `GUNCAL_uni_0b9a_016a_v1.cfg.3pt.bak`: the earlier three-point one.
- `config/inputs/ptblanka_input_0b9a_016a_v3.map` and `NB1_input_0b9a_016a_v3.map`: the gun's buttons for Point Blank
  (trigger = Button 1, gun A = Start, gun B = Coin, Select = Service). Written with `tools/mister/make_gun_map.py`.
- Nothing else changed. Point Blank is loaded from `_Arcade/_alternatives/_Point Blank/` (set 2); ROMs are `games/mame/ptblank.zip`.

To bring the setup up again after a reboot (console logged in by the user, never by this tooling):

```
python tools/mister/serial_run.py pushz build/MiSTer_tracker_debug /tmp/dbg/MiSTer10
python tools/mister/serial_run.py pushz build/GunCal.rbf /tmp/dbg/GunCal.rbf
# then on the MiSTer:  killall MiSTer; mount --bind /tmp/dbg/MiSTer10 /media/fat/MiSTer; cd /media/fat; (nohup /media/fat/MiSTer >/tmp/mister_dbg.log 2>&1 </dev/null &)
#   echo "load_core /media/fat/_Arcade/_alternatives/_Point Blank/Point Blank (World, GN2 Rev B, set 2).mra" > /dev/MiSTer_cmd
#   (the GunCal core:  echo "load_core /tmp/dbg/GunCal.rbf" > /dev/MiSTer_cmd)
```

`build/` is not tracked; rebuild with `scripts/build-main-mister.sh` (WSL) and `scripts/build-guncal.sh` (Quartus).
The `misterzine launcher watch` process on the SD card did not respawn the app on its own in any later test.

## Open

- Persistent install, other cores (NES, PSX, System 11), a grid check page for edge accuracy, fixed slopes from the gun's physical
  constants, the kernel's 8-bit Y: all listed in `docs/DESIGN.md` section 5.
- Nothing was sent upstream; the patches are a local fork of Main_MiSTer 13f1de9 (GPL).

## Lessons for whoever continues

- The user wants no ambiguity and no timer-based asks: give self-paced tools and say exactly what to press.
- Never type credentials into a login prompt; have the user log in on the console (`tools/mister/console.ps1`), then use `serial_run.py`.
- Verify claims with a trace before designing (the flash behaviour, the "no light" signature and the no-sync signature all came from traces).
