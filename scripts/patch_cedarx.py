import sys, re, io

# Lower CedarX decode buffering on the AA->CarPlay path to cut latency.
# Only numeric values are changed; comments/layout preserved.
# new values chosen for low-latency live projection (reversible via backup).
NEW = {
    "start_play_cache_video_frame_num": "2",
    "start_play_cache_size": "16",
    "cache_buffer_size": "4096",
    "cache_buffer_size_live": "2048",
    "start_play_cache_time": "1",
    "max_start_play_chache_size": "16384",
    "max_cache_buffer_size": "16384",
}

path = sys.argv[1]
src = io.open(path, encoding="utf-8", errors="replace").read()
out = src
for key, val in NEW.items():
    # match: key <spaces> = <spaces> number   (keep trailing comment)
    pat = re.compile(r"(^[ \t]*" + re.escape(key) + r"[ \t]*=[ \t]*)(\d+)",
                     re.MULTILINE)
    new_out, n = pat.subn(lambda m: m.group(1) + val, out, count=1)
    print(f"  {key}: {'set to '+val if n else 'NOT FOUND'}")
    out = new_out

if out == src:
    print("NO CHANGES"); sys.exit(2)
io.open(path, "w", encoding="utf-8").write(out)
print("WROTE", path)
