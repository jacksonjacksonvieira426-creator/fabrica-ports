#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"

PSP_MODULE_INFO("breakout", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// === APIs usadas pelo jogo original (para traduzir) ===
//    40x  javax/microedition/lcdui/Graphics.drawImage
//    33x  java/lang/System.currentTimeMillis
//    31x  javax/microedition/lcdui/Image.createImage
//    26x  javax/microedition/lcdui/Graphics.fillRect
//    16x  javax/microedition/lcdui/Graphics.setColor
//    14x  java/lang/StringBuffer.append
//    12x  javax/microedition/lcdui/Command.<init>
//    12x  java/lang/String.getBytes
//    10x  javax/microedition/lcdui/Image.getWidth
//     9x  javax/microedition/lcdui/Displayable.addCommand
//     9x  javax/microedition/lcdui/Display.setCurrent
//     8x  java/lang/StringBuffer.insert
//     8x  javax/microedition/lcdui/Image.getHeight
//     7x  javax/microedition/lcdui/Form.append
//     7x  java/lang/Throwable.printStackTrace
//     6x  javax/microedition/lcdui/Displayable.setCommandListener
//     6x  java/lang/Thread.sleep
//     6x  javax/microedition/lcdui/List.append
//     5x  javax/microedition/lcdui/Form.<init>
//     5x  java/lang/StringBuffer.<init>
//     5x  java/lang/StringBuffer.toString
//     4x  java/lang/String.<init>
//     4x  javax/microedition/rms/RecordStore.openRecordStore
//     4x  javax/microedition/rms/RecordStore.closeRecordStore
//     3x  java/lang/System.gc
//     3x  javax/microedition/lcdui/Canvas.getWidth
//     3x  javax/microedition/lcdui/Canvas.getHeight
//     3x  javax/microedition/lcdui/Graphics.drawString
//     3x  java/lang/System.arraycopy
//     2x  com/nokia/mid/ui/FullCanvas.<init>

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
