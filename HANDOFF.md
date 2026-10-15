# Handoff

## Done (2026-10-15 evening and night)
- Located the real code (Main_MiSTer + kernel driver); read the calibration, CRT-gun and scaling paths.
- Confirmed the gun's data reaches the MiSTer. Raw USB reports captured in the dark. Established the report layout,
  that "no light" is X = 0/1 with a meaningless Y, and that evdev drops unchanged values.
- Found that MiSTer grabs every input device, so measuring needs a logging build.
- Built an ARM toolchain in WSL and a reproducible build script. Stock Main_MiSTer builds clean.
- Wrote the tracker (`lightgun_crt.cpp`) and calibration safety fixes; 10 host unit tests; 10/10 integration checks on the
  MiSTer through a virtual gun; degenerate calibration file rejected without a crash.
- Details and evidence: `docs/DESIGN.md`.

## State left on the MiSTer (192.168.1.204, UART on COM3)
- Running the **debug** build (`build/MiSTer_tracker_debug`, md5 03eb85da...) from RAM via a bind mount over
  `/media/fat/MiSTer`. The SD card file is untouched; a reboot restores stock. Tracker is on (no `MiSTer.ini` change).
- `/tmp/dbg/MiSTer4` is that binary; `/tmp/fakegun.py`, `/tmp/usbraw.py` are the test scripts.
- Logs in `/tmp`: `gundbg.csv`, `gundbg_out.csv` (cleared on restart, capped at 8 MB). Synthetic test data is in them now.
- The `misterzine launcher watch` process (pid 1038) was paused for a while and is running again. It did not respawn
  MiSTer on its own in later tests; the app is started by hand with `(nohup /media/fat/MiSTer ... &)`.
- The console is logged in as root (done by the user; no credentials are stored anywhere).

## Not done / open
- Nothing tested with the real gun on a lit CRT. All thresholds are guesses until then.
- Report lag after a game flash: unmeasured. It decides whether core-side changes are worth doing.
- Calibration menu UI changes compile but were not exercised. Framebuffer-target calibration is only an idea (DESIGN.md section 5).
- No SSH key on the MiSTer; the one-liner is in the chat history (user runs it, enters the password).
- Nothing was pushed upstream. The tracker is a local fork; upstream Main_MiSTer is untouched.

## Next (tomorrow, with the user)
Follow DESIGN.md section 7. In short: wiring check, raw look at a lit screen (`usbraw.py`), flash game with the debug
build, pull and analyse the logs, A/B with `LIGHTGUN_CRT_TRACKER=0`, then tune the five thresholds from real data.
