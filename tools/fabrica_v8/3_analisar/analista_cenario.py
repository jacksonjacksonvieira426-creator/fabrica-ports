#!/usr/bin/env python3
"""
Analista de Cenario - Le o paint.txt e descreve como o jogo desenha.
Uso: python analista_cenario.py <paint.txt>
Gera: JSON com o pipeline de desenho
"""
import sys, re, json

def analisar(caminho):
    with open(caminho) as f:
        linhas = f.readlines()
    
    chamadas = []
    for linha in linhas:
        m = re.match(r'^\[\s*(\d+)\]\s+(.+)$', linha.strip())
        if not m: continue
        idx = int(m.group(1))
        instr = m.group(2)
        
        # Detecta chamadas de desenho
        if "Graphics.fillRect" in instr:
            chamadas.append({"idx": idx, "tipo": "fill_rect", "api": "j2me_gfx_fill_rect"})
        elif "Graphics.setColor" in instr:
            chamadas.append({"idx": idx, "tipo": "set_color", "api": "j2me_gfx_set_color"})
        elif "Graphics.drawImage" in instr:
            chamadas.append({"idx": idx, "tipo": "draw_image", "api": "j2me_image_blit"})
        elif "Graphics.drawRegion" in instr:
            chamadas.append({"idx": idx, "tipo": "draw_region", "api": "j2me_image_draw_region"})
        elif "Graphics.drawString" in instr:
            chamadas.append({"idx": idx, "tipo": "draw_string", "api": "j2me_font_draw"})
        elif "Graphics.setClip" in instr:
            chamadas.append({"idx": idx, "tipo": "set_clip", "api": "j2me_clip_push"})
        elif "Graphics.setFont" in instr:
            chamadas.append({"idx": idx, "tipo": "set_font", "api": "j2me_noop"})
        elif "Graphics.getFont" in instr:
            chamadas.append({"idx": idx, "tipo": "get_font", "api": "j2me_noop"})
    
    # Conta tipos
    resumo = {}
    for c in chamadas:
        resumo[c["tipo"]] = resumo.get(c["tipo"], 0) + 1
    
    # Detecta padroes
    padroes = []
    if resumo.get("draw_image", 0) > 0:
        padroes.append("usa imagens blit")
    if resumo.get("draw_region", 0) > 0:
        padroes.append("usa sprites recortados (tiles)")
    if resumo.get("fill_rect", 0) > 0:
        padroes.append("desenha formas geometricas")
    if resumo.get("draw_string", 0) > 0:
        padroes.append("desenha texto (HUD)")
    
    return {
        "total_instrucoes": len(chamadas),
        "resumo": resumo,
        "padroes": padroes,
        "sequencia": chamadas[:50],  # primeiras 50
    }

if __name__ == "__main__":
    r = analisar(sys.argv[1])
    print(json.dumps(r, indent=2, ensure_ascii=False))
