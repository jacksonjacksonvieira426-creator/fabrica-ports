#!/usr/bin/env python3
"""
Auto-Fixer - Corrige erros comuns de compilacao automaticamente.
Uso: python auto_fixer.py <main.c> <build_log.txt>
"""
import sys, re, os

def aplicar_fix(main_c, fix_nome, fix_func):
    """Aplica um fix e retorna True se modificou."""
    with open(main_c) as f:
        c_original = f.read()
    c_novo = fix_func(c_original)
    if c_novo != c_original:
        with open(main_c, 'w') as f:
            f.write(c_novo)
        print(f"  [OK] {fix_nome}")
        return True
    return False

def fix_prototipos(c):
    """Adiciona prototipos faltantes (implicit declaration)."""
    # Detecta funcoes que geram 'implicit declaration'
    usadas = set()
    for m in re.finditer(r'\b(\w+_fn_\w+)\s*\(', c):
        usadas.add(m.group(1))
    definidas = set(re.findall(r'^\w+[\w\s\*]*\s+(\w+_fn_\w+)\s*\([^;]*\)\s*\{', c, re.MULTILINE))
    faltam = usadas - definidas
    if not faltam:
        return c
    # Adiciona prototipos antes do main
    bloco = "\n// Auto-fix: prototipos\n"
    for f in sorted(faltam):
        bloco += f"void {f}();\n"
    idx = c.find("int main")
    if idx > 0:
        c = c[:idx] + bloco + c[idx:]
    return c

def fix_redefinicao(c):
    """Remove globais duplicadas."""
    for var in ["MapCanvas_OFFY", "MapCanvas_CanvasWidth", "MapCanvas_CanvasHeight",
                "Game_count", "msf_mc", "_self", "_role_self", "_p1_self", "_p2_self"]:
        # Conta definicoes
        padrao = rf'^int {var} = \d+;'
        linhas = c.split("\n")
        ocorrencias = [(i, l) for i, l in enumerate(linhas) if re.match(padrao, l)]
        if len(ocorrencias) > 1:
            # Mantem a primeira, remove as outras
            for i, _ in reversed(ocorrencias[1:]):
                linhas[i] = f"// {linhas[i]} (removida duplicata)"
            c = "\n".join(linhas)
    return c

def fix_casts(c):
    """Adiciona casts para evitar incompatible-pointer."""
    # void* -> T*
    for tipo in ["J2MEImage", "MapCanvas", "Role_Ryu", "Role_Lee"]:
        # j2me_image_blit(self->ofusc_XXXX, ...) -> j2me_image_blit((J2MEImage*)self->ofusc_XXXX, ...)
        c = re.sub(
            rf'j2me_image_blit\((self|s)->(ofusc_\w+),',
            rf'j2me_image_blit((J2MEImage*)\1->\2,',
            c
        )
    return c

def main():
    if len(sys.argv) < 3:
        print("Uso: python auto_fixer.py <main.c> <build_log.txt>")
        sys.exit(1)
    
    main_c = sys.argv[1]
    log_path = sys.argv[2]
    
    with open(log_path) as f:
        log = f.read()
    
    print("=== Auto-Fixer ===")
    print(f"Analisando: {log_path}\n")
    
    # Detecta tipos de erro
    if "implicit declaration" in log:
        aplicar_fix(main_c, "prototipos", fix_prototipos)
    if "redefinition" in log:
        aplicar_fix(main_c, "redefinicao", fix_redefinicao)
    if "incompatible-pointer" in log:
        aplicar_fix(main_c, "casts", fix_casts)
    
    print("\nDone.")

if __name__ == "__main__":
    main()
