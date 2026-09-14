#!/usr/bin/env python3
"""
Analisa todos os .jar de uma pasta, classifica por dificuldade,
e gera um ranking ordenado dos mais faceis para os mais dificeis.
Uso: python ranquear_jogos.py <pasta> [pasta_saida]
"""
import sys, os, json, glob, zipfile, io
from jawa.cf import ClassFile

FABRICANTES = ("com/nokia", "com/siemens", "com/motorola",
               "com/sonyericsson", "com/samsung", "com/lg",
               "com/microsoft", "com/jblend", "mmpp")

def analisar(jar):
    APIs = {}
    classes_internas = set()
    classes = metodos = 0
    try:
        z = zipfile.ZipFile(jar)
    except Exception:
        return None
    with z:
        for n in z.namelist():
            if n.endswith(".class"):
                classes_internas.add(n[:-6])
        for n in z.namelist():
            if not n.endswith(".class"):
                continue
            classes += 1
            try:
                cf = ClassFile(io.BytesIO(z.read(n)))
            except Exception:
                continue
            for m in list(cf.methods):
                metodos += 1
                if not m.code:
                    continue
                try:
                    instrs = list(m.code.disassemble())
                except Exception:
                    continue
                for i in instrs:
                    if i.mnemonic not in ("invokevirtual","invokestatic",
                                          "invokespecial","invokeinterface"):
                        continue
                    if not i.operands:
                        continue
                    try:
                        const = cf.constants.get(i.operands[0].value)
                        owner = const.class_.name.value
                        nome = const.name_and_type.name.value
                    except Exception:
                        continue
                    if owner in classes_internas:
                        continue
                    k = f"{owner}.{nome}"
                    APIs[k] = APIs.get(k, 0) + 1
    return {"classes": classes, "metodos": metodos, "apis": APIs}

def classificar(r):
    apis = r["apis"]
    total = len(apis)
    tem_threads = any("Thread" in a for a in apis)
    tem_timer = any("Timer" in a for a in apis)
    tem_audio = any(("Audio" in a or "Sound" in a or "Player" in a) for a in apis)
    tem_image = sum(1 for a in apis if "Image." in a)
    tem_nokia = any(a.startswith(FABRICANTES) for a in apis)
    tem_form = any("Form." in a or "TextField" in a for a in apis)
    tem_canvas = sum(1 for a in apis if "Canvas." in a)

    # Pontuacao de dificuldade (menor = mais facil)
    score = 0
    score += total                     # APIs
    score += r["classes"] * 3          # classes
    score += r["metodos"] // 2         # metodos
    if tem_threads: score += 40
    if tem_timer:   score += 20
    if tem_audio:   score += 30
    if tem_nokia:   score += 50
    if tem_form:    score += 15
    score += tem_image * 5             # uso de Image

    # Classificacao
    if score < 120: nivel = "SIMPLES"
    elif score < 250: nivel = "MEDIO"
    else: nivel = "COMPLEXO"

    return nivel, score, {
        "apis": total, "classes": r["classes"], "metodos": r["metodos"],
        "threads": tem_threads, "timer": tem_timer, "audio": tem_audio,
        "nokia": tem_nokia, "imagens": tem_image, "form": tem_form,
        "canvas": tem_canvas
    }

def main():
    if len(sys.argv) < 2:
        print("Uso: python ranquear_jogos.py <pasta_jars>")
        sys.exit(1)
    pasta = sys.argv[1]
    jars = sorted(glob.glob(os.path.join(pasta, "*.jar")))

    print(f"Analisando {len(jars)} jogos...\n")
    resultados = []

    for i, jar in enumerate(jars, 1):
        nome = os.path.basename(jar)
        print(f"[{i}/{len(jars)}] {nome[:45]:45s}", end=" ", flush=True)
        try:
            r = analisar(jar)
            if not r:
                print("FALHOU")
                continue
            nivel, score, info = classificar(r)
            tam_kb = os.path.getsize(jar) // 1024
            print(f"{nivel:9s} | score {score:4d} | {tam_kb:4d}KB")
            resultados.append({
                "jogo": nome, "nivel": nivel, "score": score,
                "tamanho_kb": tam_kb, **info
            })
        except Exception as e:
            print(f"ERRO: {e}")

    # Ordena por score (menor primeiro)
    resultados.sort(key=lambda x: x["score"])

    print("\n" + "=" * 80)
    print("RANKING (mais facil -> mais dificil)")
    print("=" * 80)
    print(f"{'#':>3} {'JOGO':<32} {'NIVEL':<9} {'SCORE':>5} {'KB':>5} {'API':>4} {'CLS':>4} {'T':>2} {'A':>2} {'N':>2} {'I':>3}")
    print("-" * 80)
    for i, r in enumerate(resultados, 1):
        print(f"{i:>3} {r['jogo'][:32]:<32} {r['nivel']:<9} {r['score']:>5} "
              f"{r['tamanho_kb']:>5} {r['apis']:>4} {r['classes']:>4} "
              f"{'T' if r['threads'] else '.':>2} "
              f"{'A' if r['audio'] else '.':>2} "
              f"{'N' if r['nokia'] else '.':>2} "
              f"{r['imagens']:>3}")

    # Salva JSON
    saida = os.path.join(pasta, "_ranking.json")
    with open(saida, "w") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\nRanking salvo em: {saida}")

    # Top 3 recomendados
    print("\n" + "=" * 80)
    print("TOP 3 MAIS FACEIS")
    print("=" * 80)
    for i, r in enumerate(resultados[:3], 1):
        print(f"\n{i}. {r['jogo']}")
        print(f"   Nivel: {r['nivel']}  |  Score: {r['score']}")
        print(f"   {r['apis']} APIs, {r['classes']} classes, {r['metodos']} metodos")
        print(f"   Tamanho: {r['tamanho_kb']} KB")
        flags = []
        if r['threads']: flags.append("Threads")
        if r['audio']: flags.append("Audio")
        if r['nokia']: flags.append("Nokia API")
        if flags: print(f"   Aviso: {', '.join(flags)}")
        else: print(f"   Limpo (sem threads/audio/nokia)")

if __name__ == "__main__":
    main()
