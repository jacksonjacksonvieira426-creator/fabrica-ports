#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    int contador_fire = 0;
    char ultima_tecla = '-';

    while (1) {
        j2me_input_update();

        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("TESTE DE INPUT", 10, 10);

        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("Direcao:", 10, 40);

        int acoes = j2me_input_get_actions();
        j2me_gfx_set_color(0x00FF00);
        if (acoes & J2ME_UP)    j2me_font_draw("CIMA",  120, 40);
        if (acoes & J2ME_DOWN)  j2me_font_draw("BAIXO", 120, 55);
        if (acoes & J2ME_LEFT)  j2me_font_draw("ESQ",   180, 40);
        if (acoes & J2ME_RIGHT) j2me_font_draw("DIR",   180, 55);

        if (j2me_input_is_pressed(J2ME_FIRE)) contador_fire++;

        j2me_gfx_set_color(0x00FFFF);
        j2me_font_draw("FIRE (X/O):", 10, 90);

        char buf[16];
        int n = contador_fire, i = 0;
        if (n == 0) buf[i++] = '0';
        else {
            char tmp[16]; int t = 0;
            while (n > 0) { tmp[t++] = '0' + (n % 10); n /= 10; }
            while (t > 0) buf[i++] = tmp[--t];
        }
        buf[i] = 0;
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw(buf, 140, 90);

        char tecla = j2me_input_get_key();
        if (tecla) ultima_tecla = tecla;

        j2me_gfx_set_color(0xFF00FF);
        j2me_font_draw("Ultima tecla:", 10, 120);
        j2me_gfx_set_color(0xFFFFFF);
        char tbuf[2] = { ultima_tecla, 0 };
        j2me_font_draw(tbuf, 180, 120);

        j2me_gfx_set_color(0x808080);
        j2me_font_draw("D-Pad: direcoes", 10, 180);
        j2me_font_draw("X / O: FIRE (edge)", 10, 195);
        j2me_font_draw("Tri:1 Cir:2 Qua:4 X:5", 10, 210);
        j2me_font_draw("L:7 R:9 Sel:0 Sta:# (sai)", 10, 225);

        j2me_gfx_flip();

        if (j2me_input_should_quit()) break;
    }

    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
