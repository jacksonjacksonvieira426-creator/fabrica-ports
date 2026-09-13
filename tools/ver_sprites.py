#!/usr/bin/env python3
import sys, importlib.util
arg = sys.argv[1]
spec = importlib.util.spec_from_file_location("conv",
    "/data/data/com.termux/files/home/fabrica-ports/tools/converter_png.py")
conv = importlib.util.module_from_spec(spec)
sys.argv = ['conv']
spec.loader.exec_module(conv)

w, h, pixels = conv.ler_png(arg)
print(f"{arg}: {w}x{h}\n")

# Mostra cada sprite de 16x16 como mini-ASCII
cols = w // 16
rows = h // 16
for ty in range(min(rows, 8)):
    linha_silhuetas = ""
    for tx in range(cols):
        # Conta pixels nao transparentes
        n = 0
        for py in range(16):
            for px in range(16):
                idx = (ty*16+py)*w + tx*16+px
                if (pixels[idx] >> 24) != 0:
                    n += 1
        # Representa como um caractere de densidade
        if n == 0: simbolo = "."
        elif n < 20: simbolo = "."
        elif n < 60: simbolo = ":"
        elif n < 120: simbolo = "*"
        elif n < 200: simbolo = "#"
        else: simbolo = "@"
        linha_silhuetas += simbolo
    print(f"  linha {ty}: {linha_silhuetas}")
