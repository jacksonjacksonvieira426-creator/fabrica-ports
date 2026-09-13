#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    // Cria uma imagem offscreen 60x40 com um "sprite" simples
    J2MEImage* sprite = j2me_image_create(60, 40);

    // Desenha o sprite (agora fill_rect vai pra imagem, nao pra tela)
    j2me_image_bind(sprite);
    j2me_gfx_set_color(0xFF0000);  j2me_gfx_fill_rect(0, 0, 60, 10);   // vermelho
    j2me_gfx_set_color(0x00FF00);  j2me_gfx_fill_rect(0, 10, 60, 10);  // verde
    j2me_gfx_set_color(0x0000FF);  j2me_gfx_fill_rect(0, 20, 60, 10);  // azul
    j2me_gfx_set_color(0xFFFF00);  j2me_gfx_fill_rect(0, 30, 60, 10);  // amarelo
    j2me_image_unbind();

    int x = 50, y = 100, vx = 2, vy = 1;

    while (1) {
        j2me_input_update();
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        // Titulo
        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("TESTE DE IMAGE (offscreen)", 10, 10);

        // Blit do sprite em 3 posicoes diferentes
        j2me_image_blit(sprite, 50, 50);
        j2me_image_blit(sprite, 200, 50);
        j2me_image_blit(sprite, 350, 50);

        // Sprite movel
        j2me_image_blit(sprite, x, y);

        // Legenda
        j2me_gfx_set_color(0x808080);
        j2me_font_draw("3 sprites estaticos em cima", 10, 200);
        j2me_font_draw("1 sprite movel no meio", 10, 215);
        j2me_font_draw("START sai", 10, 230);

        j2me_gfx_flip();

        // Move o sprite movel
        x += vx; y += vy;
        if (x <= 0 || x + 60 >= 480) vx = -vx;
        if (y <= 100 || y + 40 >= 190) vy = -vy;

        if (j2me_input_should_quit()) break;
    }

    j2me_image_free(sprite);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
