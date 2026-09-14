#!/usr/bin/env python3
"""
Gerador V3 - Tradutor de bytecode JVM -> C.
Simula a pilha do JVM e emite C equivalente.
Uso: python portador_gerar_v3.py <estrutura.json> <jar> [saida.c]
"""
import sys, os, json, zipfile, io
from jawa.cf import ClassFile

# Opcodes que empilham constantes
CONSTANTES = {
    "iconst_m1": -1, "iconst_0": 0, "iconst_1": 1, "iconst_2": 2,
    "iconst_3": 3, "iconst_4": 4, "iconst_5": 5,
}

# Aritmetica: (a, b) -> expressao
ARITMETICA = {
    "iadd": "({} + {})", "isub": "({} - {})", "imul": "({} * {})",
    "idiv": "({} / {})", "irem": "({} % {})",
    "iand": "({} & {})", "ior": "({} | {})", "ixor": "({} ^ {})",
    "ishl": "({} << {})", "ishr": "({} >> {})", "iushr": "((unsigned){} >> {})",
    "ladd": "({} + {})", "lsub": "({} - {})", "lmul": "({} * {})",
    "fadd": "({} + {})", "fsub": "({} - {})", "fmul": "({} * {})",
    "dadd": "({} + {})", "dsub": "({} - {})", "dmul": "({} * {})",
}

# Comparacoes
COMPARACOES = {
    "if_icmpeq": "==", "if_icmpne": "!=",
    "if_icmplt": "<",  "if_icmple": "<=",
    "if_icmpgt": ">",  "if_icmpge": ">=",
    "if_acmpeq": "==", "if_acmpne": "!=",
}

def desaninhar_nome(nome):
    if not nome: return "x"
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        return nome if not nome[0].isdigit() else f"_{nome}"
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{cp:04x}"

def resolver_constante(cf, idx):
    try: return cf.constants.get(idx)
    except: return None


def analisar_saltos(instrs):
    """Analisa saltos: retorna (inicios_loop, destinos_if, tem_loop)."""
    inicios_loop = set()
    destinos_if = {}
    for idx, instr in enumerate(instrs):
        mn = instr.mnemonic
        if mn == "goto" and instr.operands:
            dest = idx + instr.operands[0].value
            if dest <= idx:  # goto pra tras ou mesmo ponto = loop
                inicios_loop.add(dest)
        elif mn.startswith("if") and instr.operands:
            dest = idx + instr.operands[0].value
            destinos_if[idx] = dest
    return inicios_loop, destinos_if

