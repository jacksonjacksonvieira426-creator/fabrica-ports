#include "j2me_gfx.h"
#include "j2me_image.h"
#include <pspkernel.h>
#include <pspdisplay.h>
#include <string.h>

#define SCR_W J2ME_SCREEN_W
#define SCR_H J2ME_SCREEN_H
#define STRIDE 512

#define VRAM ((unsigned int*)0x44000000)

static unsigned int backbuf[SCR_H * SCR_W] __attribute__((aligned(64)));

static unsigned int cur_color_rgb = 0x000000;

extern J2MEImage* j2me_image_get_target(void);

static unsigned int rgb_to_psp(unsigned int rgb) {
    unsigned int r = (rgb >> 16) & 0xFF;
    unsigned int g = (rgb >>  8) & 0xFF;
    unsigned int b =  rgb        & 0xFF;
    return 0xFF000000u | (b << 16) | (g << 8) | r;
}

void j2me_gfx_init(void) {
    sceDisplaySetMode(0, SCR_W, SCR_H);
    sceDisplaySetFrameBuf(VRAM, STRIDE, PSP_DISPLAY_PIXEL_FORMAT_8888,
                          PSP_DISPLAY_SETBUF_IMMEDIATE);
    memset(backbuf, 0, sizeof(backbuf));
}

void j2me_gfx_shutdown(void) { }
void j2me_gfx_begin_frame(void) { }

void j2me_gfx_flip(void) {
    for (int y = 0; y < SCR_H; y++) {
        unsigned int* dst = VRAM + y * STRIDE;
        unsigned int* src = backbuf + y * SCR_W;
        memcpy(dst, src, SCR_W * sizeof(unsigned int));
    }
    sceKernelDcacheWritebackAll();
    sceDisplayWaitVblankStart();
}

void j2me_gfx_set_color(unsigned int rgb) { cur_color_rgb = rgb; }

unsigned int j2me_gfx_get_color_raw(void) { return cur_color_rgb; }
void j2me_gfx_set_color_raw(unsigned int rgb) { cur_color_rgb = rgb; }

void j2me_gfx_clear(unsigned int rgb) {
    unsigned int c = rgb_to_psp(rgb);
    for (int i = 0; i < SCR_H * SCR_W; i++) backbuf[i] = c;
}

void j2me_gfx_fill_rect(int x, int y, int w, int h) {
    if (w <= 0 || h <= 0) return;
    unsigned int c = rgb_to_psp(cur_color_rgb);
    J2MEImage* alvo = j2me_image_get_target();

    if (alvo) {
        for (int j = 0; j < h; j++) {
            int dy = y + j;
            if (dy < 0 || dy >= alvo->h) continue;
            unsigned int* row = alvo->pixels + dy * alvo->w;
            int x0 = x < 0 ? 0 : x;
            int x1 = x + w > alvo->w ? alvo->w : x + w;
            for (int i = x0; i < x1; i++) row[i] = c;
        }
    } else {
        if (x < 0) { w += x; x = 0; }
        if (y < 0) { h += y; y = 0; }
        if (x + w > SCR_W)  w = SCR_W - x;
        if (y + h > SCR_H) h = SCR_H - y;
        if (w <= 0 || h <= 0) return;
        for (int j = 0; j < h; j++) {
            unsigned int* row = backbuf + (y + j) * SCR_W + x;
            for (int i = 0; i < w; i++) row[i] = c;
        }
    }
}

unsigned int* j2me_gfx_backbuf(void) {
    return backbuf;
}
