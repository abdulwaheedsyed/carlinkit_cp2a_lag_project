# Carlinkit CP2A Lag Project

Reverse-engineering and firmware tuning notes for the **Carlinkit CPC200-CP2A**
wireless **Android Auto → CarPlay** adapter, aimed at reducing video/audio lag
and stutter on a CarPlay-only head unit — plus unlocking the hidden web-UI
options, debloating, and a tiny Rust supervisor daemon.

> ## ⚠️ WARNING — this can permanently brick your device
>
> This is **personal research shared as-is, for educational purposes only.**
> Flashing the SPI NOR over FEL can **destroy the dongle with no guaranteed
> recovery.** It **voids your warranty** and is **not** endorsed by Carlinkit,
> Allwinner, Apple, or Google. **Make and verify your own full flash backup
> first**, understand every command before you run it, and accept that **you do
> this entirely at your own risk.** The author takes **no responsibility** for
> bricked hardware or any other damage.
>
> **See [DISCLAIMER.md](DISCLAIMER.md) for the full warning. Read it.**
>
> **No firmware, binaries, disassembly, or keys are distributed here** — only
> original scripts and docs. CarPlay is MFi-gated; the stock firmware is
> proprietary. Don't redistribute it, and **never publish your own backup** (it
> holds your device's private MFi/CarPlay keys and BT pairing).

---

## The problem

On this unit, the AA→CarPlay picture (and audio) stutters/lags on the head unit
while the **phone itself stays perfectly smooth**. The lag is immediate, survives
a factory reset, and persists with the case off (so it is **not** a simple
thermal problem). The goal was to see how far the lag could be reduced purely
through firmware configuration and tuning, without touching the closed CarPlay /
Android Auto app or the hardware codec.

## Hardware (this board)

| Part | Detail |
|------|--------|
| SoC | Allwinner **V553** = `sun8iw21`, **V851/V853** family (Cortex-A7 + RISC-V, HW H.264 enc/dec) |
| FEL id | `0x00188600` (V851/V853) |
| Flash | **XTX XT25F128F**, 16 MB SPI NOR |
| RAM | 128 MB DDR3 |
| Wi-Fi/BT | **AICSemi aic8800** module |
| OS | Allwinner Tina Linux (OpenWrt-based), musl, ARM 32-bit userspace |

> Offsets and values below are for **this** board revision. Other revisions can
> differ — do not blindly reuse them.

## Access: FEL / xfel

Entering FEL (Allwinner USB recovery, VID:PID `1f3a:efe8`):

