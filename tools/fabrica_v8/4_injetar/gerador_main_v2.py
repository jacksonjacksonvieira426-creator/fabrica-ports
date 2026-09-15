#!/usr/bin/env python3
"""
Gerador V2 - main.c 100% consistente.
Corrige os 5 problemas estruturais do V8:
1. Metodos tem (void* self, ...) uniforme
2. Campos sem _ no inicio
3. Prototipos sempre antes do uso
4. Stubs de biblioteca sempre presentes
5. Sem colisao #define vs int
"""
import sys, json, os, re, zipfile, io
from jawa.cf import ClassFile

def san(nome):
    """Remove _ inicial para padronizar."""
    if not nome: return "x"
    nome = nome.lstrip("_")
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        return nome if not nome[0].isdigit() else f"_{nome}"
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{cp:04x}"

def parse_desc(desc):
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

def gerar(estrutura, jar):
    nome = estrutura["nome_projeto"]
    L = []
    
    # ===== Header =====
    L.append(f"// {nome} - main.c gerado por V10 (consistente)")
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
    L.append('#define SCR_W 480')
    L.append('#define SCR_H 272')
    L.append("")
    
    # ===== Tipos base =====
    L.append("// Tipos J2ME como void*")
    for t in ["Image","Graphics","Font","String","Command","Display","Displayable",
              "MIDlet","Canvas","Random","Timer","TimerTask","Vector","InputStream",
              "DataInputStream","Thread"]:
        L.append(f"typedef void* {t};")
    L.append("")
    
    # ===== Stubs biblioteca =====
    L.append("// Stubs de biblioteca")
    L.append("void j2me_canvas_repaint(void) { }")
    L.append("void j2me_canvas_serviceRepaints(void) { }")
    L.append("void j2me_gc(void) { }")
    L.append("void* j2me_image_get_graphics(void* img) { return img; }")
    L.append("")
    
    # ===== Globais =====
    L.append("// Globais")
    L.append("void* _self = 0;")
    L.append("void* _p1_self = 0;")
    L.append("void* _p2_self = 0;")
    L.append("void* _role_self = 0;")
    L.append(f"{san(estrutura.get('canvas') or 'Canvas')}* msf_mc = 0;")
    L.append("int Game_count = 0;")
    for var in ["MapCanvas_OFFY","MapCanvas_OFFX","MapCanvas_CanvasWidth",
                "MapCanvas_CanvasHeight","MapCanvas_still","MapCanvas_lightflag"]:
        L.append(f"int {var} = 0;")
    L.append("MapCanvas_OFFY = 96;")
    L.append("MapCanvas_OFFX = 180;")
    L.append("MapCanvas_CanvasWidth = 480;")
    L.append("MapCanvas_CanvasHeight = 272;")
    L.append("")
    
    # ===== Forward typedef =====
    L.append("// Forward declarations")
    for c in estrutura["classes"]:
        n = san(c["nome"])
        L.append(f"typedef struct {n}_s {n};")
    L.append("")
    
    # ===== Structs =====
    for c in estrutura["classes"]:
        L.append(f"struct {san(c['nome'])}_s {{")
        for campo in c["campos"]:
            L.append(f"    {campo['tipo_c']:<12} {san(campo['nome'])};")
        if not c["campos"]:
            L.append("    int _vazio;")
        L.append("};")
        L.append("")
    
    # ===== Prototipos =====
    L.append("// Prototipos")
    z = zipfile.ZipFile(jar)
    protos = []
    for c in estrutura["classes"]:
        try: cf = ClassFile(io.BytesIO(z.read(c["arquivo"])))
        except: continue
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            nm = m.name.value
            nome_fn = san(nm.replace("<init>","constructor").replace("-","_"))
            cn = san(c["nome"])
            fn = f"{cn}_{nome_fn}"
            params, rt = parse_desc(m.descriptor.value)
            all_params = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]
            protos.append(f"{rt} {fn}({', '.join(all_params)});")
            L.append(protos[-1])
    L.append("")
    
    # ===== Implementacoes =====
    L.append("// Implementacoes")
    for c in estrutura["classes"]:
        try: cf = ClassFile(io.BytesIO(z.read(c["arquivo"])))
        except: continue
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            nm = m.name.value
            nome_fn = san(nm.replace("<init>","constructor").replace("-","_"))
            cn = san(c["nome"])
            fn = f"{cn}_{nome_fn}"
            params, rt = parse_desc(m.descriptor.value)
            all_params = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]
            
            L.append(f"{rt} {fn}({', '.join(all_params)}) {{")
            L.append(f"    {cn}* s = ({cn}*)self;")
            L.append(f"    if (!s) return;")
            L.append(f"    // TODO: traduzir")
            if rt != "void": L.append("    return 0;")
            L.append("}")
            L.append("")
    
    # ===== main() =====
    canvas = estrutura.get("canvas")
    personagens = []
    for c in estrutura["classes"]:
        metodos = [m["nome"] for m in c["metodos"]]
        if "reset" in metodos and ("forward" in metodos or "punch" in metodos):
            personagens.append(c["nome"])
    personagens.sort(key=lambda x: (0 if "Ryu" in x else 1, x))
    
    L.append("// Main")
    L.append("int main(void) {")
    L.append("    j2me_gfx_init();")
    L.append("    j2me_input_init();")
    L.append("    j2me_random_init();")
    L.append("")
    if canvas:
        cn = san(canvas)
        L.append(f"    {cn}* mc = ({cn}*)calloc(1, sizeof({cn}));")
        L.append(f"    _self = mc;")
        L.append(f"    msf_mc = mc;")
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
    if len(sys.argv) < 3:
        print("Uso: python gerador_main_v2.py <estrutura.json> <jogo.jar>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    codigo = gerar(estrutura, sys.argv[2])
    with open("/data/data/com.termux/files/home/main_v10.c", "w") as f:
        f.write(codigo)
    print(f"Gerado: {len(codigo.splitlines())} linhas")
    print(codigo[:1500])
