# -*- coding: utf-8 -*-
import sys, io

# Translate the hardcoded Chinese labels/values on the newly-exposed rows
# to English. Exact, unique substring replacements only (no comments touched).
REPLACERS = [
    ("<p>功能切换</p>", "<p>Function Switch</p>"),
    ("<p>录音方式</p>", "<p>Recording Mode</p>"),
    ("<p>鼠标模式</p>", "<p>Mouse Mode</p>"),
    ("<p>车标选择</p>", "<p>Car Logo</p>"),
    ("<p>连接方式</p>", "<p>Connection Mode</p>"),
    ("<p>自适应模式</p>", "<p>Adaptive Mode</p>"),
    ("<p>HiCar布局</p>", "<p>HiCar Layout</p>"),
    ("id=\"mic\">默认<", "id=\"mic\">Default<"),
    ("id=\"mouse\">默认<", "id=\"mouse\">Default<"),
    ("id=\"conn\">默认<", "id=\"conn\">Default<"),
    ("id=\"hicar\">默认<", "id=\"hicar\">Default<"),
    ("label: \"默认\", value: \"aoa\"", "label: \"Default\", value: \"aoa\""),
    ("ledlb = ['开启', '关闭']", "ledlb = ['On', 'Off']"),
]

path = sys.argv[1]
src = io.open(path, encoding="utf-8").read()
out = src
for cn, en in REPLACERS:
    n = out.count(cn)
    out = out.replace(cn, en)
    print(f"  {'OK ' if n else 'MISS'} ({n}x) -> {en}")

if out == src:
    print("NO CHANGES"); sys.exit(2)
io.open(path, "w", encoding="utf-8").write(out)
print("WROTE", path)
