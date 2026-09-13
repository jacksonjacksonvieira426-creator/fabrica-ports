#include <pspkernel.h>
#include <pspctrl.h>
#include "j2me_gfx.h"
#include "j2me_font.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    j2me_gfx_init();

    while (1) {
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        // Titulo em amarelo
        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("FUNTETRIS PSP", 10, 10);

        // Texto branco
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("Fase 5: fonte bitmap OK!", 10, 30);
        j2me_font_draw("ABCDEFGHIJKLM", 10, 50);
        j2me_gfx_set_color(0x00FF00);
        j2me_font_draw("NOPQRSTUVWXYZ", 10, 70);
        j2me_gfx_set_color(0x00FFFF);
        j2me_font_draw("0123456789 !?@#$%", 10, 90);
        j2me_gfx_set_color(0xFF00FF);
        j2me_font_draw("abcdefghijklmnop", 10, 110);
        j2me_gfx_set_color(0xFF8080);
        j2me_font_draw("qrstuvwxyz . , : ;", 10, 130);

        // Simula HUD de jogo
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("SCORE: 001234", 10, 240);
        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("LINES: 42", 200, 240);

        j2me_gfx_flip();

        SceCtrlData pad;
        sceCtrlReadBufferPositive(&pad, 1);
        if (pad.Buttons & PSP_CTRL_START) break;
    }

    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
