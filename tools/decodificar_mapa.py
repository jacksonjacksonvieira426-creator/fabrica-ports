#!/usr/bin/env python3
"""
Decodifica arquivo de mapa do CoD J2ME.
Formato suspeito: cada byte = 2 nibbles.
Uso: python decodificar_mapa.py <arquivo> [largura_grid]
"""
import sys

with open(sys.argv[1], 'rb') as f:
    dados = f.read()

largura = int(sys.argv[2]) if len(sys.argv) > 2 else 16

print(f"Arquivo: {sys.argv[1]}")
print(f"Tamanho: {len(dados)} bytes = {len(dados)*2} nibbles\n")

# Extrai todos os nibbles
nibbles = []
for b in dados:
    nibbles.append((b >> 4) & 0xF)
    nibbles.append(b & 0xF)

print(f"Primeiros 40 nibbles:")
for i in range(0, min(40, len(nibbles)), 2):
    if i+1 < len(nibbles):
        print(f"  [{i:3d}] ({nibbles[i]:2d}, {nibbles[i+1]:2d})")

# Estatisticas: valores unicos por posicao
pares_x = nibbles[0::2]
pares_y = nibbles[1::2]

print(f"\n=== Estatisticas (assumindo pares X,Y) ===")
print(f"X: min={min(pares_x)}, max={max(pares_x)}, unicos={sorted(set(pares_x))[:20]}")
print(f"Y: min={min(pares_y)}, max={max(pares_y)}, unicos={sorted(set(pares_y))[:20]}")

# Tenta 4 nibbles por entrada (x, y, valor, ???)
print(f"\n=== Tentando 4 nibbles por entrada (x, y, tipo, valor) ===")
for i in range(0, min(40, len(nibbles)), 4):
    if i+3 < len(nibbles):
        x, y, t, v = nibbles[i:i+4]
        print(f"  [{i//4:3d}] pos=({x:2d},{y:2d})  tipo={t}  val={v}")
