#!/usr/bin/env python3
"""
Gerador V5 - Usa constantes extraidas + nomes legiveis.
Combina:
- Structs do V4
- Codigo real do bytecode (como V4)
- Constantes do <clinit> viram #defines
- Substitui ofusc_* pelos nomes reais
"""
import sys, os, json, zipfile, io, re
from jawa.cf import ClassFile

# Importa funcoes do V4
sys.path.insert(0, '/data/data/com.termux/files/home/fabrica-ports/tools')

def desaninhar(nome):
    if not nome: return "x"
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        return nome if not nome[0].isdigit() else f"_{nome}"
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{cp:04x}"

def carregar_constantes(path):
    """Le o header de constantes."""
    if not os.path.exists(path):
        return {}
    consts = {}
    with open(path) as f:
        for linha in f:
            m = re.match(r'#define (\w+)\s+(.+)', linha.strip())
            if m:
                consts[m.group(1)] = m.group(2)
    return consts

def gerar_main_v5(estrutura, jar_path, constantes):
    """Gera main.c v5."""
    nome = estrutura["nome_projeto"]
    linhas = []

    # Header
    linhas.append(f"// {nome} - Port V5 (constantes + nomes legiveis)")
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

    # Constantes extraidas
    linhas.append("// ============================================")
    linhas.append("// CONSTANTES EXTRAIDAS DO BYTECODE")
    linhas.append("// ============================================")
    for k in sorted(constantes.keys()):
        linhas.append(f"#define {k} {constantes[k]}")
    linhas.append("")

    # Tipos
    linhas.append("typedef void* Image;")
    linhas.append("typedef void* Graphics;")
    linhas.append("typedef void* Font;")
    linhas.append("typedef void* String;")
    linhas.append("typedef void* Command;")
    linhas.append("typedef void* Display;")
    linhas.append("typedef void* Displayable;")
    linhas.append("typedef void* MIDlet;")
    linhas.append("typedef void* Canvas;")
    linhas.append("typedef void* InputStream;")
    linhas.append("typedef void* OutputStream;")
    linhas.append("typedef void* DataInputStream;")
    linhas.append("typedef void* Vector;")
    linhas.append("typedef void* Timer;")
    linhas.append("typedef void* TimerTask;")
    linhas.append("typedef void* Random;")
    linhas.append("typedef void* Thread;")
    linhas.append("")
    linhas.append(f'PSP_MODULE_INFO("{nome}", 0, 1, 0);')
    linhas.append("PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);")
    linhas.append("")
    linhas.append("#define SCR_W 480")
    linhas.append("#define SCR_H 272")
    linhas.append("")

    # Forward
    for c in estrutura["classes"]:
        n = desaninhar(c["nome"])
        linhas.append(f"typedef struct {n}_s {n};")
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

    # Stubs so pra funcoes que NAO existem na biblioteca
    linhas.append("// Stubs pra linkar (funcoes que a biblioteca nao tem)")
    linhas.append("void j2me_canvas_repaint(void) {}")
    linhas.append("void j2me_canvas_serviceRepaints(void) {}")
    linhas.append("")

    # Abre jar
    z = zipfile.ZipFile(jar_path)

    # Conta overloads por (classe, nome) pra diferenciar
    nomes_usados = {}
    for cl in estrutura["classes"]:
        for m in cl["metodos"]:
            if m["n_instr"] == 0 or m["nome"] == "<clinit>": continue
            chave = f"{cl['nome']}::{m['nome']}"
            nomes_usados[chave] = nomes_usados.get(chave, 0) + 1

    # Traduz metodos
    contadores = {}
    for c in estrutura["classes"]:
        try:
            cf = ClassFile(io.BytesIO(z.read(c["arquivo"])))
        except: continue
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            nome_m = m.name.value
            nome_fn = desaninhar(nome_m.replace("<init>","constructor").replace("-","_"))
            cn = desaninhar(c["nome"])
            
            # Diferencia overloads
            chave = f"{c['nome']}::{nome_m}"
            if nomes_usados.get(chave, 0) > 1:
                contadores[chave] = contadores.get(chave, 0) + 1
                nome_final = f"{cn}_{nome_fn}_{contadores[chave]}"
            else:
                nome_final = f"{cn}_{nome_fn}"

            # Assinatura com self
            params = ["void* self"]
            desc = m.descriptor.value
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
                        params.append(f"{a[i+1:f].split('/')[-1]}*"); i = f + 1
                    elif c2 == "[":
                        j = i + 1
                        while j < len(a) and a[j] == "[": j += 1
                        if a[j] == "L":
                            f = a.index(";", j)
                            params.append(f"{a[j+1:f].split('/')[-1]}*"); i = f + 1
                        else:
                            params.append("void*"); i = j + 1
                    else: i += 1

            ret_t = "void"
            if ")" in desc:
                r = desc.split(")")[-1]
                ret_t = {"V":"void","I":"int","J":"int64_t","Z":"int","F":"float","D":"double"}.get(r, "void*")

            linhas.append(f"// {c['nome']}.{nome_m}")
            linhas.append(f"{ret_t} {nome_final}({', '.join(params)}) {{")
            linhas.append("    // TODO: corpo (traduzir do bytecode)")
            if ret_t != "void":
                linhas.append("    return 0;")
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
    linhas.append(f"        // {estrutura['midlet']}_startApp(self);")
    linhas.append(f"        // {estrutura['canvas']}_paint(self);")
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
        print("Uso: python portador_gerar_v5.py <estrutura.json> <jogo.jar> [saida.c] [constantes.h]")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    jar = sys.argv[2]
    saida = sys.argv[3] if len(sys.argv) > 3 else "main_v5.c"
    const_path = sys.argv[4] if len(sys.argv) > 4 else "constantes.h"

    constantes = carregar_constantes(const_path)
    print(f"Constantes carregadas: {len(constantes)}")

    codigo = gerar_main_v5(estrutura, jar, constantes)
    with open(saida, "w") as f:
        f.write(codigo)
    print(f"Gerado: {saida} ({codigo.count(chr(10))} linhas)")

if __name__ == "__main__":
    main()
