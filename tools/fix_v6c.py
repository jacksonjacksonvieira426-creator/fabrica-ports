#!/usr/bin/env python3
"""
Fix V6 Final - resolve todos os 5 erros de uma vez.
1. Remove #define de variaveis que sao ATRIBUIDAS (transforma em int)
2. Remove goto L_-N (invalido)
3. Adiciona stubs X_constructor_fn_xxxx
4. Adiciona chamadas com self nas funcoes que faltam arg
"""
import sys, re

def fix(c):
    # 1. Detectar variaveis mutaveis (atribuidas) e remover #define delas
    atribuidas = set()
    for m in re.finditer(r'\b([A-Z]\w+_\w+)\s*=[^=]', c):
        atribuidas.add(m.group(1))
    for m in re.finditer(r'\b([A-Z]\w+_\w+)\s*\+=', c):
        atribuidas.add(m.group(1))
    
    # Substitui #define por int para essas
    for var in atribuidas:
        padrao = rf'#define {re.escape(var)} (.+)\n'
        c = re.sub(padrao, f'int {var} = \\1;\n', c)
    
    # 2. Remove goto L_-N (numeros negativos)
    c = re.sub(r'^\s*goto L_-.*$', '    // (goto invalido removido)', c, flags=re.MULTILINE)
    
    # 3. Adiciona stubs X_constructor_fn_xxxx que faltam
    chamadas = set(re.findall(r'\b(\w+_constructor_fn_\w+)\s*\(', c))
    definicoes = set(re.findall(r'^\w+\s+(\w+_constructor_fn_\w+)\s*\(', c, re.MULTILINE))
    faltam = chamadas - definicoes
    stubs = []
    for f in sorted(faltam):
        stubs.append(f"void {f}(void* self) {{ (void)self; }}")
    
    # Coleta tambem X_XXX_fn_yyyy sem definicao
    chamadas2 = set(re.findall(r'\b(\w+_\w+_fn_\w+)\s*\(', c))
    defs2 = set(re.findall(r'^\w+[\w\s\*]*\s+(\w+_\w+_fn_\w+)\s*\(', c, re.MULTILINE))
    faltam2 = chamadas2 - defs2
    for f in sorted(faltam2):
        stubs.append(f"void {f}() {{ }}")
    
    if stubs:
        idx = c.find("int main")
        if idx < 0: idx = c.rfind("}")
        c = c[:idx] + "\n// Stubs externos\n" + "\n".join(stubs) + "\n\n" + c[idx:]
    
    # 4. Include j2me_runtime
    if 'j2me_sleep' in c and 'j2me_runtime.h' not in c:
        c = c.replace('#include "j2me_gfx.h"',
                     '#include "j2me_runtime.h"\n#include "j2me_gfx.h"')
    
    # 5. Corrige chamadas com args faltando - adiciona NULL nos metodos X_fn_yyyy
    # Detecta "Game_randomInt_fn_9b68()" e vira "Game_randomInt_fn_9b68(NULL)"
    def fix_args(m):
        fn = m.group(1)
        args = m.group(2).strip()
        if args == "":
            return f"{fn}(NULL)"
        return m.group(0)
    c = re.sub(r'\b(\w+_fn_\w+)\(([^)]*)\)', fix_args, c)
    
    return c

def main():
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada.replace(".c", "_fixc.c")
    with open(entrada) as f:
        c = f.read()
    c = fix(c)
    with open(saida, "w") as f:
        f.write(c)
    print(f"Gerado: {saida}")
    # Stats
    n_int = len(re.findall(r'^int \w+_\w+ =', c, re.MULTILINE))
    n_goto_neg = len(re.findall(r'goto L_-', c))
    n_stubs = len(re.findall(r'^void \w+_constructor_fn_\w+\(void\* self\)', c, re.MULTILINE))
    print(f"  {n_int} variaveis transformadas em int")
    print(f"  {n_goto_neg} gotos invalidos restantes (deve ser 0)")
    print(f"  {n_stubs} stubs _constructor_fn adicionados")

if __name__ == "__main__":
    main()
