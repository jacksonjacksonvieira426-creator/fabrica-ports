#include "j2me_gfx.h"
#include "j2me_image.h"
#include <pspkernel.h>
#include <pspdisplay.h>

#define SCR_W J2ME_SCREEN_W
#define SCR_H J2ME_SCREEN_H
#define STRIDE 512

#define VRAM ((unsigned int*)0x44000000)

static unsigned int cur_color_rgb = 0x000000;

// Declarado em j2me_image.c
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
}

void j2me_gfx_shutdown(void) { }
void j2me_gfx_begin_frame(void) { }

void j2me_gfx_flip(void) {
    sceKernelDcacheWritebackAll();
    sceDisplayWaitVblankStart();
}

void j2me_gfx_set_color(unsigned int rgb) {
    cur_color_rgb = rgb;
}

unsigned int j2me_gfx_get_color_raw(void) { return cur_color_rgb; }
void j2me_gfx_set_color_raw(unsigned int rgb) { cur_color_rgb = rgb; }

void j2me_gfx_clear(unsigned int rgb) {
    unsigned int c = rgb_to_psp(rgb);
    for (int y = 0; y < SCR_H; y++) {
        unsigned int* row = VRAM + y * STRIDE;
        for (int x = 0; x < SCR_W; x++) row[x] = c;
    }
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
            for (int i = 0; i < w; i++) {
                int dx = x + i;
                if (dx < 0 || dx >= alvo->w) continue;
                row[dx] = c;
            }
        }
    } else {
        if (x < 0) { w += x; x = 0; }
        if (y < 0) { h += y; y = 0; }
        if (x + w > SCR_W)  w = SCR_W - x;
        if (y + h > SCR_H) h = SCR_H - y;
        if (w <= 0 || h <= 0) return;

        for (int j = 0; j < h; j++) {
            unsigned int* row = VRAM + (y + j) * STRIDE + x;
            for (int i = 0; i < w; i++) row[i] = c;
        }
    }
}
