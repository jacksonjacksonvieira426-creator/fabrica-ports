#!/usr/bin/env python3
"""
Gerador V2 - Detecta padroes e gera codigo real (nao so stubs).
Uso: python portador_gerar_v2.py <estrutura.json> [saida.c]
"""
import sys, os, json, re

MAPA_API = {
    "javax/microedition/lcdui/Graphics.setColor":     "j2me_gfx_set_color",
    "javax/microedition/lcdui/Graphics.fillRect":     "j2me_gfx_fill_rect",
    "javax/microedition/lcdui/Graphics.drawString":   "j2me_font_draw",
    "javax/microedition/lcdui/Graphics.drawImage":    "j2me_image_blit",
    "javax/microedition/lcdui/Graphics.drawRegion":   "j2me_image_draw_region",
    "javax/microedition/lcdui/Graphics.setClip":      "j2me_clip_push",
    "javax/microedition/lcdui/Image.createImage":     "j2me_image_create",
    "javax/microedition/lcdui/Canvas.getWidth":       "j2me_canvas_w",
    "javax/microedition/lcdui/Canvas.getHeight":      "j2me_canvas_h",
    "javax/microedition/lcdui/Canvas.repaint":        "j2me_canvas_repaint",
    "javax/microedition/lcdui/Canvas.getGameAction":  "j2me_input_get_actions",
    "java/lang/System.currentTimeMillis":             "j2me_time_ms",
    "java/util/Random.nextInt":                       "j2me_random_next",
    "java/lang/Thread.sleep":                         "j2me_sleep",
    "java/lang/Math.abs":                             "abs",
    "java/lang/Object.<init>":                        "j2me_noop",
}

def sanitizar(nome):
    if not nome: return "campo"
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        if nome[0].isdigit(): return f"_{nome}"
        return nome
    codepoint = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{codepoint:04x}"

def detectar_papel(classe, metodo):
    """Detecta o papel do metodo pra gerar codigo especifico."""
    nome = metodo["nome"]
    if nome == "paint": return "PAINT"
    if nome in ("keyPressed", "keyProc"): return "INPUT"
    if nome == "run": return "RUN"
    if nome in ("<init>", "constructor"): return "INIT"
    if nome == "startApp": return "START"
    if nome == "reset": return "RESET"
    if nome.startswith("forward") or nome.startswith("backward"): return "MOVE"
    if nome.startswith("punch") or nome.startswith("kick") or nome.startswith("fire"): return "ATTACK"
    return "GENERICO"

def gerar_corpo_paint(classe, metodo, nome_classe):
    """Gera corpo do paint - detecta chamadas de draw."""
    linhas = []
    linhas.append("    // Auto-gerado: sequencia de desenho detectada")
    if metodo["chamadas"]:
        for idx, api in metodo["chamadas"][:10]:
            if "setColor" in api:
                linhas.append(f"    // {api} -> j2me_gfx_set_color(cor)")
            elif "fillRect" in api:
                linhas.append(f"    // {api} -> j2me_gfx_fill_rect(x, y, w, h)")
            elif "drawImage" in api:
                linhas.append(f"    // {api} -> j2me_image_blit(img, x, y)")
            elif "drawRegion" in api:
                linhas.append(f"    // {api} -> j2me_image_draw_region(...)")
            elif "drawString" in api:
                linhas.append(f"    // {api} -> j2me_font_draw(texto, x, y)")
    linhas.append("    // TODO: chamar as funcoes acima com valores corretos")
    return linhas

def gerar_corpo_input(classe, metodo, nome_classe):
    """Gera corpo do keyPressed."""
    linhas = []
    linhas.append("    // Auto-gerado: leitura de input do PSP")
    linhas.append("    j2me_input_update();")
    linhas.append("    int acoes = j2me_input_get_actions();")
    linhas.append("    // TODO: tratar cada direcao/acao conforme o jogo original")
    if metodo["apis"]:
        for api, cnt in metodo["apis"].items():
            if "getGameAction" in api:
                linhas.append(f"    // {api} -> acoes")
                break
    linhas.append("    (void)acoes;")
    return linhas

def gerar_corpo_run(classe, metodo, nome_classe):
    """Gera corpo do thread/run - game loop."""
    linhas = []
    linhas.append("    // Auto-gerado: loop principal detectado")
    linhas.append("    while (1) {")
    linhas.append("        j2me_input_update();")
    linhas.append("        if (j2me_input_should_quit()) break;")
    linhas.append("        // TODO: logica do loop")
    linhas.append("        j2me_gfx_begin_frame();")
    linhas.append("        j2me_gfx_clear(0x101020);")
    linhas.append("        // TODO: chamar paint()")
    linhas.append("        j2me_gfx_flip();")
    if any("Thread.sleep" in a for a in metodo["apis"]):
        linhas.append("        j2me_sleep(16);  // ~60fps (do Thread.sleep original)")
    linhas.append("    }")
    return linhas

