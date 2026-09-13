// Call of Duty - versao simplificada (top-down shooter)
#include <pspkernel.h>
#include <string.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_runtime.h"

PSP_MODULE_INFO("cod_psp", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// === Configuracao ===
#define TILE       24
#define MAP_W      30
#define MAP_H      20
#define VIEW_W     480
#define VIEW_H     272
#define PLAYER_SPD 2

// === Mapa: 0=chao, 1=parede, 2=agua ===
static const unsigned char mapa[MAP_H][MAP_W] = {
    {1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,1,0,0,0,0,0,2,2,2,2,0,0,0,0,0,1,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,1,0,0,0,0,0,2,2,2,2,0,0,0,0,0,1,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1},
    {1,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,1},
    {1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1},
    {1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1},
    {1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1},
    {1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1},
    {1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1},
    {1,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1},
    {1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,1},
    {1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1},
};

// === Estado ===
static int player_x = 100;
static int player_y = 100;
static int camera_x = 0;
static int camera_y = 0;

// === Desenho ===
static void desenhar_mundo(void) {
    // So desenha tiles visiveis na tela
    int ini_x = camera_x / TILE;
    int ini_y = camera_y / TILE;
    int fim_x = ini_x + VIEW_W / TILE + 2;
    int fim_y = ini_y + VIEW_H / TILE + 2;

    if (ini_x < 0) ini_x = 0;
    if (ini_y < 0) ini_y = 0;
    if (fim_x > MAP_W) fim_x = MAP_W;
    if (fim_y > MAP_H) fim_y = MAP_H;

    for (int y = ini_y; y < fim_y; y++) {
        for (int x = ini_x; x < fim_x; x++) {
            int sx = x * TILE - camera_x;
            int sy = y * TILE - camera_y;
            unsigned char t = mapa[y][x];

            if (t == 1)       j2me_gfx_set_color(0x505050);  // parede cinza
            else if (t == 2)  j2me_gfx_set_color(0x004080);  // agua azul
            else              j2me_gfx_set_color(0x204020);  // chao verde

            j2me_gfx_fill_rect(sx, sy, TILE, TILE);
        }
    }
}

static void desenhar_jogador(void) {
    int sx = player_x - camera_x;
    int sy = player_y - camera_y;

    // Corpo
    j2me_gfx_set_color(0xFFCC00);
    j2me_gfx_fill_rect(sx, sy, 16, 16);
    // Cabeca
    j2me_gfx_set_color(0xFFE0A0);
    j2me_gfx_fill_rect(sx + 4, sy + 2, 8, 8);
    // Arma (aponta pra cima)
    j2me_gfx_set_color(0x404040);
    j2me_gfx_fill_rect(sx + 6, sy - 6, 4, 10);
}

static void int_to_str(int n, char* buf) {
    int i = 0;
    if (n == 0) buf[i++] = '0';
    else {
        char t[16]; int k = 0;
        while (n > 0) { t[k++] = '0' + n % 10; n /= 10; }
        while (k > 0) buf[i++] = t[--k];
    }
    buf[i] = 0;
}

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        // Movimento
        int acoes = j2me_input_get_actions();
        if (acoes & J2ME_LEFT)  player_x -= PLAYER_SPD;
        if (acoes & J2ME_RIGHT) player_x += PLAYER_SPD;
        if (acoes & J2ME_UP)    player_y -= PLAYER_SPD;
        if (acoes & J2ME_DOWN)  player_y += PLAYER_SPD;

        // Colisao simples
        int cx = player_x / TILE;
        int cy = player_y / TILE;
        if (cx < 0 || cx >= MAP_W || cy < 0 || cy >= MAP_H || mapa[cy][cx] == 1) {
            // Reverte (chuta de volta)
            if (acoes & J2ME_LEFT)  player_x += PLAYER_SPD;
            if (acoes & J2ME_RIGHT) player_x -= PLAYER_SPD;
            if (acoes & J2ME_UP)    player_y += PLAYER_SPD;
            if (acoes & J2ME_DOWN)  player_y -= PLAYER_SPD;
        }

        // Camera segue jogador
        camera_x = player_x - VIEW_W / 2;
        camera_y = player_y - VIEW_H / 2;
        if (camera_x < 0) camera_x = 0;
        if (camera_y < 0) camera_y = 0;
        if (camera_x > MAP_W * TILE - VIEW_W) camera_x = MAP_W * TILE - VIEW_W;
        if (camera_y > MAP_H * TILE - VIEW_H) camera_y = MAP_H * TILE - VIEW_H;

        // Desenho
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x000000);
        desenhar_mundo();
        desenhar_jogador();

        // HUD
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("COD PSP - MVP", 10, 10);
        char buf[32];
        j2me_font_draw("POS:", 10, 25);
        int_to_str(player_x, buf);
        j2me_font_draw(buf, 50, 25);
        j2me_font_draw(",", 90, 25);
        int_to_str(player_y, buf);
        j2me_font_draw(buf, 100, 25);

        j2me_gfx_flip();
    }

    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
