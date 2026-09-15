#!/usr/bin/env python3
"""
Tradutor de Padroes - Traduz bytecode comum pra C automaticamente.
Cobre 60-70% dos metodos. Os complexos ficam pra IA.
Uso: python tradutor_padroes.py <metodo.txt>
"""
import sys, re, os

# Mapeamento de APIs J2ME -> C
API_MAP = {
    "Graphics.setColor":   "j2me_gfx_set_color",
    "Graphics.fillRect":   "j2me_gfx_fill_rect",
    "Graphics.drawString": "j2me_font_draw",
    "Graphics.drawImage":  "j2me_image_blit",
    "Graphics.drawRegion": "j2me_image_draw_region",
    "Graphics.setClip":    "j2me_clip_push",
    "Graphics.drawLine":   "j2me_gfx_draw_line",
    "Graphics.drawRect":   "j2me_gfx_draw_rect",
    "Canvas.getWidth":     "SCR_W",
    "Canvas.getHeight":    "SCR_H",
    "Canvas.getGameAction":"j2me_input_get_actions",
    "Canvas.repaint":      "j2me_canvas_repaint",
    "Thread.sleep":        "j2me_sleep",
    "Random.nextInt":      "j2me_random_next",
    "Random.<init>":       "j2me_random_init",
    "Image.createImage":   "j2me_image_create",
    "Image.getGraphics":   "j2me_image_get_graphics",
    "System.currentTimeMillis": "j2me_time_ms",
    "Math.abs":            "abs",
    "Math.max":            "MAX",
    "Math.min":            "MIN",
    "Object.<init>":       "/* skip */",
    "Integer.<init>":      "/* skip */",
    "Integer.parseInt":    "atoi",
    "StringBuffer.<init>": "/* skip */",
    "StringBuffer.append": "/* skip */",
    "StringBuffer.toString": "/* skip */",
}

def classificar_instrucao(linha):
    m = re.match(r'^\[\s*(\d+)\]\s+(.+)$', linha.strip())
    if not m: return None
    return int(m.group(1)), m.group(2).strip()

def tradutor_simples(instr):
    """Traduz instrucoes simples e retorna (tipo, operacao)."""
    # Constants
    if instr.startswith("iconst_"):
        n = instr.replace("iconst_m1", "-1").replace("iconst_", "")
        return ("push", n)
    if instr.startswith("bipush ") or instr.startswith("sipush "):
        return ("push", instr.split()[-1])
    if instr.startswith("sipush "):
        return ("push", instr.split()[-1])
    
    # Loads
    if instr == "aload_0": return ("load", "self")
    if instr.startswith("aload_"): return ("load", f"arg{instr[-1]}")
    if instr.startswith("iload_"): return ("load", f"arg{instr[-1]}")
    
    # Return
    if instr == "return": return ("return", None)
    
    return None

