#include <pspkernel.h>
#include <pspdisplay.h>
#include <pspctrl.h>

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define SCR_W 480
#define SCR_H 272

int main(void) {
    while (1) {
        void* fb = NULL;
        int stride = 0;
        sceDisplayGetFrameBuf(&fb, &stride, NULL, PSP_DISPLAY_SETBUF_IMMEDIATE);
        
        unsigned int* buf = (unsigned int*)fb;
        int buf_w = stride / 4;
        
        // Fundo azul escuro na tela toda
        for (int y = 0; y < SCR_H; y++) {
            for (int x = 0; x < SCR_W; x++) {
                buf[y * buf_w + x] = 0xFF201010;
            }
        }
        
        // Retangulo vermelho grande
        for (int y = 50; y < 220; y++) {
            for (int x = 100; x < 380; x++) {
                buf[y * buf_w + x] = 0xFF0000FF;
            }
        }
        
        sceDisplayWaitVblankStart();
        
        SceCtrlData pad;
        sceCtrlReadBufferPositive(&pad, 1);
        if (pad.Buttons & PSP_CTRL_START) break;
    }
    
    sceKernelExitGame();
    return 0;
}
