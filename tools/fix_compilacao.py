#!/usr/bin/env python3
"""
Pos-processador: conserta erros comuns do V4 pra compilar.
1. Adiciona 'self' como 1o parametro em todo metodo
2. Declara campos estaticos como globais
3. Ajusta chamadas com args extras (j2me_image_blit)
4. Adiciona labels faltantes
5. Corrige assinaturas conflitantes
"""
import sys, re

def fix_self(c):
    """Garante que todo metodo com self-> tenha self como parametro."""
    linhas = c.split('\n')
    saida = []
    i = 0
    while i < len(linhas):
        l = linhas[i]
        # Detecta inicio de funcao
        m = re.match(r'^(\w+[\w\s\*]*)\s+(\w+)\(([^)]*)\)\s*\{', l)
        if m:
            ret, nome, params = m.groups()
            # Coleta corpo
            corpo = [l]
            prof = 1
            j = i + 1
            while j < len(linhas) and prof > 0:
                for ch in linhas[j]:
                    if ch == '{': prof += 1
                    elif ch == '}': prof -= 1
                corpo.append(linhas[j])
                j += 1
            # Verifica se usa self->
            usa_self = any('self->' in x for x in corpo)
            # Verifica se params ja tem self
            tem_self = 'self' in params
            if usa_self and not tem_self:
                # Adiciona self
                if params.strip():
                    novo_params = f"void* self, {params}"
                else:
                    novo_params = "void* self"
                # Renomeia todos os tipos void* pra tipo especifico
                # Primeiro, normaliza: se era 'Image* arg0' e agora precisa virar 'void* self, Image* arg0'
                nova_linha = f"{ret} {nome}({novo_params}) {{"
                corpo[0] = nova_linha
                # Como self eh void*, precisamos typedef void* pra todos
                # Adiciona cast no inicio
                corpo.insert(1, f"    // self eh void*, cast pra tipo real nao necessario em C")
            saida.extend(corpo)
            i = j
            continue
        saida.append(l)
        i += 1
    return '\n'.join(saida)

def fix_prototipos(c):
    """Remove prototipos que conflitam com definicoes."""
    # Coleta definicoes reais
    definicoes = {}
    for m in re.finditer(r'^(\w+[\w\s\*]*)\s+(\w+)\(([^)]*)\)\s*\{', c, re.MULTILINE):
        ret, nome, params = m.groups()
        definicoes[nome] = (ret, params)
    # Remove prototipos que conflitam
    linhas = c.split('\n')
    saida = []
    for l in linhas:
        m = re.match(r'^(\w+[\w\s\*]*)\s+(\w+)\(([^)]*)\)\s*;$', l)
        if m:
            ret, nome, params = m.groups()
            if nome in definicoes:
                # Substitui pelo correto
                ret2, params2 = definicoes[nome]
                saida.append(f"{ret2} {nome}({params2});")
                continue
        saida.append(l)
    return '\n'.join(saida)

def fix_chamadas(c):
    """Corrige chamadas com numero errado de args."""
    # j2me_image_blit: sempre 3 args (img, x, y)
    def fix_blit(m):
        args = m.group(1).split(',')
        # Pega so os 3 primeiros
        args = [a.strip() for a in args][:3]
        return f"j2me_image_blit({', '.join(args)})"
    c = re.sub(r'j2me_image_blit\(([^;]+?)\)(?!\s*;)', fix_blit, c)
    # MatrixImage_paint: 3 args
    return c

def fix_campos_estaticos(c):
    """Declara campos estaticos (Game_count, MapCanvas_OFFY, etc) como globais."""
    # Coleta todos os X_Y referenciados
    padrao = r'\b([A-Z]\w+)_([A-Za-z]\w*)\b'
    refs = set()
    for m in re.finditer(padrao, c):
        nome = f"{m.group(1)}_{m.group(2)}"
        # Filtra os que NAO sao funcoes (funcao tem parenteses depois)
        pos = m.end()
        if pos < len(c) and c[pos] == '(':
            continue
        refs.add((m.group(1), m.group(2)))
    # Declara como int (default)
    decls = []
    for cls, campo in sorted(refs):
        decls.append(f"int {cls}_{campo};")
    # Insere depois dos typedefs
    marker = "typedef void* Canvas;"
    if marker in c:
        c = c.replace(marker, marker + "\n\n// Globais auto-declarados\n" + "\n".join(decls))
    return c

def fix_labels_faltantes(c):
    """Adiciona labels faltantes no final de cada funcao."""
    linhas = c.split('\n')
    saida = []
    for i, l in enumerate(linhas):
        saida.append(l)
    # Pega todos os labels usados
    labels_usados = set(re.findall(r'goto (L_\d+)', c))
    labels_definidos = set(re.findall(r'^(L_\d+):', c, re.MULTILINE))
    faltam = labels_usados - labels_definidos
    if faltam:
        print(f"  Labels faltando: {len(faltam)}")
        # Adiciona todos antes do ultimo }
        # Pega o ultimo }
        idx = c.rfind('}')
        # Pega o ultimo // antes do }
        antes = c[:idx]
        adicao = "\n// Labels faltantes\n" + "\n".join(f"{lbl}:;" for lbl in sorted(faltam)) + "\n"
        c = antes + adicao + c[idx:]
    return c

def main():
    if len(sys.argv) < 2:
        print("Uso: python fix_compilacao.py <entrada.c> [saida.c]")
        sys.exit(1)
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada.replace(".c", "_fix.c")
    with open(entrada) as f:
        c = f.read()
    print("Aplicando fixes...")
    c = fix_chamadas(c)
    print("  [1/5] Chamadas ajustadas")
    c = fix_campos_estaticos(c)
    print("  [2/5] Campos estaticos declarados")
    c = fix_self(c)
    print("  [3/5] self adicionado aos metodos")
    c = fix_prototipos(c)
    print("  [4/5] Prototipos corrigidos")
    c = fix_labels_faltantes(c)
    print("  [5/5] Labels faltantes adicionados")
    with open(saida, "w") as f:
        f.write(c)
    print(f"Gerado: {saida}")

if __name__ == "__main__":
    main()
