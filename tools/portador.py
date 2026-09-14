#!/usr/bin/env python3
"""
PORTADOR - Transforma .jar em projeto PSP pronto pra build.
Uso: python portador.py <jogo.jar> [--nome=meu_port]

Pipeline:
  1. Extrai recursos (PNGs, GIFs, textos)
  2. Analisa estrutura (classes, campos, metodos, padroes)
  3. Converte imagens PNG -> .h C
  4. Gera main.c com structs + stubs + TODOs
  5. Cria Makefile + workflow GitHub Actions
  6. (Opcional) Faz git init + push
"""
import sys, os, json, subprocess, zipfile, shutil

BASE = os.path.expanduser("~/fabrica-ports")
TOOLS = os.path.join(BASE, "tools")
SRC = os.path.join(BASE, "src")

def rodar(cmd, cwd=None):
    print(f"  $ {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    ERRO: {r.stderr[:200]}")
        return False
    return True

def extrair_recursos(jar, pasta_saida):
    print(f"\n[1/5] Extraindo recursos de {os.path.basename(jar)}")
    os.makedirs(pasta_saida, exist_ok=True)
    cmd = f"python {TOOLS}/extrair_jar.py '{jar}' '{pasta_saida}'"
    rodar(cmd)
    return True

def analisar_estrutura(jar, saida_json):
    print(f"\n[2/5] Analisando estrutura")
    cmd = f"python {TOOLS}/portador_analisar.py '{jar}' '{saida_json}'"
    rodar(cmd)
    return os.path.exists(saida_json)

def converter_imagens(pasta_extraida, pasta_destino, nome_proj):
    print(f"\n[3/5] Convertendo imagens PNG -> C")
    pasta_img = os.path.join(pasta_extraida, "imagem")
    if not os.path.exists(pasta_img):
        print("  Sem imagens para converter")
        return []

    headers = []
    for arq in sorted(os.listdir(pasta_img)):
        if not arq.endswith(".png"): continue
        nome = os.path.splitext(arq)[0].lower().replace(" ", "_").replace("-", "_")
        nome = "".join(c for c in nome if c.isalnum() or c == "_")
        header = os.path.join(pasta_destino, f"{nome_proj}_{nome}.h")
        cmd = f"python {TOOLS}/converter_png.py '{pasta_img}/{arq}' '{header}' {nome_proj}_{nome}"
        if rodar(cmd):
            headers.append(header)
            print(f"    OK: {os.path.basename(header)}")
    return headers

def gerar_main(estrutura_json, saida_c, nome_proj):
    print(f"\n[4/5] Gerando main.c")
    cmd = f"python {TOOLS}/portador_gerar.py '{estrutura_json}' '{saida_c}'"
    rodar(cmd)

def gerar_makefile(caminho, nome_proj):
    with open(caminho, "w") as f:
        f.write(f"""TARGET = {nome_proj}
OBJS = main.o j2me_runtime.o j2me_gfx.o j2me_font.o j2me_input.o \\
       j2me_image.o j2me_clip.o j2me_vector.o j2me_string.o j2me_rms.o

EXTRA_TARGETS = EBOOT.PBP
PSP_EBOOT_TITLE = {nome_proj}

PSPSDK = $(shell psp-config --pspsdk-path)
include $(PSPSDK)/lib/build.mak
""")

def gerar_workflow(caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w") as f:
        f.write("""name: Build PSP
on: [push, workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/pspdev/pspdev:latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          cd src
          make
      - uses: actions/upload-artifact@v4
        with:
          name: EBOOT-PSP
          path: src/EBOOT.PBP
          if-no-files-found: error
""")

def copiar_biblioteca(pasta_destino):
    print(f"  Copiando biblioteca j2me_*")
    for arq in os.listdir(SRC):
        if arq.startswith("j2me_") and (arq.endswith(".c") or arq.endswith(".h")):
            shutil.copy(os.path.join(SRC, arq), os.path.join(pasta_destino, arq))

def main():
    if len(sys.argv) < 2:
        print("Uso: python portador.py <jogo.jar> [--nome=meu_port]")
        sys.exit(1)

    jar = sys.argv[1]
    nome = os.path.splitext(os.path.basename(jar))[0].lower().replace(" ", "_")
    for arg in sys.argv[2:]:
        if arg.startswith("--nome="):
            nome = arg.split("=", 1)[1]

    print(f"╔══════════════════════════════════════════════╗")
    print(f"║ PORTADOR - {nome:<32} ║")
    print(f"╚══════════════════════════════════════════════╝")

    # Cria pasta de trabalho
    pasta_projeto = os.path.join(BASE, "ports", nome)
    if os.path.exists(pasta_projeto):
        print(f"Limpando {pasta_projeto}")
        shutil.rmtree(pasta_projeto)
    os.makedirs(os.path.join(pasta_projeto, "src"))

    # 1. Extrai
    pasta_extraida = os.path.join(pasta_projeto, "_extraido")
    extrair_recursos(jar, pasta_extraida)

    # 2. Analisa
    estrutura_json = os.path.join(pasta_projeto, "estrutura.json")
    if not analisar_estrutura(jar, estrutura_json):
        print("ERRO: analise falhou")
        sys.exit(1)

    # 3. Copia biblioteca + converte imagens
    copiar_biblioteca(os.path.join(pasta_projeto, "src"))
    converter_imagens(pasta_extraida, os.path.join(pasta_projeto, "src"), nome)

    # 4. Gera main.c + makefile
    gerar_main(estrutura_json, os.path.join(pasta_projeto, "src", "main.c"), nome)
    gerar_makefile(os.path.join(pasta_projeto, "src", "Makefile"), nome)
    gerar_workflow(os.path.join(pasta_projeto, ".github", "workflows", "build.yml"))

    # 5. Git init (sem push - usuario decide)
    print(f"\n[5/5] Inicializando git")
    rodar("git init -q", cwd=pasta_projeto)
    rodar(f'git config user.name "portador"', cwd=pasta_projeto)
    rodar(f'git config user.email "portador@local"', cwd=pasta_projeto)
    with open(os.path.join(pasta_projeto, ".gitignore"), "w") as f:
        f.write("*.jar\n*.o\n*.elf\n*.pbp\n_extraido/\n")
    rodar("git add .", cwd=pasta_projeto)
    rodar(f'git commit -q -m "Port automatico de {os.path.basename(jar)}"', cwd=pasta_projeto)

    # Resumo
    print(f"\n╔══════════════════════════════════════════════╗")
    print(f"║ PORT COMPLETO                                ║")
    print(f"╚══════════════════════════════════════════════╝")
    print(f"Pasta: {pasta_projeto}")
    print(f"Arquivos: {os.listdir(pasta_projeto)}")
    print(f"\nProximos passos:")
    print(f"  cd {pasta_projeto}")
    print(f"  # Edite src/main.c (procure por TODO)")
    print(f"  gh repo create {nome}-psp --public --source=. --remote=origin --push")

if __name__ == "__main__":
    main()
