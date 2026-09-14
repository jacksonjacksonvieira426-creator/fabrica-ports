#!/usr/bin/env python3
"""
Extrai sprites do msf.gif usando os crops definidos no bytecode do MapCanvas.
Gera headers C prontos pra usar no PSP.
"""
import sys, os, importlib.util

spec = importlib.util.spec_from_file_location("conv",
    "/data/data/com.termux/files/home/fabrica-ports/tools/converter_png.py")
conv = importlib.util.module_from_spec(spec)
sys.argv = ['conv']
spec.loader.exec_module(conv)

# Crops do bytecode (x, y, w, h) + nome
SPRITES = [
    ("r_intro1",  0,  0, 18, 40),
    ("r_intro2", 18,  0, 22, 39),
    ("r_intro3", 40,  0, 29, 39),
    ("r_intro4", 70,  0, 30, 33),
    ("r_item1",  70, 34, 22, 12),
    ("r_parado",  0, 41, 15, 34),
    ("r_soco",   16, 41, 19, 34),
    ("r_chute",  37, 41, 33, 34),
    ("r_and1",    0, 77, 21, 19),
    ("r_and2",   22, 77, 38, 19),
    ("r_extra",  76, 50, 13, 13),
]

def extrair():
    gif_path = '/data/data/com.termux/files/home/msf_extraido/imagem/msf_frame_0.png'
    w, h, pixels = conv.ler_png(gif_path)
    print(f"GIF: {w}x{h}")

    saida_dir = '/data/data/com.termux/files/home/fabrica-ports/src/'
    for nome, sx, sy, sw, sh in SPRITES:
        # Copia pixels
        sub = []
        for y in range(sh):
            for x in range(sw):
                idx = (sy + y) * w + (sx + x)
                sub.append(pixels[idx] if idx < len(pixels) else 0)

        # Gera header
        path = os.path.join(saida_dir, f"msf_{nome}.h")
        with open(path, 'w') as f:
            f.write(f"// {nome}: {sw}x{sh} de ({sx},{sy})\n")
            f.write(f"#ifndef _MSF_{nome.upper()}_H\n#define _MSF_{nome.upper()}_H\n\n")
            f.write(f"#define MSF_{nome.upper()}_W {sw}\n")
            f.write(f"#define MSF_{nome.upper()}_H {sh}\n\n")
            f.write(f"static const unsigned int msf_{nome}_pixels[{len(sub)}] = {{\n")
            for i in range(0, len(sub), 8):
                linha = sub[i:i+8]
                f.write("    " + ", ".join(f"0x{p:08X}u" for p in linha) + ",\n")
            f.write("};\n\n#endif\n")
        print(f"  {nome}: {sw}x{sh} -> msf_{nome}.h")

if __name__ == "__main__":
    extrair()
