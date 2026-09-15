#!/usr/bin/env python3
"""
V15 - Corrige 2 bugs do V14:
1. Nomes de classe do projeto NAO sao emitidos como typedef void*
2. Colisao classe/metodo renomeada (Blackjack_a classe vs Blackjack_a metodo)
"""
import sys, json, os, zipfile, io, re
from jawa.cf import ClassFile

C_KEYWORDS = {
    "int","char","long","short","float","double","void","if","else","for","while",
    "do","switch","case","break","continue","return","goto","sizeof","struct",
    "union","enum","typedef","static","extern","const","volatile","register",
    "auto","signed","unsigned","default","inline","restrict","bool","true","false",
    "NULL","this","new","delete","try","catch","throw","class","public",
    "private","protected","virtual","template","typename","namespace","using",
    "operator","friend","mutable","explicit","export","asm"
}

def san(nome):
    if not nome: return "x"
    nome = nome.replace("$", "_").lstrip("_")
    if nome.lower() in (k.lower() for k in C_KEYWORDS):
        nome = f"{nome}_x"
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        return nome if not nome[0].isdigit() else f"_{nome}"
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{cp:04x}"

TIPOS_BASE = [
    "Image","Graphics","DirectGraphics","Font","String","StringBuffer",
    "Command","Display","Displayable","Canvas","FullCanvas","GameCanvas",
    "Random","Timer","TimerTask","Vector","List","Form","TextField",
    "InputStream","DataInputStream","OutputStream","RecordStore",
    "Thread","MIDlet","Object","Class","Math","System","Integer",
    "Long","Short","Byte","Character","Boolean","Float","Double",
    "TextBox","Alert","AlertType","ImageItem","Spacer","Gauge","DateField",
    "ChoiceGroup","ListItem","Ticker","Item","Screen",
    "Sound","DeviceControl","Player","Manager","Control",
    "ByteArrayInputStream","ByteArrayOutputStream","DataOutputStream",
    "Runtime","Process","Enumeration","Iterator","Hashtable","Stack","Queue",
    "Calendar","Date","TimeZone","Locale","StringTokenizer",
]