def gerar_corpo_init(classe, metodo, nome_classe):
    """Gera corpo do construtor com valores default das constantes."""
    linhas = []
    if metodo["constantes"]:
        linhas.append("    // Auto-gerado: valores default detectados no bytecode")
        for idx, valor in metodo["constantes"][:8]:
            linhas.append(f"    // campo = {valor};  // (offset {idx})")
    linhas.append("    // TODO: inicializar campos da struct")
    return linhas

def gerar_corpo_reset(classe, metodo, nome_classe):
    """Reset do personagem - zera posicao, status, hp."""
    linhas = []
    linhas.append("    // Auto-gerado: reset padrao de personagem")
    linhas.append("    // TODO: ajustar valores baseado no bytecode original")
    if metodo["constantes"]:
        for idx, valor in metodo["constantes"][:6]:
            linhas.append(f"    // valor detectado: {valor}")
    return linhas

def gerar_corpo_attack(classe, metodo, nome_classe):
    """Punch/kick/fire - seta estado de ataque."""
    nome = metodo["nome"]
    linhas = []
    linhas.append(f"    // Auto-gerado: acao de ataque ({nome})")
    if "punch" in nome:
        linhas.append("    self->status = ST_SOCO;  // TODO: verificar nome do campo")
    elif "kick" in nome:
        linhas.append("    self->status = ST_CHUTE;  // TODO: verificar nome do campo")
    elif "fire" in nome:
        linhas.append("    // TODO: criar projetil")
    linhas.append("    self->count = 20;  // duracao padrao")
    return linhas

def gerar_corpo_generico(classe, metodo, nome_classe):
    """Fallback: gera TODOs com dicas do bytecode."""
    linhas = []
    linhas.append("    // TODO: traduzir logica do bytecode")
    # Dicas das chamadas
    if metodo["chamadas"]:
        linhas.append("    // Chamadas detectadas:")
        for idx, api in metodo["chamadas"][:5]:
            trad = MAPA_API.get(api, f"??? {api}")
            linhas.append(f"    //   [{idx}] {api} -> {trad}")
    # Dicas dos campos
    if metodo["fields"]:
        linhas.append("    // Acesso a campos:")
        for idx, op, campo in metodo["fields"][:4]:
            linhas.append(f"    //   [{idx}] {op} {campo}")
    return linhas

def gerar_stub(classe, metodo, nomes_usados):
    """Gera stub inteligente baseado no papel do metodo."""
    nome_orig = metodo["nome"]
    nome = nome_orig.replace("<init>", "constructor").replace("-", "_")
    nome = sanitizar(nome)
    nome_classe = sanitizar(classe["nome"])

    # Nome unico
    chave = f"{nome_classe}_{nome}"
    nome_final = chave
    contador = 1
    while nome_final in nomes_usados:
        contador += 1
        nome_final = f"{chave}_{contador}"
    nomes_usados.add(nome_final)

    tipo_ret = metodo["tipo_ret"]
    papel = detectar_papel(classe, metodo)

    linhas = []
    linhas.append(f"// === {classe['nome']}.{nome_orig} ({papel}) ===")
    linhas.append(f"// Instrucoes: {metodo['n_instr']}")
    linhas.append(f"{tipo_ret} {nome_final}() {{")

    # Gera corpo baseado no papel
    if papel == "PAINT":
        corpo = gerar_corpo_paint(classe, metodo, nome_classe)
    elif papel == "INPUT":
        corpo = gerar_corpo_input(classe, metodo, nome_classe)
    elif papel == "RUN":
        corpo = gerar_corpo_run(classe, metodo, nome_classe)
    elif papel == "INIT":
        corpo = gerar_corpo_init(classe, metodo, nome_classe)
    elif papel == "RESET":
        corpo = gerar_corpo_reset(classe, metodo, nome_classe)
    elif papel == "ATTACK":
        corpo = gerar_corpo_attack(classe, metodo, nome_classe)
    else:
        corpo = gerar_corpo_generico(classe, metodo, nome_classe)

    linhas.extend(corpo)

    if tipo_ret != "void":
        linhas.append(f"    return 0;  // TODO")
    linhas.append("}")
    return "\n".join(linhas)

