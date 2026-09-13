// main.c - Funtetris (traduzido do J2ME)
#include <pspkernel.h>
#include <string.h>
#include <stdlib.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_runtime.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// ====== Configuracao ======
#define GRID_W     10
#define GRID_H     20
#define CELL       12
#define GRID_PX_W  (GRID_W * CELL)
#define GRID_PX_H  (GRID_H * CELL)
#define GRID_X     60
#define GRID_Y     14

// ====== Pecas (16 bits = 4x4) ======
static const unsigned short PECAS[7][4] = {
    { 0x0F00, 0x2222, 0x00F0, 0x4444 }, // I
    { 0x0660, 0x0660, 0x0660, 0x0660 }, // O
    { 0x0E40, 0x4C40, 0x4E00, 0x4640 }, // T
    { 0x06C0, 0x8C40, 0x06C0, 0x8C40 }, // S
    { 0x0C60, 0x4C80, 0x0C60, 0x4C80 }, // Z
    { 0x44C0, 0x8E00, 0x6440, 0x0E20 }, // J
    { 0x4460, 0x0E80, 0xC440, 0x2E00 }  // L
};

static const unsigned int CORES[7] = {
    0x00FFFF, 0xFFFF00, 0x800080, 0x00FF00,
    0xFF0000, 0x0000FF, 0xFF8000
};

// ====== Estado ======
static int table[GRID_H][GRID_W];
static int peca_atual = 0;
static int rotacao_atual = 0;
static int peca_x = 3;
static int peca_y = 0;
static int score = 0;
static int linhas_removidas = 0;
static int game_over = 0;
static int drop_ms = 800;

// ====== Helpers ======
static int peca_bit(int peca, int rot, int x, int y) {
    int mask = PECAS[peca][rot & 3];
    int bit = 15 - (y * 4 + x);
    return (mask >> bit) & 1;
}

static int pode_mover(int px, int py, int rot) {
    for (int j = 0; j < 4; j++) {
        for (int i = 0; i < 4; i++) {
            if (!peca_bit(peca_atual, rot, i, j)) continue;
            int gx = px + i;
            int gy = py + j;
            if (gx < 0 || gx >= GRID_W) return 0;
            if (gy >= GRID_H) return 0;
            if (gy < 0) continue;
            if (table[gy][gx] != 0) return 0;
        }
    }
    return 1;
}

static void fixar_peca(void) {
    for (int j = 0; j < 4; j++) {
        for (int i = 0; i < 4; i++) {
            if (!peca_bit(peca_atual, rotacao_atual, i, j)) continue;
            int gx = peca_x + i;
            int gy = peca_y + j;
            if (gy >= 0 && gy < GRID_H && gx >= 0 && gx < GRID_W) {
                table[gy][gx] = peca_atual + 1;
            }
        }
    }
}

static int linha_completa(int y) {
    for (int x = 0; x < GRID_W; x++) {
        if (table[y][x] == 0) return 0;
    }
    return 1;
}

static void remover_linha(int y) {
    for (int i = y; i > 0; i--) {
        for (int x = 0; x < GRID_W; x++) {
            table[i][x] = table[i-1][x];
        }
    }
    for (int x = 0; x < GRID_W; x++) table[0][x] = 0;
}

static int checar_linhas(void) {
    int removidas = 0;
    for (int y = GRID_H - 1; y >= 0; y--) {
        if (linha_completa(y)) {
            remover_linha(y);
            removidas++;
            y++;
        }
    }
    return removidas;
}

static void nova_peca(void) {
    peca_atual = j2me_random_next(7);
    rotacao_atual = 0;
    peca_x = 3;
    peca_y = -2;
    if (!pode_mover(peca_x, peca_y, rotacao_atual)) {
        game_over = 1;
    }
}

static void drop(void) {
    if (pode_mover(peca_x, peca_y + 1, rotacao_atual)) {
        peca_y++;
    } else {
        fixar_peca();
        int removidas = checar_linhas();
        if (removidas > 0) {
            score += removidas * removidas * 100;
            linhas_removidas += removidas;
            drop_ms = 800 - linhas_removidas * 20;
            if (drop_ms < 100) drop_ms = 100;
        }
        nova_peca();
    }
}

// ====== Desenho ======
static void desenhar_celula(int x, int y, unsigned int cor) {
    j2me_gfx_set_color(cor);
    j2me_gfx_fill_rect(GRID_X + x * CELL, GRID_Y + y * CELL, CELL - 1, CELL - 1);
}

static void int_to_str(int n, char* buf) {
    int idx = 0;
    if (n == 0) { buf[idx++] = '0'; }
    else {
        char tmp[16]; int t = 0;
        while (n > 0) { tmp[t++] = '0' + (n % 10); n /= 10; }
        while (t > 0) buf[idx++] = tmp[--t];
    }
    buf[idx] = 0;
}

