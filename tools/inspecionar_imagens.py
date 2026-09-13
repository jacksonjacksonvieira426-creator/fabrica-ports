#!/usr/bin/env python3
"""Mostra dimensoes e formato de cada imagem extraida."""
import sys, os
from PIL import Image

pasta = sys.argv[1] if len(sys.argv) > 1 else "."
print(f"{'Arquivo':<25} {'Tamanho':>10} {'Formato':<10} {'Modo':<6}")
print("-" * 55)

for arq in sorted(os.listdir(pasta)):
    caminho = os.path.join(pasta, arq)
    if not os.path.isfile(caminho): continue
    try:
        img = Image.open(caminho)
        print(f"{arq:<25} {img.size[0]}x{img.size[1]:<6} {img.format or '?':<10} {img.mode:<6}")
    except Exception as e:
        print(f"{arq:<25} (nao e imagem: {e})")
