#include <pspkernel.h>
#include <string.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"
#include "cod_player.h"
#include "cod_axis.h"
#include "cod_ground.h"
#include "cod_special.h"
#include "cod_bang.h"

PSP_MODULE_INFO("inspetor", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

static J2MEImage* img_from(const unsigned int* src, int w, int h) {
    J2MEImage* img = j2me_image_create(w, h);
    memcpy(img->pixels, src, w * h * sizeof(unsigned int));
    return img;
}

static void desenha_borda(int x, int y, int w, int h, unsigned int cor) {
    j2me_gfx_set_color(cor);
    j2me_gfx_fill_rect(x - 1, y - 1, w + 2, 1);
    j2me_gfx_fill_rect(x - 1, y + h, w + 2, 1);
    j2me_gfx_fill_rect(x - 1, y - 1, 1, h + 2);
    j2me_gfx_fill_rect(x + w, y - 1, 1, h + 2);
}

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    J2MEImage* s_player  = img_from(cod_player_pixels,  COD_PLAYER_W,  COD_PLAYER_H);
    J2MEImage* s_axis    = img_from(cod_axis_pixels,    COD_AXIS_W,    COD_AXIS_H);
    J2MEImage* s_ground  = img_from(cod_ground_pixels,  COD_GROUND_W,  COD_GROUND_H);
    J2MEImage* s_special = img_from(cod_special_pixels, COD_SPECIAL_W, COD_SPECIAL_H);
    J2MEImage* s_bang    = img_from(cod_bang_pixels,    COD_BANG_W,    COD_BANG_H);

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("PNGs ORIGINAIS DO JAR (sem cortar)", 10, 5);

        // GROUND (112x64) - canto superior esquerdo
        j2me_gfx_set_color(0x00FF00);
        j2me_font_draw("ground.png (112x64)", 10, 22);
        desenha_borda(10, 35, 112, 64, 0x404040);
        j2me_image_blit(s_ground, 10, 35);

        // PLAYER (48x128) - ao lado
        j2me_gfx_set_color(0x00FFFF);
        j2me_font_draw("player.png (48x128)", 140, 22);
        desenha_borda(140, 35, 48, 128, 0x404040);
        j2me_image_blit(s_player, 140, 35);

        // AXIS (48x128)
        j2me_gfx_set_color(0xFF8080);
        j2me_font_draw("axis.png (48x128)", 200, 22);
        desenha_borda(200, 35, 48, 128, 0x404040);
        j2me_image_blit(s_axis, 200, 35);

        // SPECIAL (144x48)
        j2me_gfx_set_color(0xFF00FF);
        j2me_font_draw("special.png (144x48)", 260, 22);
        desenha_borda(260, 35, 144, 48, 0x404040);
        j2me_image_blit(s_special, 260, 35);

        // BANG (128x64)
        j2me_gfx_set_color(0xFFFF80);
        j2me_font_draw("bang.png (128x64)", 260, 100);
        desenha_borda(260, 113, 128, 64, 0x404040);
        j2me_image_blit(s_bang, 260, 113);

        j2me_gfx_set_color(0x808080);
        j2me_font_draw("Cada PNG desenhado 1:1, sem corte, sem escala.", 10, 250);
        j2me_font_draw("START sai", 10, 262);

        j2me_gfx_flip();
    }

    j2me_image_free(s_player);
    j2me_image_free(s_axis);
    j2me_image_free(s_ground);
    j2me_image_free(s_special);
    j2me_image_free(s_bang);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
