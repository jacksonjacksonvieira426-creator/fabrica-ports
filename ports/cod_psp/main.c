#include <pspkernel.h>
#include <string.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"
#include "cod_player.h"   // cod_player_pixels[6144], 48x128
#include "cod_ground.h"   // cod_ground_pixels[...], 112x64
#include "cod_axis.h"     // cod_axis_pixels[...], 48x128

PSP_MODULE_INFO("cod_psp", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// Cria uma J2MEImage a partir de um array ARGB
static J2MEImage* imagem_de_pixels(const unsigned int* src, int w, int h) {
    J2MEImage* img = j2me_image_create(w, h);
    if (!img) return NULL;
    for (int i = 0; i < w * h; i++) {
        img->pixels[i] = src[i];
    }
    return img;
}

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    J2MEImage* player = imagem_de_pixels(cod_player_pixels, COD_PLAYER_W, COD_PLAYER_H);
    J2MEImage* ground = imagem_de_pixels(cod_ground_pixels, COD_GROUND_W, COD_GROUND_H);
    J2MEImage* axis   = imagem_de_pixels(cod_axis_pixels,   COD_AXIS_W,   COD_AXIS_H);

    int frame = 0;
    int t = 0;

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("CoD sprites extraidos do JAR original", 10, 10);

        // Bloco de chao (grade 7x4 de 16x16)
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("ground.png (112x64):", 10, 30);
        j2me_image_blit(ground, 10, 50);

        // Axis (inimigo)
        j2me_gfx_set_color(0xFF8080);
        j2me_font_draw("axis.png (48x128):", 150, 30);
        j2me_image_blit(axis, 150, 50);

        // Player com animacao simples (4 frames alternando)
        j2me_gfx_set_color(0x80FF80);
        j2me_font_draw("player.png (48x128):", 280, 30);
        j2me_image_blit(player, 280, 50);

        // Player ampliado 2x no canto inferior
        j2me_gfx_set_color(0x80FFFF);
        j2me_font_draw("Player 2x (animando frame):", 10, 200);
        // Desenha o player em escala 2x (desenha pixel por pixel)
        for (int y = 0; y < COD_PLAYER_H; y++) {
            for (int x = 0; x < COD_PLAYER_W; x++) {
                unsigned int cor = player->pixels[y * COD_PLAYER_W + x];
                if ((cor & 0xFF000000) == 0) continue;
                j2me_gfx_set_color(cor & 0xFFFFFF);
                j2me_gfx_fill_rect(200 + x * 2, 100 + y * 2 - (frame % 4) * 32 * 2, 2, 2);
            }
        }

        // Contador de frames
        t++;
        if (t % 30 == 0) frame++;

        j2me_gfx_flip();
    }

    j2me_image_free(player);
    j2me_image_free(ground);
    j2me_image_free(axis);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
