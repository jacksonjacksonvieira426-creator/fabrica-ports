#include <pspkernel.h>
#include <pspdisplay.h>
#include <pspctrl.h>

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define SCR_W 480
#define SCR_H 272
#define STRIDE 512

// VRAM do PSP: 0x04000000 (cached) ou 0x44000000 (uncached)
// Usamos uncached para GPU ver direto
#define VRAM ((unsigned int*)0x44000000)

int main(void) {
    // Diz pro display usar essa VRAM como framebuffer
    sceDisplaySetMode(0, SCR_W, SCR_H);
    sceDisplaySetFrameBuf(VRAM, STRIDE, PSP_DISPLAY_PIXEL_FORMAT_8888,
                          PSP_DISPLAY_SETBUF_IMMEDIATE);

    while (1) {
        // Escreve direto nos pixels
        for (int y = 0; y < SCR_H; y++) {
            unsigned int* row = VRAM + y * STRIDE;
            for (int x = 0; x < SCR_W; x++) {
                row[x] = 0xFF201010;  // azul escuro (ABGR)
            }
        }

        // Retangulo vermelho GRANDE no centro
        for (int y = 50; y < 220; y++) {
            unsigned int* row = VRAM + y * STRIDE;
            for (int x = 100; x < 380; x++) {
                row[x] = 0xFF0000FF;  // vermelho (ABGR)
            }
        }

        // Garante que a GPU veja o que escrevemos
        sceKernelDcacheWritebackAll();

        sceDisplayWaitVblankStart();

        SceCtrlData pad;
        sceCtrlReadBufferPositive(&pad, 1);
        if (pad.Buttons & PSP_CTRL_START) break;
    }

    sceKernelExitGame();
    return 0;
}
