#!/usr/bin/env python3
"""
Extrai valores de <clinit> e <init> de todas as classes.
Gera um arquivo de #defines legiveis.
"""
import sys, zipfile, io, json
from jawa.cf import ClassFile

def extrair(jar_path):
    """Extrai constantes estaticas do <clinit> de cada classe."""
    z = zipfile.ZipFile(jar_path)
    constantes = {}   # classe -> [(campo, valor, tipo)]

    for n in z.namelist():
        if not n.endswith(".class"): continue
        try:
            cf = ClassFile(io.BytesIO(z.read(n)))
        except: continue
        nome_cls = n[:-6].split("/")[-1]

        # Lista campos estaticos
        campos_estaticos = []
        for c in list(cf.fields):
            try:
                flags = c.access_flags
                # Tenta converter pra int
                if hasattr(flags, 'value'):
                    flags_int = flags.value
                elif hasattr(flags, '__int__'):
                    flags_int = int(flags)
                else:
                    flags_int = 0
                if flags_int & 0x0008:  # ACC_STATIC
                    campos_estaticos.append(c.name.value)
            except Exception:
                # Se der erro, inclui todos
                campos_estaticos.append(c.name.value)

        # Acha <clinit>
        for m in list(cf.methods):
            if m.name.value != "<clinit>": continue
            if not m.code: continue

            # Simula a pilha: valores empilhados + putstatic
            try:
                instrs = list(m.code.disassemble())
            except: continue

            pilha = []
            for instr in instrs:
                mn = instr.mnemonic
                ops = instr.operands

                # Empilha constantes
                if mn.startswith("iconst_") and mn != "iconst_m1":
                    pilha.append(int(mn.split("_")[1]))
                elif mn == "iconst_m1": pilha.append(-1)
                elif mn == "bipush" and ops: pilha.append(ops[0].value)
                elif mn == "sipush" and ops: pilha.append(ops[0].value)
                elif mn in ("ldc","ldc_w") and ops:
                    try:
                        const = cf.constants.get(ops[0].value)
                        # Tenta varios atributos
                        v = None
                        if hasattr(const, 'value'):
                            inner = const.value
                            if hasattr(inner, 'value'):
                                v = inner.value
                            else:
                                v = inner
                        if v is None:
                            v = 0
                        # Se for string numerica, converte
                        if isinstance(v, str):
                            try:
                                v = int(v)
                            except ValueError:
                                pass
                        pilha.append(v)
                    except:
                        pilha.append(0)
                elif mn == "ldc2_w" and ops:
                    try:
                        const = cf.constants.get(ops[0].value)
                        v = 0
                        if hasattr(const, 'value'):
                            inner = const.value
                            if hasattr(inner, 'high') and hasattr(inner, 'low'):
                                v = (inner.high << 32) | (inner.low & 0xFFFFFFFF)
                            elif hasattr(inner, 'value'):
                                v = inner.value
                        pilha.append(v)
                    except:
                        pilha.append(0)
                elif mn in ("lconst_0","lconst_1"):
                    pilha.append(0 if mn == "lconst_0" else 1)
                elif mn == "putstatic" and ops:
                    try:
                        const = cf.constants.get(ops[0].value)
                        campo = const.name_and_type.name.value
                        cls = const.class_.name.value.split("/")[-1]
                        v = pilha.pop() if pilha else 0
                        constantes.setdefault(cls, []).append((campo, v))
                    except: pass
                elif mn in ("iadd","isub","imul","idiv"):
                    if len(pilha) >= 2:
                        b = pilha.pop(); a = pilha.pop()
                        if mn == "iadd": pilha.append(a + b)
                        elif mn == "isub": pilha.append(a - b)
                        elif mn == "imul": pilha.append(a * b)
                        elif mn == "idiv" and b != 0: pilha.append(a // b)
                # Ignora o resto

    return constantes

def gerar_header(constantes, nome_proj):
    linhas = []
    linhas.append(f"// {nome_proj}_constantes.h")
    linhas.append("// Constantes extraidas automaticamente do bytecode")
    linhas.append("")
    linhas.append("#ifndef _CONSTANTES_H")
    linhas.append("#define _CONSTANTES_H")
    linhas.append("")
    for cls, campos in sorted(constantes.items()):
        linhas.append(f"// === {cls} ===")
        for campo, valor in campos:
            # Sanitiza
            nome = campo
            if not all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
                cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
                nome = f"ofusc_{cp:04x}"
            if isinstance(valor, int):
                linhas.append(f"#define {cls}_{nome} {valor}")
            else:
                linhas.append(f"#define {cls}_{nome} {valor}")
        linhas.append("")
    linhas.append("#endif")
    return "\n".join(linhas)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python extrair_constantes.py <jogo.jar> [saida.h]")
        sys.exit(1)
    jar = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else "constantes.h"
    constantes = extrair(jar)
    with open(saida, "w") as f:
        f.write(gerar_header(constantes, "jogo"))
    total = sum(len(v) for v in constantes.values())
    print(f"Extraidas {total} constantes de {len(constantes)} classes")
    print(f"Salvo em: {saida}")
    for cls, campos in sorted(constantes.items()):
        if campos:
            print(f"\n{cls}:")
            for c, v in campos[:8]:
                print(f"  {c} = {v}")
