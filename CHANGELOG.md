# Carlinkit CP2A (Allwinner V851/V853) — Custom Lean ROM

Built from your stock firmware (full verified backup kept). Keeps the parts that
must stay proprietary (CarPlay/AndroidAuto app, HW codec, kernel, bootloader);
cleans and tunes everything else.

## What changed

**Reliability**
- Disabled OTA auto-update (removed `startup3`/`libappupdate` from startup.json)
  → no surprise updates, no update-time bricking, no update phone-home.

**Privacy / telemetry**
- `/etc/hosts` sinks `data.carlinkit.com` → 127.0.0.1 (blocks usage/feedback upload).
- Left intact on purpose: NTP time sync (CarPlay certs need correct time) and the
  activation/blacklist host (avoids breaking a working, activated device).

**Performance (lag)**
- CedarX decode buffering trimmed: startup cache 5s→1s, live buffer 20MB→2MB,
  startup frames 30→2 (cuts accumulated latency on the AA→CarPlay path).
- CPU pinned to `performance` governor at boot (best-effort; avoids clock-ramp lag).
  NOTE: slightly more heat — revert if it ever runs hot.

**Debloat**
- Removed unused UI asset sets for other head-unit resolutions
  (1024x480, 1280x480, 480x1024, 480x600) — your HU is 800x480. ~1.9 MB.

**Usability (already flashed earlier)**
- Web UI exposes ALL options (Video/Audio Stream Mode, Connection, Mic, Mouse,
  Icon, GPS, Display, HiCar Layout) and in English.

## NOT changed (and why)
- CarPlay/AndroidAuto app, HW video codec, Wi-Fi/BT drivers, kernel, bootloader:
  closed-source/MFi-gated — cannot be rebuilt in any language. Left stock.
- `conn=ADB` mode: do NOT use it; it disables Wi-Fi on this unit.

## Anti-jitter round (after drive test showed stutter + choppy audio)

Choppy **audio** was the key clue: audio is tiny bandwidth / trivial to decode,
so the bottleneck is the shared wireless link (or periodic CPU stalls), not
transcode throughput or resolution.

- **Wi-Fi AP-only**: `LY_AP_P2P_MIXED=1 → 0`. The box was running a hostapd AP
  **and** a Wi-Fi-Direct P2P group at once on the single aic8800 radio. Android
  Auto uses the AP (confirmed in `lylinkapp`); the P2P group is only for HiCar
  (unused here) and was stealing airtime. AP-only gives the AA link the whole radio.
- **Thermal throttle disabled** (opt-in; accepts heat): `rc.final` + the Rust
  daemon pin `scaling_min = scaling_max = cpuinfo_max`, set `thermal_zone*/mode
  = disabled`, and raise all `trip_point_*_temp` to 150000, re-asserted every 5 s.
- **CedarX buffer re-tuned** from ultra-tight (1 s / 2 frames) to **moderate**
  (2 s / 8 frames, 8 MB live, 64 MB max). The tiny buffer couldn't absorb aic8800
  jitter and could itself cause stutter; moderate trades a little latency for
  smoothness.
- Rust `rom_watchdog` extended to also hold thermal throttling off each tick.

## Confirmed no-op (documented so nobody wastes time)
- **Forcing 480p / lower resolution.** The box already requests the head unit's
  real size (800×480) and 30 fps is hard-coded. No benefit.

## Flash (over FEL; full backup = instant revert)
- rootfs  -> xfel spinor write 0x540000 rom_rootfs.sqfs
- customer-> xfel spinor write 0x9c0000 rom_customer.sqfs
- Revert all -> xfel spinor write 0 stock-flash-backup.bin
