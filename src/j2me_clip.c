#include "j2me_clip.h"
#include <pspkernel.h>

#define SCR_W   480
#define SCR_H   272

extern unsigned int* j2me_gfx_backbuf(void);
#define VRAM    (j2me_gfx_backbuf())
#define STRIDE  SCR_W

typedef struct {
    int x, y, w, h;
} ClipRect;

static ClipRect pilha[32];
static int topo = -1;
static ClipRect atual = {0, 0, SCR_W, SCR_H};

extern J2MEImage* j2me_image_get_target(void);

void j2me_clip_push(int x, int y, int w, int h) {
    if (topo < 31) pilha[++topo] = atual;
    int nx = (x > atual.x) ? x : atual.x;
    int ny = (y > atual.y) ? y : atual.y;
    int nx2 = (x + w < atual.x + atual.w) ? x + w : atual.x + atual.w;
    int ny2 = (y + h < atual.y + atual.h) ? y + h : atual.y + atual.h;
    atual.x = nx; atual.y = ny;
    atual.w = (nx2 > nx) ? nx2 - nx : 0;
    atual.h = (ny2 > ny) ? ny2 - ny : 0;
}

void j2me_clip_pop(void) {
    if (topo >= 0) atual = pilha[topo--];
}

void j2me_clip_reset(void) {
    topo = -1;
    atual.x = 0; atual.y = 0;
    atual.w = SCR_W; atual.h = SCR_H;
}

void j2me_clip_get(int* x, int* y, int* w, int* h) {
    if (x) *x = atual.x;
    if (y) *y = atual.y;
    if (w) *w = atual.w;
    if (h) *h = atual.h;
}

void j2me_image_draw_region(J2MEImage* src,
                            int sx, int sy, int sw, int sh,
                            int transform,
                            int dx, int dy, int anchor) {
    if (!src || !src->pixels) return;
    if (sw <= 0 || sh <= 0) return;

    if (anchor & HCENTER) dx -= sw / 2;
    if (anchor & VCENTER) dy -= sh / 2;
    if (anchor & RIGHT)   dx -= sw;
    if (anchor & BOTTOM)  dy -= sh;

    J2MEImage* alvo = j2me_image_get_target();
    int aw = alvo ? alvo->w : SCR_W;
    int ah = alvo ? alvo->h : SCR_H;

    for (int j = 0; j < sh; j++) {
        int ty = dy + j;
        if (ty < 0 || ty >= ah) continue;

        for (int i = 0; i < sw; i++) {
            int tx = dx + i;
            if (tx < 0 || tx >= aw) continue;

            int px = sx + i;
            int py = sy + j;
            if (transform == TRANS_ROT90)  { px = sx + j; py = sy + (sw - 1 - i); }
            if (transform == TRANS_ROT180) { px = sx + (sw - 1 - i); py = sy + (sh - 1 - j); }
            if (transform == TRANS_ROT270) { px = sx + (sh - 1 - j); py = sy + i; }
            if (transform == TRANS_MIRROR) { px = sx + (sw - 1 - i); py = sy + j; }

            if (px < 0 || px >= src->w) continue;
            if (py < 0 || py >= src->h) continue;

            unsigned int cor = src->pixels[py * src->w + px];
            if ((cor & 0xFF000000u) == 0) continue;

            if (tx < atual.x || tx >= atual.x + atual.w) continue;
            if (ty < atual.y || ty >= atual.y + atual.h) continue;

            if (alvo) {
                alvo->pixels[ty * alvo->w + tx] = cor;
            } else {
                VRAM[ty * STRIDE + tx] = cor;
            }
        }
    }
}
