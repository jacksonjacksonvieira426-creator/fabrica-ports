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

def cor_char(c):
    a = (c >> 24) & 0xFF
    if a == 0: return '.'
    r = (c >> 16) & 0xFF
    g = (c >> 8) & 0xFF
    b = c & 0xFF
    # Tom de pele
    if r > 180 and g > 130 and b > 90 and r > g > b: return 'S'
    # Verde (uniforme)
    if g > r and g > b and g > 100: return 'V'
    # Marrom (capacete)
    if r > 100 and g > 80 and b < 80 and r > b: return 'C'
    # Azul
    if b > r and b > g: return 'A'
    # Branco
    if r > 200 and g > 200 and b > 200: return 'W'
    # Preto/escuro
    if r < 80 and g < 80 and b < 80: return '#'
    # Amarelo
    if r > 180 and g > 180 and b < 100: return 'Y'
    # Vermelho
    if r > 180 and g < 100 and b < 100: return 'R'
    return '?'

# Mostra os primeiros 8 sprites (linha 0 toda)
for tx in range(cols):
    print(f"=== Coluna {tx}, Linha 0 (sprite {tx}) ===")
    for py in range(16):
        linha = ""
        for px in range(16):
            idx = (0*16+py)*w + tx*16+px
            linha += cor_char(pixels[idx])
        print(f"  {linha}")
    print()