def traduzir_metodo(cf, metodo, classes_internas, nome_classe):
    """Traduz bytecode pra C com simulacao de pilha."""
    linhas = []
    pilha = []  # expressoes C
    locais = {} # indice -> nome da variavel
    nome_m = metodo.name.value
    desc = metodo.descriptor.value

    # Extrai nomes dos parametros do descritor (I = int, L...; = ponteiro)
    params = []
    if ")" in desc:
        args = desc[1:desc.index(")")]
        i = 0
        while i < len(args):
            c = args[i]
            if c == "I" or c == "S" or c == "B" or c == "Z" or c == "C":
                params.append("int")
                i += 1
            elif c == "J":
                params.append("int64_t")
                i += 1
            elif c == "F":
                params.append("float")
                i += 1
            elif c == "D":
                params.append("double")
                i += 1
            elif c == "L":
                fim = args.index(";", i)
                nome = args[i+1:fim].split("/")[-1]
                params.append(f"{nome}*")
                i = fim + 1
            elif c == "[":
                # Array: avanca ate o tipo base
                j = i + 1
                while j < len(args) and args[j] == "[":
                    j += 1
                if args[j] == "L":
                    fim = args.index(";", j)
                    nome = args[j+1:fim].split("/")[-1]
                    params.append(f"{nome}**")
                    i = fim + 1
                else:
                    params.append("void*")
                    i = j + 1
            else:
                i += 1

    # locais[0] = this, locais[1..] = params
    locais[0] = "self"
    for i, t in enumerate(params):
        locais[i+1] = f"arg{i}"

    if not metodo.code:
        return None

    try:
        instrs = list(metodo.code.disassemble())
    except Exception:
        return None

    if len(instrs) > 500:
        linhas.append(f"    // AVISO: metodo com {len(instrs)} instrucoes (muito grande)")
        linhas.append(f"    // TODO: traduzir manualmente")
        return linhas

    n_empilhados = 0
    labels_usadas = set()

    def emitir(linha, indent="    "):
        linhas.append(f"{indent}{linha}")

    def pop():
        return pilha.pop() if pilha else "?"

    def peek():
        return pilha[-1] if pilha else "?"

    for idx, instr in enumerate(instrs):
        mn = instr.mnemonic
        ops = instr.operands

        # === CONSTANTES ===
        if mn in CONSTANTES:
            pilha.append(str(CONSTANTES[mn]))
            continue

        if mn == "bipush" and ops:
            pilha.append(str(ops[0].value))
            continue

        if mn == "sipush" and ops:
            pilha.append(str(ops[0].value))
            continue

        if mn in ("ldc", "ldc_w", "ldc2_w") and ops:
            const = resolver_constante(cf, ops[0].value)
            if const and hasattr(const, 'value'):
                v = const.value
                if hasattr(v, 'value'):
                    v = v.value
                if isinstance(v, str):
                    pilha.append(f'"{v}"')
                else:
                    pilha.append(str(v))
            else:
                pilha.append(f"/* const#{ops[0].value} */0")
            continue

        if mn == "lconst_0": pilha.append("0L"); continue
        if mn == "lconst_1": pilha.append("1L"); continue
        if mn == "aconst_null": pilha.append("NULL"); continue

        # === CARREGAR VARIAVEL LOCAL ===
        if mn in ("iload", "fload", "aload", "lload", "dload"):
            if ops:
                i = ops[0].value
                nome = locais.get(i, f"var{i}")
                pilha.append(nome)
            continue
        if mn in ("iload_0","iload_1","iload_2","iload_3"):
            i = int(mn[-1]); pilha.append(locais.get(i, f"var{i}")); continue
        if mn in ("aload_0","aload_1","aload_2","aload_3"):
            i = int(mn[-1]); pilha.append(locais.get(i, f"var{i}")); continue
        if mn in ("fload_0","fload_1","fload_2","fload_3"):
            i = int(mn[-1]); pilha.append(locais.get(i, f"var{i}")); continue

        # === ARMAZENAR VARIAVEL LOCAL ===
        if mn in ("istore", "astore", "fstore", "lstore", "dstore"):
            if ops:
                i = ops[0].value
                val = pop()
                nome = locais.get(i, f"var{i}")
                if nome not in locais.values():
                    emitir(f"int {nome} = {val};")
                    locais[i] = nome
                else:
                    emitir(f"{nome} = {val};")
            continue
        if mn in ("istore_0","istore_1","istore_2","istore_3"):
            i = int(mn[-1]); val = pop()
            nome = locais.get(i, f"var{i}")
            if nome not in locais.values():
                emitir(f"int {nome} = {val};"); locais[i] = nome
            else:
                emitir(f"{nome} = {val};")
            continue
        if mn in ("astore_0","astore_1","astore_2","astore_3"):
            i = int(mn[-1]); val = pop()
            nome = locais.get(i, f"var{i}")
            if nome not in locais.values():
                emitir(f"void* {nome} = {val};"); locais[i] = nome
            else:
                emitir(f"{nome} = {val};")
            continue

        # === ARITMETICA ===
        if mn in ARITMETICA:
            b = pop(); a = pop()
            pilha.append(ARITMETICA[mn].format(a, b))
            continue

        if mn == "ineg": pilha.append(f"(-{pop()})"); continue
        if mn == "iinc" and ops and len(ops) >= 2:
            i = ops[0].value; inc = ops[1].value
            nome = locais.get(i, f"var{i}")
            emitir(f"{nome} += {inc};")
            continue

        # === CAMPOS (get/put) ===
        if mn == "getfield" and ops:
            const = resolver_constante(cf, ops[0].value)
            if const:
                cls = const.class_.name.value.split("/")[-1]
                campo = desaninhar_nome(const.name_and_type.name.value)
                obj = pop()
                pilha.append(f"{obj}->{campo}")
            else:
                pilha.append("/* ??? */0")
            continue

        if mn == "putfield" and ops:
            const = resolver_constante(cf, ops[0].value)
            if const:
                cls = const.class_.name.value.split("/")[-1]
                campo = desaninhar_nome(const.name_and_type.name.value)
                val = pop()
                obj = pop()
                emitir(f"{obj}->{campo} = {val};")
            continue

        if mn == "getstatic" and ops:
            const = resolver_constante(cf, ops[0].value)
            if const:
                cls = const.class_.name.value.split("/")[-1]
                campo = desaninhar_nome(const.name_and_type.name.value)
                pilha.append(f"{cls}_{campo}")
            else:
                pilha.append("/* ??? */0")
            continue

        if mn == "putstatic" and ops:
            const = resolver_constante(cf, ops[0].value)
            if const:
                cls = const.class_.name.value.split("/")[-1]
                campo = desaninhar_nome(const.name_and_type.name.value)
                val = pop()
                emitir(f"{cls}_{campo} = {val};")
            continue

        # === CHAMADAS DE METODO ===
        if mn in ("invokevirtual","invokestatic","invokespecial","invokeinterface"):
            if not ops: continue
            const = resolver_constante(cf, ops[0].value)
            if not const:
                continue
            owner = const.class_.name.value
            nome_met = const.name_and_type.name.value
            desc_met = const.name_and_type.descriptor.value

            # Conta argumentos
            n_args = 0
            if ")" in desc_met:
                args = desc_met[1:desc_met.index(")")]
                i = 0
                while i < len(args):
                    if args[i] == "L":
                        i = args.index(";", i) + 1
                    elif args[i] == "[":
                        while args[i] == "[": i += 1
                        if args[i] == "L": i = args.index(";", i) + 1
                        else: i += 1
                    else:
                        i += 1
                    n_args += 1

            # Pop argumentos (ordem reversa)
            argv = [pop() for _ in range(n_args)]
            argv.reverse()

            eh_static = (mn == "invokestatic")
            obj = None if eh_static else pop()

            # Traduz chamada
            short_owner = owner.split("/")[-1]
            short_met = nome_met

            if owner.startswith("javax/microedition"):
                # Mapeamento de API conhecida
                API_MAP = {
                    ("javax/microedition/lcdui/Graphics","setColor"): ("j2me_gfx_set_color", 1),
                    ("javax/microedition/lcdui/Graphics","fillRect"): ("j2me_gfx_fill_rect", 4),
                    ("javax/microedition/lcdui/Graphics","drawString"): ("j2me_font_draw", 3),
                    ("javax/microedition/lcdui/Graphics","drawImage"): ("j2me_image_blit", 3),
                    ("javax/microedition/lcdui/Graphics","drawRegion"): ("j2me_image_draw_region", 9),
                    ("javax/microedition/lcdui/Graphics","setClip"): ("j2me_clip_push", 4),
                    ("javax/microedition/lcdui/Canvas","getWidth"): ("SCR_W", 0),
                    ("javax/microedition/lcdui/Canvas","getHeight"): ("SCR_H", 0),
                    ("javax/microedition/lcdui/Canvas","getGameAction"): ("j2me_input_get_actions", 0),
                    ("javax/microedition/lcdui/Canvas","repaint"): ("j2me_canvas_repaint", 0),
                    ("java/util/Random","nextInt"): ("j2me_random_next", 1),
                    ("java/lang/System","currentTimeMillis"): ("j2me_time_ms", 0),
                    ("java/lang/Thread","sleep"): ("j2me_sleep", 1),
                    ("java/lang/Math","abs"): ("abs", 1),
                    ("java/lang/Math","max"): ("MAX", 2),
                    ("java/lang/Math","min"): ("MIN", 2),
                    ("java/lang/Object","<init>"): ("j2me_noop", 0),
                }
                chave = (owner, nome_met)
                if chave in API_MAP:
                    func, _ = API_MAP[chave]
                    if n_args == 0:
                        if func in ("SCR_W","SCR_H"):
                            pilha.append(func)
                        else:
                            emitir(f"{func}();")
                    else:
                        emitir(f"{func}({', '.join(argv)});")
                else:
                    emitir(f"// TODO: {short_owner}.{short_met}({', '.join(argv)})")
                    pilha.append("/* ret */0")
            else:
                # Chamada interna
                if eh_static:
                    emitir(f"{short_owner}_{desaninhar_nome(short_met)}({', '.join(argv)});")
                else:
                    args_str = ", ".join([obj] + argv) if obj else ", ".join(argv)
                    emitir(f"{short_owner}_{desaninhar_nome(short_met)}({args_str});")
                # Se retorna algo, empilha
                if ")" in desc_met and desc_met.split(")")[-1] != "V":
                    pilha.append("/* ret */0")
            continue

        # === COMPARACOES / SALTOS ===
        if mn in COMPARACOES:
            b = pop(); a = pop()
            emitir(f"if ({a} {COMPARACOES[mn]} {b}) {{")
            emitir(f"    // [corpo do if - offset {idx}]", "    ")
            continue

        if mn in ("ifeq","ifne","iflt","ifle","ifgt","ifge"):
            v = pop()
            op = {"ifeq":"==","ifne":"!=","iflt":"<","ifle":"<=","ifgt":">","ifge":">="}[mn]
            emitir(f"if ({v} {op} 0) {{")
            emitir(f"    // [corpo do if - offset {idx}]", "    ")
            continue

        if mn == "ifnonnull":
            v = pop()
            emitir(f"if ({v} != NULL) {{")
            emitir(f"    // [corpo do if - offset {idx}]", "    ")
            continue

        if mn == "ifnull":
            v = pop()
            emitir(f"if ({v} == NULL) {{")
            emitir(f"    // [corpo do if - offset {idx}]", "    ")
            continue

        if mn == "if_icmpne" or mn.startswith("if_icmp"):
            b = pop(); a = pop()
            if mn == "if_icmpne": op = "!="
            elif mn == "if_icmpeq": op = "=="
            elif mn == "if_icmplt": op = "<"
            elif mn == "if_icmple": op = "<="
            elif mn == "if_icmpgt": op = ">"
            elif mn == "if_icmpge": op = ">="
            else: op = "=="
            emitir(f"if ({a} {op} {b}) {{")
            continue

        if mn == "goto":
            dest = idx + instr.operands[0].value if ops else idx
            if dest <= idx:
                emitir("// FIM DO LOOP (goto pra tras)")
                emitir("break;  // TODO: verificar condicao do while")
            else:
                emitir("// FIM DO IF (goto pra frente)")
            continue

        # === RETORNO ===
        if mn == "return":
            if pilha: pilha.clear()
            emitir("return;")
            continue

        if mn in ("ireturn","areturn","freturn","lreturn","dreturn"):
            v = pop() if pilha else "0"
            emitir(f"return {v};")
            continue

        # === OUTROS ===
        if mn == "dup":
            v = peek(); pilha.append(v); continue
        if mn == "pop":
            pop(); continue
        if mn == "pop2":
            if pilha: pop()
            if pilha: pop()
            continue
        if mn == "swap":
            if len(pilha) >= 2:
                pilha[-1], pilha[-2] = pilha[-2], pilha[-1]
            continue

        if mn == "new":
            emitir(f"// new (TODO)")
            pilha.append("/* new */NULL")
            continue
        if mn == "anewarray":
            n = pop()
            pilha.append(f"/* array[{n}] */NULL")
            continue
        if mn == "newarray":
            n = pop()
            pilha.append(f"/* prim-array[{n}] */NULL")
            continue

        if mn.startswith("i2") or mn.startswith("l2") or mn.startswith("f2") or mn.startswith("d2"):
            # Cast
            v = pop()
            if mn == "i2l": pilha.append(f"(int64_t){v}")
            elif mn == "i2f": pilha.append(f"(float){v}")
            elif mn == "i2s": pilha.append(f"(short){v}")
            elif mn == "i2b": pilha.append(f"(signed char){v}")
            else: pilha.append(v)
            continue

        # Ignorar outros
        # emitir(f"// [nao traduzido] {mn}")

    if pilha:
        emitir(f"// AVISO: pilha nao vazia ao final: {pilha}")

    return linhas

