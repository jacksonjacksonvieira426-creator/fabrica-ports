#!/usr/bin/env python3
"""
V12 - Corrige:
1. TODOS os tipos Java conhecidos como typedef
2. Typedefs ANTES de globais (ja no V11, mas garante)
3. Palavras-chave C (int, do, for, while, if, else...) sanitizadas como sufixo _
"""
import sys, json, os, zipfile, io, re
from jawa.cf import ClassFile

# Palavras-chave C que nao podem ser nomes de variavel
C_KEYWORDS = {
    "int","char","long","short","float","double","void","if","else","for","while",
    "do","switch","case","break","continue","return","goto","sizeof","struct",
    "union","enum","typedef","static","extern","const","volatile","register",
    "auto","signed","unsigned","default","inline","restrict"
}

def san(nome):
    nome = nome.replace('$', '_')  # kickboxing tem h$a
    if not nome: return "x"
    nome = nome.lstrip("_")
    if nome in C_KEYWORDS:
        nome = f"{nome}_x"
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

def gerar(estrutura, jar_path):
    nome = estrutura["nome_projeto"]
    L = []
    
    L.append(f"// {nome} - main.c gerado por V12")
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
    
    # ===== TODOS os tipos base =====
    L.append("// Tipos J2ME (todos como void*)")
    tipos = ["Image","Graphics","DirectGraphics","Font","String","StringBuffer",
             "Command","Display","Displayable","Canvas","FullCanvas","GameCanvas",
             "Random","Timer","TimerTask","Vector","List","Form","TextField",
             "InputStream","DataInputStream","OutputStream","RecordStore",
             "Thread","MIDlet","Object","Class","Math","System","Integer",
             "Long","Short","Byte","Character","Boolean","Float","Double",
             "Sound","DeviceControl","SpriteEvent","SpriteListener","SpriteAction",
             "MIDP","SoundListener","Player","PlayerListener","Control",
             "Manager","DataInputStream2","ByteArrayInputStream","ByteArrayOutputStream"]
    for t in tipos:
        L.append(f"typedef void* {t};")
    L.append("")
    
    # ===== Stubs biblioteca =====
    L.append("// Stubs de biblioteca")
    L.append("void j2me_canvas_repaint(void) { }")
    L.append("void j2me_canvas_serviceRepaints(void) { }")
    L.append("void j2me_gc(void) { }")
    L.append("void* j2me_image_get_graphics(void* img) { return img; }")
    L.append("")
    
    # ===== FOWARD typedefs das classes do projeto =====
    L.append("// Forward typedefs das classes do projeto")
    for c in estrutura["classes"]:
        n = san(c["nome"])
        if n == "main":  # classe chamada "main" colide com int main()
            n = "main_cls"
        L.append(f"typedef struct {n}_s {n};")
        # Garante o typedef do struct tambem (V12.3 esqueceu)
        L.append(f"typedef struct {n}_s {n}_s;")
    L.append("")
    
    # ===== Globais =====
    L.append("// Globais")
    L.append("void* _self = 0;")
    L.append("void* _p1_self = 0;")
    L.append("void* _p2_self = 0;")
    L.append("void* _role_self = 0;")
    canvas = estrutura.get("canvas") or "Canvas"
    canvas_tipo = san(canvas)
    if canvas_tipo == "main":
        canvas_tipo = "main_cls"
    L.append(f"{canvas_tipo}* msf_mc = 0;")
    L.append("int Game_count = 0;")
    L.append("int MapCanvas_OFFY = 96;")
    L.append("int MapCanvas_OFFX = 180;")
    L.append("int MapCanvas_CanvasWidth = 480;")
    L.append("int MapCanvas_CanvasHeight = 272;")
    L.append("int MapCanvas_still = 0;")
    L.append("int MapCanvas_lightflag = 0;")
    L.append("")
    
    # ===== Structs =====
    L.append("// Structs")
    for c in estrutura["classes"]:
        L.append(f"struct {san(c['nome'])}_s {{")
        for campo in c["campos"]:
            L.append(f"    {campo['tipo_c']:<12} {san(campo['nome'])};")
        if not c["campos"]:
            L.append("    int _vazio;")
        L.append("};")
        L.append("")
    
    # ===== Metodos (overloads com sufixo) =====
    L.append("// Prototipos")
    z = zipfile.ZipFile(jar_path)
    metodos = []
    contadores = {}
    
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
                contadores[chave] = 0
            contadores[chave] += 1
            
            base = nome_java.replace("<init>","constructor").replace("-","_")
            base = base.replace("$", "_")  # kickboxing h$a
            base = san(base)
            # Se virou "main" (colide com entry point), renomeia
            if base == "main":
                base = "main_x"
            cn = san(c["nome"])
            nome_fn = f"{cn}_{base}"
            if base == cn:  # classe X, metodo X -> colisao
                nome_fn = f"{cn}_{base}_fn"
            if contadores[chave] > 1:
                nome_fn += f"_{contadores[chave]}"
            
            metodos.append((c["nome"], nome_java, desc, nome_fn, params, rt))
    
    for (cls, nm, desc, fn, params, rt) in metodos:
        all_params = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]
        L.append(f"{rt} {fn}({', '.join(all_params)});")
    L.append("")
    
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
        L.append("    (void)s;")
        if rt != "void":
            L.append("    return 0;")
        L.append("}")
        L.append("")
    
    # ===== main() =====
    personagens = []
    for c in estrutura["classes"]:
        metodos_c = [m["nome"] for m in c["metodos"]]
        if "reset" in metodos_c and ("forward" in metodos_c or "punch" in metodos_c):
            personagens.append(c["nome"])
    personagens.sort(key=lambda x: (0 if "Ryu" in x else 1, x))
    
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
        if pn == "main":
            pn = "main_cls"
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
    with open("/data/data/com.termux/files/home/main_v12.c", "w") as f:
        f.write(codigo)
    print(f"Gerado: {len(codigo.splitlines())} linhas")
