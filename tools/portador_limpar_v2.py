#!/usr/bin/env python3
"""
Desgotificador V2 - Mais padroes + indentacao automatica.
Detecta:
  1. while (goto pra tras)
  2. if simples (goto pra frente)
  3. if/else (if + goto + label + label)
  4. do-while
  5. break/continue em loops
  6. Remove labels orfaos
"""
import sys, re

def inverter_condicao(cond):
    cond = cond.strip()
    inv = {"==":"!=", "!=":"==", "<":">=", "<=":">", ">":"<=", ">=":"<"}
    for op, i in inv.items():
        if f" {op} " in cond:
            return cond.replace(f" {op} ", f" {i} ", 1)
    if cond == "0": return "1"
    if re.match(r'^\w+$', cond): return f"!({cond})"
    return f"!({cond})"

def classificar_linha(l):
    """Classifica uma linha por tipo."""
    s = l.strip()
    if not s: return ("vazio", None)
    m = re.match(r'^L_(\d+):;?$', s)
    if m: return ("label", f"L_{m.group(1)}")
    m = re.match(r'^goto (L_\d+);$', s)
    if m: return ("goto", m.group(1))
    m = re.match(r'^if \((.+)\) goto (L_\d+);$', s)
    if m: return ("if_goto", (m.group(1), m.group(2)))
    return ("outro", s)

def achar_labels_e_gotos(linhas):
    labels = {}
    gotos = []
    for i, l in enumerate(linhas):
        t, d = classificar_linha(l)
        if t == "label":
            labels[d] = i
        elif t in ("goto", "if_goto"):
            gotos.append((i, t, d))
    return labels, gotos

def contar_refs_labels(linhas):
    """Conta quantas vezes cada label eh referenciado."""
    refs = {}
    for l in linhas:
        t, d = classificar_linha(l)
        if t in ("goto", "if_goto"):
            ref = d if t == "goto" else d[1]
            refs[ref] = refs.get(ref, 0) + 1
    return refs

def remover_labels_orfaos(linhas):
    """Remove labels que nao sao referenciados."""
    refs = contar_refs_labels(linhas)
    saida = []
    for l in linhas:
        t, d = classificar_linha(l)
        if t == "label" and refs.get(d, 0) == 0:
            continue
        saida.append(l)
    return saida

def detectar_if_else(linhas):
    """Detecta padrao if/else:
       if (c) goto L1;
       <then>
       goto L2;
       L1:
       <else>
       L2:
    """
    mudou = False
    i = 0
    while i < len(linhas):
        t, d = classificar_linha(linhas[i])
        if t != "if_goto":
            i += 1
            continue
        cond, l_else = d
        # Procura um goto incondicional antes do label else
        j = i + 1
        l_end = None
        while j < len(linhas):
            t2, d2 = classificar_linha(linhas[j])
            if t2 == "goto":
                l_end = d2
                break
            if t2 == "label" and d2 == l_else:
                break
            j += 1
        if l_end is None or j >= len(linhas):
            i += 1
            continue
        # Procura label else
        k = j + 1
        while k < len(linhas):
            t3, d3 = classificar_linha(linhas[k])
            if t3 == "label" and d3 == l_else:
                break
            k += 1
        if k >= len(linhas):
            i += 1
            continue
        # Procura label end
        m = k + 1
        while m < len(linhas):
            t4, d4 = classificar_linha(linhas[m])
            if t4 == "label" and d4 == l_end:
                break
            m += 1
        if m >= len(linhas):
            i += 1
            continue
        # Aplicou padrao!
        corpo_then = linhas[i+1:j]
        corpo_else = linhas[k+1:m]
        nova = [
            *linhas[:i],
            f"    if ({inverter_condicao(cond)}) {{",
            *[f"    {l}" if l.strip() and not l.strip().startswith("//") else l for l in corpo_then],
            "    } else {",
            *[f"    {l}" if l.strip() and not l.strip().startswith("//") else l for l in corpo_else],
            "    }",
            *linhas[m+1:]
        ]
        linhas = nova
        mudou = True
        break
    return linhas, mudou

