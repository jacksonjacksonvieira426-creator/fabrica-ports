#!/usr/bin/env python3
"""
PRODUCAO - Pipeline completo V8+V9 num comando.
Uso: python producao.py <pasta_jars>
"""
import sys, os, subprocess, glob, json

BASE = os.path.expanduser("~/fabrica-ports")
FAB8 = os.path.join(BASE, "tools", "fabrica_v8")
FAB9 = os.path.join(BASE, "tools", "fabrica_v9")

def rodar(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def processar_jar(jar):
    nome = os.path.splitext(os.path.basename(jar))[0].lower().replace(" ", "_")
    print(f"\n{'='*60}")
    print(f"PROCESSANDO: {nome}")
    print(f"{'='*60}\n")
    
    pasta_proj = os.path.join(BASE, "ports", nome)
    pasta_metodos = os.path.join(pasta_proj, "_metodos")
    
    # 1. Gera projeto V5
    print("[1/7] Gerando projeto base...")
    r = rodar(f"python {BASE}/tools/portador.py '{jar}'")
    if not os.path.exists(pasta_proj):
        print("  ✗ Falha")
        return None
    
    # 2. Extrai metodos
    print("[2/7] Extraindo metodos...")
    rodar(f"python {FAB8}/1_extrair/extrair_metodos.py '{jar}' '{pasta_metodos}'")
    
    # 3. Rankeia
    print("[3/7] Rankeando metodos...")
    r = rodar(f"python {FAB8}/2_analisar/rankear_metodos.py '{pasta_metodos}'")
    
    # 4. Gera briefing
    print("[4/7] Gerando briefing...")
    rodar(f"python {FAB8}/3_analisar/relator.py '{pasta_metodos}' '{pasta_proj}'")
    
    # 5. Detecta dependencias
    print("[5/7] Analisando dependencias...")
    r = rodar(f"python {FAB8}/3_analisar/detector_dependencias.py '{pasta_metodos}'")
    # Pega os 10 primeiros (folhas)
    top10 = []
    for l in r.stdout.split("\n"):
        if ". " in l and "deps" in l:
            try:
                partes = l.split()
                met = [p for p in partes if "." in p and "de" not in p]
                if met: top10.append(met[0])
            except: pass
    
    # 6. Gera main() automatico
    print("[6/7] Gerando main()...")
    estrutura = os.path.join(pasta_proj, "estrutura.json")
    if os.path.exists(estrutura):
        r = rodar(f"python {FAB8}/4_injetar/gerador_main.py '{estrutura}'")
        if r.stdout:
            # Salva o main gerado
            with open(os.path.join(pasta_proj, "_main_gerado.txt"), "w") as f:
                f.write(r.stdout)
    
    # 7. Layout e calibracao (V9)
    print("[7/7] Aplicando layout...")
    r = rodar(f"python {FAB9}/auto_layout.py 2 480 240")
    
    return {
        "nome": nome,
        "pasta": pasta_proj,
        "n_metodos": len(os.listdir(pasta_metodos)) if os.path.exists(pasta_metodos) else 0,
        "top10": top10[:10],
        "main_gerado": os.path.exists(os.path.join(pasta_proj, "_main_gerado.txt")),
    }

def main():
    if len(sys.argv) < 2:
        print("Uso: python producao.py <pasta_jars>")
        sys.exit(1)
    
    pasta = sys.argv[1]
    jars = sorted(glob.glob(os.path.join(pasta, "*.jar")))
    
    print(f"{'='*60}")
    print(f"PRODUCAO EM LOTE - {len(jars)} jogos")
    print(f"{'='*60}")
    
    resultados = []
    for jar in jars:
        r = processar_jar(jar)
        if r: resultados.append(r)
    
    # Resumo
    print(f"\n{'='*60}")
    print(f"RESUMO FINAL")
    print(f"{'='*60}\n")
    for r in resultados:
        print(f"  [{r['nome']}]")
        print(f"    Pasta: {r['pasta']}")
        print(f"    Metodos: {r['n_metodos']}")
        print(f"    main() gerado: {'sim' if r['main_gerado'] else 'nao'}")
        if r['top10']:
            print(f"    Top metodos: {', '.join(r['top10'][:5])}")
        print()
    
    print(f"Total processados: {len(resultados)}")

if __name__ == "__main__":
    main()