def traduzir(caminho):
    with open(caminho) as f:
        linhas = [l for l in f.readlines()]
    
    # Header
    classe = "?"
    metodo = "?"
    desc = "?"
    for l in linhas[:6]:
        if "Classe:" in l: classe = l.split(":")[-1].strip()
        if "Metodo:" in l: metodo = l.split(":")[-1].strip()
        if "Descritor:" in l: desc = l.split(":")[-1].strip()
    
    # Parse instrucoes
    instrucoes = []
    for l in linhas:
        r = classificar_instrucao(l)
        if r: instrucoes.append(r)
    
    if not instrucoes:
        return None
    
    # Analise: pilha simulada
    pilha = []
    codigo = []
    sucesso = True
    
    i = 0
    while i < len(instrucoes):
        idx, instr = instrucoes[i]
        
        # ==== PADRAO 1: field = constante ====
        # aload_0; iconst_N; putfield X
        if (instr == "aload_0" and i + 2 < len(instrucoes) and
            instrucoes[i+1][1].startswith(("iconst_", "bipush", "sipush")) and
            instrucoes[i+2][1].startswith("putfield")):
            valor = instrucoes[i+1][1].replace("iconst_", "").replace("bipush ", "").replace("sipush ", "")
            campo = instrucoes[i+2][1].split()[-1].split(".")[-1]
            codigo.append(f"    self->{campo} = {valor};  // [{idx}]")
            i += 3
            continue
        
        # ==== PADRAO 2: getfield + getfield + op + putfield ====
        # aload_0; getfield X; aload_0; getfield Y; op; putfield Z
        if (instr == "aload_0" and i + 6 < len(instrucoes)):
            if (instrucoes[i+1][1].startswith("getfield") and
                instrucoes[i+2][1] == "aload_0" and
                instrucoes[i+3][1].startswith("getfield") and
                instrucoes[i+4][1] in ("iadd", "isub", "imul", "idiv", "irem") and
                instrucoes[i+5][1].startswith("putfield")):
                c1 = instrucoes[i+1][1].split()[-1].split(".")[-1]
                c2 = instrucoes[i+3][1].split()[-1].split(".")[-1]
                op = {"iadd":"+","isub":"-","imul":"*","idiv":"/","irem":"%"}[instrucoes[i+4][1]]
                c3 = instrucoes[i+5][1].split()[-1].split(".")[-1]
                codigo.append(f"    self->{c3} = self->{c1} {op} self->{c2};  // [{idx}]")
                i += 6
                continue
        
        # ==== PADRAO 3: if_icmpne + goto ====
        # getfield X; iconst_N; if_icmpne +off
        if i + 2 < len(instrucoes):
            if (instrucoes[i][1].startswith("getfield") and
                instrucoes[i+1][1].startswith("iconst") and
                instrucoes[i+2][1].startswith("if_icmp")):
                campo = instrucoes[i][1].split()[-1].split(".")[-1]
                valor = instrucoes[i+1][1].replace("iconst_", "")
                op = {"if_icmpeq":"==","if_icmpne":"!=","if_icmplt":"<","if_icmpge":">=",
                      "if_icmple":"<=","if_icmpgt":">"}[instrucoes[i+2][1].split()[0]]
                codigo.append(f"    if (self->{campo} {op} {valor}) goto ...;  // [{idx}]")
                i += 3
                continue
        
        # ==== PADRAO 4: chamada de API ====
        if instr.startswith("invokevirtual") or instr.startswith("invokestatic"):
            api_completa = instr.split()[-1]
            api = api_completa.split(".")[-2] + "." + api_completa.split(".")[-1] if "." in api_completa else api_completa
            # Tenta mapear
            for k, v in API_MAP.items():
                if k in instr:
                    codigo.append(f"    {v}(/* args */);  // [{idx}] {k}")
                    i += 1
                    break
            else:
                codigo.append(f"    // [{idx}] {instr} (TODO)")
                sucesso = False
                i += 1
            continue
        
        # ==== PADRAO 5: return ====
        if instr == "return":
            codigo.append(f"    return;  // [{idx}]")
            i += 1
            continue
        
        # Nao reconhecido
        codigo.append(f"    // [{idx}] {instr} (nao traduzido)")
        sucesso = False
        i += 1
    
    return {
        "classe": classe,
        "metodo": metodo,
        "desc": desc,
        "codigo": "\n".join(codigo),
        "sucesso": sucesso,
        "n_instrucoes": len(instrucoes),
        "n_nao_traduzidas": sum(1 for l in codigo if "nao traduzido" in l),
    }

def main():
    if len(sys.argv) < 2:
        print("Uso: python tradutor_padroes.py <metodo.txt>")
        sys.exit(1)
    
    r = traduzir(sys.argv[1])
    if not r:
        print("ERRO: nao foi possivel traduzir")
        sys.exit(1)
    
    print(f"// {r['classe']}.{r['metodo']} - {r['n_instrucoes']} instrucoes")
    print(f"// Traduzidas: {r['n_instrucoes'] - r['n_nao_traduzidas']}")
    print(f"// Nao traduzidas: {r['n_nao_traduzidas']}")
    print()
    print(f"void {r['classe']}_{r['metodo']}_fn(void* self, ...) {{")
    print(r['codigo'])
    print("}")

if __name__ == "__main__":
    main()
