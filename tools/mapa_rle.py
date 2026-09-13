#!/usr/bin/env python3
"""
Testa hipotese: mapa em RLE (tipo, run_length)
Cada byte = (tipo << 4) | run_length
Uso: python mapa_rle.py <arquivo> [largura]
"""
import sys

with open(sys.argv[1], 'rb') as f:
    dados = f.read()

largura = int(sys.argv[2]) if len(sys.argv) > 2 else 32

print(f"Arquivo: {sys.argv[1]} ({len(dados)} bytes)")
print(f"Largura da linha: {largura}\n")

# Decodifica em uma unica linha continua
tiles = []
for b in dados:
    tipo = (b >> 4) & 0xF
    run  = b & 0xF
    if run == 0: run = 16  # 0 = 16 talvez
    for _ in range(run):
        tiles.append(tipo)

print(f"Total de tiles: {len(tiles)}")
print(f"Tiles por linha ({largura}): {len(tiles) // largura} linhas\n")

# Desenha o mapa em ASCII
# Tipo 0 = vazio (.)
# Tipo 1 = parede (#)
# Tipo 2 = agua (~)
# etc
simbolos = ".#~@*+=-:;"

print("=== MAPA VISUAL (ASCII) ===")
for y in range(min(30, len(tiles) // largura)):
    linha = ""
    for x in range(largura):
        idx = y * largura + x
        if idx < len(tiles):
            t = tiles[idx]
            linha += simbolos[t] if t < len(simbolos) else '?'
    print(f"  {y:2d} {linha}")

# Mostra os tipos usados
print(f"\n=== Tipos usados ===")
tipos = {}
for t in tiles:
    tipos[t] = tipos.get(t, 0) + 1
for t in sorted(tipos.keys()):
    print(f"  tipo {t}: {tipos[t]} tiles")
