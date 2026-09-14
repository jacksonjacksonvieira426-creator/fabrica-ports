#!/usr/bin/env python3
"""
Le estrutura.json e gera um main.c compilavel com TODOs marcados.
Uso: python portador_gerar.py <estrutura.json> [saida_dir]
"""
import sys, os, json

# Mapa de API J2ME -> funcao da nossa biblioteca
MAPA_API = {
    "javax/microedition/lcdui/Graphics.setColor":     "j2me_gfx_set_color",
    "javax/microedition/lcdui/Graphics.fillRect":     "j2me_gfx_fill_rect",
    "javax/microedition/lcdui/Graphics.drawString":   "j2me_font_draw",
    "javax/microedition/lcdui/Graphics.drawImage":    "j2me_image_blit",
    "javax/microedition/lcdui/Graphics.drawRegion":   "j2me_image_draw_region",
    "javax/microedition/lcdui/Graphics.setClip":      "j2me_clip_push",
    "javax/microedition/lcdui/Graphics.setFont":      "j2me_noop",
    "javax/microedition/lcdui/Image.createImage":     "j2me_image_create",
    "javax/microedition/lcdui/Image.getGraphics":     "j2me_image_get_graphics",
    "javax/microedition/lcdui/Canvas.getWidth":       "j2me_canvas_w",
    "javax/microedition/lcdui/Canvas.getHeight":      "j2me_canvas_h",
    "javax/microedition/lcdui/Canvas.repaint":        "j2me_canvas_repaint",
    "javax/microedition/lcdui/Canvas.getGameAction":  "j2me_input_get_actions",
    "javax/microedition/lcdui/Display.getDisplay":    "j2me_display_get",
    "javax/microedition/lcdui/Display.setCurrent":    "j2me_display_set",
    "java/lang/System.currentTimeMillis":             "j2me_time_ms",
    "java/util/Random.nextInt":                       "j2me_random_next",
    "java/util/Random.<init>":                        "j2me_random_init",
    "java/lang/Thread.sleep":                         "j2me_sleep",
    "java/lang/Thread.start":                         "j2me_thread_start",
    "java/lang/Math.abs":                             "abs",
    "java/lang/Math.max":                             "max",
    "java/lang/Math.min":                             "min",
    "java/lang/Object.<init>":                        "j2me_noop",
    "java/lang/Integer.<init>":                       "j2me_int_new",
    "java/lang/Integer.toString":                     "j2me_int_to_string",
    "java/lang/Integer.parseInt":                     "j2me_int_parse",
    "java/lang/System.arraycopy":                     "memcpy",
}


def sanitizar(nome):
    """Converte nomes ofuscados (Unicode) em nomes C validos."""
    if not nome:
        return "campo"
    # Se for ASCII valido (letra, numero, _), mantem
    if all(c.isascii() and (c.isalnum() or c == '_') for c in nome):
        if nome[0].isdigit():
            return f"_{nome}"
        return nome
    # Se for Unicode ofuscado, converte pra campo_NNN
    # Usa o codepoint pra gerar um nome estavel
    codepoint = ord(nome[0]) if len(nome) == 1 else sum(ord(c) for c in nome)
    return f"ofusc_{codepoint:04x}"

def gerar_struct(classe):
    """Gera struct C pros campos da classe."""
    linhas = [f"// === Classe: {classe['nome']} (extends {classe['super']}) ==="]
    linhas.append(f"// Padroes detectados: {', '.join(classe['padroes']) or 'nenhum'}")
    linhas.append(f"struct {sanitizar(classe['nome'])}_s {{")
    for campo in classe["campos"]:
        nome_s = sanitizar(campo['nome'])
        linhas.append(f"    {campo['tipo_c']:<15} {nome_s};  // {campo['nome']} ({campo['desc']})")
    if not classe["campos"]:
        linhas.append("    int _vazio;")
    linhas.append("};")
    return "\n".join(linhas)

_nomes_usados = set()

def gerar_stub(classe, metodo):
    """Gera stub de função com TODOs marcados."""
    global _nomes_usados
    nome = metodo["nome"].replace("<init>", "constructor")
    nome = nome.replace("-", "_")
    nome = sanitizar(nome)
    tipo_ret = metodo["tipo_ret"]
    apis = metodo["apis"]

    # Nome unico global (evita redefinicao)
    chave = f"{classe['nome']}_{nome}"
    contador = 1
    nome_final = chave
    while nome_final in _nomes_usados:
        contador += 1
        nome_final = f"{chave}_{contador}"
    _nomes_usados.add(nome_final)
    nome = nome_final

    linhas = [f"// === {classe['nome']}.{nome} ({metodo['desc']}) ==="]
    linhas.append(f"// Instrucoes: {metodo['n_instr']}")

    if apis:
        linhas.append(f"// APIs usadas:")
        for api, cnt in sorted(apis.items(), key=lambda x: -x[1])[:8]:
            trad = MAPA_API.get(api, f"??? {api}")
            linhas.append(f"//   {cnt}x {api} -> {trad}")

    linhas.append(f"{tipo_ret} {nome}() {{")
    linhas.append(f"    // TODO: traduzir logica do bytecode")
    if tipo_ret != "void":
        linhas.append(f"    return 0;  // TODO")
    linhas.append("}")
    return "\n".join(linhas)

