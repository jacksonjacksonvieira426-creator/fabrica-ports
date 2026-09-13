#include "j2me_gfx.h"
#include <pspkernel.h>
#include <pspdisplay.h>
#include <pspgu.h>
#include <pspgum.h>
#include <string.h>

#define BUF_WIDTH  512
#define SCR_WIDTH  J2ME_SCREEN_W
#define SCR_HEIGHT J2ME_SCREEN_H

static unsigned int __attribute__((aligned(16))) list[65536];
static void* framebuf[2];
static int cur_buf = 0;
static unsigned int cur_color_rgb = 0x000000;

typedef struct {
    unsigned short x, y, z;
    unsigned int   color;
} Vertex;

static Vertex __attribute__((aligned(4))) rect_v[2];

// Converte RGB (0xRRGGBB) do J2ME para o formato ABGR do sceGu
static unsigned int rgb_to_psp(unsigned int rgb) {
    unsigned int r = (rgb >> 16) & 0xFF;
    unsigned int g = (rgb >>  8) & 0xFF;
    unsigned int b =  rgb        & 0xFF;
    return 0xFF000000u | (b << 16) | (g << 8) | r;
}

void j2me_gfx_init(void) {
    framebuf[0] = (void*)0x04000000;
    framebuf[1] = (void*)(0x04000000 + BUF_WIDTH * SCR_HEIGHT * 4);

    sceGuInit();
    sceGuStart(GU_DIRECT, list);

    sceGuDrawBuffer(GU_PSM_8888, framebuf[0], BUF_WIDTH);
    sceGuDispBuffer(SCR_WIDTH, SCR_HEIGHT, framebuf[1], BUF_WIDTH);
    sceGuDepthBuffer((void*)0x11000000, BUF_WIDTH);

    sceGuOffset(2048 - (SCR_WIDTH/2), 2048 - (SCR_HEIGHT/2));
    sceGuViewport(2048, 2048, SCR_WIDTH, SCR_HEIGHT);
    sceGuDepthRange(0xC350, 0xFFFF);
    sceGuScissor(0, 0, SCR_WIDTH, SCR_HEIGHT);
    sceGuEnable(GU_SCISSOR_TEST);
    sceGuDisable(GU_DEPTH_TEST);
    sceGuDisable(GU_CULL_FACE);
    sceGuDisable(GU_LIGHTING);
    sceGuDisable(GU_BLEND);
    sceGuDisable(GU_TEXTURE_2D);

    sceGuFinish();
    sceGuSync(0, 0);
    sceDisplayWaitVblankStart();
    sceGuDisplay(GU_TRUE);

    cur_buf = 0;
}

void j2me_gfx_shutdown(void) {
    sceGuDisplay(GU_FALSE);
    sceGuTerm();
}

void j2me_gfx_begin_frame(void) {
    sceGuStart(GU_DIRECT, list);
}

void j2me_gfx_clear(unsigned int rgb) {
    sceGuClearColor(rgb_to_psp(rgb));
    sceGuClear(GU_COLOR_BUFFER_BIT);
}

void j2me_gfx_flip(void) {
    sceGuFinish();
    sceGuSync(0, 0);
    framebuf[cur_buf] = sceGuSwapBuffers();
    cur_buf ^= 1;
    sceDisplayWaitVblankStart();
}

void j2me_gfx_set_color(unsigned int rgb) {
    cur_color_rgb = rgb;
}

void j2me_gfx_fill_rect(int x, int y, int w, int h) {
    if (w <= 0 || h <= 0) return;

    unsigned int c = rgb_to_psp(cur_color_rgb);

    rect_v[0].x = (unsigned short)x;
    rect_v[0].y = (unsigned short)y;
    rect_v[0].z = 0;
    rect_v[0].color = c;

    rect_v[1].x = (unsigned short)(x + w);
    rect_v[1].y = (unsigned short)(y + h);
    rect_v[1].z = 0;
    rect_v[1].color = c;

    sceGuDrawArray(GU_SPRITES,
                   GU_VERTEX_16BIT | GU_COLOR_8888 | GU_TRANSFORM_2D,
                   2, 0, rect_v);
}