def gerar_struct(classe):
    linhas = []
    linhas.append(f"// === Classe: {classe['nome']} (extends {classe['super']}) ===")
    linhas.append(f"// Padroes: {', '.join(classe['padroes']) or 'nenhum'}")
    linhas.append(f"struct {sanitizar(classe['nome'])}_s {{")
    for campo in classe["campos"]:
        nome_s = sanitizar(campo["nome"])
        linhas.append(f"    {campo['tipo_c']:<15} {nome_s};  // {campo['nome']}")
    if not classe["campos"]:
        linhas.append("    int _vazio;")
    linhas.append("};")
    return "\n".join(linhas)

def gerar_main_c(estrutura):
    nome = estrutura["nome_projeto"]
    linhas = []
    linhas.append(f"// {nome} - Port automatico J2ME -> PSP (v2)")
    linhas.append(f"// Gerado por portador_gerar_v2.py")
    linhas.append(f"// MIDlet: {estrutura['midlet']}  Canvas: {estrutura['canvas']}")
    linhas.append("")
    linhas.append("#include <pspkernel.h>")
    linhas.append("#include <string.h>")
    linhas.append("#include <stdlib.h>")
    linhas.append("#include <stdint.h>")
    linhas.append("#include \"j2me_gfx.h\"")
    linhas.append("#include \"j2me_font.h\"")
    linhas.append("#include \"j2me_input.h\"")
    linhas.append("#include \"j2me_image.h\"")
    linhas.append("#include \"j2me_clip.h\"")
    linhas.append("#include \"j2me_runtime.h\"")
    linhas.append("")
    linhas.append("// Tipos Java -> ponteiros opacos")
    linhas.append("typedef void* Image;")
    linhas.append("typedef void* Graphics;")
    linhas.append("typedef void* Font;")
    linhas.append("typedef void* String;")
    linhas.append("typedef void* Command;")
    linhas.append("typedef void* Display;")
    linhas.append("typedef void* Displayable;")
    linhas.append("typedef void* MIDlet;")
    linhas.append("typedef void* Canvas;")
    linhas.append("")
    linhas.append(f'PSP_MODULE_INFO("{nome}", 0, 1, 0);')
    linhas.append("PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);")
    linhas.append("")
    linhas.append("#define SCR_W 480")
    linhas.append("#define SCR_H 272")
    linhas.append("")
    linhas.append("// Forward declarations")
    for classe in estrutura["classes"]:
        n = sanitizar(classe["nome"])
        linhas.append(f"typedef struct {n}_s {n};")
    linhas.append("")
    linhas.append("// Structs")
    for classe in estrutura["classes"]:
        linhas.append(gerar_struct(classe))
        linhas.append("")

    # Gerar stubs
    linhas.append("// Metodos")
    nomes_usados = set()
    for classe in estrutura["classes"]:
        for metodo in classe["metodos"]:
            if metodo["n_instr"] > 0 and metodo["nome"] != "<clinit>":
                linhas.append(gerar_stub(classe, metodo, nomes_usados))
                linhas.append("")

    # Main
    linhas.append("// Game loop")
    linhas.append("int main(void) {")
    linhas.append("    j2me_gfx_init();")
    linhas.append("    j2me_input_init();")
    linhas.append("    j2me_random_init();")
    linhas.append("")
    linhas.append("    while (1) {")
    linhas.append("        j2me_input_update();")
    linhas.append("        if (j2me_input_should_quit()) break;")
    linhas.append("        j2me_gfx_begin_frame();")
    linhas.append("        j2me_gfx_clear(0x101020);")
    linhas.append(f"        // TODO: chamar {estrutura['midlet']}_startApp() e {estrutura['canvas']}_paint()")
    linhas.append("        j2me_gfx_flip();")
    linhas.append("    }")
    linhas.append("")
    linhas.append("    j2me_gfx_shutdown();")
    linhas.append("    sceKernelExitGame();")
    linhas.append("    return 0;")
    linhas.append("}")
    return "\n".join(linhas)

def main():
    if len(sys.argv) < 2:
        print("Uso: python portador_gerar_v2.py <estrutura.json> [saida.c]")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        estrutura = json.load(f)
    saida = sys.argv[2] if len(sys.argv) > 2 else "main_v2.c"
    codigo = gerar_main_c(estrutura)
    with open(saida, "w") as f:
        f.write(codigo)
    linhas = codigo.count("\n")
    print(f"Gerado: {saida} ({linhas} linhas)")

if __name__ == "__main__":
    main()
