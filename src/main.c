#include <pspkernel.h>
#include <string.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"
#include "cod_player.h"

PSP_MODULE_INFO("sprites_test", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    J2MEImage* img = j2me_image_create(COD_PLAYER_W, COD_PLAYER_H);
    memcpy(img->pixels, cod_player_pixels, COD_PLAYER_W * COD_PLAYER_H * 4);

    int frame = 0;

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        // Muda com L/R
        if (j2me_input_is_pressed(J2ME_LEFT))  frame--;
        if (j2me_input_is_pressed(J2ME_RIGHT)) frame++;

        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("TODOS OS 24 SPRITES DO PLAYER.PNG", 10, 10);
        j2me_gfx_set_color(0x808080);
        j2me_font_draw("Cada sprite = 16x16. Numero = (linha, coluna)", 10, 25);

        // Desenha grade 3x8 com numeros
        for (int lin = 0; lin < 8; lin++) {
            for (int col = 0; col < 3; col++) {
                int x = 60 + col * 90;
                int y = 50 + lin * 26;
                int idx = lin * 3 + col;

                // Sprite (ampliado 1.5x pra ver melhor)
                j2me_image_draw_region(img, col*16, lin*16, 16, 16, TRANS_NONE,
                    x, y, TOP|LEFT);

                // Numero
                char buf[16];
                buf[0] = '0' + lin;
                buf[1] = ',';
                buf[2] = '0' + col;
                buf[3] = 0;

                j2me_gfx_set_color(idx == frame ? 0x00FF00 : 0xFFFFFF);
                j2me_font_draw(buf, x + 22, y + 5);
            }
        }

        // Destaca o sprite atual (frame)
        int dcol = frame % 3;
        int dlin = frame / 3;
        int dx = 60 + dcol * 90;
        int dy = 50 + dlin * 26;
        j2me_gfx_set_color(0xFF0000);
        j2me_gfx_fill_rect(dx - 2, dy - 2, 20, 2);
        j2me_gfx_fill_rect(dx - 2, dy + 16, 20, 2);
        j2me_gfx_fill_rect(dx - 2, dy, 2, 18);
        j2me_gfx_fill_rect(dx + 16, dy, 2, 18);

        j2me_gfx_set_color(0x00FFFF);
        j2me_font_draw("<- -> muda o destaque", 10, 250);

        j2me_gfx_flip();
    }

    j2me_image_free(img);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
