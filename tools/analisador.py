import sys, json, zipfile, io, os

def analisar_jar(caminho_jar):
    APIs = {}
    classes = 0
    metodos = 0
    try:
        z = zipfile.ZipFile(caminho_jar)
    except Exception as e:
        print(f"ERRO ao abrir {caminho_jar}: {e}")
        return None

    with z:
        for nome in z.namelist():
            if not nome.endswith(".class"):
                continue
            classes += 1
            try:
                from jawa.cf import ClassFile
                cf = ClassFile(io.BytesIO(z.read(nome)))
            except Exception:
                continue
            for metodo in cf.methods:
                metodos += 1
                if not metodo.code:
                    continue
                for instr in metodo.code.disassemble():
                    if instr.mnemonic not in ("invokevirtual","invokestatic",
                                              "invokespecial","invokeinterface"):
                        continue
                    try:
                        owner = instr.operands[0].name.value
                        nome_metodo = instr.operands[1].value
                    except Exception:
                        continue
                    chave = f"{owner}.{nome_metodo}"
                    APIs[chave] = APIs.get(chave, 0) + 1
    return {"classes": classes, "metodos": metodos, "apis": APIs}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python analisador.py jogo.jar")
        sys.exit(1)
    r = analisar_jar(sys.argv[1])
    if not r:
        sys.exit(1)
    nome_base = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    saida = f"../relatorios/{nome_base}.json"
    with open(saida, "w") as f:
        json.dump(r, f, indent=2, ensure_ascii=False)
    print(f"Classes: {r['classes']} | Metodos: {r['metodos']} | APIs distintas: {len(r['apis'])}")
    print(f"Relatorio salvo em: {saida}")
    print("\nTop 15 APIs mais usadas:")
    for api, c in sorted(r["apis"].items(), key=lambda x: -x[1])[:15]:
        print(f"  {c:4d}x  {api}")
