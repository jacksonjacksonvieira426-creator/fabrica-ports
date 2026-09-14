#!/usr/bin/env python3
import sys, os, subprocess

BASE = os.path.expanduser("~/fabrica-ports")
FABRICA = os.path.join(BASE, "tools", "fabrica_v8")

def rodar(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def main():
    if len(sys.argv) < 2:
        print("Uso: python fabrica.py <jogo.jar>")
        sys.exit(1)
    
    jar = sys.argv[1]
    nome = os.path.splitext(os.path.basename(jar))[0].lower().replace(" ", "_")
    pasta_proj = os.path.join(BASE, "ports", nome)
    pasta_metodos = os.path.join(pasta_proj, "_metodos")
    
    print(f"=== FABRICA V8: {nome} ===\n")
    
    print("[1/6] Gerando projeto V5...")
    rodar(f"python {BASE}/tools/portador.py '{jar}'")
    
    print("[2/6] Extraindo metodos...")
    rodar(f"python {FABRICA}/1_extrair/extrair_metodos.py '{jar}' '{pasta_metodos}'")
    
    print("[3/6] Rankeando metodos...")
    r = rodar(f"python {FABRICA}/2_analisar/rankear_metodos.py '{pasta_metodos}'")
    print(r.stdout[:800])
    
    print("\n[4/6] Gerando briefing...")
    rodar(f"python {FABRICA}/3_analisar/relator.py '{pasta_metodos}' '{pasta_proj}'")
    
    print("\n[5/6] Analisando cenario (paint)...")
    paint = os.path.join(pasta_metodos, "MapCanvas", "paint.txt")
    if os.path.exists(paint):
        r = rodar(f"python {FABRICA}/3_analisar/analista_cenario.py '{paint}'")
        print(r.stdout[:600])
    
    print("\n[6/6] Analisando estados (keyProc/run)...")
    rodar(f"python {FABRICA}/3_analisar/analista_estados.py '{pasta_metodos}'")
    
    print(f"\n=== PRONTO ===")
    print(f"Projeto: {pasta_proj}")
    print(f"Metodos: {pasta_metodos}")
    print(f"Briefing: {pasta_proj}/briefing.json")
    print(f"\nPra traduzir um metodo:")
    print(f"  python {FABRICA}/3_analisar/tradutor_ia.py {pasta_metodos}/Role_Ryu/reset.txt")

if __name__ == "__main__":
    main()
