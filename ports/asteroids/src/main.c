#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"

PSP_MODULE_INFO("asteroids", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// === APIs usadas pelo jogo original (para traduzir) ===
//    19x  java/lang/Math.abs
//    17x  javax/microedition/lcdui/Graphics.setColor
//    16x  javax/microedition/lcdui/Graphics.drawString
//    15x  java/util/Random.nextInt
//    10x  javax/microedition/lcdui/Font.stringWidth
//     8x  javax/microedition/lcdui/Graphics.drawLine
//     7x  javax/microedition/lcdui/Graphics.setFont
//     6x  java/util/Timer.schedule
//     6x  javax/microedition/rms/RecordStore.closeRecordStore
//     4x  javax/microedition/lcdui/Canvas.getHeight
//     4x  java/lang/Object.<init>
//     3x  javax/microedition/lcdui/Canvas.getWidth
//     3x  javax/microedition/lcdui/Graphics.drawArc
//     3x  javax/microedition/lcdui/Command.<init>
//     3x  javax/microedition/lcdui/Displayable.addCommand
//     2x  javax/microedition/lcdui/Graphics.drawChars
//     2x  javax/microedition/lcdui/Font.getHeight
//     2x  java/lang/System.currentTimeMillis
//     2x  javax/microedition/lcdui/Font.getFont
//     2x  javax/microedition/rms/RecordStore.openRecordStore
//     2x  java/io/ByteArrayOutputStream.<init>
//     2x  java/io/DataOutputStream.<init>
//     2x  java/io/DataOutputStream.writeInt
//     2x  java/io/DataOutputStream.writeUTF
//     2x  java/io/DataOutputStream.flush
//     2x  java/io/DataOutputStream.close
//     2x  java/io/ByteArrayOutputStream.toByteArray
//     2x  javax/microedition/lcdui/Displayable.setCommandListener
//     2x  java/util/Random.<init>
//     2x  java/util/Timer.cancel

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
