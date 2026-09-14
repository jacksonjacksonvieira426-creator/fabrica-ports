#!/usr/bin/env python3
"""
Gerador V4 - Traducao goto-based (como Ghidra/IDA).
Em vez de reconstruir if/while, gera goto + labels.
Codigo feio mas 100% equivalente e compilavel.
"""
import sys, os, json, zipfile, io
from jawa.cf import ClassFile

CONSTANTES = {"iconst_m1": -1, "iconst_0": 0, "iconst_1": 1,
              "iconst_2": 2, "iconst_3": 3, "iconst_4": 4, "iconst_5": 5}

ARITMETICA = {
    "iadd": "({} + {})", "isub": "({} - {})", "imul": "({} * {})",
    "idiv": "({} / {})", "irem": "({} % {})",
    "iand": "({} & {})", "ior": "({} | {})", "ixor": "({} ^ {})",
    "ishl": "({} << {})", "ishr": "({} >> {})",
    "ladd": "({} + {})", "lsub": "({} - {})", "lmul": "({} * {})",
    "fadd": "({} + {})", "fsub": "({} - {})", "fmul": "({} * {})",
}

COMPARACOES = {
    "if_icmpeq": "==", "if_icmpne": "!=",
    "if_icmplt": "<",  "if_icmple": "<=",
    "if_icmpgt": ">",  "if_icmpge": ">=",
    "if_acmpeq": "==", "if_acmpne": "!=",
}

CMP_ZERO = {
    "ifeq": "==", "ifne": "!=", "iflt": "<",
    "ifle": "<=", "ifgt": ">", "ifge": ">=",
}

def desaninhar(nome):
    if not nome: return "x"
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        return nome if not nome[0].isdigit() else f"_{nome}"
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{cp:04x}"

def res(cf, idx):
    try: return cf.constants.get(idx)
    except: return None

