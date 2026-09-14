#!/usr/bin/env python3
"""
Gerador V6 - Tudo integrado.
Objetivo: gerar C que COMPILA, usando goto-based (como Ghidra).
Features:
- Simulacao de pilha com tipos
- Pre-declaracao de todas as variaveis locais
- Pre-coleta de todos os labels
- Assinaturas corretas baseadas no descritor
- Constantes do <clinit> como #define
- Self como void* (simplifica)
- Casts para evitar erros de tipo
"""
import sys, os, json, zipfile, io, re
from jawa.cf import ClassFile

CONSTANTES = {"iconst_m1": -1, "iconst_0": 0, "iconst_1": 1,
              "iconst_2": 2, "iconst_3": 3, "iconst_4": 4, "iconst_5": 5}
ARIT = {
    "iadd": "+", "isub": "-", "imul": "*", "idiv": "/", "irem": "%",
    "iand": "&", "ior": "|", "ixor": "^", "ishl": "<<", "ishr": ">>",
    "ladd": "+", "lsub": "-", "lmul": "*",
    "fadd": "+", "fsub": "-", "fmul": "*",
}
CMP = {
    "if_icmpeq":"==", "if_icmpne":"!=", "if_icmplt":"<", "if_icmple":"<=",
    "if_icmpgt":">", "if_icmpge":">=", "if_acmpeq":"==", "if_acmpne":"!=",
}
CMP0 = {"ifeq":"==", "ifne":"!=", "iflt":"<", "ifle":"<=", "ifgt":">", "ifge":">="}

def san(nome):
    if not nome: return "x"
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        return nome if not nome[0].isdigit() else f"_{nome}"
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{cp:04x}"

def res(cf, idx):
    try: return cf.constants.get(idx)
    except: return None


def nome_metodo(classe, nome_java, desc=""):
    """Gera nome unico incluindo hash do descritor (distingue overloads)."""
    base = nome_java.replace("<init>","constructor").replace("-","_")
    base = san(base)
    cn = san(classe)
    # Hash simples do descritor
    h = 0
    for ch in desc:
        h = (h * 31 + ord(ch)) & 0xFFFF
    return f"{cn}_{base}_fn_{h:04x}"

def parse_desc(desc):
    """Retorna (params_list, return_type)."""
    if "(" not in desc or ")" not in desc:
        return [], "void"
    args = desc[1:desc.index(")")]
    ret = desc[desc.index(")")+1:]
    params = []
    i = 0
    while i < len(args):
        c = args[i]
        if c in "ISBZC": params.append(("int", c)); i += 1
        elif c == "J": params.append(("int64_t","J")); i += 1
        elif c == "F": params.append(("float","F")); i += 1
        elif c == "D": params.append(("double","D")); i += 1
        elif c == "L":
            fim = args.index(";", i)
            params.append((f"void*", "L")); i = fim + 1
        elif c == "[":
            j = i+1
            while j < len(args) and args[j]=="[": j += 1
            if j < len(args) and args[j]=="L":
                fim = args.index(";", j); i = fim + 1
            else: i = j + 1
            params.append(("void*", "["))
        else: i += 1
    # ret
    if not ret: rt = "void"
    else:
        c = ret[0]
        if c == "V": rt = "void"
        elif c in "ISBZC": rt = "int"
        elif c == "J": rt = "int64_t"
        elif c == "F": rt = "float"
        elif c == "D": rt = "double"
        elif c in "L[": rt = "void*"
        else: rt = "void"
    return params, rt