def extrair_tipos_do_jar(jar_path):
    tipos = set()
    z = zipfile.ZipFile(jar_path)
    for n in z.namelist():
        if not n.endswith(".class"): continue
        try:
            cf = ClassFile(io.BytesIO(z.read(n)))
        except: continue
        for const in cf.constants:
            try:
                if hasattr(const, 'name') and hasattr(const.name, 'value'):
                    tipo = const.name.value
                    if "/" in tipo and not tipo.startswith("["):
                        simple = tipo.split("/")[-1]
                        if simple and not simple[0].isdigit():
                            tipos.add(simple)
            except: pass
        try:
            sup = cf.super_class.name.value
            tipos.add(sup.split("/")[-1])
        except: pass
    return sorted(tipos)

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
    tipos_detectados = extrair_tipos_do_jar(jar_path)
    
    # === FIX 1: nomes de classe do projeto ===
    classes_san = {}
    nomes_classes = set()
    for c in estrutura["classes"]:
        n = san(c["nome"])
        if n == "main":
            n = "main_cls"
        base = n
        contador = 1
        while n in nomes_classes:
            contador += 1
            n = f"{base}_{contador}"
        nomes_classes.add(n)
        classes_san[c["nome"]] = n
    
    # === FIX 2: tipos base NAO incluem nomes de classe do projeto ===
    todos_tipos = set()
    for t in TIPOS_BASE + tipos_detectados:
        t_san = san(t)
        if t_san in nomes_classes:
            continue  # pula, ja eh classe do projeto
        todos_tipos.add(t_san)
    
    L = []
    L.append(f"// {nome} - main.c gerado por V15")
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
    
    L.append("// Tipos J2ME (sem colidir com classes do projeto)")
    for t in sorted(todos_tipos):
        L.append(f"typedef void* {t};")
    L.append("")
    
    L.append("// Stubs de biblioteca")
    L.append("void j2me_canvas_repaint(void) { }")
    L.append("void j2me_canvas_serviceRepaints(void) { }")
    L.append("void j2me_gc(void) { }")
    L.append("void* j2me_image_get_graphics(void* img) { return img; }")
    L.append("")
    
    L.append("// Forward typedefs das classes do projeto")
    for c in estrutura["classes"]:
        n = classes_san[c["nome"]]
        L.append(f"typedef struct {n}_s {n};")
        L.append(f"typedef struct {n}_s {n}_s;")
    L.append("")
    
    # Globais
    L.append("// Globais")
    L.append("void* _self = 0;")
    L.append("void* _p1_self = 0;")
    L.append("void* _p2_self = 0;")
    L.append("void* _role_self = 0;")
    canvas = estrutura.get("canvas") or "Canvas"
    canvas_tipo = classes_san.get(canvas, san(canvas))
    L.append(f"{canvas_tipo}* msf_mc = 0;")
    L.append("int Game_count = 0;")
    L.append("int MapCanvas_OFFY = 96;")
    L.append("int MapCanvas_OFFX = 180;")
    L.append("int MapCanvas_CanvasWidth = 480;")
    L.append("int MapCanvas_CanvasHeight = 272;")
    L.append("int MapCanvas_still = 0;")
    L.append("int MapCanvas_lightflag = 0;")
    L.append("")
    
    # Structs
    L.append("// Structs")
    for c in estrutura["classes"]:
        cn = classes_san[c["nome"]]
        L.append(f"struct {cn}_s {{")
        for campo in c["campos"]:
            tipo_c = campo["tipo_c"].replace("$", "_")
            if not any(tipo_c.startswith(t) for t in ["int","char","long","short","float","double","void","int64"]):
                tipo_c = "void*"
            L.append(f"    {tipo_c:<12} {san(campo['nome'])};")
        if not c["campos"]:
            L.append("    int _vazio;")
        L.append("};")
        L.append("")
    
    # Metodos
    L.append("// Prototipos")
    z = zipfile.ZipFile(jar_path)
    metodos = []
    nomes_fn_usados = set()
    nomes_cls_usados = set(classes_san.values())
    
    for c in estrutura["classes"]:
        cn = classes_san[c["nome"]]
        try: cf = ClassFile(io.BytesIO(z.read(c["arquivo"])))
        except: continue
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            nome_java = m.name.value
            desc = m.descriptor.value
            params, rt = parse_desc(desc)
            
            base = nome_java.replace("<init>","constructor").replace("-","_")
            base = san(base)
            if base == "main": base = "main_fn"
            if base == cn: base = f"{base}_fn"
            
            nome_fn = f"{cn}_{base}"
            # FIX 2: dedup contra nomes de classe tambem
            original = nome_fn
            contador = 1
            while nome_fn in nomes_fn_usados or nome_fn in nomes_cls_usados:
                contador += 1
                nome_fn = f"{original}_{contador}"
            nomes_fn_usados.add(nome_fn)
            
            metodos.append((cn, nome_java, desc, nome_fn, params, rt))
    
    for (cn, nm, desc, fn, params, rt) in metodos:
        all_params = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]
        L.append(f"{rt} {fn}({', '.join(all_params)});")
    L.append("")
    
    L.append("// Implementacoes")
    for (cn, nm, desc, fn, params, rt) in metodos:
        all_params = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]
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
    
    # main()
    personagens = []
    for c in estrutura["classes"]:
        metodos_c = [m["nome"] for m in c["metodos"]]
        if "reset" in metodos_c and ("forward" in metodos_c or "punch" in metodos_c):
            personagens.append(classes_san[c["nome"]])
    
    L.append("int main(void) {")
    L.append("    j2me_gfx_init();")
    L.append("    j2me_input_init();")
    L.append("    j2me_random_init();")
    L.append("")
    L.append(f"    {canvas_tipo}* mc = ({canvas_tipo}*)calloc(1, sizeof({canvas_tipo}));")
    L.append("    _self = mc;")
    L.append("    msf_mc = mc;")
    for i, p in enumerate(personagens):
        L.append(f"    {p}* p{i+1} = ({p}*)calloc(1, sizeof({p}));")
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
    
    return "\n".join(L), len(tipos_detectados)

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    codigo, n_tipos = gerar(estrutura, sys.argv[2])
    with open("/data/data/com.termux/files/home/main_v15.c", "w") as f:
        f.write(codigo)
    print(f"Gerado: {len(codigo.splitlines())} linhas, {n_tipos} tipos detectados")
