#include <pspkernel.h>
#include <string.h>
#include <stdlib.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"
#include "j2me_image.h"
#include "j2me_clip.h"
#include "j2me_runtime.h"
#include "msf_ryu_parado.h"
#include "msf_ryu_soco.h"
#include "msf_ryu_chute.h"
#include "msf_lee_parado.h"
#include "msf_lee_soco.h"
#include "msf_lee_chute.h"
#include "msf_back.h"
#include "msf_intro.h"

PSP_MODULE_INFO("msf_psp", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

#define SCR_W 480
#define SCR_H 272
#define CHAO_Y 220
#define P1_INI_X 150
#define P2_INI_X 330

#define ST_PARADO  0
#define ST_SOCO    1
#define ST_CHUTE   2

#define J_INTRO   0
#define J_LUTA    1
#define J_VITORIA 2
#define J_DERROTA 3

static J2MEImage* img_from(const unsigned int* src, int w, int h) {
    J2MEImage* img = j2me_image_create(w, h);
    memcpy(img->pixels, src, w * h * sizeof(unsigned int));
    return img;
}

static J2MEImage *ryu_parado, *ryu_soco, *ryu_chute;
static J2MEImage *lee_parado, *lee_soco, *lee_chute;

static void desenha_personagem(J2MEImage* img, int x, int y, int flip, int escala) {
    if (!img) return;
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

static int p1_x = P1_INI_X, p1_hp = 100, p1_estado = ST_PARADO, p1_frame_time = 0, p1_face = 1;
static int p2_x = P2_INI_X, p2_hp = 100, p2_estado = ST_PARADO, p2_frame_time = 0, p2_face = -1;
static int estado = J_INTRO;
static int tempo_estado = 0;
static int timer_luta = 99, timer_tick = 0, cooldown_hit = 0;

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

static J2MEImage* ryu_sprite(int e) {
    if (e == ST_SOCO) return ryu_soco;
    if (e == ST_CHUTE) return ryu_chute;
    return ryu_parado;
}
static J2MEImage* lee_sprite(int e) {
    if (e == ST_SOCO) return lee_soco;
    if (e == ST_CHUTE) return lee_chute;
    return lee_parado;
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

    ryu_parado = img_from(msf_ryu_parado_pixels, MSF_RYU_PARADO_W, MSF_RYU_PARADO_H);
    ryu_soco   = img_from(msf_ryu_soco_pixels,   MSF_RYU_SOCO_W,   MSF_RYU_SOCO_H);
    ryu_chute  = img_from(msf_ryu_chute_pixels,  MSF_RYU_CHUTE_W,  MSF_RYU_CHUTE_H);
    lee_parado = img_from(msf_lee_parado_pixels, MSF_LEE_PARADO_W, MSF_LEE_PARADO_H);
    lee_soco   = img_from(msf_lee_soco_pixels,   MSF_LEE_SOCO_W,   MSF_LEE_SOCO_H);
    lee_chute  = img_from(msf_lee_chute_pixels,  MSF_LEE_CHUTE_W,  MSF_LEE_CHUTE_H);
    J2MEImage* fundo = img_from(msf_back_pixels, MSF_BACK_W, MSF_BACK_H);
    J2MEImage* menu  = img_from(msf_intro_pixels, MSF_INTRO_W, MSF_INTRO_H);

    estado = J_INTRO;

    while (1) {
        j2me_input_update();
        if (j2me_input_should_quit()) break;
        tempo_estado++;

        // INTRO
        if (estado == J_INTRO) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x101020);
            // Menu 60x330: desenha no centro, começa em y=0
            j2me_image_blit(menu, 210, 20);
            j2me_gfx_set_color(0x00FF00);
            if ((tempo_estado / 20) % 2 == 0)
                j2me_font_draw("X - LUTAR!", 200, 250);
            j2me_gfx_set_color(0x808080);
            j2me_font_draw("D-Pad mover | X soco | Cima chute | START sair", 30, 265);
            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        if (estado == J_VITORIA) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x001800);
            j2me_gfx_set_color(0x00FF00);
            j2me_font_draw("VITORIA!", 190, 100);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("X - lutar de novo", 150, 160);
            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        if (estado == J_DERROTA) {
            j2me_gfx_begin_frame();
            j2me_gfx_clear(0x180000);
            j2me_gfx_set_color(0xFF0000);
            j2me_font_draw("DERROTA...", 190, 100);
            j2me_gfx_set_color(0xFFFFFF);
            j2me_font_draw("X - tentar de novo", 150, 160);
            j2me_gfx_flip();
            if (j2me_input_is_pressed(J2ME_FIRE)) reset_luta();
            continue;
        }

        // LUTA
        int acoes = j2me_input_get_actions();

        if (p1_estado == ST_PARADO) {
            if (acoes & J2ME_LEFT)       { p1_x -= 3; p1_face = -1; }
            else if (acoes & J2ME_RIGHT) { p1_x += 3; p1_face = 1; }
            if (p1_x < 20) p1_x = 20;
            if (p1_x > 280) p1_x = 280;
            if (j2me_input_is_pressed(J2ME_FIRE)) { p1_estado = ST_SOCO; p1_frame_time = 0; }
            else if (j2me_input_is_pressed(J2ME_UP)) { p1_estado = ST_CHUTE; p1_frame_time = 0; }
        } else {
            p1_frame_time++;
            if (p1_frame_time > 20) { p1_estado = ST_PARADO; p1_frame_time = 0; }
        }

        if (p2_estado == ST_PARADO) {
            int dist = p1_x - p2_x;
            p2_face = (dist > 0) ? 1 : -1;
            if (abs(dist) > 70) {
                p2_x += (dist > 0) ? 2 : -2;
            } else {
                int r = j2me_random_next(100);
                if (r < 5)      { p2_estado = ST_SOCO;  p2_frame_time = 0; }
                else if (r < 8) { p2_estado = ST_CHUTE; p2_frame_time = 0; }
            }
            if (p2_x < 180) p2_x = 180;
            if (p2_x > 440) p2_x = 440;
        } else {
            p2_frame_time++;
            if (p2_frame_time > 25) { p2_estado = ST_PARADO; p2_frame_time = 0; }
        }

        if (cooldown_hit > 0) cooldown_hit--;
        if (cooldown_hit == 0) {
            if (colidiu(p1_x, p1_face, p1_estado, p2_x)) { p2_hp -= dano_de(p1_estado); cooldown_hit = 30; }
            if (colidiu(p2_x, p2_face, p2_estado, p1_x)) { p1_hp -= dano_de(p2_estado); cooldown_hit = 30; }
        }

        timer_tick++;
        if (timer_tick >= 60) {
            timer_tick = 0;
            timer_luta--;
            if (timer_luta <= 0) { estado = (p1_hp >= p2_hp) ? J_VITORIA : J_DERROTA; continue; }
        }
        if (p1_hp <= 0) { estado = J_DERROTA; continue; }
        if (p2_hp <= 0) { estado = J_VITORIA; continue; }

        // ===== DESENHO =====
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x000000);

        // Fundo: ceu solido + 1 copia do back.png no topo
        // Cor do ceu (roxo escuro combinando com chao)
        j2me_gfx_set_color(0x2A1848);
        j2me_gfx_fill_rect(0, 0, SCR_W, CHAO_Y);
        // back.png (120x80) desenhado 2x: um na esquerda, um na direita
        j2me_image_blit(fundo, 0, 0);
        j2me_image_blit(fundo, 360, 0);
        // Gradiente simples entre os dois (preenche o meio)
        j2me_gfx_set_color(0x1A1038);
        j2me_gfx_fill_rect(120, 0, 240, 80);
        // Chão
        j2me_gfx_set_color(0x604020);
        j2me_gfx_fill_rect(0, CHAO_Y, SCR_W, SCR_H - CHAO_Y);
        j2me_gfx_set_color(0x301808);
        j2me_gfx_fill_rect(0, CHAO_Y, SCR_W, 2);

        // Ryu
        desenha_personagem(ryu_sprite(p1_estado), p1_x, CHAO_Y, p1_face < 0, 3);
        // Lee
        desenha_personagem(lee_sprite(p2_estado), p2_x, CHAO_Y, p2_face > 0, 3);

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
        j2me_font_draw("D-Pad mover | X soco | Cima chute", 90, 265);

        j2me_gfx_flip();
    }

    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
