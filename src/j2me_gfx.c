#include "j2me_gfx.h"
#include <pspkernel.h>
#include <pspdisplay.h>
#include <pspgu.h>

#define BUF_WIDTH  512
#define SCR_WIDTH  J2ME_SCREEN_W
#define SCR_HEIGHT J2ME_SCREEN_H

static unsigned int __attribute__((aligned(16))) list[262144];
static unsigned int cur_color_rgb = 0x000000;

typedef struct __attribute__((packed)) {
    unsigned short x, y, z;
    unsigned int   color;
} Vertex;

static unsigned int rgb_to_psp(unsigned int rgb) {
    unsigned int r = (rgb >> 16) & 0xFF;
    unsigned int g = (rgb >>  8) & 0xFF;
    unsigned int b =  rgb        & 0xFF;
    return 0xFF000000u | (b << 16) | (g << 8) | r;
}

void j2me_gfx_init(void) {
    sceGuInit();
    sceGuStart(GU_DIRECT, list);
    sceGuDrawBuffer(GU_PSM_8888, (void*)0, BUF_WIDTH);
    sceGuDispBuffer(SCR_WIDTH, SCR_HEIGHT, (void*)0x88000, BUF_WIDTH);
    sceGuDepthBuffer((void*)0x110000, BUF_WIDTH);
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
    sceGuDisable(GU_ALPHA_TEST);
    sceGuFinish();
    sceGuSync(0, 0);
    sceDisplayWaitVblankStart();
    sceGuDisplay(GU_TRUE);
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
    sceGuSwapBuffers();
    sceDisplayWaitVblankStart();
}

void j2me_gfx_set_color(unsigned int rgb) {
    cur_color_rgb = rgb;
}

void j2me_gfx_fill_rect(int x, int y, int w, int h) {
    if (w <= 0 || h <= 0) return;

    unsigned int c = rgb_to_psp(cur_color_rgb);
    int x2 = x + w;
    int y2 = y + h;

    Vertex* v = (Vertex*)sceGuGetMemory(6 * sizeof(Vertex));
    if (!v) return;

    // Triangulo 1: TL, TR, BR
    v[0].x = x;  v[0].y = y;  v[0].z = 0; v[0].color = c;
    v[1].x = x2; v[1].y = y;  v[1].z = 0; v[1].color = c;
    v[2].x = x2; v[2].y = y2; v[2].z = 0; v[2].color = c;

    // Triangulo 2: TL, BR, BL
    v[3].x = x;  v[3].y = y;  v[3].z = 0; v[3].color = c;
    v[4].x = x2; v[4].y = y2; v[4].z = 0; v[4].color = c;
    v[5].x = x;  v[5].y = y2; v[5].z = 0; v[5].color = c;

    sceGuDrawArray(GU_TRIANGLES,
                   GU_VERTEX_16BIT | GU_COLOR_8888 | GU_TRANSFORM_2D,
                   6, 0, v);
}
