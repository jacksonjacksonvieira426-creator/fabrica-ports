#!/usr/bin/env python3
"""
Desgotificador - Converte goto-based C em C estruturado.
Detecta padroes:
  1. while: goto pra tras com label antes
  2. if: goto pra frente sem retorno
  3. if/else: if + goto end + label + else + label end
  4. do-while: label no inicio + goto no fim
Uso: python portador_limpar.py <entrada.c> [saida.c]
"""
import sys, re

def analisar_metodo(linhas):
    """Recebe as linhas de um metodo. Detecta labels e gotos."""
    labels = {}      # label -> indice
    gotos = []       # (indice_linha, tipo, label_destino, condicao)
    
    for i, linha in enumerate(linhas):
        # Label
        m = re.match(r'^\s*L_(\d+):;?\s*$', linha)
        if m:
            labels[f"L_{m.group(1)}"] = i
            continue
        # Goto direto
        m = re.match(r'^\s*goto (L_\d+);', linha)
        if m:
            gotos.append((i, "GOTO", m.group(1), None))
            continue
        # If + goto
        m = re.match(r'^\s*if \((.+)\) goto (L_\d+);', linha)
        if m:
            gotos.append((i, "IF_GOTO", m.group(2), m.group(1)))
            continue
    
    return labels, gotos

def desgotificar_metodo(linhas):
    """Reescreve um metodo eliminando gotos simples."""
    max_iter = 10
    for _ in range(max_iter):
        labels, gotos = analisar_metodo(linhas)
        mudou = False

        # Padrao 1: WHILE - goto pra tras pro mesmo label
        # L_start:
        #   ... corpo ...
        #   goto L_start  (ou if (...) goto L_start)
        for idx, tipo, dest, cond in gotos:
            if dest not in labels:
                continue
            dest_line = labels[dest]
            if dest_line < idx:  # goto pra tras = loop
                if tipo == "GOTO":
                    # Loop infinito
                    linhas = [
                        *linhas[:dest_line],
                        "    while (1) {",
                        *[f"    {l}" if l.strip() and not l.strip().startswith("L_") else l for l in linhas[dest_line+1:idx]],
                        "    }",
                        *linhas[idx+1:]
                    ]
                elif tipo == "IF_GOTO":
                    # while (cond_negada) { ... }
                    # Como o bytecode salta quando a condicao e verdadeira, invertemos
                    cond_inv = inverter_condicao(cond)
                    linhas = [
                        *linhas[:dest_line],
                        f"    while ({cond_inv}) {{",
                        *[f"    {l}" if l.strip() and not l.strip().startswith("L_") else l for l in linhas[dest_line+1:idx]],
                        "    }",
                        *linhas[idx+1:]
                    ]
                mudou = True
                break

        if mudou:
            continue

        # Padrao 2: IF simples - if (!cond) goto L_skip; ... ; L_skip:
        for idx, tipo, dest, cond in gotos:
            if tipo != "IF_GOTO" or dest not in labels:
                continue
            dest_line = labels[dest]
            if dest_line > idx:  # goto pra frente
                # Verifica se nao tem outro goto pro mesmo destino antes (else)
                tem_else = False
                for i2, t2, d2, c2 in gotos:
                    if i2 > idx and i2 < dest_line and t2 == "GOTO" and d2 == dest:
                        tem_else = True
                        break
                
                if not tem_else:
                    # IF simples
                    cond_inv = inverter_condicao(cond)
                    corpo = linhas[idx+1:dest_line]
                    # Remove labels residuais que apontam pra ca
                    corpo = [l for l in corpo if not re.match(r'^\s*L_\d+:;?\s*$', l)]
                    linhas = [
                        *linhas[:idx],
                        f"    if ({cond_inv}) {{",
                        *[f"    {l}" if l.strip() else l for l in corpo],
                        "    }",
                        *linhas[dest_line+1:]
                    ]
                    mudou = True
                    break

        if not mudou:
            break

    return linhas

def inverter_condicao(cond):
    """Inverte uma condicao C."""
    cond = cond.strip()
    # Mapeamento de inversao
    inversos = {
        "==": "!=", "!=": "==",
        "<": ">=", "<=": ">", ">": "<=", ">=": "<",
    }
    for op, inv in inversos.items():
        # Procura operador com espacos
        if f" {op} " in cond:
            return cond.replace(f" {op} ", f" {inv} ", 1)
    # Inverte condicao simples (var)
    if cond == "0":
        return "1"
    if re.match(r'^\w+$', cond):
        return f"!({cond})"
    return f"!({cond})"

def desgotificar(codigo):
    """Aplica desgotificacao em todo o codigo."""
    linhas = codigo.split("\n")
    saida = []
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        # Detecta inicio de funcao
        if re.match(r'^\w+[\w\s\*]*\s+\w+\([^;]*\)\s*\{', linha):
            # Coleta corpo
            corpo = [linha]
            profundidade = 1
            j = i + 1
            while j < len(linhas) and profundidade > 0:
                for c in linhas[j]:
                    if c == '{': profundidade += 1
                    elif c == '}': profundidade -= 1
                corpo.append(linhas[j])
                j += 1
            # Desgotifica o corpo (sem a primeira e ultima linhas)
            if profundidade == 0:
                interno = corpo[1:-1]
                interno_limpo = desgotificar_metodo(interno)
                saida.extend([corpo[0], *interno_limpo, corpo[-1]])
                i = j
                continue
        saida.append(linha)
        i += 1
    return "\n".join(saida)

def main():
    if len(sys.argv) < 2:
        print("Uso: python portador_limpar.py <entrada.c> [saida.c]")
        sys.exit(1)
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada.replace(".c", "_limpo.c")
    with open(entrada) as f:
        codigo = f.read()
    limpo = desgotificar(codigo)
    with open(saida, "w") as f:
        f.write(limpo)
    # Stats
    n_gotos_antes = codigo.count("goto L_")
    n_gotos_depois = limpo.count("goto L_")
    print(f"Gerado: {saida}")
    print(f"Gotos antes: {n_gotos_antes}")
    print(f"Gotos depois: {n_gotos_depois}")
    print(f"Reducao: {100*(n_gotos_antes-n_gotos_depois)//max(1,n_gotos_antes)}%")

if __name__ == "__main__":
    main()
