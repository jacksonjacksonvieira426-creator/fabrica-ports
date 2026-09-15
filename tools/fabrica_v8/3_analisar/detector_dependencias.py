#!/usr/bin/env python3
"""
Detector de Dependencias - Mapeia quem chama quem.
Diz a ordem correta de traducao (bottom-up).
Uso: python detector_dependencias.py <pasta_metodos>
"""
import sys, os, re

def analisar(pasta):
    deps = {}  # metodo -> [metodos que ele chama]
    
    for classe in os.listdir(pasta):
        p = os.path.join(pasta, classe)
        if not os.path.isdir(p): continue
        for arq in os.listdir(p):
            if not arq.endswith(".txt"): continue
            metodo = f"{classe}.{arq[:-4]}"
            with open(os.path.join(p, arq)) as f:
                conteudo = f.read()
            
            # Encontra chamadas internas (invokevirtual Classe.metodo)
            chamadas = re.findall(r'invoke\w*\s+(\w+)\.(\w+)', conteudo)
            deps[metodo] = [f"{c}.{m}" for c, m in chamadas 
                            if c != classe or m != arq[:-4]]  # ignora recursao
    
    return deps

def ordenar_topologico(deps):
    """Ordena metodos pra traducao (folhas primeiro)."""
    visitados = set()
    ordem = []
    
    def visitar(m):
        if m in visitados or m not in deps: return
        visitados.add(m)
        for dep in deps[m]:
            visitar(dep)
        ordem.append(m)
    
    for m in deps:
        visitar(m)
    
    return ordem

def main():
    if len(sys.argv) < 2:
        print("Uso: python detector_dependencias.py <pasta_metodos>")
        sys.exit(1)
    
    deps = analisar(sys.argv[1])
    ordem = ordenar_topologico(deps)
    
    print(f"\n{'='*60}")
    print("ORDEM DE TRADUCAO (bottom-up)")
    print(f"{'='*60}\n")
    
    for i, m in enumerate(ordem, 1):
        n_deps = len(deps.get(m, []))
        print(f"  {i:3d}. {m:<40} ({n_deps} deps)")
    
    print(f"\nSugestao: comece pelos primeiros 5 (folhas).")

if __name__ == "__main__":
    main()
