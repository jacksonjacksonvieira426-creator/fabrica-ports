#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"

PSP_MODULE_INFO("centipede", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// === APIs usadas pelo jogo original (para traduzir) ===
//    45x  javax/microedition/lcdui/Image.createImage
//    32x  java/lang/System.currentTimeMillis
//    19x  javax/microedition/lcdui/Graphics.fillRect
//    17x  java/lang/StringBuffer.append
//    17x  javax/microedition/lcdui/Graphics.setColor
//    14x  javax/microedition/lcdui/Graphics.drawImage
//    12x  java/lang/String.getBytes
//    10x  java/lang/Throwable.printStackTrace
//    10x  javax/microedition/lcdui/Image.getWidth
//    10x  javax/microedition/lcdui/Image.getHeight
//     9x  java/lang/System.gc
//     8x  javax/microedition/lcdui/Display.setCurrent
//     7x  javax/microedition/lcdui/Command.<init>
//     7x  javax/microedition/lcdui/Displayable.addCommand
//     6x  javax/microedition/lcdui/List.append
//     5x  javax/microedition/lcdui/Form.append
//     5x  javax/microedition/lcdui/Displayable.setCommandListener
//     5x  java/lang/Thread.sleep
//     5x  java/lang/StringBuffer.<init>
//     5x  java/lang/StringBuffer.toString
//     5x  javax/microedition/lcdui/Graphics.drawString
//     4x  javax/microedition/lcdui/Form.<init>
//     4x  javax/microedition/rms/RecordStore.openRecordStore
//     4x  javax/microedition/rms/RecordStore.closeRecordStore
//     4x  java/lang/Object.<init>
//     3x  java/lang/String.<init>
//     3x  java/lang/System.arraycopy
//     3x  javax/microedition/lcdui/Canvas.getGameAction
//     2x  java/lang/Runtime.getRuntime
//     2x  javax/microedition/rms/RecordStore.addRecord

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
