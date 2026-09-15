#!/usr/bin/env python3
"""
Batch Porter - Processa varios JARs de uma vez.
Uso: python batch_porter.py <pasta_jars>
"""
import sys, os, subprocess, glob

BASE = os.path.expanduser("~/fabrica-ports")
FABRICA = os.path.join(BASE, "tools", "fabrica_v8")

def main():
    if len(sys.argv) < 2:
        print("Uso: python batch_porter.py <pasta_jars>")
        sys.exit(1)
    
    pasta = sys.argv[1]
    jars = sorted(glob.glob(os.path.join(pasta, "*.jar")))
    
    print(f"=== BATCH PORTER ===")
    print(f"Processando {len(jars)} jogos\n")
    
    resultados = []
    for i, jar in enumerate(jars, 1):
        nome = os.path.basename(jar)
        print(f"[{i}/{len(jars)}] {nome}")
        r = subprocess.run(
            f"python {FABRICA}/fabrica.py '{jar}'",
            shell=True, capture_output=True, text=True
        )
        if r.returncode == 0:
            resultados.append((nome, "OK"))
            print(f"  ✓ Projeto gerado")
        else:
            resultados.append((nome, "ERRO"))
            print(f"  ✗ {r.stderr[:100]}")
    
    print(f"\n{'='*60}")
    print(f"RESUMO: {sum(1 for _, s in resultados if s == 'OK')}/{len(jars)} projetos gerados")
    print(f"{'='*60}")
    
    for nome, status in resultados:
        print(f"  [{status}] {nome}")

if __name__ == "__main__":
    main()
