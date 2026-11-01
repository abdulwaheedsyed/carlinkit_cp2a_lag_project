//! rom_watchdog — tiny, dependency-free supervisor for the Carlinkit lean ROM.
//! - Re-pins every CPU to the `performance` governor (defends against resets).
//! - Holds CPU thermal throttling OFF: disables thermal zones, maxes trip
//!   points, and pins scaling_min_freq == scaling_max_freq so frequency never
//!   dips when warm (user accepts the overheating risk).
//! - Tracks whether the CarPlay/AndroidAuto app is alive, writes a status file.
//! Intentionally does NOT kill/restart the app: the firmware already has a
//! hardware watchdog, and fighting it would cause reboot loops.

use std::fs;
use std::thread::sleep;
use std::time::Duration;

const TICK: Duration = Duration::from_secs(5);
const APP_NAMES: [&str; 3] = ["lylinkapp", "rcpservice-all", "rcpservice"];

fn pin_governor() {
    let Ok(cpus) = fs::read_dir("/sys/devices/system/cpu") else { return };
    for cpu in cpus.flatten() {
        let base = cpu.path().join("cpufreq");
        let gov = base.join("scaling_governor");
        if gov.exists() {
            let _ = fs::write(&gov, b"performance");
        }
        // Pin min freq to the max available so the CPU never clocks down.
        if let Ok(maxf) = fs::read_to_string(base.join("cpuinfo_max_freq")) {
            let maxf = maxf.trim();
            if !maxf.is_empty() {
                let _ = fs::write(base.join("scaling_max_freq"), maxf.as_bytes());
                let _ = fs::write(base.join("scaling_min_freq"), maxf.as_bytes());
            }
        }
    }
}

/// Hold thermal throttling off: put every thermal zone in "disabled" mode and
/// push its trip points far above any temperature the SoC will reach, so the
/// cpufreq cooling device never forces a lower frequency.
fn disable_thermal() {
    let Ok(zones) = fs::read_dir("/sys/class/thermal") else { return };
    for z in zones.flatten() {
        let p = z.path();
        let name = p.file_name().and_then(|s| s.to_str()).unwrap_or("");
        if name.starts_with("thermal_zone") {
            // Best-effort: some kernels reject this, that's fine.
            let _ = fs::write(p.join("mode"), b"disabled");
            // Raise all trip points we can see to 150C.
            if let Ok(entries) = fs::read_dir(&p) {
                for e in entries.flatten() {
                    let ep = e.path();
                    let en = ep.file_name().and_then(|s| s.to_str()).unwrap_or("");
                    if en.starts_with("trip_point_") && en.ends_with("_temp") {
                        let _ = fs::write(&ep, b"150000");
                    }
                }
            }
        }
    }
}

fn app_alive() -> bool {
    let Ok(procs) = fs::read_dir("/proc") else { return false };
    for p in procs.flatten() {
        if let Ok(comm) = fs::read_to_string(p.path().join("comm")) {
            let name = comm.trim();
            if APP_NAMES.iter().any(|n| *n == name) {
                return true;
            }
        }
    }
    false
}

fn main() {
    let mut dead_secs: u64 = 0;
    loop {
        pin_governor();
        disable_thermal();
        let alive = app_alive();
        if alive {
            dead_secs = 0;
        } else {
            dead_secs = dead_secs.saturating_add(TICK.as_secs());
        }
        let _ = fs::write(
            "/tmp/rom_watchdog.status",
            format!(
                "governor=performance thermal=disabled app_alive={alive} app_dead_secs={dead_secs}\n"
            ),
        );
        sleep(TICK);
    }
}
