#!/usr/bin/env python3
import sys, importlib.util
arg = sys.argv[1]
spec = importlib.util.spec_from_file_location("conv",
    "/data/data/com.termux/files/home/fabrica-ports/tools/converter_png.py")
conv = importlib.util.module_from_spec(spec)
sys.argv = ['conv']
spec.loader.exec_module(conv)

w, h, pixels = conv.ler_png(arg)

def cor_char(c):
    a = (c >> 24) & 0xFF
    if a == 0: return '.'
    r = (c >> 16) & 0xFF
    g = (c >> 8) & 0xFF
    b = c & 0xFF
    if r > 180 and g > 130 and b > 90 and r > g > b: return 'S'
    if g > r and g > b and g > 100: return 'V'
    if r > 100 and g > 80 and b < 80 and r > b: return 'C'
    if b > r and b > g: return 'A'
    if r > 200 and g > 200 and b > 200: return 'W'
    if r < 80 and g < 80 and b < 80: return '#'
    return '?'

# Mostra todas as 8 linhas, coluna 0
print(f"=== COLUNA 0, TODAS AS 8 LINHAS ===\n")
for ty in range(8):
    print(f"--- Linha {ty} ---")
    for py in range(16):
        linha = ""
        for px in range(16):
            idx = (ty*16+py)*w + 0*16+px
            linha += cor_char(pixels[idx])
        print(f"  {linha}")
    print()
