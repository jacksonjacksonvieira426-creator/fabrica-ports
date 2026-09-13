// CoD PSP - MVP com sprites originais do JAR
#include <pspkernel.h>
#include <string.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"
#include "j2me_clip.h"
#include "j2me_runtime.h"
#include "cod_player.h"
#include "cod_axis.h"
#include "cod_ground.h"

PSP_MODULE_INFO("cod_psp", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define TILE   16
#define MAP_W  40
#define MAP_H  24
#define VIEW_W 480
#define VIEW_H 272

// Tile IDs (indices no ground.png)
#define T_GRAMA   0
#define T_TERRA   1
#define T_AGUA    10
#define T_PEDRA   14
#define T_GRAMA2  2

static unsigned char mapa[MAP_H][MAP_W];

static void init_mapa(void) {
    for (int y = 0; y < MAP_H; y++)
        for (int x = 0; x < MAP_W; x++)
            mapa[y][x] = T_GRAMA;

    // Borda de pedra
    for (int x = 0; x < MAP_W; x++) { mapa[0][x] = T_PEDRA; mapa[MAP_H-1][x] = T_PEDRA; }
    for (int y = 0; y < MAP_H; y++) { mapa[y][0] = T_PEDRA; mapa[y][MAP_W-1] = T_PEDRA; }

    // Estrada horizontal
    for (int x = 3; x < 37; x++) { mapa[12][x] = T_TERRA; mapa[13][x] = T_TERRA; }

    // Estrada vertical
    for (int y = 5; y < 20; y++) { mapa[y][20] = T_TERRA; mapa[y][21] = T_TERRA; }

    // Lago
    for (int y = 5; y < 9; y++)
        for (int x = 5; x < 10; x++)
            mapa[y][x] = T_AGUA;

    // Predios
    for (int y = 4; y < 8; y++)
        for (int x = 28; x < 34; x++)
            mapa[y][x] = T_PEDRA;
    for (int y = 16; y < 20; y++)
        for (int x = 6; x < 10; x++)
            mapa[y][x] = T_PEDRA;

    // Detalhes de grama clara
    for (int i = 0; i < 60; i++) {
        int x = 1 + j2me_random_next(MAP_W - 2);
        int y = 1 + j2me_random_next(MAP_H - 2);
        if (mapa[y][x] == T_GRAMA) mapa[y][x] = T_GRAMA2;
    }
}

static J2MEImage* img_from(const unsigned int* src, int w, int h) {
    J2MEImage* img = j2me_image_create(w, h);
    if (!img) return NULL;
    memcpy(img->pixels, src, w * h * sizeof(unsigned int));
    return img;
}

// Jogador
static int px = 200, py = 150;
static int cam_x = 0, cam_y = 0;
static int direcao = 1;
static int frame_anim = 0, frame_time = 0;
static int score = 0, hp = 100;

// Inimigos
typedef struct { int x, y, hp, vivo; } Enemy;
#define MAX_E 8
static Enemy inimigos[MAX_E];
static int n_inimigos = 4;

// Tiros
typedef struct { int x, y, dx, dy, vivo, tempo; } Tiro;
#define MAX_T 32
static Tiro tiros[MAX_T];

static void spawn(void) {
    for (int i = 0; i < n_inimigos; i++) {
        inimigos[i].x = 100 + i * 60;
        inimigos[i].y = 100 + (i % 2) * 80;
        inimigos[i].hp = 20;
        inimigos[i].vivo = 1;
    }
}

static int tile_solido(int x, int y) {
    int tx = x / TILE, ty = y / TILE;
    if (tx < 0 || tx >= MAP_W || ty < 0 || ty >= MAP_H) return 1;
    unsigned char t = mapa[ty][tx];
    return (t == T_AGUA || t == T_PEDRA);
}

static int livre(int x, int y) {
    return !tile_solido(x, y) && !tile_solido(x+11, y) &&
           !tile_solido(x, y+15) && !tile_solido(x+11, y+15);
}

static void atirar(void) {
    for (int i = 0; i < MAX_T; i++) {
        if (tiros[i].vivo) continue;
        tiros[i].x = px + 6; tiros[i].y = py + 8;
        tiros[i].dx = tiros[i].dy = 0;
        if (direcao == 0) tiros[i].dy = -8;
        if (direcao == 1) tiros[i].dy =  8;
        if (direcao == 2) tiros[i].dx = -8;
        if (direcao == 3) tiros[i].dx =  8;
        tiros[i].vivo = 1; tiros[i].tempo = 60;
        return;
    }
}

static void update_tiros(void) {
    for (int i = 0; i < MAX_T; i++) {
        if (!tiros[i].vivo) continue;
        tiros[i].x += tiros[i].dx;
        tiros[i].y += tiros[i].dy;
        tiros[i].tempo--;
        if (tiros[i].tempo <= 0 || tiros[i].x < 0 || tiros[i].x > MAP_W*TILE ||
            tiros[i].y < 0 || tiros[i].y > MAP_H*TILE ||
            tile_solido(tiros[i].x, tiros[i].y)) { tiros[i].vivo = 0; continue; }
        for (int j = 0; j < n_inimigos; j++) {
            if (!inimigos[j].vivo) continue;
            if (tiros[i].x > inimigos[j].x && tiros[i].x < inimigos[j].x + 16 &&
                tiros[i].y > inimigos[j].y && tiros[i].y < inimigos[j].y + 16) {
                inimigos[j].hp -= 10;
                if (inimigos[j].hp <= 0) { inimigos[j].vivo = 0; score += 100; }
                tiros[i].vivo = 0;
                break;
            }
        }
    }
}

static void update_inimigos(void) {
    for (int i = 0; i < n_inimigos; i++) {
        if (!inimigos[i].vivo) continue;
        int dx = px - inimigos[i].x, dy = py - inimigos[i].y;
        if (dx*dx + dy*dy < 40000) {
            if (dx > 0 && livre(inimigos[i].x + 1, inimigos[i].y)) inimigos[i].x++;
            else if (dx < 0 && livre(inimigos[i].x - 1, inimigos[i].y)) inimigos[i].x--;
            if (dy > 0 && livre(inimigos[i].x, inimigos[i].y + 1)) inimigos[i].y++;
            else if (dy < 0 && livre(inimigos[i].x, inimigos[i].y - 1)) inimigos[i].y--;
        }
        if (inimigos[i].x < px+16 && inimigos[i].x+16 > px &&
            inimigos[i].y < py+16 && inimigos[i].y+16 > py) hp--;
    }
}

static void int_str(int n, char* b) {
    int i = 0;
    if (!n) b[i++] = '0';
    else { char t[16]; int k = 0;
        while (n > 0) { t[k++] = '0' + n%10; n /= 10; }
        while (k > 0) b[i++] = t[--k];
    }
    b[i] = 0;
}

int main(void) {
    j2me_gfx_init();
    j2me_input_init();
    j2me_random_init();
    init_mapa();
    spawn();
    memset(tiros, 0, sizeof(tiros));

    J2MEImage* s_player = img_from(cod_player_pixels, COD_PLAYER_W, COD_PLAYER_H);
    J2MEImage* s_axis   = img_from(cod_axis_pixels,   COD_AXIS_W,   COD_AXIS_H);
    J2MEImage* s_ground = img_from(cod_ground_pixels, COD_GROUND_W, COD_GROUND_H);

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        int a = j2me_input_get_actions();
        int moveu = 0;
        if (a & J2ME_LEFT)  { direcao = 2; if (livre(px-2, py)) { px -= 2; moveu = 1; } }
        if (a & J2ME_RIGHT) { direcao = 3; if (livre(px+2, py)) { px += 2; moveu = 1; } }
        if (a & J2ME_UP)    { direcao = 0; if (livre(px, py-2)) { py -= 2; moveu = 1; } }
        if (a & J2ME_DOWN)  { direcao = 1; if (livre(px, py+2)) { py += 2; moveu = 1; } }
        if (j2me_input_is_pressed(J2ME_FIRE)) atirar();

        if (moveu) { frame_time++; if (frame_time > 6) { frame_anim = (frame_anim+1)%4; frame_time = 0; } }

        update_tiros();
        update_inimigos();

        cam_x = px - VIEW_W/2;
        cam_y = py - VIEW_H/2;
        if (cam_x < 0) cam_x = 0;
        if (cam_y < 0) cam_y = 0;
        if (cam_x > MAP_W*TILE - VIEW_W) cam_x = MAP_W*TILE - VIEW_W;
        if (cam_y > MAP_H*TILE - VIEW_H) cam_y = MAP_H*TILE - VIEW_H;

        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x000000);

        // Mapa
        int t0x = cam_x/TILE, t0y = cam_y/TILE;
        int t1x = t0x + VIEW_W/TILE + 2, t1y = t0y + VIEW_H/TILE + 2;
        if (t0x < 0) t0x = 0; if (t0y < 0) t0y = 0;
        if (t1x > MAP_W) t1x = MAP_W; if (t1y > MAP_H) t1y = MAP_H;

        for (int y = t0y; y < t1y; y++)
            for (int x = t0x; x < t1x; x++) {
                int sx = x*TILE - cam_x, sy = y*TILE - cam_y;
                int t = mapa[y][x], col = t % 7, row = t / 7;
                j2me_image_draw_region(s_ground, col*16, row*16, 16, 16,
                    TRANS_NONE, sx, sy, TOP|LEFT);
            }

        // Tiros
        j2me_gfx_set_color(0xFFFF00);
        for (int i = 0; i < MAX_T; i++)
            if (tiros[i].vivo)
                j2me_gfx_fill_rect(tiros[i].x - cam_x - 2, tiros[i].y - cam_y - 2, 4, 4);

        // Inimigos
        for (int i = 0; i < n_inimigos; i++) {
            if (!inimigos[i].vivo) continue;
            j2me_image_draw_region(s_axis, 0, 0, 16, 16, TRANS_NONE,
                inimigos[i].x - cam_x, inimigos[i].y - cam_y, TOP|LEFT);
        }

        // Player
        int fx = (frame_anim % 2) * 16;
        j2me_image_draw_region(s_player, fx, 0, 16, 16, TRANS_NONE,
            px - cam_x, py - cam_y, TOP|LEFT);

        // HUD
        char buf[16];
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("HP:", 10, 10);
        int_str(hp, buf);
        j2me_gfx_set_color(hp > 50 ? 0x00FF00 : hp > 20 ? 0xFFFF00 : 0xFF0000);
        j2me_font_draw(buf, 40, 10);

        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("SCORE:", 10, 25);
        int_str(score, buf);
        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw(buf, 70, 25);

        j2me_gfx_set_color(0x808080);
        j2me_font_draw("X: atirar   START: sair", 10, 250);

        j2me_gfx_flip();

        if (hp <= 0) {
            j2me_gfx_set_color(0xFF0000);
            j2me_font_draw("GAME OVER", 200, 130);
            j2me_gfx_flip();
            sceKernelSleepThread();
        }
    }

    j2me_image_free(s_player);
    j2me_image_free(s_axis);
    j2me_image_free(s_ground);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
