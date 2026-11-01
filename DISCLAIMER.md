# ⚠️ Disclaimer & Warning — READ BEFORE YOU DO ANYTHING

This repository documents **personal reverse-engineering and firmware tinkering**
on a Carlinkit CPC200-CP2A wireless Android Auto → CarPlay adapter. It is shared
**for educational and research purposes only.**

## This can permanently destroy your device

- Writing to the SPI NOR flash over FEL **can brick the dongle**. There is no
  guaranteed recovery if you corrupt the bootloader (boot0/SPL).
- **Make your own full 16 MB flash backup first and verify it**, or accept that
  you may end up with a dead device. Recovery here depends entirely on having a
  known-good backup of *your own* unit.
- This **voids any warranty** and is **not** sanctioned by Carlinkit, Allwinner,
  Apple, or Google.

## No firmware is distributed here

- This repo contains **only original work**: patch scripts, a small Rust daemon,
  and notes.
- It contains **no** Carlinkit/Allwinner firmware, **no** extracted binaries,
  **no** disassembly, and **no** keys. CarPlay is MFi-gated and the stock
  firmware is proprietary — do not redistribute it, and do not ask for it.
- **Never publish your own flash backup.** It contains proprietary firmware plus
  **your device's private MFi/CarPlay keys and Bluetooth pairing data.**

## Device specific

- These offsets, partition layout, Wi-Fi chip (aic8800), and tuning values match
  **one specific board revision** (Allwinner V553 / V851-V853 family, 16 MB XT25
  NOR). Yours may differ. Blindly reusing another unit's values/images is how
  devices get bricked.

## No warranty

Everything here is provided **"AS IS", without warranty of any kind.** You assume
**all** risk. The author is **not liable** for any damage, data loss, bricked
hardware, voided warranties, or anything else resulting from use of this material.

## Legality

Reverse engineering for interoperability/repair of a device **you own** is lawful
in many jurisdictions, but this varies. **You are responsible** for complying
with the laws that apply to you and with any applicable third-party terms.

**If you are not comfortable recovering a bricked device yourself, stop now.**
