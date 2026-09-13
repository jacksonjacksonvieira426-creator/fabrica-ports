#include <pspkernel.h>
#include <pspctrl.h>
#include "j2me_gfx.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    j2me_gfx_init();

    while (1) {
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x101020);

        j2me_gfx_set_color(0xFF0000);
        j2me_gfx_fill_rect(10, 10, 100, 100);

        j2me_gfx_set_color(0x00FF00);
        j2me_gfx_fill_rect(370, 10, 100, 100);

        j2me_gfx_set_color(0x0000FF);
        j2me_gfx_fill_rect(10, 162, 100, 100);

        j2me_gfx_set_color(0xFFFF00);
        j2me_gfx_fill_rect(370, 162, 100, 100);

        j2me_gfx_flip();

        SceCtrlData pad;
        sceCtrlReadBufferPositive(&pad, 1);
        if (pad.Buttons & PSP_CTRL_START) break;
    }

    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
