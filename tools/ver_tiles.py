#!/usr/bin/env python3
import sys, importlib.util
spec = importlib.util.spec_from_file_location("conv",
    "/data/data/com.termux/files/home/fabrica-ports/tools/converter_png.py")
conv = importlib.util.module_from_spec(spec)
# Impede que o __main__ rode
import sys as _sys
_argv = _sys.argv
_sys.argv = ['conv']
try:
    spec.loader.exec_module(conv)
finally:
    _sys.argv = _argv

w, h, pixels = conv.ler_png(_sys.argv[1])
print(f"Ground: {w}x{h} = {w//16}x{h//16} tiles de 16x16\n")

for ty in range(h // 16):
    for tx in range(w // 16):
        print(f"=== Tile ({tx},{ty}) ===")
        for py in range(16):
            linha = ""
            for px in range(16):
                idx = (ty*16 + py) * w + (tx*16 + px)
                cor = pixels[idx]
                a = (cor >> 24) & 0xFF
                r = (cor >> 16) & 0xFF
                g = (cor >> 8) & 0xFF
                b = cor & 0xFF
                if a == 0: linha += "."
                elif r > 128 and g < 100: linha += "#"
                elif g > 128 and r < 100: linha += "~"
                elif b > 128: linha += "@"
                elif r > 200 and g > 200: linha += "*"
                else: linha += "o"
            print(f"  {linha}")
        print()
