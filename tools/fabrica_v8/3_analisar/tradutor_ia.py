#!/usr/bin/env python3
import sys, os, json

def gerar_prompt(caminho):
    with open(caminho) as f:
        bytecode = f.read()
    
    classe = "?"
    metodo = "?"
    desc = "?"
    for l in bytecode.split("\n")[:5]:
        if "Classe:" in l: classe = l.split(":")[-1].strip()
        if "Metodo:" in l: metodo = l.split(":")[-1].strip()
        if "Descritor:" in l: desc = l.split(":")[-1].strip()
    
    prompt = f"""Traduza este bytecode JVM para C limpo.

CONTEXTO:
- Classe: {classe}
- Metodo: {metodo}
- Descritor: {desc}
- Port J2ME -> PSP

API DISPONIVEL:
- j2me_gfx_set_color(cor)
- j2me_gfx_fill_rect(x, y, w, h)
- j2me_font_draw(texto, x, y)
- j2me_image_blit(img, x, y)
- j2me_image_draw_region(img, sx, sy, sw, sh, tr, dx, dy, anchor)
- j2me_input_get_actions()
- j2me_random_next(max)
- j2me_sleep(ms)

REGRAS:
1. Assinatura: void {classe}_{metodo}_fn(void* self, <args>)
2. Primeira linha: {classe}_s* s = ({classe}_s*)self;
3. Acesso a campo: s->campo
4. Graphics.X -> j2me_gfx_X
5. if_icmp + goto -> if/while
6. Comentar blocos

BYTECODE:
{bytecode}

Gere apenas o codigo C."""
    return prompt

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python tradutor_ia.py <metodo.txt>")
        sys.exit(1)
    print(gerar_prompt(sys.argv[1]))
