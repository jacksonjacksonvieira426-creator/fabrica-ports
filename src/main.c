// CoD PSP - Versao completa com 9 missoes
#include <pspkernel.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"
#include "j2me_clip.h"
#include "j2me_runtime.h"
#include "j2me_rms.h"
#include "cod_player.h"
#include "cod_axis.h"
#include "cod_ground.h"
#include "cod_special.h"
#include "missoes.h"

PSP_MODULE_INFO("cod_psp", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define TILE    16
#define MAP_W   40
#define MAP_H   30
#define VIEW_W  480
#define VIEW_H  272
#define MAX_E   20
#define MAX_T   32

#define T_GRAMA  0
#define T_TERRA  1
#define T_AGUA   10
#define T_PEDRA  14
#define T_GRAMA2 2

// Estados do jogo
typedef enum {
    ST_BRIEFING,
    ST_JOGANDO,
    ST_VITORIA,
    ST_DERROTA,
    ST_FIM
} Estado;

// Mapa
static unsigned char mapa[MAP_H][MAP_W];
static int flag_x, flag_y;  // objetivo

// Player
static int px, py, hp, muni;
static int direcao, frame_anim, frame_time;
static int score;
static int cooldown_dano;

// Inimigos
typedef struct { int x, y, hp, vivo; } Enemy;
static Enemy inimigos[MAX_E];
static int n_inimigos;

// Tiros
typedef struct { int x, y, dx, dy, vivo, tempo; } Tiro;
static Tiro tiros[MAX_T];

// Estado global
static Estado estado = ST_BRIEFING;
static int missao_atual = 0;
static int tempo_estado = 0;
static int mortos_total = 0;

// RS para high scores
static RecordStore* rs = 0;

// PRNG simples com seed
static unsigned int prng_state;
static void prng_seed(unsigned int s) { prng_state = s ? s : 1; }
static int prng_next(int max) {
    prng_state = prng_state * 1103515245 + 12345;
    return (int)((prng_state >> 16) % (unsigned int)max);
}

// ===== Geracao de mapa procedural =====
static void gerar_mapa(unsigned int seed, int dificuldade) {
    prng_seed(seed);

    // Base: grama
    for (int y = 0; y < MAP_H; y++)
        for (int x = 0; x < MAP_W; x++)
            mapa[y][x] = T_GRAMA;

    // Borda de pedra
    for (int x = 0; x < MAP_W; x++) { mapa[0][x] = T_PEDRA; mapa[MAP_H-1][x] = T_PEDRA; }
    for (int y = 0; y < MAP_H; y++) { mapa[y][0] = T_PEDRA; mapa[y][MAP_W-1] = T_PEDRA; }

    // Rio vertical (posicao aleatoria)
    int rio_x = 8 + prng_next(24);
    for (int y = 1; y < MAP_H-1; y++) {
        mapa[y][rio_x] = T_AGUA;
        mapa[y][rio_x+1] = T_AGUA;
    }
    // Ponte na metade
    int ponte_y = 5 + prng_next(MAP_H - 12);
    mapa[ponte_y][rio_x] = T_TERRA;
    mapa[ponte_y][rio_x+1] = T_TERRA;
    mapa[ponte_y+1][rio_x] = T_TERRA;
    mapa[ponte_y+1][rio_x+1] = T_TERRA;

    // Estradas horizontais
    for (int y = 4; y < MAP_H; y += 6) {
        for (int x = 1; x < MAP_W-1; x++) {
            if (mapa[y][x] != T_AGUA) mapa[y][x] = T_TERRA;
            if (y+1 < MAP_H-1 && mapa[y+1][x] != T_AGUA) mapa[y+1][x] = T_TERRA;
        }
    }

    // Blocos de predios (3-6)
    int n_predios = 4 + dificuldade / 2;
    for (int i = 0; i < n_predios; i++) {
        int bx = 3 + prng_next(MAP_W - 10);
        int by = 3 + prng_next(MAP_H - 10);
        int bw = 2 + prng_next(4);
        int bh = 2 + prng_next(3);
        for (int y = by; y < by+bh && y < MAP_H-1; y++)
            for (int x = bx; x < bx+bw && x < MAP_W-1; x++)
                if (mapa[y][x] == T_GRAMA) mapa[y][x] = T_PEDRA;
    }

    // Detalhes de grama clara
    for (int i = 0; i < 80; i++) {
        int x = 1 + prng_next(MAP_W - 2);
        int y = 1 + prng_next(MAP_H - 2);
        if (mapa[y][x] == T_GRAMA) mapa[y][x] = T_GRAMA2;
    }

    // Spawn do player (canto esquerdo, embaixo)
    px = 3 * TILE;
    py = (MAP_H - 4) * TILE;
    // Garante que nao ta em parede
    if (mapa[py/TILE][px/TILE] == T_PEDRA || mapa[py/TILE][px/TILE] == T_AGUA) {
        for (int x = 1; x < 10; x++) {
            if (mapa[(MAP_H-4)][x] == T_GRAMA) { px = x * TILE; break; }
        }
    }

    // Bandeira vermelha (canto direito, em cima)
    flag_x = (MAP_W - 4) * TILE;
    flag_y = 3 * TILE;
    for (int y = 1; y < 8; y++) {
        for (int x = MAP_W - 6; x < MAP_W - 2; x++) {
            if (mapa[y][x] == T_GRAMA || mapa[y][x] == T_GRAMA2) {
                flag_x = x * TILE;
                flag_y = y * TILE;
                y = 8; break;
            }
        }
    }
}

static void spawn_inimigos(int n) {
    n_inimigos = n;
    for (int i = 0; i < n; i++) {
        int tx, ty;
        int tent = 0;
        do {
            tx = 5 + prng_next(MAP_W - 10);
            ty = 3 + prng_next(MAP_H - 6);
            tent++;
        } while (tent < 50 && (mapa[ty][tx] == T_PEDRA || mapa[ty][tx] == T_AGUA ||
                                (tx*TILE > px - 150 && tx*TILE < px + 150 &&
                                 ty*TILE > py - 150 && ty*TILE < py + 150)));
        inimigos[i].x = tx * TILE;
        inimigos[i].y = ty * TILE;
        inimigos[i].hp = 20 + missao_atual * 5;
        inimigos[i].vivo = 1;
    }
}

// ===== Helpers =====
static J2MEImage* img_from(const unsigned int* src, int w, int h) {
    J2MEImage* img = j2me_image_create(w, h);
    if (!img) return NULL;
    memcpy(img->pixels, src, w * h * sizeof(unsigned int));
    return img;
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
    if (muni <= 0) return;
    for (int i = 0; i < MAX_T; i++) {
        if (tiros[i].vivo) continue;
        tiros[i].x = px + 6; tiros[i].y = py + 8;
        tiros[i].dx = tiros[i].dy = 0;
        if (direcao == 0) tiros[i].dy = -8;
        if (direcao == 1) tiros[i].dy =  8;
        if (direcao == 2) tiros[i].dx = -8;
        if (direcao == 3) tiros[i].dx =  8;
        tiros[i].vivo = 1; tiros[i].tempo = 60;
        muni--;
        return;
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

// ===== Inicio de missao =====
static void iniciar_missao(int m) {
    missao_atual = m;
    gerar_mapa(MISSOES[m].seed, MISSOES[m].dificuldade);
    spawn_inimigos(MISSOES[m].n_inimigos);
    memset(tiros, 0, sizeof(tiros));

    hp = 100;
    muni = 30 + missao_atual * 5;
    score = 0;
    direcao = 1;
    frame_anim = 0;
    frame_time = 0;
    cooldown_dano = 0;

    estado = ST_BRIEFING;
    tempo_estado = 0;
}

// ===== Desenho =====
static void desenhar_mundo(J2MEImage* s_ground) {
    int cam_x = px - VIEW_W/2;
    int cam_y = py - VIEW_H/2;
    if (cam_x < 0) cam_x = 0;
    if (cam_y < 0) cam_y = 0;
    if (cam_x > MAP_W*TILE - VIEW_W) cam_x = MAP_W*TILE - VIEW_W;
    if (cam_y > MAP_H*TILE - VIEW_H) cam_y = MAP_H*TILE - VIEW_H;

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
    return;
}

static int get_cam_x(void) {
    int c = px - VIEW_W/2;
    if (c < 0) c = 0;
    if (c > MAP_W*TILE - VIEW_W) c = MAP_W*TILE - VIEW_W;
    return c;
}
static int get_cam_y(void) {
    int c = py - VIEW_H/2;
    if (c < 0) c = 0;
    if (c > MAP_H*TILE - VIEW_H) c = MAP_H*TILE - VIEW_H;
    return c;
}

// ===== Main =====
int main(void) {
    j2me_gfx_init();
    j2me_input_init();
    j2me_random_init();

    J2MEImage* s_player = img_from(cod_player_pixels, COD_PLAYER_W, COD_PLAYER_H);
    J2MEImage* s_axis   = img_from(cod_axis_pixels,   COD_AXIS_W,   COD_AXIS_H);
    J2MEImage* s_ground = img_from(cod_ground_pixels, COD_GROUND_W, COD_GROUND_H);
    J2MEImage* s_special = img_from(cod_special_pixels, COD_SPECIAL_W, COD_SPECIAL_H);

    rs = j2me_rms_open("cod_save", 1);
    iniciar_missao(0);

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        tempo_estado++;

        // ===== ESTADO: BRIEFING =====
        if (estado == ST_BRIEFING) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x101820);

            j2me_gfx_set_color(0xFFFF00);
            j2me_font_draw(MISSOES[missao_atual].titulo, 30, 40);

            j2me_gfx_set_color(0xFFFFFF);
            // Quebra briefing em linhas de ~50 chars
            const char* txt = MISSOES[missao_atual].briefing;
            char linha[64];
            int li = 0, cx = 30, cy = 80;
            int ultimo_espaco = -1;
            for (int i = 0; txt[i] || li > 0; i++) {
                char ch = txt[i];
                if (ch == 0) {
                    if (li > 0) { linha[li] = 0; j2me_font_draw(linha, cx, cy); }
                    break;
                }
                if (ch == ' ') ultimo_espaco = li;
                linha[li++] = ch;
                if (li >= 50) {
                    if (ultimo_espaco > 0) {
                        // Volta pro ultimo espaco
                        int guardar = li - ultimo_espaco - 1;
                        linha[ultimo_espaco] = 0;
                        j2me_font_draw(linha, cx, cy);
                        cy += 12;
                        // Move o resto pra frente
                        for (int k = 0; k < guardar; k++)
                            linha[k] = linha[ultimo_espaco + 1 + k];
                        li = guardar;
                        ultimo_espaco = -1;
                    } else {
                        linha[li] = 0;
                        j2me_font_draw(linha, cx, cy);
                        cy += 12;
                        li = 0;
                        ultimo_espaco = -1;
                    }
                }
            }

            j2me_gfx_set_color(0x00FF00);
            j2me_font_draw("X - INICIAR MISSAO", 30, 230);
            j2me_gfx_set_color(0x808080);
            j2me_font_draw("START - sair", 250, 230);

            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) {
                estado = ST_JOGANDO;
                tempo_estado = 0;
            }
            continue;
        }

        // ===== ESTADO: VITORIA =====
        if (estado == ST_VITORIA) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x001800);
            j2me_gfx_set_color(0x00FF00);
            j2me_font_draw("MISSAO CUMPRIDA!", 140, 100);
            char b[16];
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("Inimigos:", 150, 140);
            int_str(mortos_total, b);
            j2me_font_draw(b, 260, 140);

            if (missao_atual < 8) {
                j2me_gfx_set_color(0xFFFF00);
                j2me_font_draw("X - proxima missao", 130, 200);
            } else {
                j2me_gfx_set_color(0x00FFFF);
                j2me_font_draw("VOCE ZEROU O JOGO!", 120, 200);
            }
            j2me_gfx_flip();

            if (j2me_input_is_pressed(J2ME_FIRE)) {
                mortos_total = 0;
                if (missao_atual < 8) iniciar_missao(missao_atual + 1);
                else estado = ST_FIM;
            }
            continue;
        }

        // ===== ESTADO: DERROTA =====
        if (estado == ST_DERROTA) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x180000);
            j2me_gfx_set_color(0xFF0000);
            j2me_font_draw("VOCE MORREU", 170, 100);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("X - tentar de novo", 140, 150);
            j2me_gfx_set_color(0x808080);
            j2me_font_draw("START - sair", 170, 180);
            j2me_gfx_flip();

            if (j2me_input_is_pressed(J2ME_FIRE)) iniciar_missao(missao_atual);
            continue;
        }

        // ===== ESTADO: FIM =====
        if (estado == ST_FIM) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x000018);
            j2me_gfx_set_color(0x00FFFF);
            j2me_font_draw("OBRIGADO POR JOGAR!", 120, 100);
            j2me_gfx_set_color(0xFFFF00);
            j2me_font_draw("Call of Duty PSP", 140, 130);
            j2me_gfx_flip();
            continue;
        }

        // ===== ESTADO: JOGANDO =====
        int a = j2me_input_get_actions();
        int moveu = 0;
        if (a & J2ME_LEFT)  { direcao = 2; if (livre(px-2, py)) { px -= 2; moveu = 1; } }
        if (a & J2ME_RIGHT) { direcao = 3; if (livre(px+2, py)) { px += 2; moveu = 1; } }
        if (a & J2ME_UP)    { direcao = 0; if (livre(px, py-2)) { py -= 2; moveu = 1; } }
        if (a & J2ME_DOWN)  { direcao = 1; if (livre(px, py+2)) { py += 2; moveu = 1; } }
        if (j2me_input_is_pressed(J2ME_FIRE)) atirar();

        if (moveu) { frame_time++; if (frame_time > 6) { frame_anim = (frame_anim+1)%3; frame_time = 0; } }

        // Atualiza tiros
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
                    if (inimigos[j].hp <= 0) {
                        inimigos[j].vivo = 0;
                        score += 100;
                        mortos_total++;
                    }
                    tiros[i].vivo = 0;
                    break;
                }
            }
        }

        // Atualiza inimigos
        if (cooldown_dano > 0) cooldown_dano--;
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
                inimigos[i].y < py+16 && inimigos[i].y+16 > py) {
                if (cooldown_dano <= 0) {
                    hp -= 10;
                    cooldown_dano = 30;
                }
            }
        }

        // Verifica vitoria (chegou na bandeira)
        if (px < flag_x + 32 && px + 16 > flag_x &&
            py < flag_y + 32 && py + 16 > flag_y) {
            estado = ST_VITORIA;
            tempo_estado = 0;
            continue;
        }

        // Verifica derrota
        if (hp <= 0) {
            estado = ST_DERROTA;
            tempo_estado = 0;
            continue;
        }

        // Recarrega municao com o tempo (de graca)
        if (tempo_estado % 120 == 0 && muni < 50) muni++;

        // ===== DESENHO =====
        int cam_x = get_cam_x();
        int cam_y = get_cam_y();

        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x000000);
        desenhar_mundo(s_ground);

        // Bandeira (objetivo) - usa special.png
        j2me_image_draw_region(s_special, 5*16, 2*16, 16, 16, TRANS_NONE,
            flag_x - cam_x, flag_y - cam_y, TOP|LEFT);
        // Brilho vermelho em volta
        j2me_gfx_set_color(0xFF0000);
        j2me_gfx_fill_rect(flag_x - cam_x - 2, flag_y - cam_y - 2, 20, 2);
        j2me_gfx_fill_rect(flag_x - cam_x - 2, flag_y - cam_y + 16, 20, 2);

        // Tiros
        j2me_gfx_set_color(0xFFFF00);
        for (int i = 0; i < MAX_T; i++)
            if (tiros[i].vivo)
                j2me_gfx_fill_rect(tiros[i].x - cam_x - 2, tiros[i].y - cam_y - 2, 4, 4);

        // Inimigos
        for (int i = 0; i < n_inimigos; i++) {
            if (!inimigos[i].vivo) continue;
            // Inimigo olha na direcao do player
            int edx = px - inimigos[i].x;
            int edy = py - inimigos[i].y;
            int elin;
            if (abs(edx) > abs(edy)) elin = (edx > 0) ? 3 : 2;  // dir ou esq
            else                     elin = (edy > 0) ? 1 : 0;  // baixo ou cima
            j2me_image_draw_region(s_axis, 0, elin*16, 16, 16, TRANS_NONE,
                inimigos[i].x - cam_x, inimigos[i].y - cam_y, TOP|LEFT);
        }

        // Player - LINHA = direcao, COLUNA = frame de caminhada
        // direcao: 0=cima, 1=baixo, 2=esq, 3=dir
        int lin_spr;
        if (direcao == 0)      lin_spr = 1;  // cima -> sprite baixo
        else if (direcao == 1) lin_spr = 0;  // baixo -> sprite cima
        else if (direcao == 2) lin_spr = 3;  // esquerda -> sprite direita
        else                   lin_spr = 2;  // direita -> sprite esquerda
        
        int col_spr = frame_anim % 3;  // 3 frames de caminhada
        
        j2me_image_draw_region(s_player, col_spr*16, lin_spr*16, 16, 16, TRANS_NONE,
            px - cam_x, py - cam_y, TOP|LEFT);

        // HUD
        char buf[16];
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("HP", 10, 10);
        int_str(hp, buf);
        j2me_gfx_set_color(hp > 50 ? 0x00FF00 : hp > 20 ? 0xFFFF00 : 0xFF0000);
        j2me_font_draw(buf, 35, 10);

        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("MUN", 10, 25);
        int_str(muni, buf);
        j2me_gfx_set_color(0x00FFFF);
        j2me_font_draw(buf, 45, 25);

        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("SCORE", 10, 40);
        int_str(score, buf);
        j2me_gfx_set_color(0xFFFF00);
        j2me_font_draw(buf, 65, 40);

        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("MS", 10, 55);
        int_str(missao_atual + 1, buf);
        j2me_gfx_set_color(0x80FF80);
        j2me_font_draw(buf, 40, 55);

        // Seta apontando pra bandeira
        int dx = flag_x - px, dy = flag_y - py;
        int dist = (dx*dx + dy*dy);
        if (dist > 10000) {
            j2me_gfx_set_color(0xFF4040);
            j2me_font_draw("-> OBJETIVO", 380, 10);
        }

        j2me_gfx_flip();
    }

    if (rs) j2me_rms_close(rs);
    j2me_image_free(s_player);
    j2me_image_free(s_axis);
    j2me_image_free(s_ground);
    j2me_image_free(s_special);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