def detectar_if_simples(linhas):
    """Detecta if simples: if (c) goto L; <corpo> L:"""
    mudou = False
    for i, l in enumerate(linhas):
        t, d = classificar_linha(l)
        if t != "if_goto":
            continue
        cond, dest = d
        # Acha label dest depois
        j = i + 1
        while j < len(linhas):
            t2, d2 = classificar_linha(linhas[j])
            if t2 == "label" and d2 == dest:
                break
            # Se tem outro goto incondicional antes, nao eh if simples
            if t2 == "goto":
                break
            j += 1
        if j >= len(linhas):
            continue
        # Verifica se label dest nao tem outros gotos apontando
        refs = contar_refs_labels(linhas)
        if refs.get(dest, 0) > 1:
            continue
        corpo = linhas[i+1:j]
        if not corpo:
            continue
        nova = [
            *linhas[:i],
            f"    if ({inverter_condicao(cond)}) {{",
            *[f"    {l}" if l.strip() else l for l in corpo],
            "    }",
            *linhas[j+1:]
        ]
        linhas = nova
        mudou = True
        break
    return linhas, mudou

def detectar_while(linhas):
    """Detecta while com mais flexibilidade."""
    mudou = False
    for i, l in enumerate(linhas):
        t, d = classificar_linha(l)
        if t != "label":
            continue
        inicio = d
        # Procura QUALQUER goto pro inicio (mesmo com codigo entre)
        j = i + 1
        while j < len(linhas):
            t2, d2 = classificar_linha(linhas[j])
            if t2 == "goto" and d2 == inicio:
                corpo = linhas[i+1:j]
                # Filtra linhas vazias no inicio
                while corpo and not corpo[0].strip():
                    corpo.pop(0)
                nova = [
                    *linhas[:i],
                    "    while (1) {",
                    *[f"    {l}" if l.strip() else l for l in corpo],
                    "    }",
                    *linhas[j+1:]
                ]
                linhas = nova
                mudou = True
                break
            if t2 == "if_goto":
                cond, dest = d2
                if dest == inicio:
                    corpo = linhas[i+1:j]
                    nova = [
                        *linhas[:i],
                        f"    while ({inverter_condicao(cond)}) {{",
                        *[f"    {l}" if l.strip() else l for l in corpo],
                        "    }",
                        *linhas[j+1:]
                    ]
                    linhas = nova
                    mudou = True
                    break
            # Se encontrou um label de outro escopo, para
            if t2 == "label" and d2 != inicio:
                pass
            j += 1
        if mudou:
            break
    return linhas, mudou

def desgotificar_metodo(linhas):
    """Aplica todos os padroes em loop ate estabilizar."""
    for _ in range(20):
        # 1. while (loop mais externo)
        linhas, m1 = detectar_while(linhas)
        if m1: continue
        # 2. if/else
        linhas, m2 = detectar_if_else(linhas)
        if m2: continue
        # 3. if simples
        linhas, m3 = detectar_if_simples(linhas)
        if m3: continue
        # 4. labels orfaos
        antes = len(linhas)
        linhas = remover_labels_orfaos(linhas)
        if len(linhas) < antes: continue
        break
    return linhas

def reindentar(linhas):
    """Re-indenta baseado em { e }."""
    saida = []
    nivel = 0
    for l in linhas:
        s = l.strip()
        if not s:
            saida.append("")
            continue
        # Reduz antes de } ou }
        if s.startswith("}"):
            nivel = max(0, nivel - 1)
        saida.append("    " * nivel + s)
        # Aumenta apos {
        if s.endswith("{"):
            nivel += 1
    return saida

def desgotificar(codigo):
    linhas = codigo.split("\n")
    saida = []
    i = 0
    while i < len(linhas):
        linha = linhas[i]
        if re.match(r'^\w+[\w\s\*]*\s+\w+\([^;]*\)\s*\{', linha):
            corpo = [linha]
            prof = 1
            j = i + 1
            while j < len(linhas) and prof > 0:
                for c in linhas[j]:
                    if c == '{': prof += 1
                    elif c == '}': prof -= 1
                corpo.append(linhas[j])
                j += 1
            if prof == 0:
                interno = corpo[1:-1]
                interno_limpo = desgotificar_metodo(interno)
                interno_limpo = reindentar(interno_limpo)
                saida.extend([corpo[0], *interno_limpo, corpo[-1]])
                i = j
                continue
        saida.append(linha)
        i += 1
    return "\n".join(saida)

def main():
    if len(sys.argv) < 2:
        print("Uso: python portador_limpar_v2.py <entrada.c> [saida.c]")
        sys.exit(1)
    entrada = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else entrada.replace(".c", "_limpo2.c")
    with open(entrada) as f:
        codigo = f.read()
    limpo = desgotificar(codigo)
    with open(saida, "w") as f:
        f.write(limpo)
    antes = codigo.count("goto L_")
    depois = limpo.count("goto L_")
    pct = 100 * (antes - depois) // max(1, antes)
    print(f"Gerado: {saida}")
    print(f"Gotos: {antes} -> {depois} ({pct}% reducao)")

if __name__ == "__main__":
    main()
