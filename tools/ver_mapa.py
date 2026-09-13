#!/usr/bin/env python3
"""Mostra as primeiras linhas de um arquivo de mapa em hex + ASCII."""
import sys

with open(sys.argv[1], 'rb') as f:
    dados = f.read()

print(f"Tamanho: {len(dados)} bytes\n")
print("HEX (primeiros 256 bytes):")
for i in range(0, min(256, len(dados)), 16):
    bloco = dados[i:i+16]
    hexa = ' '.join(f'{b:02X}' for b in bloco)
    ascii_ = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bloco)
    print(f"  {i:04X}  {hexa:<48}  {ascii_}")