static void desenhar(void) {
    j2me_gfx_begin_frame();
    j2me_gfx_clear(0x000000);

    // Borda do grid
    j2me_gfx_set_color(0x404040);
    j2me_gfx_fill_rect(GRID_X - 2, GRID_Y - 2, GRID_PX_W + 4, GRID_PX_H + 4);
    j2me_gfx_set_color(0x000000);
    j2me_gfx_fill_rect(GRID_X, GRID_Y, GRID_PX_W, GRID_PX_H);

    // Blocos fixos
    for (int y = 0; y < GRID_H; y++) {
        for (int x = 0; x < GRID_W; x++) {
            if (table[y][x] != 0) {
                desenhar_celula(x, y, CORES[table[y][x] - 1]);
            }
        }
    }

    // Peça atual
    if (!game_over) {
        for (int j = 0; j < 4; j++) {
            for (int i = 0; i < 4; i++) {
                if (peca_bit(peca_atual, rotacao_atual, i, j)) {
                    int gx = peca_x + i;
                    int gy = peca_y + j;
                    if (gy >= 0) desenhar_celula(gx, gy, CORES[peca_atual]);
                }
            }
        }
    }

    // HUD
    int hud_x = GRID_X + GRID_PX_W + 30;
    char buf[16];

    j2me_gfx_set_color(0xFFFFFF);
    j2me_font_draw("SCORE", hud_x, 30);
    j2me_gfx_set_color(0xFFFF00);
    int_to_str(score, buf);
    j2me_font_draw(buf, hud_x, 45);

    j2me_gfx_set_color(0xFFFFFF);
    j2me_font_draw("LINHAS", hud_x, 80);
    j2me_gfx_set_color(0x00FF00);
    int_to_str(linhas_removidas, buf);
    j2me_font_draw(buf, hud_x, 95);

    // Controles
    j2me_gfx_set_color(0x808080);
    j2me_font_draw("<- ->  mover", 10, 240);
    j2me_font_draw("^      rotac.", 180, 240);
    j2me_font_draw("v      drop", 340, 240);

    // Game Over
    if (game_over) {
        j2me_gfx_set_color(0xFF0000);
        j2me_font_draw("GAME OVER", GRID_X + 15, GRID_Y + 110);
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("X p/ reiniciar", GRID_X - 5, GRID_Y + 130);
    }

    j2me_gfx_flip();
}

static void reiniciar(void) {
    memset(table, 0, sizeof(table));
    score = 0;
    linhas_removidas = 0;
    game_over = 0;
    drop_ms = 800;
    nova_peca();
}

int main(void) {
    j2me_gfx_init();
    j2me_input_init();
    j2me_random_init();
    reiniciar();

    int64_t t_drop = j2me_time_ms();
    int64_t t_move = j2me_time_ms();
    #define MOVE_REPEAT_MS 130

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        int64_t agora = j2me_time_ms();

        if (game_over) {
            if (j2me_input_is_pressed(J2ME_FIRE)) reiniciar();
        } else {
            int acoes = j2me_input_get_actions();

            // Esquerda
            if (acoes & J2ME_LEFT) {
                if (j2me_input_is_pressed(J2ME_LEFT) ||
                    (agora - t_move > MOVE_REPEAT_MS)) {
                    if (pode_mover(peca_x - 1, peca_y, rotacao_atual)) peca_x--;
                    t_move = agora;
                }
            }
            // Direita
            if (acoes & J2ME_RIGHT) {
                if (j2me_input_is_pressed(J2ME_RIGHT) ||
                    (agora - t_move > MOVE_REPEAT_MS)) {
                    if (pode_mover(peca_x + 1, peca_y, rotacao_atual)) peca_x++;
                    t_move = agora;
                }
            }
            // Rotação (com wall kick simples)
            if (j2me_input_is_pressed(J2ME_UP)) {
                int nova = (rotacao_atual + 1) & 3;
                if (pode_mover(peca_x, peca_y, nova)) rotacao_atual = nova;
                else if (pode_mover(peca_x - 1, peca_y, nova)) { peca_x--; rotacao_atual = nova; }
                else if (pode_mover(peca_x + 1, peca_y, nova)) { peca_x++; rotacao_atual = nova; }
            }
            // Drop rápido
            if (acoes & J2ME_DOWN) {
                if (agora - t_drop > 50) {
                    drop();
                    t_drop = agora;
                }
            } else if (agora - t_drop > drop_ms) {
                drop();
                t_drop = agora;
            }
        }

        desenhar();
    }

    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
