#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"

PSP_MODULE_INFO("tetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// === APIs usadas pelo jogo original (para traduzir) ===
//    14x  javax/microedition/lcdui/Graphics.setColor
//    10x  javax/microedition/lcdui/Graphics.fillRect
//     7x  java/lang/System.currentTimeMillis
//     7x  javax/microedition/lcdui/Image.createImage
//     7x  javax/microedition/lcdui/Image.getGraphics
//     7x  javax/microedition/lcdui/Graphics.drawImage
//     6x  java/lang/Math.abs
//     4x  javax/microedition/lcdui/Canvas.repaint
//     3x  java/util/Random.nextInt
//     3x  javax/microedition/lcdui/Graphics.drawString
//     3x  javax/microedition/lcdui/Graphics.drawRect
//     2x  java/lang/Thread.start
//     2x  java/lang/Thread.<init>
//     2x  java/lang/Thread.sleep
//     2x  javax/microedition/lcdui/Form.append
//     2x  javax/microedition/lcdui/TextField.getString
//     2x  javax/microedition/lcdui/StringItem.setText
//     2x  javax/microedition/lcdui/Canvas.getGameAction
//     1x  javax/microedition/midlet/MIDlet.<init>
//     1x  javax/microedition/lcdui/Display.getDisplay
//     1x  javax/microedition/lcdui/Display.setCurrent
//     1x  java/lang/Object.<init>
//     1x  java/util/Random.<init>
//     1x  javax/microedition/lcdui/Graphics.drawLine
//     1x  javax/microedition/lcdui/Form.<init>
//     1x  javax/microedition/lcdui/Displayable.setCommandListener
//     1x  javax/microedition/lcdui/TextField.<init>
//     1x  javax/microedition/lcdui/StringItem.<init>
//     1x  javax/microedition/lcdui/Command.<init>
//     1x  javax/microedition/lcdui/Displayable.addCommand

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
