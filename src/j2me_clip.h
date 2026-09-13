#ifndef J2ME_CLIP_H
#define J2ME_CLIP_H

#include "j2me_image.h"

void j2me_clip_push(int x, int y, int w, int h);
void j2me_clip_pop(void);
void j2me_clip_reset(void);
void j2me_clip_get(int* x, int* y, int* w, int* h);

// Desenha uma regiao (sprite) de uma imagem
void j2me_image_draw_region(J2MEImage* src,
                            int sx, int sy, int sw, int sh,
                            int transform,
                            int dx, int dy, int anchor);

// Transformacoes (igual J2ME)
#define TRANS_NONE    0
#define TRANS_MIRROR  2
#define TRANS_ROT90   5
#define TRANS_ROT180  3
#define TRANS_ROT270  6

// Anchors (igual J2ME)
#define HCENTER  1
#define VCENTER  2
#define LEFT     4
#define RIGHT    8
#define TOP      16
#define BOTTOM   32

#endif
