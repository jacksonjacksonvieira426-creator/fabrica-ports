#!/usr/bin/env python3
import sys
n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
w = int(sys.argv[2]) if len(sys.argv) > 2 else 480
h = int(sys.argv[3]) if len(sys.argv) > 3 else 272
print("// LAYOUT AUTOMATICO")
print("#define CHAO_Y", int(h*0.8))
margem = int(w*0.15)
passo = (w - 2*margem) // max(1, n-1)
nomes = ["ryu", "lee", "p3", "p4"]
for i in range(n):
    x = margem + i*passo
    nome = nomes[i] if i < len(nomes) else "p" + str(i+1)
    print("    " + nome + "->x = " + str(x) + ";")
    print("    " + nome + "->y = CHAO_Y;")
