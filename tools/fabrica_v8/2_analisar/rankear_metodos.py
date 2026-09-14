#!/usr/bin/env python3
"""
Rankeia metodos por importancia pra traducao.
Prioridade alta: paint, keyPressed, run, reset, init
Prioridade baixa: getters/setters
"""
import sys, os, re

PRIORIDADE = {
    "paint": 100,
    "keyPressed": 95, "keyProc": 95, "keyRepeated": 90,
    "run": 85,
    "init": 80,
    "reset": 75,
    "startApp": 70, "constructor": 65,
    "forward": 60, "backward": 60, "punch": 60, "kick": 60, "fire": 60,
}

def rankear(pasta):
    metodos = []
    for classe in sorted(os.listdir(pasta)):
        p_cls = os.path.join(pasta, classe)
        if not os.path.isdir(p_cls): continue
        for arq in sorted(os.listdir(p_cls)):
            if not arq.endswith(".txt"): continue
            nome = arq[:-4]
            caminho = os.path.join(p_cls, arq)
            with open(caminho) as f:
                conteudo = f.read()
            # Conta instrucoes
            n = len(re.findall(r'^\[\s*\d+\]', conteudo, re.MULTILINE))
            # Prioridade
            pri = 0
            for k, v in PRIORIDADE.items():
                if k in nome: pri = max(pri, v)
            metodos.append({
                "classe": classe,
                "metodo": nome,
                "instrucoes": n,
                "prioridade": pri,
                "caminho": caminho,
            })
    # Ordena: prioridade DESC, instrucoes ASC
    metodos.sort(key=lambda x: (-x["prioridade"], x["instrucoes"]))
    return metodos

def main():
    pasta = sys.argv[1]
    metodos = rankear(pasta)
    print(f"{'PRI':>3} {'INS':>4} {'CLASSE':<20} {'METODO':<30}")
    print("-" * 65)
    for m in metodos[:40]:
        print(f"{m['prioridade']:>3} {m['instrucoes']:>4} {m['classe']:<20} {m['metodo']:<30}")

if __name__ == "__main__":
    main()
