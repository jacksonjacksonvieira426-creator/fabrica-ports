#!/usr/bin/env python3
"""
Analista de Estados - Le metodos de controle e mapeia fluxo do jogo.
Uso: python analista_estados.py <pasta_metodos>
"""
import sys, os, re, json

def analisar_metodo(caminho):
    """Detecta mudancas de estado (status =, mode =) e chamadas de acao."""
    with open(caminho) as f:
        linhas = f.readlines()
    
    eventos = []
    for linha in linhas:
        m = re.match(r'^\[\s*(\d+)\]\s+(.+)$', linha.strip())
        if not m: continue
        idx = int(m.group(1))
        instr = m.group(2)
        
        # PUTFIELD de status/mode
        if "putfield" in instr and ("status" in instr or "mode" in instr):
            eventos.append({"idx": idx, "tipo": "muda_estado", "campo": instr.split()[-1]})
        # Chamadas pra metodos de acao
        elif any(x in instr for x in ["punch", "kick", "fire", "reset", "forward", "backward"]):
            metodo = instr.split()[-1]
            eventos.append({"idx": idx, "tipo": "acao", "metodo": metodo})
        # Chamadas de tela
        elif any(x in instr for x in ["setCurrent", "repaint", "startApp"]):
            eventos.append({"idx": idx, "tipo": "controle", "chamada": instr.split()[-1]})
        # Fim de jogo
        elif "if_icmp" in instr or "ifeq" in instr:
            eventos.append({"idx": idx, "tipo": "condicao", "instrucao": instr})
    
    return eventos

def main():
    pasta = sys.argv[1]
    fluxo = {}
    
    # Procura por metodos que controlam estados
    for classe in os.listdir(pasta):
        p = os.path.join(pasta, classe)
        if not os.path.isdir(p): continue
        for arq in os.listdir(p):
            if not arq.endswith(".txt"): continue
            nome = arq[:-4]
            if any(x in nome for x in ["keyPressed", "keyProc", "commandAction", "run", "startApp"]):
                caminho = os.path.join(p, arq)
                eventos = analisar_metodo(caminho)
                if eventos:
                    fluxo[f"{classe}.{nome}"] = eventos
    
    print(json.dumps(fluxo, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
