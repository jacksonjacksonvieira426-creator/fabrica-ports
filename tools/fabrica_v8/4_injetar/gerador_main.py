#!/usr/bin/env python3
"""
Gerador de main() - Le estrutura do jogo e gera main() pronto.
Uso: python gerador_main.py <estrutura.json>
"""
import sys, json, os, re

def analisar(estrutura):
    """Detecta classes importantes e gera main()."""
    midlet = estrutura.get("midlet")
    canvas = estrutura.get("canvas")
    
    # Detecta classe que tem 'run' (game loop)
    game_loop = None
    for c in estrutura["classes"]:
        for m in c["metodos"]:
            if m["nome"] == "run" and m["n_instr"] > 50:
                game_loop = c["nome"]
    
    # Detecta personagens (classes com reset, forward, punch)
    personagens = []
    for c in estrutura["classes"]:
        metodos = [m["nome"] for m in c["metodos"]]
        if "reset" in metodos and "forward" in metodos and "punch" in metodos:
            personagens.append(c["nome"])
    # Ordena: nomes com "Ryu" (jogador) primeiro, outros depois
    personagens.sort(key=lambda x: (0 if "Ryu" in x else 1, x))
    
    # Detecta classe de canvas principal
    canvas_principal = None
    for c in estrutura["classes"]:
        if c["nome"] == canvas: continue
        metodos = [m["nome"] for m in c["metodos"]]
        if "paint" in metodos and "keyProc" in metodos:
            canvas_principal = c["nome"]
    
    return {
        "midlet": midlet,
        "canvas": canvas,
        "game_loop": game_loop,
        "personagens": personagens,
        "canvas_principal": canvas_principal,
    }

def gerar_main(info, nome_proj):
    """Gera o codigo C do main()."""
    linhas = []
    linhas.append("// ============================================")
    linhas.append("// MAIN AUTO-GERADO pela Fabrica V8")
    linhas.append("// ============================================")
    linhas.append("")
    linhas.append("int main(void) {")
    linhas.append("    j2me_gfx_init();")
    linhas.append("    j2me_input_init();")
    linhas.append("    j2me_random_init();")
    linhas.append("")
    
    # Cria objetos das classes principais
    canvas = info.get("canvas_principal")
    if canvas:
        linhas.append(f"    // Cria Canvas principal")
        linhas.append(f"    {canvas}* mc = ({canvas}*)calloc(1, sizeof({canvas}));")
        linhas.append(f"    _self = mc;")
        linhas.append(f"    msf_mc = ({canvas}*)mc;")
        linhas.append("")
    
    # Cria personagens
    personagens = info.get("personagens", [])
    for i, p in enumerate(personagens):
        var = f"p{i+1}"
        linhas.append(f"    // Cria {p} (jogador {i+1})")
        linhas.append(f"    {p}* {var} = ({p}*)calloc(1, sizeof({p}));")
        linhas.append(f"    _p{i+1}_self = {var};")
        if i == 0:
            linhas.append(f"    _role_self = {var};")
        linhas.append("")
    
    # Liga personagens ao canvas
    if canvas and len(personagens) >= 2:
        linhas.append(f"    // Liga personagens ao canvas")
        linhas.append(f"    mc->ofusc_00ff = p1;   // Jogador 1")
        linhas.append(f"    mc->ofusc_0100 = p2;   // Jogador 2")
        linhas.append(f"    mc->ofusc_0101 = 100;  // HP P1")
        linhas.append(f"    mc->ofusc_0102 = 100;  // HP P2")
        linhas.append(f"    mc->ofusc_00e6 = j2me_image_create(480, 272);")
        linhas.append("")
    
    # Chama constructors
    for i, p in enumerate(personagens):
        linhas.append(f"    {p}_constructor();")
    linhas.append("")
    
    # Game loop
    linhas.append("    // Game loop")
    linhas.append("    while (1) {")
    linhas.append("        j2me_input_update();")
    linhas.append("        if (j2me_input_should_quit()) break;")
    linhas.append("")
    linhas.append("        j2me_gfx_begin_frame();")
    linhas.append("        j2me_gfx_clear(0x101020);")
    linhas.append("")
    if canvas:
        linhas.append(f"        {canvas}_keyProc();")
        linhas.append(f"        {canvas}_paint(NULL);")
    linhas.append("")
    linhas.append("        j2me_gfx_flip();")
    linhas.append("    }")
    linhas.append("")
    linhas.append("    j2me_gfx_shutdown();")
    linhas.append("    sceKernelExitGame();")
    linhas.append("    return 0;")
    linhas.append("}")
    
    return "\n".join(linhas)

def main():
    if len(sys.argv) < 2:
        print("Uso: python gerador_main.py <estrutura.json>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    
    info = analisar(estrutura)
    print("// Analise:")
    print(f"//   MIDlet:      {info.get('midlet')}")
    print(f"//   Canvas:      {info.get('canvas')}")
    print(f"//   Game loop:   {info.get('game_loop')}")
    print(f"//   Personagens: {info.get('personagens')}")
    print(f"//   Canvas princ: {info.get('canvas_principal')}")
    print()
    print(gerar_main(info, estrutura["nome_projeto"]))

if __name__ == "__main__":
    main()
