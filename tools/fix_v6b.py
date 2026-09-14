#!/usr/bin/env python3
"""
Fix V6 - versao cirurgica.
1. Adiciona label faltante no FINAL da funcao onde eh usado
2. Adiciona stubs de classes externas
3. Adiciona typedef struct X_s X_s
"""
import sys, re

def encontrar_fim_funcao(linhas, inicio):
    """Acha o } que fecha a funcao que comeca em 'inicio'."""
    prof = 0
    for i in range(inicio, len(linhas)):
        for ch in linhas[i]:
            if ch == '{': prof += 1
            elif ch == '}': prof -= 1
            if prof == 0 and i > inicio:
                return i
    return -1

def fix(c):
    linhas = c.split('\n')
    
    # 1. Adiciona typedef struct X_s X_s
    typedefs = re.findall(r'typedef struct (\w+)_s (\w+);', c)
    for struct_n, alias in typedefs:
        marker = f'typedef struct {struct_n}_s {alias};'
        adicao = f'typedef struct {struct_n}_s {struct_n}_s;'
        if adicao not in c:
            c = c.replace(marker, marker + "\n" + adicao)
    
    linhas = c.split('\n')
    
    # 2. Para cada funcao, adiciona labels faltantes no final
    i = 0
    while i < len(linhas):
        l = linhas[i]
        # Detecta inicio de funcao (retorno nome(...) {)
        m = re.match(r'^[\w\*]+[\w\s\*]*\s+(\w+)\s*\([^;]*\)\s*\{', l)
        if not m:
            i += 1
            continue
        fim = encontrar_fim_funcao(linhas, i)
        if fim < 0:
            i += 1
            continue
        corpo = linhas[i:fim+1]
        corpo_str = '\n'.join(corpo)
        # Coleta labels usados vs definidos NESTA funcao
        usados = set(re.findall(r'goto (L_\d+)', corpo_str))
        definidos = set(re.findall(r'^\s*(L_\d+):', corpo_str, re.MULTILINE))
        faltantes = usados - definidos
        if faltantes:
            # Adiciona labels antes do } final
            adicao = [f"    {lbl}:; // (auto-adicionado)" for lbl in sorted(faltantes)]
            linhas = linhas[:fim] + adicao + linhas[fim:]
            i = fim + len(adicao) + 1
        else:
            i = fim + 1
    
    c = '\n'.join(linhas)
    
    # 3. Stubs de classes externas (com sufixo _fn_ do gerador)
    stubs_extra = [
        "void Thread_constructor_fn_9b75(void* self) { (void)self; }",
        "void Timer_constructor_fn(void* self) { (void)self; }",
        "void TimerTask_constructor_fn(void* self) { (void)self; }",
    ]
    
    # Acha todas as chamadas X_constructor_fn_xxxx sem definicao
    chamadas = set(re.findall(r'\b(\w+_constructor_fn_\w+)\s*\(', c))
    definicoes = set(re.findall(r'^\w+\s+(\w+_constructor_fn_\w+)\s*\(', c, re.MULTILINE))
    faltam = chamadas - definicoes
    
    stubs_add = []
    for f in sorted(faltam):
        stubs_add.append(f"void {f}(void* self) {{ (void)self; }}")
    
    # Tambem captura funcoes X_fn_yyyy que sao chamadas mas nao definidas
    chamadas_fn = set(re.findall(r'\b(\w+_\w+_fn_\w+)\s*\(', c))
    defs_fn = set(re.findall(r'^\w+[\w\s\*]*\s+(\w+_\w+_fn_\w+)\s*\(', c, re.MULTILINE))
    faltam_fn = chamadas_fn - defs_fn
    for f in sorted(faltam_fn):
        stubs_add.append(f"void {f}() {{ }}")
    
    if stubs_add:
        idx = c.find("int main")
        if idx < 0: idx = c.rfind("}")
        stubs_str = "\n// ===== STUBS EXTERNOS =====\n" + "\n".join(stubs_add) + "\n"
        c = c[:idx] + stubs_str + c[idx:]
    
    # 4. Include j2me_runtime se j2me_sleep usado
    if 'j2me_sleep' in c and 'j2me_runtime.h' not in c:
        c = c.replace('#include "j2me_gfx.h"',
                     '#include "j2me_runtime.h"\n#include "j2me_gfx.h"')
    
    return c

def main():
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada.replace(".c", "_fix2.c")
    with open(entrada) as f:
        c = f.read()
    c = fix(c)
    with open(saida, "w") as f:
        f.write(c)
    print(f"Gerado: {saida}")

if __name__ == "__main__":
    main()
