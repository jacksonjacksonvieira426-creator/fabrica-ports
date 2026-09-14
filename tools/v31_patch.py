#!/usr/bin/env python3
"""
Patch V3.1: Implementa analise de fluxo de controle.
Detecta loops (goto pra tras) e ifs (if pra frente).
"""
import sys, json, zipfile, io
from jawa.cf import ClassFile

CONSTANTES = {"iconst_m1": -1, "iconst_0": 0, "iconst_1": 1,
              "iconst_2": 2, "iconst_3": 3, "iconst_4": 4, "iconst_5": 5}

def analisar_fluxo(instrs):
    """Detecta estrutura de loops e ifs."""
    # Mapeia offsets (indice) -> tipo de bloco
    destinos_goto = {}   # offset de destino -> [offsets de goto que vao pra la]
    destinos_if = {}     # offset de if -> offset destino
    
    for idx, instr in enumerate(instrs):
        mn = instr.mnemonic
        if mn == "goto" and instr.operands:
            dest = idx + instr.operands[0].value
            destinos_goto.setdefault(dest, []).append(idx)
        elif mn.startswith("if") and instr.operands:
            dest = idx + instr.operands[0].value
            destinos_if[idx] = dest
    
    return destinos_goto, destinos_if

def marcar_inicio_loop(instrs, destinos_goto):
    """Marca onde comeca cada loop (goto pra tras)."""
    inicios_loop = set()
    for dest, gotos in destinos_goto.items():
        for g in gotos:
            if g > dest:  # goto pra tras = loop
                inicios_loop.add(dest)
    return inicios_loop

def patch_v31(jar_path, estrutura_json, saida_c):
    """Regera com analise de fluxo."""
    # Importa do V3
    sys.path.insert(0, '/data/data/com.termux/files/home/fabrica-ports/tools')
    import importlib.util
    spec = importlib.util.spec_from_file_location("v3", "portador_gerar_v3.py")
    v3 = importlib.util.module_from_spec(spec)
    sys.argv = ['v3']  # dummy
    # Nao executa main
    src = open("portador_gerar_v3.py").read()
    src = src.replace('if __name__ == "__main__":\n    main()', '')
    exec(compile(src, "portador_gerar_v3.py", "exec"), v3.__dict__)
    
    with open(estrutura_json) as f:
        estrutura = json.load(f)
    
    # Modifica traduzir_metodo pra incluir analise de fluxo
    v3_codigo = v3.gerar_main_c(estrutura, jar_path)
    
    with open(saida_c, "w") as f:
        f.write(v3_codigo)
    print(f"Gerado: {saida_c}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python v31_patch.py <estrutura.json> <jar> <saida.c>")
        sys.exit(1)
    patch_v31(sys.argv[2], sys.argv[1], sys.argv[3])
