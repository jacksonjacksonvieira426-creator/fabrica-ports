#include "j2me_gfx.h"
#include <pspkernel.h>
#include <pspdisplay.h>
#include <pspgu.h>

#define BUF_WIDTH  512
#define SCR_WIDTH  J2ME_SCREEN_W
#define SCR_HEIGHT J2ME_SCREEN_H

static unsigned int __attribute__((aligned(16))) list[262144];
static unsigned int cur_color_rgb = 0x000000;

// Sem packed! Floats garantem alinhamento de 4 bytes
typedef struct {
    float x, y, z;
    unsigned int color;
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
    float fx  = (float)x;
    float fy  = (float)y;
    float fx2 = (float)(x + w);
    float fy2 = (float)(y + h);

    Vertex* v = (Vertex*)sceGuGetMemory(6 * sizeof(Vertex));
    if (!v) return;

    // Triangulo 1: TL, TR, BR
    v[0].x = fx;  v[0].y = fy;  v[0].z = 0.0f; v[0].color = c;
    v[1].x = fx2; v[1].y = fy;  v[1].z = 0.0f; v[1].color = c;
    v[2].x = fx2; v[2].y = fy2; v[2].z = 0.0f; v[2].color = c;

    // Triangulo 2: TL, BR, BL
    v[3].x = fx;  v[3].y = fy;  v[3].z = 0.0f; v[3].color = c;
    v[4].x = fx2; v[4].y = fy2; v[4].z = 0.0f; v[4].color = c;
    v[5].x = fx;  v[5].y = fy2; v[5].z = 0.0f; v[5].color = c;

    sceGuDrawArray(GU_TRIANGLES,
                   GU_VERTEX_32BITF | GU_COLOR_8888 | GU_TRANSFORM_2D,
                   6, 0, v);
}
