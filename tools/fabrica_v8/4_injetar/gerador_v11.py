#!/usr/bin/env python3
"""
Gerador V11 - Corrige os 5 bugs estruturais do V10:
1. Typedefs ANTES das globais
2. Overloads com sufixo (_2, _3)
3. Prototipos e definicoes com MESMA assinatura
4. return 0 apenas em nao-void
5. Sem globais duplicadas
"""
import sys, json, os, zipfile, io, re
from jawa.cf import ClassFile

def san(nome):
    if not nome: return "x"
    nome = nome.lstrip("_")
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        return nome if not nome[0].isdigit() else f"_{nome}"
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{cp:04x}"

def parse_desc(desc):
    """Retorna (params, return_type). Parametros NAO incluem self."""
    if "(" not in desc or ")" not in desc:
        return [], "void"
    args = desc[1:desc.index(")")]
    params = []
    i = 0
    while i < len(args):
        c = args[i]
        if c in "ISBZC": params.append(("int", c)); i += 1
        elif c == "J": params.append(("int64_t","J")); i += 1
        elif c == "F": params.append(("float","F")); i += 1
        elif c == "D": params.append(("double","D")); i += 1
        elif c == "L":
            fim = args.index(";", i); params.append(("void*","L")); i = fim + 1
        elif c == "[":
            j = i+1
            while j < len(args) and args[j]=="[": j += 1
            if j < len(args) and args[j]=="L":
                fim = args.index(";", j); i = fim + 1
            else: i = j + 1
            params.append(("void*","["))
        else: i += 1
    r = desc.split(")")[-1]
    rt = {"V":"void","I":"int","J":"int64_t","Z":"int","F":"float","D":"double"}.get(r, "void*")
    return params, rt

