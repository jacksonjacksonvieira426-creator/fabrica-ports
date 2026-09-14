#!/usr/bin/env python3
"""
Injeta um metodo traduzido no main.c (substitui o stub).
Uso: python injetar.py <main.c> <classe> <metodo> <arquivo_traduzido.c>
"""
import sys, re

def injetar(main_c, classe, metodo, codigo_novo):
    with open(main_c) as f:
        c = f.read()
    with open(codigo_novo) as f:
        novo = f.read()
    
    # Encontra stub do metodo: "void Classe_metodo_fn_xxxx(void* self, ...) { ... }"
    padrao = rf'void {re.escape(classe)}_{re.escape(metodo)}_fn_\w+\([^)]*\)\s*\{{[^}}]*\}}'
    if re.search(padrao, c):
        c = re.sub(padrao, novo, c, count=1)
        print(f"Substituido: {classe}.{metodo}")
    else:
        print(f"AVISO: stub de {classe}.{metodo} nao encontrado")
        return
    
    with open(main_c, "w") as f:
        f.write(c)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Uso: python injetar.py <main.c> <classe> <metodo> <traduzido.c>")
        sys.exit(1)
    injetar(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
