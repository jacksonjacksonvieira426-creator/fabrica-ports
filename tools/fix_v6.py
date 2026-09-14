#!/usr/bin/env python3
"""
Pos-processador do V6.
Corrige:
1. Typedef struct X X (para cast (X*)self funcionar)
2. Labels faltantes
3. Globais mutaveis faltando
4. Stubs com sufixo _fn_xxxx
5. Include do j2me_runtime.h
"""
import sys, re

def fix(c):
    # 1. Adiciona typedef struct X X (permite cast)
    # Detecta typedef struct X_s X e adiciona typedef struct X_s X_s tambem
    typedefs = re.findall(r'typedef struct (\w+)_s (\w+);', c)
    for struct_n, alias in typedefs:
        # Adiciona typedef de X_s para o cast funcionar
        marker = f'typedef struct {struct_n}_s {alias};'
        adicao = f'typedef struct {struct_n}_s {struct_n}_s;'
        if adicao not in c:
            c = c.replace(marker, marker + "\n" + adicao)
    
    # 2. Stubs com sufixo _fn_xxxx
    # Coleta todos os X_constructor_fn_xxxx que sao chamados mas nao definidos
    stubs_faltantes = set()
    for m in re.finditer(r'\b(\w+_constructor_fn_\w+)\s*\(', c):
        nome = m.group(1)
        # Verifica se tem definicao
        if f"{nome}(" not in c.split("int main")[0] or c.count(f"{nome}(") < 2:
            stubs_faltantes.add(nome)
    
    # 3. Globais mutaveis faltando
    globais_faltantes = set()
    for m in re.finditer(r'\b(\w+_ofusc_\w+)\s*=[^=]', c):
        nome = m.group(1)
        if f"int {nome}" not in c and f"void* {nome}" not in c:
            globais_faltantes.add(nome)
    
    # 4. Labels faltantes
    labels_usados = set(re.findall(r'goto (L_\d+)', c))
    labels_definidos = set(re.findall(r'^(L_\d+):', c, re.MULTILINE))
    labels_faltantes = labels_usados - labels_definidos
    
    # 5. Include j2me_runtime (que tem j2me_sleep)
    if 'j2me_sleep' in c and 'j2me_runtime.h' not in c:
        c = c.replace('#include "j2me_gfx.h"', 
                     '#include "j2me_runtime.h"\n#include "j2me_gfx.h"')
    
    # Aplica todos os fixes: insere antes de "int main"
    idx = c.find("int main")
    if idx < 0:
        idx = c.rfind("}")
    
    adicoes = []
    adicoes.append("\n// ===== FIXES AUTO-GERADOS =====\n")
    
    if globais_faltantes:
        adicoes.append("// Globais faltantes\n")
        for g in sorted(globais_faltantes):
            adicoes.append(f"int {g};\n")
        adicoes.append("\n")
    
    if stubs_faltantes:
        adicoes.append("// Stubs faltantes\n")
        for s in sorted(stubs_faltantes):
            adicoes.append(f"void {s}(void* self) {{ (void)self; }}\n")
        adicoes.append("\n")
    
    if labels_faltantes:
        adicoes.append("// Labels faltantes (nao usados, so pra compilar)\n")
        adicoes.append("void _labels_dummy(void) {\n")
        for l in sorted(labels_faltantes):
            adicoes.append(f"    {l}:; (void)0;\n")
        adicoes.append("}\n\n")
    
    c = c[:idx] + "".join(adicoes) + c[idx:]
    return c

def main():
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada.replace(".c", "_fix.c")
    with open(entrada) as f:
        c = f.read()
    c = fix(c)
    with open(saida, "w") as f:
        f.write(c)
    print(f"Gerado: {saida}")

if __name__ == "__main__":
    main()
