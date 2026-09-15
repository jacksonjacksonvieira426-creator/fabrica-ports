#!/usr/bin/env python3
"""
Auto-Fixer V2 - Detecta e corrige 5 padroes de erro.
Uso: python auto_fixer_v2.py <main.c> <build_log.txt>
"""
import sys, re

def fix_underscore(c):
    """Remove _ do inicio de campos em todo o codigo."""
    campos = set()
    for m in re.finditer(r'^\s+\w+\s+(_\w+);', c, re.MULTILINE):
        campos.add(m.group(1))
    for campo in campos:
        sem_ = campo[1:]
        # Substitui no codigo (apos ->), mas nao nas declaracoes
        c = re.sub(rf'(->|\bs->)\s*({re.escape(sem_)})\b(?!\w)', rf'\1{campo}', c)
    return c

def fix_self(c):
    """Troca void* self por _self quando acesso."""
    # Se funcao usa "s = (Tipo*)_self" mas _self nao existe, adiciona
    if '_self = 0' not in c and '_self' in c:
        c = c.replace('int Animator_IMAGES', 'void* _self = 0;\nint Animator_IMAGES')
    return c

def fix_stubs(c):
    """Adiciona stubs que faltam."""
    stubs_fixos = {
        'j2me_canvas_repaint': 'void j2me_canvas_repaint(void) { }',
        'j2me_canvas_serviceRepaints': 'void j2me_canvas_serviceRepaints(void) { }',
    }
    for nome, stub in stubs_fixos.items():
        if f'{nome}(' in c and f'void {nome}(void)' not in c and f'{stub}' not in c:
            # Adiciona antes do primeiro struct
            idx = c.find('struct ')
            if idx > 0:
                c = c[:idx] + f'// STUB\n{stub}\n\n' + c[idx:]
    return c

def fix_typedef(c):
    """Remove typedef orfao."""
    c = re.sub(r'^typedef\s*\n(?:[^t].*\n)*?', '', c, flags=re.MULTILINE)
    return c

def fix_animator_call(c):
    """Corrige chamadas com args errados."""
    # Animator_keyPressed(a, b) -> Animator_keyPressed(a)
    c = re.sub(r'Animator_keyPressed\(([^,]+),[^)]+\)', r'Animator_keyPressed(\1)', c)
    return c

def aplicar(main_c, log_path):
    with open(main_c) as f:
        c = f.read()
    with open(log_path) as f:
        log = f.read()
    
    print("=== Auto-Fixer V2 ===")
    
    fixes = [
        ("campos _prefix", fix_underscore),
        ("_self declarado", fix_self),
        ("typedef orfao", fix_typedef),
        ("stubs faltantes", fix_stubs),
        ("chamadas com args", fix_animator_call),
    ]
    
    for nome, fn in fixes:
        antes = c
        c = fn(c)
        if c != antes:
            print(f"  [OK] {nome}")
    
    with open(main_c, 'w') as f:
        f.write(c)
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python auto_fixer_v2.py <main.c> <build_log.txt>")
        sys.exit(1)
    aplicar(sys.argv[1], sys.argv[2])
