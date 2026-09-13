#ifndef J2ME_FONT_H
#define J2ME_FONT_H

// Fonte 5x7 (ASCII 32-126), desenhada com fill_rect
// Cada caractere eh 5 colunas x 7 linhas

// Desenha uma string com a fonte padrao
void j2me_font_draw(const char* texto, int x, int y);

// Largura em pixels de uma string
int j2me_font_width(const char* texto);

// Altura em pixels da fonte
#define J2ME_FONT_H 7

#endif