def gerar_main_c(estrutura, jar_path):
    nome = estrutura["nome_projeto"]
    linhas = []
    linhas.append(f"// {nome} - Port V3 (bytecode traduzido)")
    linhas.append(f"// Gerado por portador_gerar_v3.py")
    linhas.append("")
    linhas.append("#include <pspkernel.h>")
    linhas.append("#include <string.h>")
    linhas.append("#include <stdlib.h>")
    linhas.append("#include <stdint.h>")
    linhas.append("#include \"j2me_gfx.h\"")
    linhas.append("#include \"j2me_font.h\"")
    linhas.append("#include \"j2me_input.h\"")
    linhas.append("#include \"j2me_image.h\"")
    linhas.append("#include \"j2me_clip.h\"")
    linhas.append("#include \"j2me_runtime.h\"")
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
    linhas.append("// Forward")
    for c in estrutura["classes"]:
        n = desaninhar_nome(c["nome"])
        linhas.append(f"typedef struct {n}_s {n};")
    linhas.append("")

    # Structs
    for classe in estrutura["classes"]:
        linhas.append(f"// {classe['nome']} (extends {classe['super']})")
        linhas.append(f"struct {desaninhar_nome(classe['nome'])}_s {{")
        for campo in classe["campos"]:
            linhas.append(f"    {campo['tipo_c']:<12} {desaninhar_nome(campo['nome'])};")
        if not classe["campos"]:
            linhas.append("    int _vazio;")
        linhas.append("};")
        linhas.append("")

    # Abre o jar e traduz metodos
    z = zipfile.ZipFile(jar_path)
    classes_internas = {n[:-6] for n in z.namelist() if n.endswith(".class")}

    for classe in estrutura["classes"]:
        arquivo = classe["arquivo"]
        try:
            cf = ClassFile(io.BytesIO(z.read(arquivo)))
        except Exception:
            continue

        for m in list(cf.methods):
            nome_m = m.name.value
            if nome_m == "<clinit>":
                continue

            # Nome da funcao
            nome_fn = desaninhar_nome(nome_m.replace("<init>", "constructor"))
            classe_n = desaninhar_nome(classe["nome"])
            nome_final = f"{classe_n}_{nome_fn}"

            # Assinatura
            desc = m.descriptor.value
            tipo_ret = "void"
            if ")" in desc:
                r = desc.split(")")[-1]
                tipo_ret = {"V":"void","I":"int","J":"int64_t","Z":"int","F":"float","D":"double"}.get(r, "void*")

            # Parametros (simplificado)
            n_params = 0
            if "(" in desc and ")" in desc:
                args = desc[1:desc.index(")")]
                i = 0
                while i < len(args):
                    if args[i] == "L": i = args.index(";", i) + 1
                    elif args[i] == "[":
                        while args[i] == "[": i += 1
                        if args[i] == "L": i = args.index(";", i) + 1
                        else: i += 1
                    else: i += 1
                    n_params += 1

            linhas.append(f"// === {classe['nome']}.{nome_m} ({m.descriptor.value}) ===")
            params_str = ", ".join([f"int arg{i}" for i in range(n_params)])
            linhas.append(f"{tipo_ret} {nome_final}({params_str}) {{")

            if not m.code:
                linhas.append("    // (sem codigo)")
            else:
                corpo = traduzir_metodo(cf, m, classes_internas, classe["nome"])
                if corpo:
                    linhas.extend(corpo)
                else:
                    linhas.append("    // TODO")

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
        print("Uso: python portador_gerar_v3.py <estrutura.json> <jogo.jar> [saida.c]")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    jar = sys.argv[2]
    saida = sys.argv[3] if len(sys.argv) > 3 else "main_v3.c"
    codigo = gerar_main_c(estrutura, jar)
    with open(saida, "w") as f:
        f.write(codigo)
    print(f"Gerado: {saida} ({codigo.count(chr(10))} linhas)")

if __name__ == "__main__":
    main()
