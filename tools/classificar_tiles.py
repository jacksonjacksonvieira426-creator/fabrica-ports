#!/usr/bin/env python3
import sys, importlib.util

arg = sys.argv[1]  # guarda ANTES de mexer em sys.argv

spec = importlib.util.spec_from_file_location("conv",
    "/data/data/com.termux/files/home/fabrica-ports/tools/converter_png.py")
conv = importlib.util.module_from_spec(spec)
sys.argv = ['conv']  # impede __main__ de rodar
spec.loader.exec_module(conv)

w, h, pixels = conv.ler_png(arg)
cols, rows = w // 16, h // 16
print(f"{cols}x{rows} = {cols*rows} tiles\n")

for ty in range(rows):
    for tx in range(cols):
        sr = sg = sb = n = 0
        for py in range(16):
            for px in range(16):
                idx = (ty*16+py)*w + tx*16+px
                c = pixels[idx]
                if (c >> 24) == 0: continue
                sr += (c >> 16) & 0xFF
                sg += (c >> 8) & 0xFF
                sb += c & 0xFF
                n += 1
        if n == 0:
            print(f"  [{ty},{tx}] = vazio")
            continue
        r, g, b = sr//n, sg//n, sb//n
        if g > r and g > b and g > 80: tipo = "grama"
        elif r > 150 and g > 130 and b < 100: tipo = "areia/terra"
        elif r < 100 and g < 100 and b < 100: tipo = "pedra/escuro"
        elif b > r and b > g: tipo = "agua"
        elif r > 150 and g < 100: tipo = "vermelho"
        else: tipo = "outro"
        print(f"  [{ty},{tx}] RGB({r:3d},{g:3d},{b:3d})  {tipo}")
