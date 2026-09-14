#!/usr/bin/env python3
"""
Fix V7 - Integrado. Uma passada, resolve tudo:
1. Include de j2me_runtime.h
2. Typedef struct X_s X_s
3. Variaveis mutaveis (#define -> int)
4. Stubs com assinatura correta baseada na chamada
5. Labels faltantes dentro de cada funcao
6. Casts void* <-> int
7. Remove gotos invalidos
"""
import sys, re

def achar_fim_funcao(linhas, inicio):
    prof = 0
    for i in range(inicio, len(linhas)):
        for ch in linhas[i]:
            if ch == '{': prof += 1
            elif ch == '}': prof -= 1
        if prof == 0 and i > inicio:
            return i
    return -1

def fix(c):
    # === 1. Include j2me_runtime.h ===
    if 'j2me_sleep' in c and 'j2me_runtime.h' not in c:
        c = c.replace('#include <stdint.h>',
                     '#include <stdint.h>\n#include "j2me_runtime.h"')
    
    # === 2. Typedef struct X_s X_s ===
    for m in re.finditer(r'typedef struct (\w+)_s (\w+);', c):
        struct_n = m.group(1)
        adicao = f'typedef struct {struct_n}_s {struct_n}_s;'
        if adicao not in c:
            c = c.replace(m.group(0), m.group(0) + "\n" + adicao)
    
    linhas = c.split('\n')
    
    # === 3. Variaveis mutaveis: #define -> int ===
    atribuidas = set()
    for m in re.finditer(r'\b([A-Z]\w+_\w+)\s*(?:\+|-|\*|/|%|\^|&|\||)=?=', c):
        atribuidas.add(m.group(1))
    for m in re.finditer(r'\b([A-Z]\w+_\w+)\s*=[^=]', c):
        atribuidas.add(m.group(1))
    for var in atribuidas:
        c = re.sub(rf'^#define {re.escape(var)} (.+)$',
                   f'int {var} = \\1;', c, flags=re.MULTILINE)
    
    # === 4. Casts void* <-> int ===
    # Encontra variaveis declaradas como void*
    vars_voidp = set(re.findall(r'void\s*\*\s*(\w+)', c))
    for v in vars_voidp:
        # var = <numero>; -> var = (void*)(intptr_t)<numero>;
        c = re.sub(rf'\b{v}\s*=\s*(\d+);', rf'{v} = (void*)(intptr_t)\1;', c)
    
    # === 5. (int*)var = NULL -> 0 ===
    c = re.sub(r'\(\(int\*\)(\w+)\)\[(\w+)\]\s*=\s*/\*\s*arr\[\d+\]\s*\*/NULL;',
               r'((int*)\1)[\2] = 0;', c)
    c = re.sub(r'\(\(int\*\)(\w+)\)\[(\w+)\]\s*=\s*NULL;',
               r'((int*)\1)[\2] = 0;', c)
    
    # === 6. Labels faltantes DENTRO de cada funcao ===
    i = 0
    while i < len(linhas):
        m = re.match(r'^[\w\*]+[\w\s\*]*\s+(\w+)\s*\([^;]*\)\s*\{', linhas[i])
        if not m:
            i += 1
            continue
        fim = achar_fim_funcao(linhas, i)
        if fim < 0:
            i += 1
            continue
        corpo_str = '\n'.join(linhas[i:fim+1])
        usados = set(re.findall(r'goto (L_\d+)', corpo_str))
        definidos = set(re.findall(r'^\s*(L_\d+):', corpo_str, re.MULTILINE))
        faltantes = usados - definidos
        if faltantes:
            adicao = [f"    {lbl}:; // (auto)" for lbl in sorted(faltantes)]
            linhas = linhas[:fim] + adicao + linhas[fim:]
            i = fim + len(adicao) + 1
        else:
            i = fim + 1
    c = '\n'.join(linhas)
    
    # === 7. Remove gotos/labels invalidos (negativos) ===
    c = re.sub(r'^\s*goto L_-.*$', '    // (goto invalido)', c, flags=re.MULTILINE)
    c = re.sub(r'^\s*L_-.*:;$', '    // (label invalido)', c, flags=re.MULTILINE)
    
    # === 8. Stubs com assinatura correta ===
    # Encontra TODAS as chamadas X_yyyy_fn_xxxx com seus numeros de args
    chamadas = {}
    for m in re.finditer(r'\b(\w+_(?:\w+_)?fn_\w+)\s*\(([^)]*)\)', c):
        nome = m.group(1)
        args = m.group(2).strip()
        n_args = 0 if not args else args.count(',') + 1
        if nome not in chamadas:
            chamadas[nome] = n_args
        else:
            chamadas[nome] = max(chamadas[nome], n_args)
    
    # Encontra definicoes existentes
    definidas = set(re.findall(r'^\w+[\w\s\*]*\s+(\w+_(?:\w+_)?fn_\w+)\s*\(', c, re.MULTILINE))
    
    faltam = {n: a for n, a in chamadas.items() if n not in definidas}
    
    # Gera stubs
    stubs = []
    for nome, n_args in sorted(faltam.items()):
        params = ['void* self'] + [f'int arg{i}' for i in range(n_args - 1 if n_args > 0 else 0)]
        stubs.append(f"void {nome}({', '.join(params)}) {{ {'(void)self;' if n_args > 0 else ''} }}")
    
    # Stubs fixos de classes Java
    stubs_fixos = [
        'void Thread_constructor(void* self) { (void)self; }',
        'void InputStream_read(void* self, void* b) { (void)self; (void)b; }',
        'void System_arraycopy(void* a, int b, void* d, int e, int f) { (void)a;(void)b;(void)d;(void)e;(void)f; }',
    ]
    
    if stubs or stubs_fixos:
        idx = c.find("int main")
        if idx < 0: idx = c.rfind("}")
        adicao = "\n// ===== STUBS V7 =====\n" + "\n".join(stubs_fixos + stubs) + "\n\n"
        c = c[:idx] + adicao + c[idx:]
    
    return c

def main():
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada.replace(".c", "_v7.c")
    with open(entrada) as f:
        c = f.read()
    c = fix(c)
    with open(saida, "w") as f:
        f.write(c)
    print(f"Gerado: {saida}")

if __name__ == "__main__":
    main()