def gerar(estrutura, jar_path):
    nome = estrutura["nome_projeto"]
    L = []
    
    # ===== 1. Header =====
    L.append(f"// {nome} - main.c gerado por V11")
    L.append("#include <pspkernel.h>")
    L.append("#include <string.h>")
    L.append("#include <stdlib.h>")
    L.append("#include <stdint.h>")
    L.append('#include "j2me_gfx.h"')
    L.append('#include "j2me_font.h"')
    L.append('#include "j2me_input.h"')
    L.append('#include "j2me_image.h"')
    L.append('#include "j2me_clip.h"')
    L.append('#include "j2me_runtime.h"')
    L.append("")
    L.append(f'PSP_MODULE_INFO("{nome}", 0, 1, 0);')
    L.append("PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);")
    L.append("")
    L.append("#define SCR_W 480")
    L.append("#define SCR_H 272")
    L.append("")
    
    # ===== 2. Tipos base =====
    for t in ["Image","Graphics","Font","String","Command","Display","Displayable",
              "MIDlet","Canvas","Random","Timer","TimerTask","Vector","InputStream",
              "DataInputStream","Thread"]:
        L.append(f"typedef void* {t};")
    L.append("")
    
    # ===== 3. Stubs de biblioteca =====
    L.append("// Stubs de biblioteca")
    L.append("void j2me_canvas_repaint(void) { }")
    L.append("void j2me_canvas_serviceRepaints(void) { }")
    L.append("void j2me_gc(void) { }")
    L.append("void* j2me_image_get_graphics(void* img) { return img; }")
    L.append("")
    
    # ===== 4. FOWARD DECLARATIONS (ANTES DE TUDO) =====
    L.append("// Forward typedefs")
    for c in estrutura["classes"]:
        n = san(c["nome"])
        L.append(f"typedef struct {n}_s {n};")
    L.append("")
    
    # ===== 5. Globais (agora com tipos definidos) =====
    L.append("// Globais")
    L.append("void* _self = 0;")
    L.append("void* _p1_self = 0;")
    L.append("void* _p2_self = 0;")
    L.append("void* _role_self = 0;")
    # msf_mc com tipo do canvas
    canvas = estrutura.get("canvas") or "Canvas"
    canvas_tipo = san(canvas)
    L.append(f"{canvas_tipo}* msf_mc = 0;")
    L.append("int Game_count = 0;")
    L.append("int MapCanvas_OFFY = 96;")
    L.append("int MapCanvas_OFFX = 180;")
    L.append("int MapCanvas_CanvasWidth = 480;")
    L.append("int MapCanvas_CanvasHeight = 272;")
    L.append("int MapCanvas_still = 0;")
    L.append("int MapCanvas_lightflag = 0;")
    L.append("")
    
    # ===== 6. Estruturas =====
    L.append("// Structs")
    for c in estrutura["classes"]:
        L.append(f"struct {san(c['nome'])}_s {{")
        for campo in c["campos"]:
            L.append(f"    {campo['tipo_c']:<12} {san(campo['nome'])};")
        if not c["campos"]:
            L.append("    int _vazio;")
        L.append("};")
        L.append("")
    
    # ===== 7. Coleta TODOS os metodos com nomes UNICOS (overloads) =====
    L.append("// Prototipos")
    z = zipfile.ZipFile(jar_path)
    metodos = []  # (classe, nome_java, desc, fn_nome, params, rt)
    contadores = {}  # (classe, nome_java) -> [desc...]
    
    for c in estrutura["classes"]:
        try: cf = ClassFile(io.BytesIO(z.read(c["arquivo"])))
        except: continue
        
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            nome_java = m.name.value
            desc = m.descriptor.value
            params, rt = parse_desc(desc)
            
            chave = (c["nome"], nome_java)
            if chave not in contadores:
                contadores[chave] = []
            contadores[chave].append(desc)
            
            # Nome unico (se for overload, adiciona sufixo)
            base = san(nome_java.replace("<init>","constructor").replace("-","_"))
            cn = san(c["nome"])
            nome_fn = f"{cn}_{base}"
            if len(contadores[chave]) > 1:
                nome_fn += f"_{len(contadores[chave])}"
            
            metodos.append((c["nome"], nome_java, desc, nome_fn, params, rt))
    
    # Prototipos (todos)
    for (cls, nm, desc, fn, params, rt) in metodos:
        all_params = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]
        L.append(f"{rt} {fn}({', '.join(all_params)});")
    L.append("")
    
    # ===== 8. Implementacoes (mesma assinatura dos prototipos) =====
    L.append("// Implementacoes")
    for (cls, nm, desc, fn, params, rt) in metodos:
        all_params = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]
        cn = san(cls)
        L.append(f"{rt} {fn}({', '.join(all_params)}) {{")
        L.append(f"    {cn}* s = ({cn}*)self;")
        if rt == "void":
            L.append("    if (!s) return;")
        else:
            L.append("    if (!s) return 0;")
        L.append(f"    (void)s;")
        L.append(f"    // TODO: traduzir")
        if rt != "void":
            L.append("    return 0;")
        L.append("}")
        L.append("")
    
    # ===== 9. main() =====
    personagens = []
    for c in estrutura["classes"]:
        metodos_c = [m["nome"] for m in c["metodos"]]
        if "reset" in metodos_c and ("forward" in metodos_c or "punch" in metodos_c):
            personagens.append(c["nome"])
    personagens.sort(key=lambda x: (0 if "Ryu" in x else 1, x))
    
    L.append("// Main")
    L.append("int main(void) {")
    L.append("    j2me_gfx_init();")
    L.append("    j2me_input_init();")
    L.append("    j2me_random_init();")
    L.append("")
    if canvas:
        L.append(f"    {canvas_tipo}* mc = ({canvas_tipo}*)calloc(1, sizeof({canvas_tipo}));")
        L.append("    _self = mc;")
        L.append("    msf_mc = mc;")
    for i, p in enumerate(personagens):
        pn = san(p)
        L.append(f"    {pn}* p{i+1} = ({pn}*)calloc(1, sizeof({pn}));")
        L.append(f"    _p{i+1}_self = p{i+1};")
    if personagens:
        L.append("    _role_self = _p1_self;")
    L.append("")
    L.append("    while (1) {")
    L.append("        j2me_input_update();")
    L.append("        if (j2me_input_should_quit()) break;")
    L.append("        j2me_gfx_begin_frame();")
    L.append("        j2me_gfx_clear(0x101020);")
    L.append("        j2me_gfx_flip();")
    L.append("    }")
    L.append("    j2me_gfx_shutdown();")
    L.append("    sceKernelExitGame();")
    L.append("    return 0;")
    L.append("}")
    
    return "\n".join(L)

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    codigo = gerar(estrutura, sys.argv[2])
    with open("/data/data/com.termux/files/home/main_v11.c", "w") as f:
        f.write(codigo)
    print(f"Gerado: {len(codigo.splitlines())} linhas")
    print(f"Salvo em: ~/main_v11.c")