def gerar_main_c(estrutura):
    """Gera o main.c completo."""
    nome = estrutura["nome_projeto"]
    midlet = estrutura["midlet"] or "App"
    canvas = estrutura["canvas"] or "Screen"

    linhas = []
    linhas.append(f"// {nome} - Port automatico J2ME -> PSP")
    linhas.append(f"// Gerado por portador.py")
    linhas.append(f"// MIDlet: {midlet}  Canvas: {canvas}")
    linhas.append("")
    linhas.append("#include <pspkernel.h>")
    linhas.append("#include <string.h>")
    linhas.append("#include <stdlib.h>")
    linhas.append("#include \"j2me_gfx.h\"")
    linhas.append("#include \"j2me_font.h\"")
    linhas.append("#include \"j2me_input.h\"")
    linhas.append("#include \"j2me_image.h\"")
    linhas.append("#include \"j2me_clip.h\"")
    linhas.append("#include \"j2me_runtime.h\"")
    linhas.append("#include <stdint.h>")
    linhas.append("")
    linhas.append("// ============================================")
    linhas.append("// TIPOS J2ME -> ponteiros opacos em C")
    linhas.append("// ============================================")
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

    # Structs de todas as classes
    linhas.append("// ============================================")
    linhas.append("// FORWARD DECLARATIONS das classes do projeto")
    linhas.append("// ============================================")
    for classe in estrutura["classes"]:
        nome = sanitizar(classe["nome"])
        linhas.append(f"typedef struct {nome}_s {nome};")
    linhas.append("")
    linhas.append("// ============================================")
    linhas.append("// ESTRUTURAS DE DADOS (traduzidas do J2ME)")
    linhas.append("// ============================================")
    linhas.append("")
    for classe in estrutura["classes"]:
        linhas.append(gerar_struct(classe))
        linhas.append("")

    # Stubs de todos os métodos (só os importantes)
    linhas.append("// ============================================")
    linhas.append("// METODOS (traduzidos do bytecode)")
    linhas.append("// ============================================")
    linhas.append("")
    for classe in estrutura["classes"]:
        # Só métodos com bytecode real
        for metodo in classe["metodos"]:
            if metodo["n_instr"] > 0 and metodo["nome"] not in ("<clinit>",):
                linhas.append(gerar_stub(classe, metodo))
                linhas.append("")

    # Main loop
    linhas.append("// ============================================")
    linhas.append("// GAME LOOP PRINCIPAL")
    linhas.append("// ============================================")
    linhas.append("")
    linhas.append("int main(void) {")
    linhas.append("    j2me_gfx_init();")
    linhas.append("    j2me_input_init();")
    linhas.append("    j2me_random_init();")
    linhas.append("")
    linhas.append("    while (1) {")
    linhas.append("        j2me_input_update();")
    linhas.append("        if (j2me_input_should_quit()) break;")
    linhas.append("")
    linhas.append("        j2me_gfx_begin_frame();")
    linhas.append("        j2me_gfx_clear(0x101020);")
    linhas.append("")
    linhas.append(f"        // TODO: chamar metodos do jogo aqui")
    linhas.append(f"        // {midlet}_startApp();")
    linhas.append(f"        // {canvas}_paint();")
    linhas.append("")
    linhas.append("        j2me_gfx_flip();")
    linhas.append("    }")
    linhas.append("")
    linhas.append("    j2me_gfx_shutdown();")
    linhas.append("    sceKernelExitGame();")
    linhas.append("    return 0;")
    linhas.append("}")
    linhas.append("")

    return "\n".join(linhas)

def main():
    if len(sys.argv) < 2:
        print("Uso: python portador_gerar.py <estrutura.json> [saida.c]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        estrutura = json.load(f)

    saida = sys.argv[2] if len(sys.argv) > 2 else "main_gerado.c"

    codigo = gerar_main_c(estrutura)

    with open(saida, "w") as f:
        f.write(codigo)

    linhas = codigo.count("\n")
    print(f"Gerado: {saida} ({linhas} linhas)")
    print(f"  Classes: {estrutura['n_classes']}")
    print(f"  MIDlet: {estrutura['midlet']}")
    print(f"  Canvas: {estrutura['canvas']}")

if __name__ == "__main__":
    main()