def traduzir(cf, metodo, classe_interna):
    """Traduz um metodo. Retorna lista de linhas."""
    if not metodo.code: return None
    try: instrs = list(metodo.code.disassemble())
    except: return None
    if len(instrs) > 1500: return ["    // (metodo muito grande, pulado)"]

    nome_m = metodo.name.value
    desc = metodo.descriptor.value
    params, ret_t = parse_desc(desc)

    # Locais: self + params
    locais = {0: "self"}
    for i, (tipo, _) in enumerate(params):
        locais[i+1] = f"arg{i}"

    # Pre-scan: descobre todos os labels usados
    labels = set()
    for idx, ins in enumerate(instrs):
        mn = ins.mnemonic
        if mn in CMP or mn in CMP0 or mn in ("ifnonnull","ifnull","goto"):
            if ins.operands:
                dest = idx + ins.operands[0].value
                labels.add(dest)

    # Pre-scan: descobre locais usados (para declarar)
    tipos_locais = {}  # indice -> tipo
    for ins in instrs:
        mn = ins.mnemonic; ops = ins.operands
        if mn in ("iload","istore","iinc") and ops:
            tipos_locais.setdefault(ops[0].value, "int")
        elif mn in ("aload","astore") and ops:
            tipos_locais.setdefault(ops[0].value, "void*")
        elif mn in ("fload","fstore") and ops:
            tipos_locais.setdefault(ops[0].value, "float")
        elif mn in ("lload","lstore") and ops:
            tipos_locais.setdefault(ops[0].value, "int64_t")
        elif mn.startswith(("iload_","istore_")) and mn[-1].isdigit():
            tipos_locais.setdefault(int(mn[-1]), "int")
        elif mn.startswith(("aload_","astore_")) and mn[-1].isdigit():
            tipos_locais.setdefault(int(mn[-1]), "void*")
        elif mn.startswith(("fload_","fstore_")) and mn[-1].isdigit():
            tipos_locais.setdefault(int(mn[-1]), "float")

    linhas = []
    pilha = []
    locais_decl = set()

    def emitir(l, ind=""):
        linhas.append(f"    {ind}{l}")
    def push(v): pilha.append(v)
    def pop(): return pilha.pop() if pilha else "0"
    def peek(): return pilha[-1] if pilha else "0"

    # Declaracoes
    for i, tipo in sorted(tipos_locais.items()):
        if i in locais: continue  # eh self ou arg
        n = f"var{i}"
        emitir(f"{tipo} {n} = 0;")
        locais[i] = n
        locais_decl.add(i)

    # Loop
    for idx, ins in enumerate(instrs):
        if idx in labels:
            emitir(f"L_{idx}:;")
        mn = ins.mnemonic; ops = ins.operands

        # Constantes
        if mn in CONSTANTES:
            push(str(CONSTANTES[mn])); continue
        if mn == "bipush" and ops: push(str(ops[0].value)); continue
        if mn == "sipush" and ops: push(str(ops[0].value)); continue
        if mn in ("ldc","ldc_w") and ops:
            c = res(cf, ops[0].value)
            if c and hasattr(c,'value'):
                v = c.value
                if hasattr(v,'value'): v = v.value
                if isinstance(v, str): push(f'"{v}"')
                else: push(str(v))
            else: push("0")
            continue
        if mn == "lconst_0": push("0L"); continue
        if mn == "lconst_1": push("1L"); continue
        if mn == "aconst_null": push("NULL"); continue

        # Loads
        if mn in ("iload","fload","aload","lload","dload") and ops:
            push(locais.get(ops[0].value, f"var{ops[0].value}")); continue
        if mn in ("iload_0","iload_1","iload_2","iload_3"):
            push(locais.get(int(mn[-1]), f"var{mn[-1]}")); continue
        if mn in ("aload_0","aload_1","aload_2","aload_3"):
            push(locais.get(int(mn[-1]), f"var{mn[-1]}")); continue
        if mn in ("fload_0","fload_1","fload_2","fload_3"):
            push(locais.get(int(mn[-1]), f"var{mn[-1]}")); continue

        # Stores
        if mn in ("istore","astore","fstore","lstore","dstore") and ops:
            i = ops[0].value; v = pop()
            n = locais.get(i, f"var{i}")
            if i not in locais_decl and i not in locais:
                # Declaracao ainda nao feita (nao detectada no pre-scan)
                emitir(f"int {n} = {v};")
                locais[i] = n; locais_decl.add(i)
            else:
                emitir(f"{n} = {v};")
            continue
        if mn.startswith(("istore_","astore_","fstore_","lstore_","dstore_")):
            i = int(mn[-1]); v = pop()
            n = locais.get(i, f"var{i}")
            if i not in locais_decl and i not in locais:
                emitir(f"int {n} = {v};")
                locais[i] = n; locais_decl.add(i)
            else:
                emitir(f"{n} = {v};")
            continue

        # Aritmetica
        if mn in ARIT:
            b = pop(); a = pop()
            push(f"({a} {ARIT[mn]} {b})"); continue
        if mn == "ineg": push(f"(-{pop()})"); continue
        if mn == "iinc" and ops and len(ops) >= 2:
            i = ops[0].value; inc = ops[1].value
            emitir(f"{locais.get(i, f'var{i}')} += {inc};"); continue

        # Fields
        if mn == "getfield" and ops:
            c = res(cf, ops[0].value)
            if c:
                campo = san(c.name_and_type.name.value)
                obj = pop()
                push(f"(({c.class_.name.value.split('/')[-1]}_s*){obj})->{campo}")
            else: push("0")
            continue
        if mn == "putfield" and ops:
            c = res(cf, ops[0].value)
            if c:
                campo = san(c.name_and_type.name.value)
                cls = c.class_.name.value.split("/")[-1]
                v = pop(); obj = pop()
                emitir(f"(({cls}_s*){obj})->{campo} = {v};")
            continue
        if mn == "getstatic" and ops:
            c = res(cf, ops[0].value)
            if c:
                cls = c.class_.name.value.split("/")[-1]
                campo = san(c.name_and_type.name.value)
                push(f"{cls}_{campo}")
            else: push("0")
            continue
        if mn == "putstatic" and ops:
            c = res(cf, ops[0].value)
            if c:
                cls = c.class_.name.value.split("/")[-1]
                campo = san(c.name_and_type.name.value)
                v = pop()
                emitir(f"{cls}_{campo} = {v};")
            continue

        # Calls
        if mn in ("invokevirtual","invokestatic","invokespecial","invokeinterface"):
            if not ops: continue
            c = res(cf, ops[0].value)
            if not c: continue
            owner = c.class_.name.value
            nm = c.name_and_type.name.value
            dm = c.name_and_type.descriptor.value
            mp, _ = parse_desc(dm)
            n_args = len(mp)
            argv = [pop() for _ in range(n_args)][::-1]
            obj = None if mn == "invokestatic" else pop()

            # API conhecida
            APIs = {
                "javax/microedition/lcdui/Graphics.setColor": ("j2me_gfx_set_color","void"),
                "javax/microedition/lcdui/Graphics.fillRect": ("j2me_gfx_fill_rect","void"),
                "javax/microedition/lcdui/Graphics.drawString": ("j2me_font_draw","void"),
                "javax/microedition/lcdui/Graphics.drawImage": ("j2me_image_blit","void"),
                "javax/microedition/lcdui/Graphics.drawRegion": ("j2me_image_draw_region","void"),
                "javax/microedition/lcdui/Graphics.setClip": ("j2me_clip_push","void"),
                "javax/microedition/lcdui/Canvas.getWidth": ("SCR_W","int"),
                "javax/microedition/lcdui/Canvas.getHeight": ("SCR_H","int"),
                "javax/microedition/lcdui/Canvas.getGameAction": ("j2me_input_get_actions","int"),
                "javax/microedition/lcdui/Canvas.repaint": ("j2me_canvas_repaint","void"),
                "javax/microedition/lcdui/Canvas.serviceRepaints": ("j2me_canvas_serviceRepaints","void"),
                "java/util/Random.nextInt": ("j2me_random_next","int"),
                "java/util/Random.<init>": ("j2me_noop","void"),
                "java/lang/System.currentTimeMillis": ("j2me_time_ms","int64_t"),
                "java/lang/Thread.sleep": ("j2me_sleep","void"),
                "java/lang/Thread.start": ("j2me_noop","void"),
                "java/lang/Math.abs": ("abs","int"),
                "java/lang/Object.<init>": ("j2me_noop","void"),
                "java/lang/StringBuffer.<init>": ("j2me_noop","void"),
                "java/lang/StringBuffer.append": ("j2me_noop","void"),
                "java/lang/StringBuffer.toString": ("j2me_noop","void*"),
                "java/io/PrintStream.println": ("j2me_noop","void"),
            }
            chave = f"{owner}.{nm}"
            if chave in APIs:
                fn, rt = APIs[chave]
                if fn in ("SCR_W","SCR_H"):
                    push(fn)
                elif rt == "void":
                    emitir(f"{fn}({', '.join(argv)});")
                else:
                    push(f"{fn}({', '.join(argv)})")
            else:
                # Chamada interna
                so = san(owner.split("/")[-1])
                # Nome com mesmo formato do gerador (hash do descritor)
                nome_chamada = nome_metodo(owner.split("/")[-1], nm, dm)
                if mn == "invokestatic":
                    allargs = argv
                else:
                    allargs = [obj if obj else "NULL"] + argv
                emitir(f"{nome_chamada}({', '.join(allargs)});")
                if rt := dm.split(")")[-1]:
                    if rt != "V":
                        push("0")
            continue

        # Saltos
        if mn in CMP:
            b = pop(); a = pop()
            dest = idx + ops[0].value
            op_inv = {"==":"!=","!=":"==","<":">=","<=":">",">":"<=",">=":"<"}[CMP[mn]]
            emitir(f"if (({a}) {op_inv} ({b})) goto L_{dest};")
            continue
        if mn in CMP0:
            v = pop()
            dest = idx + ops[0].value
            op_inv = {"==":"!=","!=":"==","<":">=","<=":">",">":"<=",">=":"<"}[CMP0[mn]]
            emitir(f"if (({v}) {op_inv} 0) goto L_{dest};")
            continue
        if mn == "ifnonnull":
            v = pop(); dest = idx + ops[0].value
            emitir(f"if (({v}) == NULL) goto L_{dest};")
            continue
        if mn == "ifnull":
            v = pop(); dest = idx + ops[0].value
            emitir(f"if (({v}) != NULL) goto L_{dest};")
            continue
        if mn == "goto" and ops:
            dest = idx + ops[0].value
            emitir(f"goto L_{dest};")
            continue

        # Retornos
        if mn == "return":
            pilha.clear(); emitir("return;"); continue
        if mn in ("ireturn","areturn","freturn","lreturn","dreturn"):
            v = pop() if pilha else "0"
            emitir(f"return {v};"); continue

        # Stack
        if mn == "dup": push(peek()); continue
        if mn == "pop": pop(); continue
        if mn == "pop2":
            if pilha: pop()
            if pilha: pop()
            continue
        if mn == "swap" and len(pilha) >= 2:
            pilha[-1], pilha[-2] = pilha[-2], pilha[-1]
            continue

        if mn == "new": push("NULL"); continue
        if mn in ("anewarray","newarray"):
            n = pop(); push(f"/* arr[{n}] */NULL"); continue
        if mn == "arraylength":
            v = pop(); push(f"0"); continue

        if mn.startswith(("i2","l2","f2","d2")):
            v = pop()
            if mn == "i2l": push(f"((int64_t){v})")
            elif mn == "i2f": push(f"((float){v})")
            elif mn == "i2s": push(f"((short){v})")
            elif mn == "i2b": push(f"((signed char){v})")
            else: push(v)
            continue

        if mn in ("iaload","aaload","baload","caload","saload"):
            i = pop(); arr = pop()
            push(f"((int*){arr})[{i}]")
            continue
        if mn in ("iastore","aastore","bastore","castore","sastore"):
            v = pop(); i = pop(); arr = pop()
            emitir(f"((int*){arr})[{i}] = {v};")
            continue

        # Ignora o resto

    if pilha:
        emitir(f"// pilha residual: {pilha}")

    return linhas

