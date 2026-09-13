#!/usr/bin/env python3
import sys, importlib.util
arg = sys.argv[1]
spec = importlib.util.spec_from_file_location("conv",
    "/data/data/com.termux/files/home/fabrica-ports/tools/converter_png.py")
conv = importlib.util.module_from_spec(spec)
sys.argv = ['conv']
spec.loader.exec_module(conv)

w, h, pixels = conv.ler_png(arg)
cols = w // 16
rows = h // 16

for ty in range(rows):
    for tx in range(cols):
        # Conta cor dominante
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
            print(f"  [{ty},{tx}] vazio")
            continue
        r, g, b = sr//n, sg//n, sb//n
        # Classifica
        if r > 200 and g < 100 and b < 100: cor = "vermelho"
        elif r > 200 and g > 150 and b < 100: cor = "laranja/amarelo"
        elif r < 100 and g > 150 and b < 100: cor = "verde"
        elif r < 100 and g < 100 and b > 150: cor = "azul"
        elif r > 180 and g > 180 and b > 180: cor = "branco"
        elif r < 100 and g < 100 and b < 100: cor = "preto/escuro"
        else: cor = f"misto({r},{g},{b})"
        print(f"  [{ty},{tx}] {n:3d}px  {cor}")
