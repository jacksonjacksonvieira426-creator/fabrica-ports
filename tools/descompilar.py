#!/usr/bin/env python3
"""
Descompilador minimo de .class J2ME para pseudo-C legivel.
Nao substitui o JAD/CFR, mas da pra entender a logica do jogo.
"""
import sys, zipfile, io
from jawa.cf import ClassFile

def resolver(cf, idx):
    try: return cf.constants.get(idx)
    except: return None

def traduzir_instr(instr, cf, classes_internas):
    m = instr.mnemonic
    ops = instr.operands

    # Constantes diretas
    if m == "iconst_0": return "0"
    if m == "iconst_1": return "1"
    if m == "iconst_2": return "2"
    if m == "iconst_3": return "3"
    if m == "iconst_4": return "4"
    if m == "iconst_5": return "5"
    if m == "iconst_m1": return "-1"
    if m == "bipush":  return str(ops[0].value)
    if m == "sipush":  return str(ops[0].value)
    if m == "ldc" or m == "ldc_w":
        const = resolver(cf, ops[0].value)
        if const and hasattr(const, 'value'):
            v = const.value
            if hasattr(v, 'value'):
                return f'"{v.value}"' if isinstance(v.value, str) else str(v.value)
        return f"<const {ops[0].value}>"

    # Metodos
    if m in ("invokevirtual", "invokestatic", "invokespecial", "invokeinterface"):
        const = resolver(cf, ops[0].value)
        if const:
            owner = const.class_.name.value
            nome  = const.name_and_type.name.value
            # Encurta o nome da classe
            short = owner.split("/")[-1]
            return f"CALL {short}.{nome}"
        return f"CALL <ref {ops[0].value}>"

    # Campos
    if m in ("getfield", "putfield", "getstatic", "putstatic"):
        const = resolver(cf, ops[0].value)
        if const:
            owner = const.class_.name.value
            nome  = const.name_and_type.name.value
            short = owner.split("/")[-1]
            return f"{m.upper()} {short}.{nome}"
        return f"{m.upper()} <ref {ops[0].value}>"

    # Controle
    if m.startswith("if"):
        return f"{m} +{ops[0].value}"
    if m == "goto":
        return f"goto +{ops[0].value}"

    return m

def descompilar_metodo(cf, metodo, classes_internas):
    nome = metodo.name.value
    desc = metodo.descriptor.value
    print(f"\n    // === {nome} {desc} ===")

    if not metodo.code:
        print("      // (metodo abstrato/nativo)")
        return

    try:
        instrs = list(metodo.code.disassemble())
    except:
        print("      // (nao consegui descompilar)")
        return

    for i, instr in enumerate(instrs):
        linha = traduzir_instr(instr, cf, classes_internas)
        print(f"      [{i:3d}] {linha}")

def descompilar_jar(caminho):
    z = zipfile.ZipFile(caminho)
    classes_internas = set()
    for n in z.namelist():
        if n.endswith(".class"):
            classes_internas.add(n[:-6])

    for n in sorted(z.namelist()):
        if not n.endswith(".class"): continue
        print(f"\n{'='*60}")
        print(f"CLASSE: {n}")
        print(f"{'='*60}")
        try:
            cf = ClassFile(io.BytesIO(z.read(n)))
        except Exception as e:
            print(f"  ERRO: {e}")
            continue

        # Campos
        campos = list(cf.fields)
        if campos:
            print("\n  CAMPOS:")
            for c in campos:
                print(f"    {c.name.value} {c.descriptor.value}")

        # Metodos
        print("\n  METODOS:")
        for metodo in list(cf.methods):
            descompilar_metodo(cf, metodo, classes_internas)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python descompilar.py <arquivo.jar>")
        sys.exit(1)
    descompilar_jar(sys.argv[1])
