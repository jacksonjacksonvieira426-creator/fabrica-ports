#!/usr/bin/env python3
"""
Calibrador Visual - Le reset() e gera posicoes escaladas pro PSP.
Uso: python calibrador_visual.py <pasta_metodos> [largura_tela] [altura_tela]
"""
import sys, os, re, json

# Tamanho tipico de tela J2ME (padrao Nokia 2004)
J2ME_W_DEFAULT = 176
J2ME_H_DEFAULT = 208

# Tela PSP
PSP_W = 480
PSP_H = 272

def extrair_reset(caminho):
    """Extrai valores de posicao do reset()."""
    valores = {}
    pilha = []
    
    with open(caminho) as f:
        for l in f.readlines():
            m = re.match(r'^\[\s*(\d+)\]\s+(.+)$', l.strip())
            if not m: continue
            instr = m.group(2).strip()
            
            # Constantes
            if instr.startswith("iconst_"):
                v = instr.replace("iconst_m1", "-1").replace("iconst_", "")
                pilha.append(int(v))
            elif instr.startswith("bipush "):
                pilha.append(int(instr.split()[-1]))
            elif instr.startswith("sipush "):
                pilha.append(int(instr.split()[-1]))
            elif "getstatic" in instr:
                campo = instr.split()[-1].split(".")[-1]
                # Assume valor padrao
                if "OFFY" in campo: pilha.append("OFFY")
                elif "OFFX" in campo: pilha.append("OFFX")
                elif "CanvasWidth" in campo: pilha.append("W")
                elif "CanvasHeight" in campo: pilha.append("H")
                else: pilha.append(f"<{campo}>")
            elif instr == "iadd" and len(pilha) >= 2:
                b, a = pilha.pop(), pilha.pop()
                if isinstance(a, int) and isinstance(b, int):
                    pilha.append(a + b)
                else:
                    pilha.append(f"{a}+{b}")
            elif instr == "isub" and len(pilha) >= 2:
                b, a = pilha.pop(), pilha.pop()
                if isinstance(a, int) and isinstance(b, int):
                    pilha.append(a - b)
                else:
                    pilha.append(f"{a}-{b}")
            elif "putfield" in instr:
                campo = instr.split()[-1].split(".")[-1]
                v = pilha.pop() if pilha else 0
                valores[campo] = v
    
    return valores

def escalar(valor, escala_x, escala_y):
    """Escala valor de J2ME -> PSP."""
    if isinstance(valor, int):
        return int(valor * escala_x)
    if isinstance(valor, str):
        if "W" in valor:
            return f"({valor.replace('W', str(PSP_W))})"
        if "H" in valor:
            return f"({valor.replace('H', str(PSP_H))})"
    return valor

def main():
    if len(sys.argv) < 2:
        print("Uso: python calibrador_visual.py <pasta_metodos>")
        sys.exit(1)
    
    pasta = sys.argv[1]
    j2me_w = int(sys.argv[2]) if len(sys.argv) > 2 else J2ME_W_DEFAULT
    j2me_h = int(sys.argv[3]) if len(sys.argv) > 3 else J2ME_H_DEFAULT
    
    escala_x = PSP_W / j2me_w
    escala_y = PSP_H / j2me_h
    
    print(f"// ============================================")
    print(f"// CALIBRACAO VISUAL (fabrica V9)")
    print(f"// J2ME: {j2me_w}x{j2me_h}  ->  PSP: {PSP_W}x{PSP_H}")
    print(f"// Escala: x={escala_x:.2f}, y={escala_y:.2f}")
    print(f"// ============================================")
    print()
    
    # Constantes pra copiar pro main.c
    print(f"#define J2ME_W {j2me_w}")
    print(f"#define J2ME_H {j2me_h}")
    print(f"#define PSP_W  {PSP_W}")
    print(f"#define PSP_H  {PSP_H}")
    print()
    
    # OFFX e OFFY (centralizacao)
    offx = (PSP_W - int(120 * escala_x)) // 2
    offy = (PSP_H - int(80 * escala_y)) // 2
    print(f"int MapCanvas_OFFX = {offx};")
    print(f"int MapCanvas_OFFY = {offy};")
    print(f"int MapCanvas_CanvasWidth = {PSP_W};")
    print(f"int MapCanvas_CanvasHeight = {PSP_H};")
    print()
    
    # Posicoes de personagens
    for classe in sorted(os.listdir(pasta)):
        reset = os.path.join(pasta, classe, "reset.txt")
        if not os.path.exists(reset): continue
        
        vals = extrair_reset(reset)
        if not vals: continue
        
        print(f"// {classe}.reset (calibrado pro PSP):")
        for campo, valor in vals.items():
            if campo == "x":
                if isinstance(valor, int):
                    novo = int(valor * escala_x)
                elif "W-" in str(valor):
                    novo = f"({PSP_W} - {int((j2me_w - int(str(valor).split('-')[1])) * escala_x)})"
                else:
                    novo = valor
                print(f"//   s->x = {novo};   // (original: {valor})")
            elif campo == "y":
                if isinstance(valor, int):
                    novo = int(valor * escala_y) + offy
                elif "OFFY+" in str(valor):
                    offset = int(str(valor).split('+')[1])
                    novo = f"MapCanvas_OFFY + {int(offset * escala_y)}"
                else:
                    novo = valor
                print(f"//   s->y = {novo};   // (original: {valor})")
        print()

if __name__ == "__main__":
    main()
