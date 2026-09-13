#ifndef J2ME_GFX_H
#define J2ME_GFX_H

#include <stdint.h>

// Ciclo de vida
void j2me_gfx_init(void);
void j2me_gfx_shutdown(void);

// Frame
void j2me_gfx_begin_frame(void);
void j2me_gfx_flip(void);

// Cor (RGB 0xRRGGBB, estilo J2ME)
void j2me_gfx_set_color(unsigned int rgb);

// Primitivas
void j2me_gfx_fill_rect(int x, int y, int w, int h);
void j2me_gfx_clear(unsigned int rgb);

// Constantes de tela
#define J2ME_SCREEN_W 480
#define J2ME_SCREEN_H 272

#endif

// Acesso ao back buffer (para clip.c)
unsigned int* j2me_gfx_backbuf(void);
