#!/usr/bin/env python3
"""Testa hipotese: header + grid 128x11 em nibbles"""
import sys

with open(sys.argv[1], 'rb') as f:
    dados = f.read()

print(f"Total: {len(dados)} bytes")
print(f"Se header = 29, sobram {len(dados)-29} bytes = {(len(dados)-29)*2} nibbles")
print(f"Grid 128x11 = {128*11} tiles\n")

header = dados[:29]
grid_bytes = dados[29:]

# Decodifica nibbles
nibbles = []
for b in grid_bytes:
    nibbles.append((b >> 4) & 0xF)
    nibbles.append(b & 0xF)

# Grid 128x11
W = 128
H = 11
print("=== MAPA (128x11) - primeiras 16x11 ===")
simbolos = ".#~@*+=-:;ABCDEF"
for y in range(H):
    linha = ""
    for x in range(16):
        idx = y * W + x
        if idx < len(nibbles):
            t = nibbles[idx]
            linha += simbolos[t] if t < len(simbolos) else '?'
    print(f"  y={y:2d} {linha}")

print("\n=== HEADER (29 bytes) ===")
for i, b in enumerate(header):
    print(f"  [{i:2d}] 0x{b:02X}  = {b:3d}  nibbles=({b>>4},{b&0xF})")
