#!/usr/bin/env python3
"""
Analisa um JAR e gera estrutura.json com:
- Classes e hierarquia
- Campos com tipos
- Métodos com bytecode resumido
- Padroes detectados (MIDlet, Canvas, GameLoop, etc)
"""
import sys, os, json, zipfile, io
from jawa.cf import ClassFile

# Mapeamento de tipos J2ME -> C
TIPOS_J2ME = {
    "I": "int", "J": "int64_t", "S": "short", "B": "signed char",
    "Z": "int", "C": "unsigned short", "F": "float", "D": "double",
    "V": "void",
}

def tipo_para_c(desc):
    """Converte descritor J2ME (ex: '[I', 'Ljava/lang/String;') em tipo C."""
    if desc.startswith("["):
        base = desc[1:]
        if base.startswith("["):
            return f"{tipo_para_c(base)}*"
        return f"{tipo_para_c(base)}*"
    if desc.startswith("L"):
        nome = desc[1:-1].split("/")[-1]
        return f"{nome}*"
    return TIPOS_J2ME.get(desc, "int*")

def detectar_padroes(super_class, metodos, campos, apis):
    """Detecta qual tipo de classe eh essa (MIDlet, Canvas, etc)."""
    padroes = []
    nomes_metodos = {m[0] for m in metodos}

    if super_class == "MIDlet":
        padroes.append("MIDLET")
    if super_class in ("Canvas", "FullCanvas", "GameCanvas"):
        padroes.append("CANVAS")
    if "paint" in nomes_metodos:
        padroes.append("TEM_PAINT")
    if "keyPressed" in nomes_metodos or "keyProc" in nomes_metodos:
        padroes.append("TEM_INPUT")
    if "run" in nomes_metodos:
        padroes.append("TEM_RUN")
    if "startApp" in nomes_metodos:
        padroes.append("TEM_STARTAPP")
    if any("Timer" in a for a in apis):
        padroes.append("USA_TIMER")
    if any("Image." in a for a in apis):
        padroes.append("USA_IMAGE")
    return padroes

def analisar_classe(cf, nome_arquivo, classes_internas):
    """Extrai info de uma classe."""
    # Super classe - tenta multiplas APIs do jawa
    super_nome = "Object"
    try:
        sc = cf.super_class
        if sc is None:
            super_nome = "Object"
        elif hasattr(sc, 'name'):
            super_nome = sc.name.value.split("/")[-1]
        elif hasattr(sc, 'value'):
            super_nome = sc.value.split("/")[-1]
        else:
            super_nome = str(sc).split("/")[-1].split("'")[0]
    except Exception as e:
        pass
    # Fallback: procura no pool por "MIDlet" ou "Canvas"
    try:
        for const in cf.constants:
            if hasattr(const, 'name') and hasattr(const.name, 'value'):
                v = const.name.value
                if v.endswith("/MIDlet") or v == "MIDlet":
                    super_nome = "MIDlet"
                    break
                if v.endswith("/Canvas") or v.endswith("/FullCanvas") or v == "Canvas":
                    super_nome = "Canvas"
                    break
    except Exception:
        pass

    # Campos
    campos = []
    for c in list(cf.fields):
        campos.append({
            "nome": c.name.value,
            "desc": c.descriptor.value,
            "tipo_c": tipo_para_c(c.descriptor.value),
        })

    # Métodos + APIs usadas
    metodos = []
    todas_apis = {}
    for m in list(cf.methods):
        nome_m = m.name.value
        desc_m = m.descriptor.value
        apis_m = {}
        n_instr = 0

        if m.code:
            try:
                instrs = list(m.code.disassemble())
                n_instr = len(instrs)
                for i in instrs:
                    if i.mnemonic not in ("invokevirtual","invokestatic",
                                          "invokespecial","invokeinterface"):
                        continue
                    if not i.operands: continue
                    try:
                        const = cf.constants.get(i.operands[0].value)
                        owner = const.class_.name.value
                        nome_met = const.name_and_type.name.value
                    except Exception:
                        continue
                    if owner in classes_internas: continue
                    k = f"{owner}.{nome_met}"
                    apis_m[k] = apis_m.get(k, 0) + 1
                    todas_apis[k] = todas_apis.get(k, 0) + 1
            except Exception:
                pass

        metodos.append({
            "nome": nome_m,
            "desc": desc_m,
            "tipo_ret": tipo_para_c(desc_m.split(")")[-1]) if ")" in desc_m else "void",
            "n_instr": n_instr,
            "apis": apis_m,
        })

    padroes = detectar_padroes(super_nome, [(m["nome"], m["desc"]) for m in metodos],
                                campos, todas_apis)

    return {
        "arquivo": nome_arquivo,
        "nome": nome_arquivo[:-6].split("/")[-1],
        "super": super_nome,
        "campos": campos,
        "metodos": metodos,
        "apis": todas_apis,
        "padroes": padroes,
    }

def analisar(jar_path):
    z = zipfile.ZipFile(jar_path)
    classes_internas = set()
    for n in z.namelist():
        if n.endswith(".class"):
            classes_internas.add(n[:-6])

    classes = []
    for n in sorted(z.namelist()):
        if not n.endswith(".class"): continue
        try:
            cf = ClassFile(io.BytesIO(z.read(n)))
            info = analisar_classe(cf, n, classes_internas)
            classes.append(info)
        except Exception as e:
            print(f"  ERRO em {n}: {e}")

    # Detectar classe principal (MIDlet)
    midlet = None
    canvas = None
    for c in classes:
        if "MIDLET" in c["padroes"] and not midlet:
            midlet = c["nome"]
        if "CANVAS" in c["padroes"] and not canvas:
            canvas = c["nome"]

    estrutura = {
        "jar": os.path.basename(jar_path),
        "nome_projeto": os.path.splitext(os.path.basename(jar_path))[0].lower().replace(" ", "_"),
        "midlet": midlet,
        "canvas": canvas,
        "classes": classes,
        "n_classes": len(classes),
    }
    return estrutura

def main():
    if len(sys.argv) < 2:
        print("Uso: python portador_analisar.py <arquivo.jar> [saida.json]")
        sys.exit(1)

    jar = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(jar)[0] + "_estrutura.json"

    print(f"Analisando {jar}...")
    estrutura = analisar(jar)

    with open(saida, "w") as f:
        json.dump(estrutura, f, indent=2, ensure_ascii=False)

    print(f"\n=== RESUMO ===")
    print(f"Projeto: {estrutura['nome_projeto']}")
    print(f"Classes: {estrutura['n_classes']}")
    print(f"MIDlet: {estrutura['midlet']}")
    print(f"Canvas: {estrutura['canvas']}")
    print(f"\nClasses detectadas:")
    for c in estrutura["classes"]:
        padroes = ", ".join(c["padroes"]) if c["padroes"] else "-"
        print(f"  {c['nome']:<30} extends {c['super']:<20} [{padroes}]")
    print(f"\nSalvo em: {saida}")

if __name__ == "__main__":
    main()
