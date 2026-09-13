#!/usr/bin/env python3
"""
Gerador automatico de projeto PSP a partir de um JAR J2ME.
Cria pasta, main.c com esqueleto, Makefile, e faz commit+push.

Uso: python gerar_projeto.py <caminho_do_jar>
"""
import sys, os, json, shutil, subprocess, zipfile, io
from jawa.cf import ClassFile

BASE = os.path.expanduser("~/fabrica-ports")
PORTS = os.path.join(BASE, "ports")
LIBS = ["j2me_runtime.c", "j2me_runtime.h",
        "j2me_gfx.c", "j2me_gfx.h",
        "j2me_font.c", "j2me_font.h",
        "j2me_input.c", "j2me_input.h"]

def analisar(jar):
    APIs = {}
    classes_internas = set()
    z = zipfile.ZipFile(jar)
    for n in z.namelist():
        if n.endswith(".class"):
            classes_internas.add(n[:-6])
    for n in z.namelist():
        if not n.endswith(".class"): continue
        try:
            cf = ClassFile(io.BytesIO(z.read(n)))
        except: continue
        for m in list(cf.methods):
            if not m.code: continue
            try: instrs = list(m.code.disassemble())
            except: continue
            for i in instrs:
                if i.mnemonic not in ("invokevirtual","invokestatic",
                                      "invokespecial","invokeinterface"): continue
                if not i.operands: continue
                try:
                    const = cf.constants.get(i.operands[0].value)
                    owner = const.class_.name.value
                    nome = const.name_and_type.name.value
                except: continue
                if owner in classes_internas: continue
                k = f"{owner}.{nome}"
                APIs[k] = APIs.get(k, 0) + 1
    return APIs

def gerar_makefile(nome):
    return f"""TARGET = {nome}
OBJS = main.o j2me_runtime.o j2me_gfx.o j2me_font.o j2me_input.o

EXTRA_TARGETS = EBOOT.PBP
PSP_EBOOT_TITLE = {nome}

PSPSDK = $(shell psp-config --pspsdk-path)
include $(PSPSDK)/lib/build.mak
"""

def gerar_main(nome, apis):
    linhas = [
        '#include <pspkernel.h>',
        '#include "j2me_gfx.h"',
        '#include "j2me_font.h"',
        '#include "j2me_input.h"',
        '',
        f'PSP_MODULE_INFO("{nome}", 0, 1, 0);',
        'PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);',
        '',
        '// === APIs usadas pelo jogo original (para traduzir) ===',
    ]
    for api, cnt in sorted(apis.items(), key=lambda x: -x[1])[:30]:
        linhas.append(f'//  {cnt:4d}x  {api}')
    linhas += [
        '',
        'int main(void) {',
        '    j2me_gfx_init();',
        '    j2me_input_init();',
        '',
        '    while (1) {',
        '        j2me_input_update();',
        '        j2me_gfx_begin_frame();',
        '        j2me_gfx_clear(0x000000);',
        '',
        '        // TODO: traduzir logica do jogo aqui',
        '',
        '        j2me_gfx_flip();',
        '        if (j2me_input_should_quit()) break;',
        '    }',
        '',
        '    j2me_gfx_shutdown();',
        '    sceKernelExitGame();',
        '    return 0;',
        '}',
        ''
    ]
    return "\n".join(linhas)

def main():
    if len(sys.argv) < 2:
        print("Uso: python gerar_projeto.py <arquivo.jar>")
        sys.exit(1)

    jar = sys.argv[1]
    nome = os.path.splitext(os.path.basename(jar))[0].lower()
    nome = "".join(c for c in nome if c.isalnum() or c == "_")
    destino = os.path.join(PORTS, nome)

    print(f"Gerando projeto: {nome}")
    print(f"  Destino: {destino}")

    if os.path.exists(destino):
        print(f"  AVISO: pasta ja existe. Removendo...")
        shutil.rmtree(destino)
    os.makedirs(os.path.join(destino, "src"))

    # Analisa
    print("  Analisando APIs...")
    apis = analisar(jar)
    print(f"  Encontradas {len(apis)} APIs distintas")

    # Copia libs
    print("  Copiando bibliotecas base...")
    for lib in LIBS:
        src = os.path.join(BASE, "src", lib)
        dst = os.path.join(destino, "src", lib)
        if os.path.exists(src):
            shutil.copy(src, dst)
        else:
            print(f"    AVISO: {lib} nao encontrada em {BASE}/src/")

    # Gera main.c
    with open(os.path.join(destino, "src", "main.c"), "w") as f:
        f.write(gerar_main(nome, apis))

    # Gera Makefile
    with open(os.path.join(destino, "src", "Makefile"), "w") as f:
        f.write(gerar_makefile(nome))

    # Gera README
    with open(os.path.join(destino, "README.md"), "w") as f:
        f.write(f"# {nome} (port J2ME -> PSP)\n\n")
        f.write(f"Gerado automaticamente a partir de `{os.path.basename(jar)}`\n\n")
        f.write(f"## APIs usadas ({len(apis)} distintas)\n\n")
        for api, cnt in sorted(apis.items(), key=lambda x: -x[1])[:50]:
            f.write(f"- `{api}` — {cnt}x\n")

    # Gera workflow
    wf_dir = os.path.join(destino, ".github", "workflows")
    os.makedirs(wf_dir, exist_ok=True)
    with open(os.path.join(wf_dir, "build.yml"), "w") as f:
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

    # Gera .gitignore
    with open(os.path.join(destino, ".gitignore"), "w") as f:
        f.write("*.o\n*.elf\n*.pbp\n*.prx\nbuild/\n")

    print(f"\n✓ Projeto gerado em: {destino}")
    print(f"\nProximos passos:")
    print(f"  cd {destino}")
    print(f"  git init")
    print(f"  gh repo create {nome}-psp --public --source=. --remote=origin --push")
    print(f"  # Depois edita src/main.c pra implementar a logica")

if __name__ == "__main__":
    main()
