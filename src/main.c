#include <pspkernel.h>
#include <pspdisplay.h>
#include <pspgu.h>
#include <pspctrl.h>
#include <pspgum.h>

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define BUF_WIDTH  512
#define SCR_WIDTH  480
#define SCR_HEIGHT 272

static unsigned int __attribute__((aligned(16))) list[262144];

typedef struct {
    unsigned short x, y, z;
    unsigned int   color;
} Vtx;

int main(void) {
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

    while (1) {
        sceGuStart(GU_DIRECT, list);

        // Fundo azul escuro via clear
        sceGuClearColor(0xFF201010);
        sceGuClear(GU_COLOR_BUFFER_BIT);

        // Retangulo VERMELHO no centro cobrindo metade da tela
        Vtx* v = (Vtx*)sceGuGetMemory(2 * sizeof(Vtx));
        v[0].x = 100; v[0].y = 50; v[0].z = 0; v[0].color = 0xFF0000FF;
        v[1].x = 380; v[1].y = 220; v[1].z = 0; v[1].color = 0xFF0000FF;

        sceGuDrawArray(GU_SPRITES,
                       GU_VERTEX_16BIT | GU_COLOR_8888 | GU_TRANSFORM_2D,
                       2, 0, v);

        sceGuFinish();
        sceGuSync(0, 0);
        sceGuSwapBuffers();
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
