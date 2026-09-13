#include <pspkernel.h>
#include <pspdisplay.h>
#include <pspgu.h>
#include <pspctrl.h>

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define BUF_WIDTH  512
#define SCR_WIDTH  480
#define SCR_HEIGHT 272

static unsigned int __attribute__((aligned(16))) list[65536];
static void* framebuf[2];
static int cur_buf = 0;

typedef struct {
    unsigned short x, y, z;
    unsigned int   color;
} Vertex;

static unsigned int rgb_to_psp(unsigned int rgb) {
    unsigned int r = (rgb >> 16) & 0xFF;
    unsigned int g = (rgb >>  8) & 0xFF;
    unsigned int b =  rgb        & 0xFF;
    return 0xFF000000u | (b << 16) | (g << 8) | r;
}

static void fill_rect(int x, int y, int w, int h, unsigned int rgb) {
    unsigned int c = rgb_to_psp(rgb);
    Vertex* v = (Vertex*)sceGuGetMemory(2 * sizeof(Vertex));
    v[0].x = x;       v[0].y = y;       v[0].z = 0; v[0].color = c;
    v[1].x = x + w;   v[1].y = y + h;   v[1].z = 0; v[1].color = c;
    sceGuDrawArray(GU_SPRITES,
                   GU_VERTEX_16BIT | GU_COLOR_8888 | GU_TRANSFORM_2D,
                   2, 0, v);
}

int main(void) {
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

    while (1) {
        sceGuStart(GU_DIRECT, list);
        sceGuClearColor(rgb_to_psp(0x101020));
        sceGuClear(GU_COLOR_BUFFER_BIT);

        // Quadrado vermelho grande no centro
        fill_rect(100, 50, 280, 170, 0xFF0000);

        sceGuFinish();
        sceGuSync(0, 0);
        framebuf[cur_buf] = sceGuSwapBuffers();
        cur_buf ^= 1;
        sceDisplayWaitVblankStart();

        SceCtrlData pad;
        sceCtrlReadBufferPositive(&pad, 1);
        if (pad.Buttons & PSP_CTRL_START) break;
    }

    sceGuDisplay(GU_FALSE);
    sceGuTerm();
    sceKernelExitGame();
    return 0;
}