1. Open the case, **hold the internal button** (near the SoC).
2. While holding it, plug the dongle into a **PC** over USB.
3. Verify with [`xfel`](https://github.com/xboot/xfel): `xfel version` should
   report `AWUSBFEX ... V851/V853`.

Normal boot (not FEL) enumerates as a fake iPhone (`05ac:12a8`).

**Always back up first and verify the readback:**

```bash
xfel spinor read 0 0x1000000 stock-flash-backup.bin   # full 16 MB
# keep TWO copies; sha256sum both; this is your ONLY way back
```

Revert everything later with:

```bash
xfel spinor write 0 stock-flash-backup.bin
```

## Flash / partition map (parsed from U-Boot env @ 0x5c000)

| Region | Offset | Notes |
|--------|--------|-------|
| boot0 / SPL | `0x4` | **Do not corrupt — brick zone** |
| kernel | `0x80000` | Android image |
| recovery | `0x2e0000` | |
| **rootfs** | `0x540000` | squashfs (xz, 256K). Main OS, `/etc`, web UI |
| **customer** | `0x9c0000` | squashfs. CarPlay/AA app, Wi-Fi modules, firmware |
| private | `0xf60000` | plain `key=value` settings (e.g. `conn`, `display`) |
| UDISK | tail | jffs2 (writable; factory reset wipes) |

`/etc` lives in the **read-only rootfs squashfs** (not an overlay), so config
edits require repacking and reflashing that partition.

## What's in this repo

```
scripts/
  patch_webui.py    # unlock ALL hidden web-UI option rows
  patch_i18n.py     # translate the newly-exposed Chinese labels to English
  patch_cedarx.py   # tune CedarX decoder buffering (latency vs jitter)
rom_watchdog/       # tiny dependency-free Rust daemon (static ARM)
CHANGELOG.md        # per-change log of the lean-ROM build
```

These are applied against your **own** extracted squashfs trees
(`unsquashfs` → edit → `mksquashfs -comp xz -b 256K -noappend -all-root`),
then flashed to the matching offset and **read back + compared** before reboot.

### rom_watchdog (Rust)

A ~385 KB static ARM daemon (`std` only, no crates), launched from `rc.final`.
Every 5 s it:

- re-pins every CPU to the `performance` governor and `scaling_min = scaling_max`,
- **holds thermal throttling off** (disables thermal zones, maxes trip points) —
  *opt-in; accepts extra heat,*
- logs CarPlay/AA app liveness to `/tmp/rom_watchdog.status`.

It deliberately **does not** kill/restart the app (the firmware already has a HW
watchdog; fighting it causes reboot loops).

Cross-compile:

```bash
rustup target add armv7-unknown-linux-musleabihf
cd rom_watchdog && cargo build --release --target armv7-unknown-linux-musleabihf
# needs linker = rust-lld + crt-static + link-self-contained (see .cargo/config.toml)
```

## What helped, and what didn't (honest findings)

**Helped general responsiveness** (menus/UI):
- `performance` CPU governor + min=max frequency.

**Config levers tried for the video/audio path:**
- **CedarX decode buffering** (`cedarx.conf`): stock uses a huge ~5 s / 30-frame
  / 20 MB buffer (smooth but laggy). A tiny buffer cuts latency but **underruns
  on this Wi-Fi chip → stutter**. A *moderate* buffer (~2 s / 8 frames) is the
  compromise.
- **Wi-Fi is already 5 GHz** (channel 36 / freq 5180) for both the AP and P2P
  paths — so the common "it's on 2.4 GHz" cause does **not** apply here.
- **AP-only vs mixed AP+P2P:** the box ran a hostapd AP **and** a Wi-Fi-Direct
  P2P group **simultaneously on the single aic8800 radio** (`LY_AP_P2P_MIXED=1`).
  Android Auto uses the **AP** (confirmed in the app binary); the P2P group is
  for Huawei HiCar. Disabling the mixed P2P group frees radio airtime for the
  AA link.

**Confirmed no-op (do NOT bother):**
- **Forcing a lower resolution / 480p.** The box already sizes the AA request to
  the head unit's real dimensions (800×480) and the frame rate is hard-coded to
  30 fps in the app. The big `std::set<int>` some guides point at is the **input
  keycode table**, not a resolution list. Patching it changes nothing.

**Known trap:**
- **Connection Mode = ADB** on this unit does **not** expose ADB to a PC — it
  just **disables Wi-Fi/BT/CarPlay**. Recover by restoring the `private`
  settings block at `0xf60000`, or factory reset.

**Reality check:** the **aic8800 is a budget Wi-Fi part**, and an AA→CarPlay
converter does a **double transcode** (decode incoming AA H.264 → re-encode
CarPlay H.264) on a cheap SoC. If audio *and* video both stutter after the above,
the bottleneck is most likely the **wireless link / chip** or the USB-CarPlay
output side — not something a resolution or buffer tweak will fully cure. These
"2-in-1" converters are widely reported to stutter for exactly this reason.

## Recovery

| Problem | Fix |
|---------|-----|
| Anything wrong after a flash | `xfel spinor write 0 stock-flash-backup.bin` |
| Wi-Fi gone after `conn=adb` | restore your backup's `0xf60000` block, or factory reset |
| Won't enter FEL | hold the internal button **before** plugging into the PC |

## Credits

By **Syed Abdul Waheed** ([@abdulwaheedsyed](https://github.com/abdulwaheedsyed)).

Built on the open-source [`xfel`](https://github.com/xboot/xfel) tool and the
`squashfs-tools`. Not affiliated with Carlinkit, Allwinner, Apple, or Google.

## License

Original work in this repo is MIT-licensed — see [LICENSE](LICENSE). It covers
**only** these scripts/daemon/docs, **not** any proprietary firmware or MFi
material (none is included).
