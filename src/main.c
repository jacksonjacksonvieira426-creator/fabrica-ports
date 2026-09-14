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
#include "msf_r_parado.h"
#include "msf_r_soco.h"
#include "msf_r_chute.h"
#include "msf_r_and1.h"
#include "msf_r_and2.h"
#include "msf_back.h"

PSP_MODULE_INFO("msf_psp", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define SCR_W 480
#define SCR_H 272
#define CHAO_Y 180     // onde o chão começa (y)
#define P1_INI_X 120
#define P2_INI_X 340

#define ST_PARADO   0
#define ST_ANDANDO  1
#define ST_SOCO     2
#define ST_CHUTE    3

#define J_INTRO     0
#define J_LUTA      1
#define J_VITORIA   2
#define J_DERROTA   3

static J2MEImage* img_from(const unsigned int* src, int w, int h) {
    J2MEImage* img = j2me_image_create(w, h);
    memcpy(img->pixels, src, w * h * sizeof(unsigned int));
    return img;
}

// Sprites como imagens separadas
static J2MEImage *s_parado, *s_soco, *s_chute, *s_and1, *s_and2;

static J2MEImage* sprite_atual(int estado) {
    if (estado == ST_SOCO) return s_soco;
    if (estado == ST_CHUTE) return s_chute;
    if (estado == ST_ANDANDO) return s_and1;
    return s_parado;
}

// Desenha sprite com escala 3x, flip horizontal se quiser
static void desenha_personagem(J2MEImage* img, int x, int y, int flip, int escala) {
    if (!img) return;
    // Ponto: y = base dos pés. Desenha pra cima.
    int largura_px = img->w * escala;
    int altura_px = img->h * escala;
    int base_y = y - altura_px;

    for (int sy = 0; sy < img->h; sy++) {
        for (int sx = 0; sx < img->w; sx++) {
            unsigned int cor = img->pixels[sy * img->w + sx];
            if ((cor & 0xFF000000) == 0) continue;
            j2me_gfx_set_color(cor & 0xFFFFFF);
            int dx = flip ? (x + (img->w - 1 - sx) * escala) : (x + sx * escala);
            j2me_gfx_fill_rect(dx, base_y + sy * escala, escala, escala);
        }
    }
}

// Jogador
static int p1_x = P1_INI_X, p1_hp = 100;
static int p1_estado = ST_PARADO;
static int p1_frame_time = 0;
static int p1_face = 1;

// Inimigo
static int p2_x = P2_INI_X, p2_hp = 100;
static int p2_estado = ST_PARADO;
static int p2_frame_time = 0;
static int p2_face = -1;

static int estado = J_INTRO;
static int tempo_estado = 0;
static int timer_luta = 99;
static int timer_tick = 0;
static int cooldown_hit = 0;

static void reset_luta(void) {
    p1_x = P1_INI_X; p1_hp = 100; p1_estado = ST_PARADO; p1_face = 1;
    p2_x = P2_INI_X; p2_hp = 100; p2_estado = ST_PARADO; p2_face = -1;
    timer_luta = 99; timer_tick = 0; cooldown_hit = 0;
    estado = J_LUTA; tempo_estado = 0;
}

static int hitbox_ativo(int e) { return (e == ST_SOCO || e == ST_CHUTE); }
static int dano_de(int e) { return (e == ST_SOCO) ? 5 : (e == ST_CHUTE) ? 8 : 0; }

static int colidiu(int ax, int aface, int aestado, int bx) {
    if (!hitbox_ativo(aestado)) return 0;
    int alcance = (aestado == ST_SOCO) ? 40 : 55;
    int ataque_x = ax + (aface > 0 ? 20 : -alcance);
    return (ataque_x < bx + 40 && ataque_x + alcance > bx);
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

    s_parado = img_from(msf_r_parado_pixels, MSF_R_PARADO_W, MSF_R_PARADO_H);
    s_soco   = img_from(msf_r_soco_pixels,   MSF_R_SOCO_W,   MSF_R_SOCO_H);
    s_chute  = img_from(msf_r_chute_pixels,  MSF_R_CHUTE_W,  MSF_R_CHUTE_H);
    s_and1   = img_from(msf_r_and1_pixels,   MSF_R_AND1_W,   MSF_R_AND1_H);
    s_and2   = img_from(msf_r_and2_pixels,   MSF_R_AND2_W,   MSF_R_AND2_H);
    J2MEImage* fundo = img_from(msf_back_pixels, MSF_BACK_W, MSF_BACK_H);

    estado = J_INTRO;

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;
        tempo_estado++;

        // INTRO
        if (estado == J_INTRO) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x000000);

            j2me_gfx_set_color(0xFF0000);
            j2me_font_draw("MOBILE", 180, 60);
            j2me_gfx_set_color(0xFFFF00);
            j2me_font_draw("STREET FIGHTER", 150, 85);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("PSP EDITION", 180, 110);

            j2me_gfx_set_color(0x00FF00);
            if ((tempo_estado / 20) % 2 == 0)
                j2me_font_draw("X - LUTAR!", 180, 180);

            j2me_gfx_set_color(0x808080);
            j2me_font_draw("D-Pad: mover  X: soco  Cima: chute  START: sair", 40, 240);

            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        // VITORIA
        if (estado == J_VITORIA) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x001800);
            j2me_gfx_set_color(0x00FF00);
            j2me_font_draw("VITORIA!", 180, 100);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("X - lutar de novo", 140, 160);
            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        // DERROTA
        if (estado == J_DERROTA) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x180000);
            j2me_gfx_set_color(0xFF0000);
            j2me_font_draw("DERROTA...", 180, 100);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("X - tentar de novo", 140, 160);
            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        // LUTA
        int acoes = j2me_input_get_actions();

        // P1 (Ryu)
        if (p1_estado == ST_PARADO || p1_estado == ST_ANDANDO) {
            if (acoes & J2ME_LEFT)       { p1_x -= 2; p1_face = -1; p1_estado = ST_ANDANDO; }
            else if (acoes & J2ME_RIGHT) { p1_x += 2; p1_face = 1;  p1_estado = ST_ANDANDO; }
            else p1_estado = ST_PARADO;

            if (p1_x < 20) p1_x = 20;
            if (p1_x > 300) p1_x = 300;

            if (j2me_input_is_pressed(J2ME_FIRE)) { p1_estado = ST_SOCO; p1_frame_time = 0; }
            else if (j2me_input_is_pressed(J2ME_UP)) { p1_estado = ST_CHUTE; p1_frame_time = 0; }
        } else {
            p1_frame_time++;
            if (p1_frame_time > 20) { p1_estado = ST_PARADO; p1_frame_time = 0; }
        }

        // P2 (Lee IA)
        if (p2_estado == ST_PARADO || p2_estado == ST_ANDANDO) {
            int dist = p1_x - p2_x;
            p2_face = (dist > 0) ? 1 : -1;
            if (abs(dist) > 70) {
                p2_x += (dist > 0) ? 1 : -1;
                p2_estado = ST_ANDANDO;
            } else {
                int r = j2me_random_next(100);
                if (r < 4)      { p2_estado = ST_SOCO;  p2_frame_time = 0; }
                else if (r < 7) { p2_estado = ST_CHUTE; p2_frame_time = 0; }
                else p2_estado = ST_PARADO;
            }
            if (p2_x < 180) p2_x = 180;
            if (p2_x > 440) p2_x = 440;
        } else {
            p2_frame_time++;
            if (p2_frame_time > 25) { p2_estado = ST_PARADO; p2_frame_time = 0; }
        }

        // Colisão
        if (cooldown_hit > 0) cooldown_hit--;
        if (cooldown_hit == 0) {
            if (colidiu(p1_x, p1_face, p1_estado, p2_x)) { p2_hp -= dano_de(p1_estado); cooldown_hit = 30; }
            if (colidiu(p2_x, p2_face, p2_estado, p1_x)) { p1_hp -= dano_de(p2_estado); cooldown_hit = 30; }
        }

        // Timer
        timer_tick++;
        if (timer_tick >= 60) {
            timer_tick = 0;
            timer_luta--;
            if (timer_luta <= 0) {
                if (p1_hp >= p2_hp) estado = J_VITORIA;
                else estado = J_DERROTA;
                continue;
            }
        }

        if (p1_hp <= 0) { estado = J_DERROTA; continue; }
        if (p2_hp <= 0) { estado = J_VITORIA; continue; }

        // ===== DESENHO =====
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x201020);

        // Fundo: 4 cópias horizontais na parte de cima
        for (int x = 0; x < SCR_W; x += 120) {
            j2me_image_blit(fundo, x, 20);
        }
        // Chão (marrom)
        j2me_gfx_set_color(0x604020);
        j2me_gfx_fill_rect(0, CHAO_Y, SCR_W, SCR_H - CHAO_Y);
        // Linha do horizonte
        j2me_gfx_set_color(0x303030);
        j2me_gfx_fill_rect(0, CHAO_Y - 2, SCR_W, 2);

        // Ryu
        J2MEImage* spr1 = sprite_atual(p1_estado);
        if (p1_estado == ST_ANDANDO) spr1 = ((tempo_estado/6)%2==0) ? s_and1 : s_and2;
        desenha_personagem(spr1, p1_x, CHAO_Y + 8, p1_face < 0, 3);

        // Lee (usa os mesmos sprites por enquanto)
        J2MEImage* spr2 = sprite_atual(p2_estado);
        if (p2_estado == ST_ANDANDO) spr2 = ((tempo_estado/6)%2==0) ? s_and1 : s_and2;
        desenha_personagem(spr2, p2_x, CHAO_Y + 8, p2_face > 0, 3);

        // HUD
        char buf[8];
        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("RYU", 10, 10);
        j2me_gfx_set_color(0xFF0000);
        j2me_gfx_fill_rect(10, 25, 180, 14);
        j2me_gfx_set_color(0x00FF00);
        j2me_gfx_fill_rect(10, 25, 180 * p1_hp / 100, 14);

        j2me_gfx_set_color(0xFFFFFF);
        j2me_font_draw("LEE", 400, 10);
        j2me_gfx_set_color(0xFF0000);
        j2me_gfx_fill_rect(290, 25, 180, 14);
        j2me_gfx_set_color(0x00FF00);
        int hp_w = 180 * p2_hp / 100;
        j2me_gfx_fill_rect(290 + (180 - hp_w), 25, hp_w, 14);

        j2me_gfx_set_color(0xFFFF00);
        int_str(timer_luta, buf);
        j2me_font_draw(buf, 230, 12);

        j2me_gfx_set_color(0x808080);
        j2me_font_draw("D-Pad: mover  X: soco  Cima: chute", 90, 255);

        j2me_gfx_flip();
    }

    j2me_image_free(s_parado);
    j2me_image_free(s_soco);
    j2me_image_free(s_chute);
    j2me_image_free(s_and1);
    j2me_image_free(s_and2);
    j2me_image_free(fundo);
    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
