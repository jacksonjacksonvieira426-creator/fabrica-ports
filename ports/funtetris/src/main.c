#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// === APIs usadas pelo jogo original (para traduzir) ===
//    17x  javax/microedition/lcdui/Graphics.setColor
//     8x  javax/microedition/lcdui/Graphics.drawString
//     7x  javax/microedition/lcdui/Graphics.fillRect
//     5x  java/util/Timer.cancel
//     4x  javax/microedition/lcdui/Displayable.addCommand
//     3x  java/lang/Integer.<init>
//     3x  java/lang/Integer.toString
//     3x  java/util/Timer.<init>
//     3x  java/util/Timer.schedule
//     3x  javax/microedition/lcdui/Graphics.drawImage
//     3x  javax/microedition/lcdui/Command.<init>
//     3x  javax/microedition/lcdui/Display.setCurrent
//     2x  javax/microedition/lcdui/Image.createImage
//     2x  javax/microedition/lcdui/Image.getGraphics
//     2x  java/util/Random.nextInt
//     2x  javax/microedition/lcdui/Graphics.setClip
//     2x  javax/microedition/lcdui/TextField.<init>
//     2x  javax/microedition/lcdui/Form.append
//     2x  javax/microedition/lcdui/Displayable.setCommandListener
//     2x  javax/microedition/lcdui/TextField.getString
//     2x  java/lang/Integer.parseInt
//     1x  java/lang/Object.<init>
//     1x  java/util/TimerTask.<init>
//     1x  javax/microedition/lcdui/Canvas.repaint
//     1x  javax/microedition/lcdui/Canvas.<init>
//     1x  java/lang/System.currentTimeMillis
//     1x  java/util/Random.<init>
//     1x  javax/microedition/lcdui/Canvas.getWidth
//     1x  javax/microedition/lcdui/Canvas.getHeight
//     1x  javax/microedition/lcdui/Font.getFont

int main(void) {
    j2me_gfx_init();
    j2me_input_init();

    while (1) {
        j2me_input_update();
        j2me_gfx_begin_frame();
        j2me_gfx_clear(0x000000);

        // TODO: traduzir logica do jogo aqui

        j2me_gfx_flip();
        if (j2me_input_should_quit()) break;
    }

    j2me_gfx_shutdown();
    sceKernelExitGame();
    return 0;
}
