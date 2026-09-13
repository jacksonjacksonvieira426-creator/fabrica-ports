#include <pspkernel.h>
#include <string.h>
#include <stdio.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_rms.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    char linhas[20][40];
    int n_linhas = 0;
    #define ADD(fmt, ...) do { \
        snprintf(linhas[n_linhas], 40, fmt, ##__VA_ARGS__); \
        n_linhas++; \
    } while (0)

    // Abre/cria o RecordStore
    RecordStore* rs = j2me_rms_open("highscores", 1);

    if (!rs) {
        ADD("ERRO: nao consegui abrir RMS");
    } else {
        ADD("RecordStore aberto");
        ADD("Registros existentes: %d", j2me_rms_count(rs));

        // Adiciona 3 novos registros
        const char* placar1 = "JACKSON:9999";
        const char* placar2 = "MARIA:8500";
        const char* placar3 = "JOAO:7200";
        int id1 = j2me_rms_add(rs, (unsigned char*)placar1, 0, strlen(placar1));
        int id2 = j2me_rms_add(rs, (unsigned char*)placar2, 0, strlen(placar2));
        int id3 = j2me_rms_add(rs, (unsigned char*)placar3, 0, strlen(placar3));
        ADD("Adicionados IDs: %d %d %d", id1, id2, id3);

        // Lista todos
        ADD("--- Placar salvo ---");
        int id = j2me_rms_first_id(rs);
        while (id > 0) {
            unsigned char buf[64];
            int tam = j2me_rms_get(rs, id, buf, sizeof(buf) - 1);
            if (tam > 0) {
                buf[tam] = 0;
                ADD("#%d: %s", id, (char*)buf);
            }
            id = j2me_rms_next_id(rs, id);
        }
    }

    while (1) {
        j2me_input_update();
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw("TESTE: RMS (save/load)", 10, 10);

        for (int i = 0; i < n_linhas; i++) {
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw(linhas[i], 10, 35 + i * 15);
        }

        j2me_gfx_set_color(0x808080);
        j2me_font_draw("Dados persistem entre reinicios", 10, 240);
        j2me_font_draw("START sai", 10, 255);

        j2me_gfx_flip();
        if (j2me_input_should_quit()) break;
    }

    if (rs) j2me_rms_close(rs);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
