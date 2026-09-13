// main.c — teste do pipeline grafico
#include <pspkernel.h>
#include <pspdebug.h>
#include <pspctrl.h>
#include "j2me_runtime.h"
#include "j2me_gfx.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    j2me_gfx_init();

    int x = 100, y = 100;
    int vx = 3, vy = 2;

    while (1) {
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);   // fundo azul escuro

        // Bola vermelha
        j2me_gfx_set_color(0xFF0000);
        j2me_gfx_fill_rect(x, y, 20, 20);

        // Barra verde em baixo
        j2me_gfx_set_color(0x00FF00);
        j2me_gfx_fill_rect(0, J2ME_SCREEN_H - 20, J2ME_SCREEN_W, 20);

        // Bloco azul no canto
        j2me_gfx_set_color(0x0080FF);
        j2me_gfx_fill_rect(10, 10, 60, 40);

        j2me_gfx_flip();

        // Fisica simples da bola
        x += vx; y += vy;
        if (x <= 0 || x + 20 >= J2ME_SCREEN_W) vx = -vx;
        if (y <= 0 || y + 20 >= J2ME_SCREEN_H) vy = -vy;

        // Sai com START
        SceCtrlData pad;
        sceCtrlReadBufferPositive(&pad, 1);
        if (pad.Buttons & PSP_CTRL_START) break;
    }

    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