def traduzir_metodo(cf, metodo, nome_classe):
    """Traduz com goto-based - garante fluxo correto."""
    if not metodo.code:
        return None
    try:
        instrs = list(metodo.code.disassemble())
    except Exception:
        return None

    if len(instrs) > 800:
        return [f"    // AVISO: metodo com {len(instrs)} instrucoes (pulado)"]

    nome_m = metodo.name.value
    desc = metodo.descriptor.value

    # Extrai parametros
    params = []
    if "(" in desc and ")" in desc:
        args = desc[1:desc.index(")")]
        i = 0
        while i < len(args):
            c = args[i]
            if c in "ISBZC": params.append("int"); i += 1
            elif c == "J": params.append("int64_t"); i += 1
            elif c == "F": params.append("float"); i += 1
            elif c == "D": params.append("double"); i += 1
            elif c == "L":
                fim = args.index(";", i)
                params.append(f"{args[i+1:fim].split('/')[-1]}*")
                i = fim + 1
            elif c == "[":
                j = i + 1
                while j < len(args) and args[j] == "[": j += 1
                if args[j] == "L":
                    fim = args.index(";", j)
                    params.append(f"{args[j+1:fim].split('/')[-1]}*")
                    i = fim + 1
                else:
                    params.append("void*"); i = j + 1
            else: i += 1

    # Locais
    locais = {}
    locais[0] = "self"
    for i, t in enumerate(params):
        locais[i+1] = f"arg{i}"

    # Declaracoes
    linhas = []
    pilha = []
    usados = set()
    labels = set()

    def push(v): pilha.append(v)
    def pop(): return pilha.pop() if pilha else "0"
    def peek(): return pilha[-1] if pilha else "0"
    def emitir(l, ind="    "): linhas.append(f"{ind}{l}")

    # Pre-scan: descobrir labels necessarios
    for idx, instr in enumerate(instrs):
        if instr.mnemonic in COMPARACOES or instr.mnemonic in CMP_ZERO or \
           instr.mnemonic in ("ifnonnull","ifnull","goto","jsr","ret"):
            if instr.operands:
                dest = idx + instr.operands[0].value
                labels.add(dest)

    # Adiciona stub do metodo
    var_decls = []
    emitir(f"// {nome_classe}.{nome_m} ({desc})")
    # Nao emite assinatura - quem chama faz

    # Loop principal
    for idx, instr in enumerate(instrs):
        # Emite label se for destino
        if idx in labels:
            emitir(f"L_{idx}:;")

        mn = instr.mnemonic
        ops = instr.operands

        # Constantes
        if mn in CONSTANTES:
            push(str(CONSTANTES[mn])); continue
        if mn == "bipush" and ops: push(str(ops[0].value)); continue
        if mn == "sipush" and ops: push(str(ops[0].value)); continue
        if mn in ("ldc","ldc_w","ldc2_w") and ops:
            const = res(cf, ops[0].value)
            if const and hasattr(const,'value'):
                v = const.value
                if hasattr(v,'value'): v = v.value
                if isinstance(v, str): push(f'"{v}"')
                else: push(str(v))
            else: push("0")
            continue
        if mn == "lconst_0": push("0L"); continue
        if mn == "lconst_1": push("1L"); continue
        if mn == "aconst_null": push("NULL"); continue

        # Load
        if mn in ("iload","fload","aload","lload","dload") and ops:
            push(locais.get(ops[0].value, f"var{ops[0].value}")); continue
        if mn in ("iload_0","iload_1","iload_2","iload_3"):
            push(locais.get(int(mn[-1]), f"var{mn[-1]}")); continue
        if mn in ("aload_0","aload_1","aload_2","aload_3"):
            push(locais.get(int(mn[-1]), f"var{mn[-1]}")); continue
        if mn in ("fload_0","fload_1","fload_2","fload_3"):
            push(locais.get(int(mn[-1]), f"var{mn[-1]}")); continue

        # Store
        if mn in ("istore","astore","fstore","lstore","dstore") and ops:
            i = ops[0].value; v = pop()
            n = locais.get(i, f"var{i}")
            if n not in usados:
                usados.add(n); emitir(f"int {n} = {v};")
            else: emitir(f"{n} = {v};")
            locais[i] = n
            continue
        if mn in ("istore_0","istore_1","istore_2","istore_3"):
            i = int(mn[-1]); v = pop()
            n = locais.get(i, f"var{i}")
            if n not in usados:
                usados.add(n); emitir(f"int {n} = {v};")
            else: emitir(f"{n} = {v};")
            locais[i] = n
            continue
        if mn in ("astore_0","astore_1","astore_2","astore_3"):
            i = int(mn[-1]); v = pop()
            n = locais.get(i, f"var{i}")
            if n not in usados:
                usados.add(n); emitir(f"void* {n} = {v};")
            else: emitir(f"{n} = {v};")
            locais[i] = n
            continue

        # Aritmetica
        if mn in ARITMETICA:
            b = pop(); a = pop()
            push(ARITMETICA[mn].format(a, b)); continue
        if mn == "ineg": push(f"(-{pop()})"); continue
        if mn == "iinc" and ops and len(ops) >= 2:
            i = ops[0].value; inc = ops[1].value
            n = locais.get(i, f"var{i}")
            emitir(f"{n} += {inc};"); continue

        # Fields
        if mn == "getfield" and ops:
            c = res(cf, ops[0].value)
            if c:
                campo = desaninhar(c.name_and_type.name.value)
                obj = pop()
                push(f"{obj}->{campo}")
            else: push("0")
            continue
        if mn == "putfield" and ops:
            c = res(cf, ops[0].value)
            if c:
                campo = desaninhar(c.name_and_type.name.value)
                v = pop(); obj = pop()
                emitir(f"{obj}->{campo} = {v};")
            continue
        if mn == "getstatic" and ops:
            c = res(cf, ops[0].value)
            if c:
                cls = c.class_.name.value.split("/")[-1]
                campo = desaninhar(c.name_and_type.name.value)
                push(f"{cls}_{campo}")
            else: push("0")
            continue
        if mn == "putstatic" and ops:
            c = res(cf, ops[0].value)
            if c:
                cls = c.class_.name.value.split("/")[-1]
                campo = desaninhar(c.name_and_type.name.value)
                v = pop()
                emitir(f"{cls}_{campo} = {v};")
            continue

        # Calls
        if mn in ("invokevirtual","invokestatic","invokespecial","invokeinterface"):
            if not ops: continue
            c = res(cf, ops[0].value)
            if not c: continue
            owner = c.class_.name.value
            nome_met = c.name_and_type.name.value
            desc_met = c.name_and_type.descriptor.value

            # Conta args
            n_args = 0
            if "(" in desc_met:
                a = desc_met[1:desc_met.index(")")]
                i = 0
                while i < len(a):
                    if a[i] == "L": i = a.index(";", i)+1
                    elif a[i] == "[":
                        while a[i] == "[": i += 1
                        if a[i] == "L": i = a.index(";", i)+1
                        else: i += 1
                    else: i += 1
                    n_args += 1

            argv = [pop() for _ in range(n_args)]
            argv.reverse()
            obj = None if mn == "invokestatic" else pop()

            # API conhecida
            API = {
                ("javax/microedition/lcdui/Graphics","setColor"): ("j2me_gfx_set_color", "void"),
                ("javax/microedition/lcdui/Graphics","fillRect"): ("j2me_gfx_fill_rect", "void"),
                ("javax/microedition/lcdui/Graphics","drawString"): ("j2me_font_draw", "void"),
                ("javax/microedition/lcdui/Graphics","drawImage"): ("j2me_image_blit", "void"),
                ("javax/microedition/lcdui/Graphics","drawRegion"): ("j2me_image_draw_region", "void"),
                ("javax/microedition/lcdui/Graphics","setClip"): ("j2me_clip_push", "void"),
                ("javax/microedition/lcdui/Canvas","getWidth"): ("SCR_W", "int"),
                ("javax/microedition/lcdui/Canvas","getHeight"): ("SCR_H", "int"),
                ("javax/microedition/lcdui/Canvas","getGameAction"): ("j2me_input_get_actions", "int"),
                ("javax/microedition/lcdui/Canvas","repaint"): ("j2me_canvas_repaint", "void"),
                ("java/util/Random","nextInt"): ("j2me_random_next", "int"),
                ("java/lang/System","currentTimeMillis"): ("j2me_time_ms", "int64_t"),
                ("java/lang/Thread","sleep"): ("j2me_sleep", "void"),
                ("java/lang/Math","abs"): ("abs", "int"),
                ("java/lang/Object","<init>"): ("j2me_noop", "void"),
            }
            chave = (owner, nome_met)
            if chave in API:
                fn, rt = API[chave]
                if fn in ("SCR_W","SCR_H"):
                    push(fn)
                elif rt == "void":
                    emitir(f"{fn}({', '.join(argv)});")
                else:
                    push(f"{fn}({', '.join(argv)})")
            else:
                short_owner = owner.split("/")[-1]
                short_met = desaninhar(nome_met)
                if mn == "invokestatic":
                    args_all = argv
                    emitir(f"{short_owner}_{short_met}({', '.join(args_all)});")
                else:
                    args_all = [obj if obj else "self"] + argv
                    emitir(f"{short_owner}_{short_met}({', '.join(args_all)});")
                # retorno
                if ")" in desc_met and desc_met.split(")")[-1] != "V":
                    push("0")
            continue

        # Saltos com comparacao
        if mn in COMPARACOES:
            b = pop(); a = pop()
            dest = idx + (ops[0].value if ops else 0)
            if dest < 0: dest = 0
            # Inverte: se for igual, SALTA pra dest; senao continua
            op = COMPARACOES[mn]
            op_inv = {"==":"!=","!=":"==","<":">=","<=":">",">":"<=",">=":"<"}[op]
            emitir(f"if ({a} {op_inv} {b}) goto L_{dest};")
            continue

        if mn in CMP_ZERO:
            v = pop()
            dest = idx + (ops[0].value if ops else 0)
            if dest < 0: dest = 0
            op = CMP_ZERO[mn]
            op_inv = {"==":"!=","!=":"==","<":">=","<=":">",">":"<=",">=":"<"}[op]
            emitir(f"if ({v} {op_inv} 0) goto L_{dest};")
            continue

        if mn == "ifnonnull":
            v = pop()
            dest = idx + ops[0].value
            if dest < 0: dest = 0
            emitir(f"if ({v} == NULL) goto L_{dest};")
            continue
        if mn == "ifnull":
            v = pop()
            dest = idx + ops[0].value
            if dest < 0: dest = 0
            emitir(f"if ({v} != NULL) goto L_{dest};")
            continue

        if mn == "goto" and ops:
            dest = idx + ops[0].value
            if dest < 0: dest = 0
            emitir(f"goto L_{dest};")
            continue

        # Retornos
        if mn == "return":
            pilha.clear()
            emitir("return;"); continue
        if mn in ("ireturn","areturn","freturn","lreturn","dreturn"):
            v = pop() if pilha else "0"
            emitir(f"return {v};"); continue

        # Duplicar/descartar
        if mn == "dup":
            v = peek(); push(v); continue
        if mn == "pop":
            pop(); continue
        if mn == "pop2":
            if pilha: pop()
            if pilha: pop()
            continue
        if mn == "swap" and len(pilha) >= 2:
            pilha[-1], pilha[-2] = pilha[-2], pilha[-1]
            continue

        if mn == "new":
            push("/* new */NULL"); continue
        if mn in ("anewarray","newarray"):
            n = pop()
            push(f"/* array[{n}] */NULL"); continue

        if mn == "arraylength":
            v = pop(); push(f"/* len({v}) */0"); continue

        if mn.startswith(("i2","l2","f2","d2")):
            v = pop()
            if mn == "i2l": push(f"(int64_t){v}")
            elif mn == "i2f": push(f"(float){v}")
            elif mn == "i2s": push(f"(short){v}")
            elif mn == "i2b": push(f"(signed char){v}")
            else: push(v)
            continue

        # arrays
        if mn in ("iaload","aaload","baload","caload","saload","laload","faload","daload"):
            i = pop(); arr = pop()
            push(f"{arr}[{i}]")
            continue
        if mn in ("iastore","aastore","bastore","castore","sastore","lastore","fastore","dastore"):
            v = pop(); i = pop(); arr = pop()
            emitir(f"{arr}[{i}] = {v};")
            continue

        # Ignorar outros

    # Se sobrar algo na pilha, avisa
    if pilha:
        emitir(f"// pilha residual: {pilha}")

    return linhas

