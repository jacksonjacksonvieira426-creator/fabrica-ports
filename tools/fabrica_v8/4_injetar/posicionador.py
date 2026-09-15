#!/usr/bin/env python3
"""
Posicionador - Le reset() de cada personagem e extrai posicoes iniciais.
Gera codigo C pronto pra colar no main.c.
Uso: python posicionador.py <pasta_metodos>
"""
import sys, os, re

def extrair_constantes_reset(caminho):
    """Le reset.txt e extrai (campo, valor) das atribuicoes."""
    atribuicoes = []
    with open(caminho) as f:
        linhas = f.readlines()
    
    # Simula pilha simples
    pilha = []
    for l in linhas:
        m = re.match(r'^\[\s*(\d+)\]\s+(.+)$', l.strip())
        if not m: continue
        instr = m.group(2).strip()
        
        # Constantes
        if instr.startswith("iconst_"):
            v = instr.replace("iconst_", "").replace("m1", "-1")
            pilha.append(v)
        elif instr.startswith("bipush "):
            pilha.append(instr.split()[-1])
        elif instr.startswith("sipush "):
            pilha.append(instr.split()[-1])
        elif "getstatic" in instr:
            # Campo estatico: MapCanvas.OFFY
            campo = instr.split()[-1].split(".")[-1]
            pilha.append(f"MapCanvas_{campo}")
        elif instr == "iadd":
            b = pilha.pop() if pilha else "?"
            a = pilha.pop() if pilha else "?"
            pilha.append(f"({a} + {b})")
        elif instr == "isub":
            b = pilha.pop() if pilha else "?"
            a = pilha.pop() if pilha else "?"
            pilha.append(f"({a} - {b})")
        elif "putfield" in instr:
            campo = instr.split()[-1].split(".")[-1]
            v = pilha.pop() if pilha else "?"
            atribuicoes.append((campo, v))
    
    return atribuicoes

def sanitizar(nome):
    if not nome: return "x"
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        return nome
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{cp:04x}"

def main():
    if len(sys.argv) < 2:
        print("Uso: python posicionador.py <pasta_metodos>")
        sys.exit(1)
    
    pasta = sys.argv[1]
    
    print("// ============================================")
    print("// POSICOES INICIAIS (auto-extraidas do reset)")
    print("// ============================================")
    print()
    
    for classe in sorted(os.listdir(pasta)):
        reset_txt = os.path.join(pasta, classe, "reset.txt")
        if not os.path.exists(reset_txt):
            continue
        
        atrib = extrair_constantes_reset(reset_txt)
        if not atrib:
            continue
        
        print(f"// {classe}.reset:")
        for campo, valor in atrib:
            campo_s = sanitizar(campo)
            # Ajusta nomes comuns
            if campo_s == "x": nome = "posicao X inicial"
            elif campo_s == "y": nome = "posicao Y inicial"
            elif campo_s == "status": nome = "estado inicial"
            elif "0104" in campo_s: nome = "limite de movimento"
            elif "0103" in campo_s: nome = "offset/limite"
            elif "0107" in campo_s: nome = "flag direcao"
            else: nome = ""
            
            print(f"//   s->{campo_s:<14} = {valor:<25} // {nome}")
        print()

if __name__ == "__main__":
    main()