def gerar(estrutura, jar_path, constantes_path):
    nome = estrutura["nome_projeto"]
    consts = {}
    if os.path.exists(constantes_path):
        with open(constantes_path) as f:
            for l in f:
                m = re.match(r'#define (\w+)\s+(.+)', l.strip())
                if m: consts[m.group(1)] = m.group(2)

    L = []
    L.append(f"// {nome} - Port V6 (compilavel + codigo real)")
    L.append("")
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
    L.append("// Constantes extraidas")
    for k in sorted(consts.keys()):
        L.append(f"#define {k} {consts[k]}")
    L.append("")
    L.append("typedef void* Image;")
    L.append("typedef void* Graphics;")
    L.append("typedef void* Font;")
    L.append("typedef void* String;")
    L.append("typedef void* Command;")
    L.append("typedef void* Display;")
    L.append("typedef void* Displayable;")
    L.append("typedef void* MIDlet;")
    L.append("typedef void* Canvas;")
    L.append("typedef void* InputStream;")
    L.append("typedef void* DataInputStream;")
    L.append("typedef void* Vector;")
    L.append("typedef void* Timer;")
    L.append("typedef void* Random;")
    L.append("typedef void* Thread;")
    L.append("")
    L.append(f'PSP_MODULE_INFO("{nome}", 0, 1, 0);')
    L.append("PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);")
    L.append("")
    L.append("#define SCR_W 480")
    L.append("#define SCR_H 272")
    L.append("")

    # Stubs de funcoes da biblio que faltam
    L.append("// Stubs para compilar")
    L.append("void j2me_canvas_repaint(void) {}")
    L.append("void j2me_canvas_serviceRepaints(void) {}")
    L.append("")
    L.append("// Declaracoes globais (placeholders, serao preenchidas)")
    # Globais sao declaradas depois dos typedefs (movido abaixo)

    # Forward declarations das classes
    for c in estrutura["classes"]:
        n = san(c["nome"])
        L.append(f"typedef struct {n}_s {n};")
    L.append("")
    
    # Globais mutaveis (depois dos typedefs)
    z = zipfile.ZipFile(jar_path)
    campos_estaticos = set()
    for c in estrutura["classes"]:
        for campo in c["campos"]:
            nome_campo = f"{c['nome']}_{san(campo['nome'])}"
            if nome_campo not in consts:
                campos_estaticos.add((c['nome'], san(campo['nome']), campo['tipo_c']))
    for cls, campo, tipo in sorted(campos_estaticos):
        L.append(f"{tipo} {cls}_{campo};")
    L.append("")

    # Structs
    for c in estrutura["classes"]:
        L.append(f"// {c['nome']} (extends {c['super']})")
        L.append(f"struct {san(c['nome'])}_s {{")
        for campo in c["campos"]:
            L.append(f"    {campo['tipo_c']:<12} {san(campo['nome'])};")
        if not c["campos"]:
            L.append("    int _vazio;")
        L.append("};")
        L.append("")

    # Prototipos de todas as funcoes
    L.append("// Prototipos")
    protos = {}
    z = zipfile.ZipFile(jar_path)
    for c in estrutura["classes"]:
        try:
            cf = ClassFile(io.BytesIO(z.read(c["arquivo"])))
        except: continue
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            nm = m.name.value
            nome_final = nome_metodo(c["nome"], nm, m.descriptor.value)
            params, ret_t = parse_desc(m.descriptor.value)
            params_c = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]
            L.append(f"{ret_t} {nome_final}({', '.join(params_c)});")
    L.append("")

    # Implementacoes
    for c in estrutura["classes"]:
        try:
            cf = ClassFile(io.BytesIO(z.read(c["arquivo"])))
        except: continue
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            nome_m = m.name.value
            nome_final = nome_metodo(c["nome"], nome_m, m.descriptor.value)
            params, ret_t = parse_desc(m.descriptor.value)
            params_c = ["void* self"] + [f"{t} arg{i}" for i, (t, _) in enumerate(params)]

            L.append(f"// {c['nome']}.{nome_m}")
            L.append(f"{ret_t} {nome_final}({', '.join(params_c)}) {{")
            if not m.code:
                L.append("    // (sem code)")
            else:
                corpo = traduzir(cf, m, c['nome'])
                if corpo: L.extend(corpo)
                else: L.append("    // (falha ao traduzir)")
            L.append("}")
            L.append("")

    # Main
    L.append("int main(void) {")
    L.append("    j2me_gfx_init();")
    L.append("    j2me_input_init();")
    L.append("    j2me_random_init();")
    L.append("")
    L.append("    while (1) {")
    L.append("        j2me_input_update();")
    L.append("        if (j2me_input_should_quit()) break;")
    L.append("        j2me_gfx_begin_frame();")
    L.append("        j2me_gfx_clear(0x101020);")
    L.append(f"        // {estrutura['midlet']}_startApp(NULL);")
    L.append(f"        // {estrutura['canvas']}_paint(NULL, NULL);")
    L.append("        j2me_gfx_flip();")
    L.append("    }")
    L.append("")
    L.append("    j2me_gfx_shutdown();")
    L.append("    sceKernelExitGame();")
    L.append("    return 0;")
    L.append("}")
    return "\n".join(L)

def main():
    if len(sys.argv) < 4:
        print("Uso: python portador_gerar_v6.py <estrutura.json> <jogo.jar> <constantes.h> [saida.c]")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    saida = sys.argv[4] if len(sys.argv) > 4 else "main_v6.c"
    codigo = gerar(estrutura, sys.argv[2], sys.argv[3])
    with open(saida, "w") as f:
        f.write(codigo)
    print(f"Gerado: {saida} ({codigo.count(chr(10))} linhas)")

if __name__ == "__main__":
    main()
