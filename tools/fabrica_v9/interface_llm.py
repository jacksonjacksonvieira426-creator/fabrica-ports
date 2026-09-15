#!/usr/bin/env python3
import sys
with open(sys.argv[1]) as f:
    bytecode = f.read()
classe = metodo = "?"
for l in bytecode.split("\n")[:6]:
    if "Classe:" in l: classe = l.split(":")[-1].strip()
    if "Metodo:" in l: metodo = l.split(":")[-1].strip()
print("// Metodo: " + classe + "." + metodo)
print()
print("// ============ PROMPT PRONTO ============")
print("Traduza este bytecode JVM para C limpo (port J2ME->PSP).")
print()
print("Classe: " + classe)
print("Metodo: " + metodo)
print()
print("API: j2me_gfx_set_color, j2me_gfx_fill_rect, j2me_font_draw,")
print("     j2me_image_blit, j2me_input_get_actions, j2me_random_next")
print()
print("BYTECODE:")
print(bytecode)
print()
print("// ======================================")
