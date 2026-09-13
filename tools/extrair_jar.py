#!/usr/bin/env python3
"""
Extrator de recursos de JAR J2ME.
Separa por tipo, mostra resumo, salva tudo em pasta organizada.
Uso: python extrair_jar.py <arquivo.jar> [pasta_saida]
"""
import sys, os, zipfile, struct

TIPOS = {
    'imagem': ('.png', '.jpg', '.gif'),
    'audio':  ('.wav', '.mid', '.mp3', '.amr', '.imy'),
    'mapa':   ('.map', '.dat', '.tmx', '.lvl'),
    'texto':  ('.txt', '.mf', '.jad'),
    'codigo': ('.class',),
    'outros': (),
}

def detectar_tipo(nome):
    ext = os.path.splitext(nome)[1].lower()
    for tipo, exts in TIPOS.items():
        if ext in exts:
            return tipo
    # Se nao tem extensao, olha o conteudo
    return 'outros'

def extrair(jar_path, pasta_saida):
    os.makedirs(pasta_saida, exist_ok=True)
    for tipo in TIPOS.keys():
        os.makedirs(os.path.join(pasta_saida, tipo), exist_ok=True)

    resumo = {t: [] for t in TIPOS.keys()}
    total_tam = 0

    with zipfile.ZipFile(jar_path) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            nome = info.filename
            if nome.startswith('META-INF/'):
                continue
            tipo = detectar_tipo(nome)
            # Nome "seguro" pro filesystem
            nome_seguro = nome.replace('/', '_')
            caminho = os.path.join(pasta_saida, tipo, nome_seguro)
            try:
                with open(caminho, 'wb') as f:
                    f.write(z.read(nome))
                resumo[tipo].append((nome, info.file_size))
                total_tam += info.file_size
            except Exception as e:
                print(f"  ERRO em {nome}: {e}")

    # Relatorio
    print(f"\n=== RESUMO: {os.path.basename(jar_path)} ===")
    print(f"Tamanho total: {total_tam/1024:.1f} KB\n")
    for tipo, itens in resumo.items():
        if not itens:
            continue
        print(f"[{tipo.upper()}] {len(itens)} arquivos")
        for nome, tam in sorted(itens, key=lambda x: -x[1])[:20]:
            print(f"  {tam:>8} bytes  {nome}")
        if len(itens) > 20:
            print(f"  ... e mais {len(itens) - 20}")
        print()

    # Salva lista completa
    with open(os.path.join(pasta_saida, '_lista.txt'), 'w') as f:
        for tipo, itens in resumo.items():
            f.write(f"=== {tipo.upper()} ===\n")
            for nome, tam in itens:
                f.write(f"{tam:>10}  {nome}\n")
            f.write("\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python extrair_jar.py <arquivo.jar> [pasta_saida]")
        sys.exit(1)
    jar = sys.argv[1]
    saida = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(jar)[0] + "_extraido"
    extrair(jar, saida)
    print(f"Extraido em: {saida}")
