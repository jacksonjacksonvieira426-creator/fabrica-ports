#!/usr/bin/env python3
import sys
with open(sys.argv[1], 'rb') as f:
    dados = f.read()

# Pula 29 bytes de "header" (lista de objetos)
grid = dados[29:]

W, H = 128, 11
# Testa coluna-major
nibbles = []
for b in grid:
    nibbles.append((b >> 4) & 0xF)
    nibbles.append(b & 0xF)

simbolos = ".#~@*+=-:;ABCDEF"

print("=== COLUNA-MAJOR (x varia mais devagar) ===")
for y in range(H):
    linha = ""
    for x in range(40):
        idx = x * H + y
        if idx < len(nibbles):
            t = nibbles[idx]
            linha += simbolos[t] if t < len(simbolos) else '?'
    print(f"  y={y:2d} {linha}")
