// Mobile Street Fighter - port pro PSP
#include <pspkernel.h>
#include <string.h>
#include <stdlib.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"
#include "j2me_clip.h"
#include "j2me_runtime.h"
#include "msf_sprite.h"
#include "msf_back.h"

PSP_MODULE_INFO("msf_psp", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define SCR_W 480
#define SCR_H 272
#define CHAO_Y 150

// Estados do lutador
#define ST_PARADO   0
#define ST_ANDANDO  1
#define ST_SOCO     2
#define ST_CHUTE    3
#define ST_PULO     4
#define ST_DANO     5
#define ST_VITORIA  6

// Sprites (coluna, linha) na sprite sheet
// Assumindo: 4 cols x 5 rows, sprites ~25x20
#define SPR_W 20
#define SPR_H 20

// Estados do jogo
#define J_INTRO     0
#define J_LUTA      1
#define J_VITORIA   2
#define J_DERROTA   3

static J2MEImage* img_from(const unsigned int* src, int w, int h) {
    J2MEImage* img = j2me_image_create(w, h);
    memcpy(img->pixels, src, w * h * sizeof(unsigned int));
    return img;
}

// Jogador (Ryu) - esquerda
static int p1_x = 100, p1_y = CHAO_Y;
static int p1_hp = 100;
static int p1_estado = ST_PARADO;
static int p1_frame_time = 0;
static int p1_face = 1;  // 1 = direita

// Inimigo (Lee) - direita
static int p2_x = 320, p2_y = CHAO_Y;
static int p2_hp = 100;
static int p2_estado = ST_PARADO;
static int p2_frame_time = 0;
static int p2_face = -1;  // -1 = esquerda

static int estado = J_INTRO;
static int tempo_estado = 0;
static int timer_luta = 99;
static int timer_tick = 0;

static int int_rand(int max) { return j2me_random_next(max); }

// Aplica dano (com cooldown)
static int cooldown_hit = 0;

static void p1_atacar(int tipo) {
    if (p1_estado != ST_PARADO && p1_estado != ST_ANDANDO) return;
    p1_estado = tipo;
    p1_frame_time = 0;
}

static void p2_atacar(int tipo) {
    if (p2_estado != ST_PARADO && p2_estado != ST_ANDANDO) return;
    p2_estado = tipo;
    p2_frame_time = 0;
}

static void reset_luta(void) {
    p1_x = 100; p1_y = CHAO_Y; p1_hp = 100; p1_estado = ST_PARADO;
    p2_x = 320; p2_y = CHAO_Y; p2_hp = 100; p2_estado = ST_PARADO;
    timer_luta = 99; timer_tick = 0; cooldown_hit = 0;
    estado = J_LUTA; tempo_estado = 0;
}

static int hitbox_ativo(int estado_lut) {
    return (estado_lut == ST_SOCO || estado_lut == ST_CHUTE);
}

static int calcular_dano(int estado_lut) {
    if (estado_lut == ST_SOCO) return 5;
    if (estado_lut == ST_CHUTE) return 8;
    return 0;
}

// Retorna 1 se A acerta B
static int verificar_acerto(int ax, int aface, int aestado, int bx) {
    if (!hitbox_ativo(aestado)) return 0;
    // Alcance do ataque
    int alcance = (aestado == ST_SOCO) ? 40 : 50;
    int ataque_x = ax + (aface > 0 ? 20 : -alcance);
    // Se o ataque tá perto do B
    return (ataque_x < bx + 30 && ataque_x + alcance > bx - 5);
}

static void int_str(int n, char* b) {
    int i = 0;
    if (!n) b[i++] = '0';
    else { char t[8]; int k = 0;
        while (n>0) { t[k++]='0'+n%10; n/=10; }
        while (k>0) b[i++]=t[--k];
    }
    b[i] = 0;
}

int main(void) {
    j2me_gfx_init();
    j2me_input_init();
    j2me_random_init();

    J2MEImage* sprite = img_from(msf_sprite_pixels, MSF_SPRITE_W, MSF_SPRITE_H);
    J2MEImage* fundo  = img_from(msf_back_pixels,   MSF_BACK_W,   MSF_BACK_H);

    estado = J_INTRO;

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;

        tempo_estado++;

        // ===== INTRO =====
        if (estado == J_INTRO) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x000000);

            j2me_gfx_set_color(0xFF0000);
            j2me_font_draw("MOBILE", 180, 60);
            j2me_gfx_set_color(0xFFFF00);
            j2me_font_draw("STREET FIGHTER", 150, 80);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("PSP EDITION", 180, 100);

            j2me_gfx_set_color(0x00FF00);
            if ((tempo_estado / 20) % 2 == 0)
                j2me_font_draw("X - LUTAR!", 180, 180);

            j2me_gfx_set_color(0x808080);
            j2me_font_draw("D-Pad: mover  |  X: soco  |  O: chute", 80, 230);
            j2me_font_draw("START: sair", 180, 248);

            j2me_gfx_flip();

            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        // ===== VITORIA =====
        if (estado == J_VITORIA) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x001800);

            j2me_gfx_set_color(0x00FF00);
            j2me_font_draw("VITORIA!", 180, 100);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("X - lutar de novo", 150, 160);
            j2me_gfx_set_color(0x808080);
            j2me_font_draw("START - sair", 180, 190);

            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        // ===== DERROTA =====
        if (estado == J_DERROTA) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x180000);

            j2me_gfx_set_color(0xFF0000);
            j2me_font_draw("DERROTA...", 180, 100);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("X - tentar de novo", 150, 160);
            j2me_gfx_set_color(0x808080);
            j2me_font_draw("START - sair", 180, 190);

            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        // ===== LUTA =====
        int acoes = j2me_input_get_actions();

        // === Jogador ===
        if (p1_estado == ST_PARADO || p1_estado == ST_ANDANDO) {
            if (acoes & J2ME_LEFT) {
                p1_x -= 2; p1_face = -1; p1_estado = ST_ANDANDO;
            } else if (acoes & J2ME_RIGHT) {
                p1_x += 2; p1_face = 1; p1_estado = ST_ANDANDO;
            } else {
                p1_estado = ST_PARADO;
            }
            if (p1_x < 20) p1_x = 20;
            if (p1_x > 350) p1_x = 350;

            if (j2me_input_is_pressed(J2ME_FIRE)) p1_atacar(ST_SOCO);
            // O = chute (segundo botão)
            if (j2me_input_is_pressed(J2ME_UP)) p1_atacar(ST_CHUTE);
        } else {
            // Em estado de ataque - não pode se mover
            p1_frame_time++;
            if (p1_frame_time > 20) {
                p1_estado = ST_PARADO;
                p1_frame_time = 0;
            }
        }

        // === Inimigo (IA simples) ===
        if (p2_estado == ST_PARADO || p2_estado == ST_ANDANDO) {
            int dist = p1_x - p2_x;
            p2_face = (dist > 0) ? 1 : -1;

            if (abs(dist) > 70) {
                // Aproxima
                p2_x += (dist > 0) ? 1 : -1;
                p2_estado = ST_ANDANDO;
            } else {
                // Ataca
                int r = int_rand(100);
                if (r < 3) p2_atacar(ST_SOCO);
                else if (r < 5) p2_atacar(ST_CHUTE);
                else p2_estado = ST_PARADO;
            }
            if (p2_x < 20) p2_x = 20;
            if (p2_x > 420) p2_x = 420;
        } else {
            p2_frame_time++;
            if (p2_frame_time > 25) {
                p2_estado = ST_PARADO;
                p2_frame_time = 0;
            }
        }

        // === Colisão de ataques ===
        if (cooldown_hit > 0) cooldown_hit--;

        if (cooldown_hit == 0) {
            if (verificar_acerto(p1_x, p1_face, p1_estado, p2_x)) {
                p2_hp -= calcular_dano(p1_estado);
                cooldown_hit = 30;
            }
            if (verificar_acerto(p2_x, p2_face, p2_estado, p1_x)) {
                p1_hp -= calcular_dano(p2_estado);
                cooldown_hit = 30;
            }
        }

        // Timer
        timer_tick++;
        if (timer_tick >= 60) {
            timer_tick = 0;
            timer_luta--;
            if (timer_luta <= 0) {
                // Fim do tempo - quem tem mais vida ganha
                if (p1_hp > p2_hp) estado = J_VITORIA;
                else if (p2_hp > p1_hp) estado = J_DERROTA;
                else estado = J_VITORIA;  // empate → vitória por padrão
            }
        }

        // Fim de jogo
        if (p1_hp <= 0) { estado = J_DERROTA; continue; }
        if (p2_hp <= 0) { estado = J_VITORIA; continue; }

        // === Desenho ===
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x402040);

        // Fundo - back.png (120x80) esticado verticalmente
        for (int x = 0; x < SCR_W; x += 120) {
            j2me_image_blit(fundo, x, 0);
            j2me_image_blit(fundo, x, 80);
            j2me_image_blit(fundo, x, 160);
        }

        // Chão
        j2me_gfx_set_color(0x604020);
        j2me_gfx_fill_rect(0, CHAO_Y + 20, SCR_W, 60);

        // Personagem 1 (Ryu) - usa sprite sheet
        int p1_col = (p1_estado == ST_SOCO) ? 1 :
                     (p1_estado == ST_CHUTE) ? 2 :
                     (p1_estado == ST_ANDANDO) ? ((tempo_estado / 6) % 2) : 0;
        int p1_lin = 0;
        // Desenha Ryu em escala 2x (pixel por pixel)
        {
            int base_x = p1_col * 20;
            int base_y = p1_lin * 20;
            for (int sy = 0; sy < 20; sy++) {
                for (int sx = 0; sx < 20; sx++) {
                    int px_idx = (base_y + sy) * MSF_SPRITE_W + (base_x + sx);
                    if (px_idx >= MSF_SPRITE_W * MSF_SPRITE_H) continue;
                    unsigned int cor = sprite->pixels[px_idx];
                    if ((cor & 0xFF000000) == 0) continue;
                    int draw_x = p1_face < 0 ? (p1_x + (19 - sx) * 3) : (p1_x + sx * 3);
                    j2me_gfx_set_color(cor & 0xFFFFFF);
                    j2me_gfx_fill_rect(draw_x, p1_y + sy * 3, 3, 3);
                }
            }
        }

        // Personagem 2 (Lee)
        int p2_col = (p2_estado == ST_SOCO) ? 1 :
                     (p2_estado == ST_CHUTE) ? 2 :
                     (p2_estado == ST_ANDANDO) ? ((tempo_estado / 6) % 2) : 0;
        int p2_lin = 1;
        {
            int base_x = p2_col * 20;
            int base_y = p2_lin * 20;
            for (int sy = 0; sy < 20; sy++) {
                for (int sx = 0; sx < 20; sx++) {
                    int px_idx = (base_y + sy) * MSF_SPRITE_W + (base_x + sx);
                    if (px_idx >= MSF_SPRITE_W * MSF_SPRITE_H) continue;
                    unsigned int cor = sprite->pixels[px_idx];
                    if ((cor & 0xFF000000) == 0) continue;
                    int draw_x = p2_face > 0 ? (p2_x + (19 - sx) * 3) : (p2_x + sx * 3);
                    j2me_gfx_set_color(cor & 0xFFFFFF);
                    j2me_gfx_fill_rect(draw_x, p2_y + sy * 3, 3, 3);
                }
            }
        }

        // === HUD ===
        char buf[8];

        // Barra de vida P1
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("RYU", 10, 10);
        j2me_gfx_set_color(0xFF0000);
        j2me_gfx_fill_rect(10, 25, 180, 14);
        j2me_gfx_set_color(0x00FF00);
        j2me_gfx_fill_rect(10, 25, 180 * p1_hp / 100, 14);

        // Barra de vida P2
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("LEE", 400, 10);
        j2me_gfx_set_color(0xFF0000);
        j2me_gfx_fill_rect(290, 25, 180, 14);
        j2me_gfx_set_color(0x00FF00);
        int hp_w = 180 * p2_hp / 100;
        j2me_gfx_fill_rect(290 + (180 - hp_w), 25, hp_w, 14);

        // Timer
        j2me_gfx_set_color(0xFFFF00);
        int_str(timer_luta, buf);
        j2me_font_draw(buf, 230, 10);

        // Controles
        j2me_gfx_set_color(0x808080);
        j2me_font_draw("D-Pad: mover  X: soco  Cima: chute", 90, 255);

        j2me_gfx_flip();
    }

    j2me_image_free(sprite);
    j2me_image_free(fundo);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
