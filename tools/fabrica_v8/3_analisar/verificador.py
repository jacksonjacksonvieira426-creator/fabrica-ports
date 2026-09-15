#!/usr/bin/env python3
"""
Verificador - Compara metodo original com C traduzido.
Uso: python verificador.py <metodo.txt> <main.c>
"""
import sys, re


def sanitizar(nome):
    """Converte nome Unicode em nome C valido (mesma logica do gerador)."""
    if not nome: return "x"
    if all(ch.isascii() and (ch.isalnum() or ch == '_') for ch in nome):
        return nome if not nome[0].isdigit() else f"_{nome}"
    cp = ord(nome[0]) if len(nome) == 1 else sum(ord(ch) for ch in nome)
    return f"ofusc_{cp:04x}"

def extrair_campos_bytecode(caminho):
    campos = set()
    with open(caminho) as f:
        for l in f:
            m = re.search(r'(getfield|putfield|getstatic|putstatic)\s+\S+\.(\w+)', l)
            if m: campos.add(sanitizar(m.group(2)))
    return campos

def extrair_campos_c(main_c, classe, metodo):
    """Procura o corpo da funcao no main.c e extrai campos acessados."""
    campos = set()
    with open(main_c) as f:
        conteudo = f.read()
    
    # Acha a funcao
    padrao = rf'void {classe}_{metodo}(?:_fn_\w+)?\([^)]*\)\s*\{{(.*?)^\}}'
    m = re.search(padrao, conteudo, re.DOTALL | re.MULTILINE)
    if not m:
        return None
    
    corpo = m.group(1)
    # Procura acessos: ->campo ou self->campo
    for mm in re.finditer(r'->(\w+)', corpo):
        campos.add(mm.group(1))
    
    return campos

def main():
    if len(sys.argv) < 3:
        print("Uso: python verificador.py <metodo.txt> <main.c>")
        sys.exit(1)
    
    metodo_path = sys.argv[1]
    main_c = sys.argv[2]
    
    # Extrai classe e metodo
    with open(metodo_path) as f:
        header = f.read(300)
    m_classe = re.search(r'Classe:\s*(\w+)', header)
    m_metodo = re.search(r'Metodo:\s*(\S+)', header)
    
    if not m_classe or not m_metodo:
        print("ERRO: header do metodo incompleto")
        sys.exit(1)
    
    classe = m_classe.group(1)
    metodo = m_metodo.group(1).replace("<init>", "constructor")
    
    campos_bc = extrair_campos_bytecode(metodo_path)
    campos_c = extrair_campos_c(main_c, classe, metodo)
    
    if campos_c is None:
        print(f"AVISO: metodo {classe}.{metodo} nao encontrado no main.c")
        return
    
    faltando = campos_bc - campos_c
    extra = campos_c - campos_bc
    
    print(f"\n{'='*60}")
    print(f"VERIFICACAO: {classe}.{metodo}")
    print(f"{'='*60}\n")
    print(f"Campos no bytecode:  {len(campos_bc)}")
    print(f"Campos no C:         {len(campos_c)}")
    print(f"Faltando no C:       {len(faltando)}")
    print(f"Sobrando no C:       {len(extra)}")
    
    if faltando:
        print(f"\n[FALTANDO]")
        for c in sorted(faltando):
            print(f"  - {c}")
    
    if extra:
        print(f"\n[EXTRA]")
        for c in sorted(extra):
            print(f"  + {c}")
    
    if not faltando and not extra:
        print(f"\n[OK] Metodo traduzido 100%")

if __name__ == "__main__":
    main()
