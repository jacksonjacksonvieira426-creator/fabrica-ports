#include "j2me_gfx.h"
#include <pspkernel.h>
#include <pspdisplay.h>

#define SCR_WIDTH  J2ME_SCREEN_W
#define SCR_HEIGHT J2ME_SCREEN_H

static unsigned int* g_fb = NULL;
static int g_stride = 0;
static unsigned int cur_color_rgb = 0x000000;

static unsigned int rgb_to_fb(unsigned int rgb) {
    unsigned int r = (rgb >> 16) & 0xFF;
    unsigned int g = (rgb >>  8) & 0xFF;
    unsigned int b =  rgb        & 0xFF;
    return 0xFF000000u | (b << 16) | (g << 8) | r;
}

void j2me_gfx_init(void) {
    sceDisplaySetMode(0, SCR_WIDTH, SCR_HEIGHT);
    void* fb = NULL;
    int stride = 0;
    sceDisplayGetFrameBuf(&fb, &stride, NULL, PSP_DISPLAY_SETBUF_IMMEDIATE);
    g_fb = (unsigned int*)fb;
    g_stride = stride / 4;
}

void j2me_gfx_shutdown(void) { }

void j2me_gfx_begin_frame(void) { }

void j2me_gfx_clear(unsigned int rgb) {
    unsigned int c = rgb_to_fb(rgb);
    for (int y = 0; y < SCR_HEIGHT; y++) {
        unsigned int* row = g_fb + y * g_stride;
        for (int x = 0; x < SCR_WIDTH; x++) {
            row[x] = c;
        }
    }
}

void j2me_gfx_flip(void) {
    sceDisplayWaitVblankStart();
}

void j2me_gfx_set_color(unsigned int rgb) {
    cur_color_rgb = rgb;
}

void j2me_gfx_fill_rect(int x, int y, int w, int h) {
    if (w <= 0 || h <= 0) return;
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > SCR_WIDTH)  w = SCR_WIDTH - x;
    if (y + h > SCR_HEIGHT) h = SCR_HEIGHT - y;
    if (w <= 0 || h <= 0) return;

    unsigned int c = rgb_to_fb(cur_color_rgb);
    for (int j = 0; j < h; j++) {
        unsigned int* row = g_fb + (y + j) * g_stride + x;
        for (int i = 0; i < w; i++) {
            row[i] = c;
        }
    }
}
