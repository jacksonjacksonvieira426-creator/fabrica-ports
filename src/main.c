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

PSP_MODULE_INFO("sprites_test", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

static J2MEImage* img_from(const unsigned int* src, int w, int h) {
    J2MEImage* img = j2me_image_create(w, h);
    memcpy(img->pixels, src, w * h * sizeof(unsigned int));
    return img;
}

static void desenha_num(int n, int x, int y, unsigned int cor) {
    j2me_gfx_set_color(cor);
    char b[8];
    int i = 0;
    if (!n) b[i++] = '0';
    else { char t[8]; int k = 0;
        while (n>0) { t[k++] = '0'+n%10; n/=10; }
        while (k>0) b[i++] = t[--k];
    }
    b[i] = 0;
    j2me_font_draw(b, x, y);
}

// Desenha uma folha de sprites com grid e numeros
static void desenha_folha(J2MEImage* img, int fw, int fh, int start_x, int start_y,
                          const char* titulo, int destacar) {
    j2me_gfx_set_color(0xFFFF00);
    j2me_font_draw(titulo, start_x, start_y - 12);

    int cols = img->w / fw;
    int rows = img->h / fh;
    int gap = 4;

    for (int y = 0; y < rows; y++) {
        for (int x = 0; x < cols; x++) {
            int px = start_x + x * (fw + gap + 18);
            int py = start_y + y * (fh + gap + 4);

            // Borda
            int idx = y * cols + x;
            j2me_gfx_set_color(idx == destacar ? 0xFF0000 : 0x404040);
            j2me_gfx_fill_rect(px - 1, py - 1, fw + 2, fh + 2);
            j2me_gfx_set_color(0x101020);
            j2me_gfx_fill_rect(px, py, fw, fh);

            // Sprite
            j2me_image_draw_region(img, x*fw, y*fh, fw, fh, TRANS_NONE,
                px, py, TOP|LEFT);

            // Numero
            desenha_num(idx, px + fw + 2, py + 2, 0xFFFFFF);
        }
    }
}

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    J2MEImage* s_player  = img_from(cod_player_pixels,  COD_PLAYER_W,  COD_PLAYER_H);
    J2MEImage* s_axis    = img_from(cod_axis_pixels,    COD_AXIS_W,    COD_AXIS_H);
    J2MEImage* s_ground  = img_from(cod_ground_pixels,  COD_GROUND_W,  COD_GROUND_H);
    J2MEImage* s_special = img_from(cod_special_pixels, COD_SPECIAL_W, COD_SPECIAL_H);
    J2MEImage* s_bang    = img_from(cod_bang_pixels,    COD_BANG_W,    COD_BANG_H);

    int tela = 0;
    #define N_TELAS 3
    int destaque = 0;

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        if (j2me_input_is_pressed(J2ME_FIRE)) {
            tela = (tela + 1) % N_TELAS;
            destaque = 0;
        }
        if (j2me_input_is_pressed(J2ME_RIGHT)) destaque++;
        if (j2me_input_is_pressed(J2ME_LEFT) && destaque > 0) destaque--;
        if (destaque < 0) destaque = 0;

        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("VISUALIZADOR DE SPRITES - X: proxima tela | <- ->: muda destaque", 5, 5);

        if (tela == 0) {
            // Tela 0: player (24) + axis (24)
            j2me_gfx_set_color(0x00FF00);
            j2me_font_draw("PLAYER.PNG (48x128) - 3 col x 8 lin = 24 sprites 16x16", 5, 22);
            desenha_folha(s_player, 16, 16, 5, 40, "", destaque);

            j2me_gfx_set_color(0xFF8080);
            j2me_font_draw("AXIS.PNG (48x128) - 24 sprites 16x16", 260, 22);
            desenha_folha(s_axis, 16, 16, 260, 40, "", -1);
        }
        else if (tela == 1) {
            // Tela 1: ground (28)
            j2me_gfx_set_color(0x00FFFF);
            j2me_font_draw("GROUND.PNG (112x64) - 7 col x 4 lin = 28 tiles 16x16", 5, 22);
            desenha_folha(s_ground, 16, 16, 5, 40, "", destaque);
        }
        else if (tela == 2) {
            // Tela 2: special (27) + bang (testando 32x32 vs 16x16)
            j2me_gfx_set_color(0xFFFF00);
            j2me_font_draw("SPECIAL.PNG (144x48) - 27 sprites 16x16", 5, 22);
            desenha_folha(s_special, 16, 16, 5, 40, "", destaque);
        }

        // HUD de destaque
        char b[32];
        j2me_gfx_set_color(0xFF4040);
        j2me_font_draw("DESTAQUE:", 5, 255);
        desenha_num(destaque, 80, 255, 0xFFFFFF);

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
