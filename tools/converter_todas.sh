#!/bin/bash
# Converte todas as PNGs de uma pasta em headers C
PASTA="$1"
[ -z "$PASTA" ] && PASTA="."
for png in "$PASTA"/*.png; do
    nome=$(basename "$png" .png)
    saida="$PASTA/${nome}.h"
    python ~/fabrica-ports/tools/converter_png.py "$png" "$saida" "$nome" 2>&1 | grep -E "Lendo|opacos|Salvo"
done
