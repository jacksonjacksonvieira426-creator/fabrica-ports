import sys, os, json, glob, zipfile, io
from jawa.cf import ClassFile

FABRICANTES = ("com/nokia", "com/siemens", "com/motorola", "com/sonyericsson",
               "com/samsung", "com/lg", "com/microsoft", "com/jblend",
               "com/sprintpcs", "com/nttdocomo", "mmpp", "com/nokia/mid")

def resolver_constante(cf, idx):
    try:
        return cf.constants.get(idx)
    except Exception:
        return None

def analisar_jar(caminho):
    APIs, classes, metodos = {}, 0, 0
    classes_internas = set()
    try:
        z = zipfile.ZipFile(caminho)
    except Exception:
        return None
    with z:
        # 1) Primeiro passo: descobrir nomes internos das classes do jogo
        for nome in z.namelist():
            if nome.endswith(".class"):
                classes_internas.add(nome[:-6])  # remove ".class"

        # 2) Segundo passo: analisar bytecode
        for nome in z.namelist():
            if not nome.endswith(".class"):
                continue
            classes += 1
            try:
                cf = ClassFile(io.BytesIO(z.read(nome)))
            except Exception:
                continue
            for metodo in list(cf.methods):
                metodos += 1
                if not metodo.code:
                    continue
                try:
                    instrs = list(metodo.code.disassemble())
                except Exception:
                    continue
                for instr in instrs:
                    if instr.mnemonic not in ("invokevirtual","invokestatic",
                                              "invokespecial","invokeinterface"):
                        continue
                    if not instr.operands:
                        continue
                    idx = instr.operands[0].value
                    const = resolver_constante(cf, idx)
                    if not const:
                        continue
                    try:
                        owner = const.class_.name.value
                        nome_m = const.name_and_type.name.value
                    except Exception:
                        continue
                    # Pula classes internas do proprio jogo
                    if owner in classes_internas:
                        continue
                    chave = f"{owner}.{nome_m}"
                    APIs[chave] = APIs.get(chave, 0) + 1
    return {"classes": classes, "metodos": metodos, "apis": APIs}

def classificar(r):
    apis = r["apis"]
    total = len(apis)
    tem_threads = any("Thread" in a for a in apis)
    tem_audio = any(("Audio" in a or "Sound" in a or "Player" in a) for a in apis)
    tem_proprietaria = any(a.startswith(FABRICANTES) for a in apis)
    if total < 40 and not tem_threads and not tem_audio and not tem_proprietaria:
        return "SIMPLES", tem_threads, tem_audio, tem_proprietaria, total
    elif total < 120 and not tem_proprietaria:
        return "MEDIO", tem_threads, tem_audio, tem_proprietaria, total
    else:
        return "COMPLEXO", tem_threads, tem_audio, tem_proprietaria, total

def main():
    if len(sys.argv) < 3:
        print("Uso: python analisar_lote.py <pasta_jars> <pasta_saida>")
        sys.exit(1)
    pasta_in, pasta_out = sys.argv[1], sys.argv[2]
    os.makedirs(pasta_out, exist_ok=True)
    jars = sorted(glob.glob(os.path.join(pasta_in, "*.jar")))
    print(f"Encontrados {len(jars)} arquivos .jar\n")
    resumo = []
    for i, jar in enumerate(jars, 1):
        nome = os.path.basename(jar)
        print(f"[{i}/{len(jars)}] {nome[:40]:40s}", end=" ", flush=True)
        try:
            r = analisar_jar(jar)
            if not r:
                print("FALHOU")
                continue
            nivel, t, a, p, total = classificar(r)
            nome_base = os.path.splitext(nome)[0]
            with open(os.path.join(pasta_out, nome_base + ".json"), "w") as f:
                json.dump(r, f, indent=2, ensure_ascii=False)
            print(f"{nivel:9s} | {total:4d} APIs | T:{int(t)} A:{int(a)} P:{int(p)}")
            resumo.append({"jogo": nome, "nivel": nivel, "apis": total,
                           "classes": r["classes"], "metodos": r["metodos"],
                           "threads": t, "audio": a, "proprietaria": p})
        except Exception as e:
            print(f"ERRO: {e}")
    with open(os.path.join(pasta_out, "_resumo.json"), "w") as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)
    print("\n=== RESUMO ===")
    for nivel in ("SIMPLES", "MEDIO", "COMPLEXO"):
        q = sum(1 for x in resumo if x["nivel"] == nivel)
        print(f"{nivel:9s}: {q}")
    print(f"Total    : {len(resumo)}")

if __name__ == "__main__":
    main()
