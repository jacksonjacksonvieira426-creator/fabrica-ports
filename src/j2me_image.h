#ifndef J2ME_IMAGE_H
#define J2ME_IMAGE_H

#include <stdint.h>

// Imagem offscreen (buffer RGB)
typedef struct {
    int            w;
    int            h;
    unsigned int*  pixels;   // array w*h, formato ABGR
} J2MEImage;

// Cria imagem vazia (pixels transparentes)
J2MEImage* j2me_image_create(int w, int h);

// Libera memoria
void j2me_image_free(J2MEImage* img);

// Define a imagem como "destino" dos proximos fill_rect/set_color
// (equivalente a Graphics do J2ME)
void j2me_image_bind(J2MEImage* img);

// Volta a desenhar na tela principal
void j2me_image_unbind(void);

// Blit: desenha a imagem na tela principal em (x, y)
void j2me_image_blit(J2MEImage* img, int x, int y);

// Blit com transparencia (cor 0xFF000000 considerada transparente)
void j2me_image_blit_masked(J2MEImage* img, int x, int y);

#endif
