import sys, re, io

# Patch Carlinkit web UI index.html to expose ALL option rows regardless of
# firmware version. The UI hides rows via hd()/hdXXX() helpers that return
# early only when appver is in an allow-list. We make every such helper a
# no-op, and unhide the explicitly-hidden Head Unit Type (div_mod) row.

path = sys.argv[1]
src = io.open(path, encoding="utf-8", errors="replace").read()
orig = src

# 1) Neutralize each hide-helper by inserting an immediate return at its top.
helpers = ["hd", "hdaud", "hdwif", "hdmic", "hdvid", "hdconn",
           "hdgps", "hdled", "hdled2"]
for h in helpers:
    # match:  function NAME(args) {
    pat = re.compile(r"(function\s+" + re.escape(h) + r"\s*\([^)]*\)\s*\{)")
    def repl(m):
        return m.group(1) + " return; /*exposed*/"
    src, n = pat.subn(repl, src, count=1)
    print(f"  {h}: {'patched' if n else 'NOT FOUND'}")

# 2) Unhide the Head Unit Type row that is explicitly hidden.
before = src
src = src.replace(
    "document.getElementById('div_mod').style.display = \"none\";",
    "document.getElementById('div_mod').style.display = \"\"; /*exposed*/")
print("  div_mod unhide:", "patched" if src != before else "not found")

if src == orig:
    print("NO CHANGES MADE to", path)
    sys.exit(2)

io.open(path, "w", encoding="utf-8").write(src)
print("WROTE", path)