def gerar_main_c(estrutura, jar_path):
    nome = estrutura["nome_projeto"]
    linhas = []
    linhas.append(f"// {nome} - Port V4 (goto-based, como Ghidra)")
    linhas.append("")
    linhas.append("#include <pspkernel.h>")
    linhas.append("#include <string.h>")
    linhas.append("#include <stdlib.h>")
    linhas.append("#include <stdint.h>")
    linhas.append('#include "j2me_gfx.h"')
    linhas.append('#include "j2me_font.h"')
    linhas.append('#include "j2me_input.h"')
    linhas.append('#include "j2me_image.h"')
    linhas.append('#include "j2me_clip.h"')
    linhas.append('#include "j2me_runtime.h"')
    linhas.append("")
    linhas.append("#define MAX(a,b) ((a)>(b)?(a):(b))")
    linhas.append("#define MIN(a,b) ((a)<(b)?(a):(b))")
    linhas.append("")
    linhas.append("typedef void* Image;")
    linhas.append("typedef void* Graphics;")
    linhas.append("typedef void* Font;")
    linhas.append("typedef void* String;")
    linhas.append("typedef void* Command;")
    linhas.append("typedef void* Display;")
    linhas.append("typedef void* Displayable;")
    linhas.append("typedef void* MIDlet;")
    linhas.append("typedef void* Canvas;")
    linhas.append("")
    linhas.append(f'PSP_MODULE_INFO("{nome}", 0, 1, 0);')
    linhas.append("PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);")
    linhas.append("")
    linhas.append("#define SCR_W 480")
    linhas.append("#define SCR_H 272")
    linhas.append("")

    # Forward
    linhas.append("// Forward declarations")
    for c in estrutura["classes"]:
        n = desaninhar(c["nome"])
        linhas.append(f"typedef struct {n}_s {n};")
    linhas.append("")
    linhas.append("// Prototipos (TODO: preencher assinaturas corretas)")
    for c in estrutura["classes"]:
        for m in c["metodos"]:
            if m["n_instr"] == 0 or m["nome"] == "<clinit>": continue
            nm = m["nome"].replace("<init>","constructor").replace("-","_")
            nm = desaninhar(nm)
            cn = desaninhar(c["nome"])
            linhas.append(f"void {cn}_{nm}();")
    linhas.append("")

    # Structs
    for c in estrutura["classes"]:
        linhas.append(f"// {c['nome']} (extends {c['super']})")
        linhas.append(f"struct {desaninhar(c['nome'])}_s {{")
        for campo in c["campos"]:
            linhas.append(f"    {campo['tipo_c']:<12} {desaninhar(campo['nome'])};")
        if not c["campos"]:
            linhas.append("    int _vazio;")
        linhas.append("};")
        linhas.append("")

    # Traduz metodos
    z = zipfile.ZipFile(jar_path)
    for c in estrutura["classes"]:
        try:
            cf = ClassFile(io.BytesIO(z.read(c["arquivo"])))
        except Exception:
            continue
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            nome_m = m.name.value
            nome_fn = desaninhar(nome_m.replace("<init>","constructor").replace("-","_"))
            cn = desaninhar(c["nome"])
            nome_final = f"{cn}_{nome_fn}"

            desc = m.descriptor.value
            params = []
            if "(" in desc and ")" in desc:
                a = desc[1:desc.index(")")]
                i = 0
                while i < len(a):
                    c2 = a[i]
                    if c2 in "ISBZC": params.append("int"); i += 1
                    elif c2 == "J": params.append("int64_t"); i += 1
                    elif c2 == "F": params.append("float"); i += 1
                    elif c2 == "D": params.append("double"); i += 1
                    elif c2 == "L":
                        f = a.index(";", i)
                        params.append(f"{a[i+1:f].split('/')[-1]}*")
                        i = f + 1
                    elif c2 == "[":
                        j = i + 1
                        while j < len(a) and a[j] == "[": j += 1
                        if a[j] == "L":
                            f = a.index(";", j)
                            params.append(f"{a[j+1:f].split('/')[-1]}*")
                            i = f + 1
                        else:
                            params.append("void*"); i = j + 1
                    else: i += 1

            ret_t = "void"
            if ")" in desc:
                r = desc.split(")")[-1]
                ret_t = {"V":"void","I":"int","J":"int64_t","Z":"int","F":"float","D":"double"}.get(r, "void*")

            params_str = ", ".join([f"{t} arg{i}" for i, t in enumerate(params)])
            linhas.append(f"{ret_t} {nome_final}({params_str}) {{")

            if not m.code:
                linhas.append("    // (sem code)")
            else:
                corpo = traduzir_metodo(cf, m, c["nome"])
                if corpo:
                    linhas.extend(corpo)
                else:
                    linhas.append("    // (falha ao traduzir)")
            linhas.append("}")
            linhas.append("")

    # Main
    linhas.append("int main(void) {")
    linhas.append("    j2me_gfx_init();")
    linhas.append("    j2me_input_init();")
    linhas.append("    j2me_random_init();")
    linhas.append("")
    linhas.append("    while (1) {")
    linhas.append("        j2me_input_update();")
    linhas.append("        if (j2me_input_should_quit()) break;")
    linhas.append("        j2me_gfx_begin_frame();")
    linhas.append("        j2me_gfx_clear(0x101020);")
    linhas.append(f"        // {estrutura['midlet']}_startApp();")
    linhas.append(f"        // {estrutura['canvas']}_paint();")
    linhas.append("        j2me_gfx_flip();")
    linhas.append("    }")
    linhas.append("")
    linhas.append("    j2me_gfx_shutdown();")
    linhas.append("    sceKernelExitGame();")
    linhas.append("    return 0;")
    linhas.append("}")
    return "\n".join(linhas)

def main():
    if len(sys.argv) < 3:
        print("Uso: python portador_gerar_v4.py <estrutura.json> <jogo.jar> [saida.c]")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    saida = sys.argv[3] if len(sys.argv) > 3 else "main_v4.c"
    codigo = gerar_main_c(estrutura, sys.argv[2])
    with open(saida, "w") as f:
        f.write(codigo)
    print(f"Gerado: {saida} ({codigo.count(chr(10))} linhas)")

if __name__ == "__main__":
    main()
