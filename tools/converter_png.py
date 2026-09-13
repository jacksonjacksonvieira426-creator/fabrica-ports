#!/usr/bin/env python3
"""
Conversor PNG (paleta) -> array C (ARGB).
Sem dependencias externas - usa zlib do Python.
Uso: python converter_png.py <imagem.png> <saida.h> [nome_var]
"""
import sys, os, struct, zlib

def ler_png(caminho):
    """Le PNG paleta e retorna (w, h, pixels_argb, palette_rgb, trns)."""
    with open(caminho, 'rb') as f:
        dados = f.read()

    if dados[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError("Nao e PNG")

    pos = 8
    w = h = 0
    bit_depth = 0
    color_type = 0
    palette = b''
    trns = b''
    idat = b''

    while pos < len(dados):
        tam = struct.unpack('>I', dados[pos:pos+4])[0]
        tipo = dados[pos+4:pos+8]
        corpo = dados[pos+8:pos+8+tam]
        pos += 12 + tam

        if tipo == b'IHDR':
            w, h, bit_depth, color_type = struct.unpack('>IIBB', corpo[:10])
        elif tipo == b'PLTE':
            palette = corpo
        elif tipo == b'tRNS':
            trns = corpo
        elif tipo == b'IDAT':
            idat += corpo
        elif tipo == b'IEND':
            break

    if color_type != 3:
        raise ValueError(f"So suporta paleta (color_type=3), tem {color_type}")

    # Descomprime
    raw = zlib.decompress(idat)

    # Bytes por pixel no modo paleta
    if bit_depth == 8:
        bpp = 1
    elif bit_depth == 4:
        bpp = 0.5
    elif bit_depth == 1:
        bpp = 0.125
    else:
        raise ValueError(f"Bit depth {bit_depth} nao suportado")

    # Bytes por scanline (arredondado pra cima)
    bytes_por_linha = (w * bit_depth + 7) // 8
    linhas = []
    pos = 0
    linha_anterior = bytearray(bytes_por_linha)

    for y in range(h):
        filtro = raw[pos]
        pos += 1
        scanline = bytearray(raw[pos:pos+bytes_por_linha])
        pos += bytes_por_linha

        # Desfiltro
        for i in range(bytes_por_linha):
            a = scanline[i-1] if i > 0 else 0
            b = linha_anterior[i]
            c = linha_anterior[i-1] if i > 0 else 0

            if filtro == 0:   # None
                pass
            elif filtro == 1: # Sub
                scanline[i] = (scanline[i] + a) & 0xFF
            elif filtro == 2: # Up
                scanline[i] = (scanline[i] + b) & 0xFF
            elif filtro == 3: # Average
                scanline[i] = (scanline[i] + (a + b) // 2) & 0xFF
            elif filtro == 4: # Paeth
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                if pa <= pb and pa <= pc: pr = a
                elif pb <= pc: pr = b
                else: pr = c
                scanline[i] = (scanline[i] + pr) & 0xFF

        linhas.append(bytes(scanline))
        linha_anterior = scanline

    # Extrai indices dos pixels
    indices = []
    for y in range(h):
        linha = linhas[y]
        if bit_depth == 8:
            for x in range(w):
                indices.append(linha[x])
        elif bit_depth == 4:
            for x in range(w):
                byte = linha[x // 2]
                idx = (byte >> 4) if (x % 2 == 0) else (byte & 0xF)
                indices.append(idx)
        elif bit_depth == 1:
            for x in range(w):
                byte = linha[x // 8]
                bit = 7 - (x % 8)
                indices.append((byte >> bit) & 1)

    # Converte pra ARGB
    pixels = []
    for idx in indices:
        if idx * 3 + 2 < len(palette):
            r = palette[idx*3]
            g = palette[idx*3+1]
            b = palette[idx*3+2]
            # Transparencia: primeiro indice em trns, ou cor magica FF00FF
            alpha = 0xFF
            if idx < len(trns):
                alpha = trns[idx]
            if (r, g, b) == (0xFF, 0x00, 0xFF):
                alpha = 0
            argb = (alpha << 24) | (r << 16) | (g << 8) | b
        else:
            argb = 0
        pixels.append(argb)

    return w, h, pixels

def gerar_header(nome_var, w, h, pixels, saida):
    with open(saida, 'w') as f:
        f.write(f"// Gerado automaticamente de PNG\n")
        f.write(f"// {w}x{h}, {len(pixels)} pixels ARGB\n\n")
        f.write(f"#ifndef _{nome_var.upper()}_H\n")
        f.write(f"#define _{nome_var.upper()}_H\n\n")
        f.write(f"#define {nome_var.upper()}_W {w}\n")
        f.write(f"#define {nome_var.upper()}_H {h}\n\n")
        f.write(f"static const unsigned int {nome_var}_pixels[{len(pixels)}] = {{\n")
        for i in range(0, len(pixels), 8):
            linha = pixels[i:i+8]
            f.write("    " + ", ".join(f"0x{p:08X}u" for p in linha) + ",\n")
        f.write("};\n\n")
        f.write(f"#endif\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python converter_png.py <entrada.png> <saida.h> [nome_var]")
        sys.exit(1)
    entrada = sys.argv[1]
    saida = sys.argv[2]
    nome_var = sys.argv[3] if len(sys.argv) > 3 else os.path.splitext(os.path.basename(entrada))[0]

    print(f"Lendo {entrada}...")
    w, h, pixels = ler_png(entrada)
    print(f"  {w}x{h} = {len(pixels)} pixels")

    nao_transparentes = sum(1 for p in pixels if (p & 0xFF000000) != 0)
    print(f"  {nao_transparentes} pixels opacos")

    gerar_header(nome_var, w, h, pixels, saida)
    print(f"Salvo: {saida} ({os.path.getsize(saida)} bytes)")
