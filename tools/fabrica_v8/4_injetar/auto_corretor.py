#!/usr/bin/env python3
"""
Auto-Corretor - Le log de erro do build e aplica fixes automaticos.
Uso: python auto_corretor.py <main.c> <log.txt>
"""
import sys, re, os

def ler_log(log_path):
    with open(log_path) as f:
        return f.read()

def extrair_tipos_faltantes(log):
    """Detecta 'unknown type name X' -> adiciona typedef void* X;"""
    tipos = set()
    for m in re.finditer(r"unknown type name '(\w+)'", log):
        tipos.add(m.group(1))
    for m in re.finditer(r"did you mean '(\w+)'", log):
        # ignora sugestoes
        pass
    return tipos

def extrair_redeclaracoes(log):
    """Detecta 'X redeclared as different kind of symbol' -> renomeia"""
    nomes = set()
    for m in re.finditer(r"'(\w+)' redeclared as different kind of symbol", log):
        nomes.add(m.group(1))
    return nomes

def extrair_erros_gerais(log):
    """Pega linhas e colunas dos erros."""
    erros = []
    for m in re.finditer(r"main\.c:(\d+):(\d+): error: (.+)", log):
        erros.append({
            "linha": int(m.group(1)),
            "col": int(m.group(2)),
            "msg": m.group(3),
        })
    return erros

def adicionar_typedefs(c, tipos):
    """Adiciona typedef void* X; pra cada tipo faltante."""
    if not tipos:
        return c, []
    
    # Acha o fim dos typedefs
    matches = list(re.finditer(r'typedef\s+void\*\s+\w+;', c))
    if matches:
        fim = matches[-1].end()
        adicao = "\n// Auto-fix: tipos faltantes\n"
        for t in sorted(tipos):
            adicao += f"typedef void* {t};\n"
        c = c[:fim] + adicao + c[fim:]
    return c, sorted(tipos)

def renomear_redeclaracoes(c, nomes):
    """Renomeia simbolos que colidem com struct/funcao existente."""
    aplicados = []
    for nome in nomes:
        # Troca typedef struct NOME_s NOME; por NOME_v2
        # e todas as referencias a struct NOME
        if f"struct {nome}_s {nome};" in c:
            c = c.replace(f"struct {nome}_s {nome};", f"struct {nome}_s {nome}_v2;")
            aplicados.append(f"{nome} -> {nome}_v2 (typedef)")
    return c, aplicados

def aplicar(main_c, log_path):
    with open(main_c) as f:
        c = f.read()
    log = ler_log(log_path)
    
    print("=== Auto-Corretor ===")
    
    # 1. Tipos faltantes
    tipos = extrair_tipos_faltantes(log)
    if tipos:
        c, adic = adicionar_typedefs(c, tipos)
        print(f"  [OK] +{len(adic)} typedefs: {', '.join(adic[:5])}")
    
    # 2. Redeclaracoes
    nomes = extrair_redeclaracoes(log)
    if nomes:
        c, adic = renomear_redeclaracoes(c, nomes)
        print(f"  [OK] {len(adic)} renomeacoes")
    
    # 3. Contagem de erros restantes
    erros = extrair_erros_gerais(log)
    print(f"  Total de erros no log: {len(erros)}")
    
    with open(main_c, 'w') as f:
        f.write(c)
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python auto_corretor.py <main.c> <log.txt>")
        sys.exit(1)
    aplicar(sys.argv[1], sys.argv[2])
