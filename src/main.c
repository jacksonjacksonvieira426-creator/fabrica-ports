#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"
#include "j2me_clip.h"
#include "j2me_vector.h"
#include "j2me_string.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    // Cria sprite sheet 80x20 com 4 "sprites" de 20x20
    J2MEImage* sheet = j2me_image_create(80, 20);
    j2me_image_bind(sheet);
    j2me_gfx_set_color(0xFF0000); j2me_gfx_fill_rect( 0, 0, 20, 20);
    j2me_gfx_set_color(0x00FF00); j2me_gfx_fill_rect(20, 0, 20, 20);
    j2me_gfx_set_color(0x0000FF); j2me_gfx_fill_rect(40, 0, 20, 20);
    j2me_gfx_set_color(0xFFFF00); j2me_gfx_fill_rect(60, 0, 20, 20);
    j2me_image_unbind();

    // Testa Vector + String
    J2MEVector* v = j2me_str_split("COD:Mission:1:Complete", ':');
    int n_itens = j2me_vector_size(v);

    while (1) {
        j2me_input_update();
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("TESTE: Clip + Region + Vector + String", 10, 10);

        // Testa draw_region (4 sprites do sheet)
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("draw_region (sprites):", 10, 30);
        j2me_image_draw_region(sheet,  0, 0, 20, 20, TRANS_NONE,   10, 50, TOP|LEFT);
        j2me_image_draw_region(sheet, 20, 0, 20, 20, TRANS_NONE,   40, 50, TOP|LEFT);
        j2me_image_draw_region(sheet, 40, 0, 20, 20, TRANS_NONE,   70, 50, TOP|LEFT);
        j2me_image_draw_region(sheet, 60, 0, 20, 20, TRANS_NONE,  100, 50, TOP|LEFT);

        // Testa transformacoes
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("mirror:", 10, 80);
        j2me_image_draw_region(sheet,  0, 0, 20, 20, TRANS_MIRROR, 100, 80, TOP|LEFT);

        // Testa draw_region com zoom (desenhar 20x20 como 40x40)
        j2me_font_draw("zoom:", 10, 110);
        j2me_image_draw_region(sheet, 0, 0, 20, 20, TRANS_NONE, 100, 110, TOP|LEFT);

        // Testa setClip
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("setClip (corta 100x30):", 10, 150);
        j2me_clip_push(10, 170, 100, 30);
        j2me_image_draw_region(sheet, 0, 0, 20, 20, TRANS_NONE, 10, 165, TOP|LEFT);
        j2me_image_draw_region(sheet, 20, 0, 20, 20, TRANS_NONE, 30, 165, TOP|LEFT);
        j2me_image_draw_region(sheet, 40, 0, 20, 20, TRANS_NONE, 50, 165, TOP|LEFT);
        j2me_image_draw_region(sheet, 60, 0, 20, 20, TRANS_NONE, 70, 165, TOP|LEFT);
        j2me_clip_pop();

        // Testa Vector + String
        j2me_gfx_set_color(0x00FFFF);
        j2me_font_draw("split('COD:Mission:1:Complete', ':') =", 10, 210);
        j2me_gfx_set_color(0xFFFFFF);
        int x = 10;
        for (int i = 0; i < n_itens; i++) {
            char* item = (char*)j2me_vector_get(v, i);
            j2me_font_draw(item, x, 225);
            x += j2me_font_width(item) + 10;
        }

        j2me_gfx_set_color(0x808080);
        j2me_font_draw("START sai", 10, 250);

        j2me_gfx_flip();
        if (j2me_input_should_quit()) break;
    }

    j2me_image_free(sheet);
    j2me_vector_free(v);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
