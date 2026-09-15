#!/usr/bin/env python3
"""
Escalador de Sprites - Le headers e calcula escala ideal.
Uso: python escalador_sprites.py <pasta_src> [altura_desejada]
"""
import sys, os, re

def analisar_headers(pasta):
    """Le headers .h e extrai tamanhos."""
    sprites = {}
    for arq in os.listdir(pasta):
        if not arq.startswith("msf_") or not arq.endswith(".h"): continue
        caminho = os.path.join(pasta, arq)
        with open(caminho) as f:
            conteudo = f.read(500)
        
        w = re.search(r'#define \w+_W (\d+)', conteudo)
        h = re.search(r'#define \w+_H (\d+)', conteudo)
        if w and h:
            sprites[arq[:-2]] = (int(w.group(1)), int(h.group(1)))
    
    return sprites

def main():
    if len(sys.argv) < 2:
        print("Uso: python escalador_sprites.py <pasta_src> [altura_desejada]")
        sys.exit(1)
    
    pasta = sys.argv[1]
    altura_alvo = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    sprites = analisar_headers(pasta)
    
    print(f"// ============================================")
    print(f"// ESCALA DE SPRITES (fabrica V9)")
    print(f"// Altura alvo: {altura_alvo}px")
    print(f"// ============================================")
    print()
    
    # Agrupa por altura
    alturas = {}
    for nome, (w, h) in sprites.items():
        alturas.setdefault(h, []).append((nome, w, h))
    
    for h in sorted(alturas.keys()):
        grupo = alturas[h]
        # Calcula escala ideal
        escala = max(1, altura_alvo // h)
        print(f"// Altura {h}px -> escala {escala}x (fica {h*escala}px)")
        for nome, w, hh in grupo:
            print(f"//   {nome}: {w}x{hh} -> {w*escala}x{hh*escala}")
        print()
    
    # Sugere constante global
    escala_media = sum(altura_alvo // h for h in alturas.keys()) // len(alturas)
    print(f"// Escala sugerida: {escala_media}x")
    print(f"#define SPRITE_ESCALA {escala_media}")

if __name__ == "__main__":
    main()
