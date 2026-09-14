#!/usr/bin/env python3
"""Fix V6 final - resolve os 6 erros do ciclo 9."""
import sys, re

def fix(c):
    # 1. Adiciona include j2me_runtime ANTES de tudo se j2me_sleep usado
    if 'j2me_sleep' in c and 'j2me_runtime.h' not in c:
        c = c.replace('#include <stdint.h>',
                     '#include <stdint.h>\n#include "j2me_runtime.h"')
    
    # 2. Coleta TODAS as chamadas X_constructor_fn_xxxx e X_xxx_fn_xxxx
    chamadas_ctor = set(re.findall(r'\b(\w+_constructor_fn_\w+)\s*\(', c))
    definicoes_ctor = set(re.findall(r'^\w+\s+(\w+_constructor_fn_\w+)\s*\(', c, re.MULTILINE))
    faltam_ctor = chamadas_ctor - definicoes_ctor
    
    chamadas_fn = set(re.findall(r'\b(\w+_\w+_fn_\w+)\s*\(', c))
    defs_fn = set(re.findall(r'^\w+[\w\s\*]*\s+(\w+_\w+_fn_\w+)\s*\(', c, re.MULTILINE))
    faltam_fn = chamadas_fn - defs_fn
    
    # 3. Stubs de classes Java comuns
    stubs_fixos = [
        'void Thread_constructor_fn_9b75(void* self) { (void)self; }',
        'void InputStream_read_fn_06ef(void* self, void* b) { (void)self; (void)b; }',
        'void System_arraycopy_fn_894e(void* a, int b, void* d, int e, int f) { (void)a;(void)b;(void)d;(void)e;(void)f; }',
    ]
    
    # 4. Stubs genéricos pra funcoes faltantes
    stubs_gen = []
    for f in sorted(faltam_ctor):
        stubs_gen.append(f'void {f}(void* self) {{ (void)self; }}')
    for f in sorted(faltam_fn):
        stubs_gen.append(f'void {f}() {{ }}')
    
    # 5. Corrige var = inteiro → cast pra void*
    # Detecta "void* varN" e "varN = <int>;" e corrige pra "varN = (void*)(intptr_t)<int>;"
    for m in re.finditer(r'(\w+)\s*=\s*(\d+);', c):
        var = m.group(1)
        # Verifica se foi declarada como void*
        if f'void* {var}' in c or f'void *{var}' in c:
            c = c.replace(f'{var} = {m.group(2)};', f'{var} = (void*)(intptr_t){m.group(2)};')
    
    # 6. Corrige int* = NULL
    c = re.sub(r'\(\(int\*\)(\w+)\)\[(\w+)\] = /\* arr.*\*/NULL;',
               r'((int*)\1)[\2] = 0;', c)
    
    # 7. Insere stubs antes do main
    todos_stubs = stubs_fixos + stubs_gen
    if todos_stubs:
        idx = c.find("int main")
        if idx < 0: idx = c.rfind("}")
        c = c[:idx] + "\n// ===== STUBS FINAIS =====\n" + "\n".join(todos_stubs) + "\n\n" + c[idx:]
    
    return c

def main():
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada.replace(".c", "_fixd.c")
    with open(entrada) as f:
        c = f.read()
    c = fix(c)
    with open(saida, "w") as f:
        f.write(c)
    print(f"Gerado: {saida}")

if __name__ == "__main__":
    main()
