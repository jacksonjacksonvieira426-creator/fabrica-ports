#include "j2me_image.h"
#include <stdlib.h>
#include <string.h>

// Framebuffer da tela (mesmo do j2me_gfx.c)
#define VRAM     ((unsigned int*)0x44000000)
#define STRIDE   512
#define SCR_W    480
#define SCR_H    272

// Estado atual: se estiver desenhando numa imagem, aponta pra ela
static J2MEImage* alvo_atual = NULL;

// Cores (compartilhadas com j2me_gfx via extern)
extern unsigned int j2me_gfx_get_color_raw(void);
extern void         j2me_gfx_set_color_raw(unsigned int rgb);

J2MEImage* j2me_image_create(int w, int h) {
    if (w <= 0 || h <= 0) return NULL;
    J2MEImage* img = (J2MEImage*)malloc(sizeof(J2MEImage));
    if (!img) return NULL;
    img->w = w;
    img->h = h;
    img->pixels = (unsigned int*)malloc(w * h * sizeof(unsigned int));
    if (!img->pixels) {
        free(img);
        return NULL;
    }
    // Preenche com "transparente" (alpha=0)
    memset(img->pixels, 0, w * h * sizeof(unsigned int));
    return img;
}

void j2me_image_free(J2MEImage* img) {
    if (!img) return;
    if (alvo_atual == img) alvo_atual = NULL;
    free(img->pixels);
    free(img);
}

void j2me_image_bind(J2MEImage* img) {
    alvo_atual = img;
}

void j2me_image_unbind(void) {
    alvo_atual = NULL;
}

// Funcao auxiliar: chamada pelo j2me_gfx quando precisa saber o alvo
J2MEImage* j2me_image_get_target(void) {
    return alvo_atual;
}

void j2me_image_blit(J2MEImage* img, int x, int y) {
    if (!img || !img->pixels) return;

    for (int j = 0; j < img->h; j++) {
        int dy = y + j;
        if (dy < 0 || dy >= SCR_H) continue;

        unsigned int* dst = VRAM + dy * STRIDE;
        unsigned int* src = img->pixels + j * img->w;

        for (int i = 0; i < img->w; i++) {
            int dx = x + i;
            if (dx < 0 || dx >= SCR_W) continue;
            dst[dx] = src[i];
        }
    }
}

void j2me_image_blit_masked(J2MEImage* img, int x, int y) {
    if (!img || !img->pixels) return;

    for (int j = 0; j < img->h; j++) {
        int dy = y + j;
        if (dy < 0 || dy >= SCR_H) continue;

        unsigned int* dst = VRAM + dy * STRIDE;
        unsigned int* src = img->pixels + j * img->w;

        for (int i = 0; i < img->w; i++) {
            int dx = x + i;
            if (dx < 0 || dx >= SCR_W) continue;
            unsigned int px = src[i];
            // Se alpha == 0, pula (transparente)
            if ((px & 0xFF000000u) == 0) continue;
            dst[dx] = px;
        }
    }
}
