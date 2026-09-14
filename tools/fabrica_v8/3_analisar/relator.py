#!/usr/bin/env python3
import sys, os, json

def main():
    pasta_metodos = sys.argv[1]
    pasta_saida = sys.argv[2] if len(sys.argv) > 2 else pasta_metodos
    os.makedirs(pasta_saida, exist_ok=True)
    
    briefing = {
        "jogo": os.path.basename(pasta_metodos).replace("_metodos", ""),
        "classes": {},
        "metodos_criticos": [],
    }
    
    for classe in sorted(os.listdir(pasta_metodos)):
        p = os.path.join(pasta_metodos, classe)
        if not os.path.isdir(p): continue
        
        metodos = []
        for arq in sorted(os.listdir(p)):
            if not arq.endswith(".txt"): continue
            with open(os.path.join(p, arq)) as f:
                conteudo = f.read()
            n = len([l for l in conteudo.split("\n") if l.startswith("[")])
            metodos.append({"nome": arq[:-4], "instrucoes": n})
        
        briefing["classes"][classe] = metodos
        
        for m in metodos:
            if any(x in m["nome"] for x in ["paint", "keyPressed", "keyProc", "run"]):
                briefing["metodos_criticos"].append({
                    "classe": classe,
                    "metodo": m["nome"],
                    "instrucoes": m["instrucoes"],
                })
    
    briefing["metodos_criticos"].sort(key=lambda x: x["instrucoes"])
    
    saida = os.path.join(pasta_saida, "briefing.json")
    with open(saida, "w") as f:
        json.dump(briefing, f, indent=2, ensure_ascii=False)
    
    print(f"Briefing: {saida}")
    print(f"Classes: {len(briefing['classes'])}")
    print(f"Total metodos: {sum(len(v) for v in briefing['classes'].values())}")
    print(f"Metodos criticos: {len(briefing['metodos_criticos'])}")
    print("\nTop 5 criticos:")
    for m in briefing["metodos_criticos"][:5]:
        print(f"  {m['instrucoes']:4d} ins - {m['classe']}.{m['metodo']}")

if __name__ == "__main__":
    main()
