#include "j2me_input.h"
#include <pspctrl.h>

static SceCtrlData pad_atual;
static SceCtrlData pad_anterior;
static int inicializado = 0;

void j2me_input_init(void) {
    sceCtrlSetSamplingCycle(0);
    sceCtrlSetSamplingMode(PSP_CTRL_MODE_ANALOG);
    sceCtrlReadBufferPositive(&pad_anterior, 1);
    pad_atual = pad_anterior;
    inicializado = 1;
}

void j2me_input_update(void) {
    if (!inicializado) j2me_input_init();
    pad_anterior = pad_atual;
    sceCtrlReadBufferPositive(&pad_atual, 1);
}

int j2me_input_get_actions(void) {
    int acoes = 0;
    unsigned int b = pad_atual.Buttons;
    if (b & PSP_CTRL_UP)    acoes |= J2ME_UP;
    if (b & PSP_CTRL_DOWN)  acoes |= J2ME_DOWN;
    if (b & PSP_CTRL_LEFT)  acoes |= J2ME_LEFT;
    if (b & PSP_CTRL_RIGHT) acoes |= J2ME_RIGHT;
    if (b & (PSP_CTRL_CROSS | PSP_CTRL_CIRCLE)) acoes |= J2ME_FIRE;
    return acoes;
}

char j2me_input_get_key(void) {
    unsigned int b = pad_atual.Buttons;
    if (b & PSP_CTRL_TRIANGLE) return '1';
    if (b & PSP_CTRL_CIRCLE)   return '2';
    if (b & PSP_CTRL_CROSS)    return '5';
    if (b & PSP_CTRL_SQUARE)   return '4';
    if (b & PSP_CTRL_LTRIGGER) return '7';
    if (b & PSP_CTRL_RTRIGGER) return '9';
    if (b & PSP_CTRL_SELECT)   return '0';
    if (b & PSP_CTRL_START)    return '#';
    return 0;
}

int j2me_input_is_pressed(int action) {
    int atual = j2me_input_get_actions();
    unsigned int b = pad_anterior.Buttons;
    int anterior = 0;
    if (b & PSP_CTRL_UP)    anterior |= J2ME_UP;
    if (b & PSP_CTRL_DOWN)  anterior |= J2ME_DOWN;
    if (b & PSP_CTRL_LEFT)  anterior |= J2ME_LEFT;
    if (b & PSP_CTRL_RIGHT) anterior |= J2ME_RIGHT;
    if (b & (PSP_CTRL_CROSS | PSP_CTRL_CIRCLE)) anterior |= J2ME_FIRE;
    return (atual & action) && !(anterior & action);
}

int j2me_input_is_down(int action) {
    return (j2me_input_get_actions() & action) != 0;
}

int j2me_input_should_quit(void) {
    return (pad_atual.Buttons & PSP_CTRL_START) != 0;
}
