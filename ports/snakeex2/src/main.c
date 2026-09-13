#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"

PSP_MODULE_INFO("snakeex2", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// === APIs usadas pelo jogo original (para traduzir) ===
//    55x  java/io/DataInputStream.readInt
//    53x  java/io/DataOutputStream.writeInt
//    22x  java/util/Random.nextInt
//    20x  java/lang/Math.abs
//    18x  javax/microedition/lcdui/List.append
//    16x  java/lang/StringBuffer.append
//    15x  javax/microedition/lcdui/Graphics.drawImage
//    13x  com/nokia/mid/ui/DirectGraphics.drawPixels
//    11x  javax/microedition/lcdui/Graphics.setClip
//    10x  javax/microedition/lcdui/Displayable.addCommand
//    10x  javax/microedition/lcdui/Image.createImage
//     7x  javax/microedition/lcdui/List.setSelectedIndex
//     7x  javax/microedition/lcdui/Graphics.setColor
//     6x  java/lang/StringBuffer.<init>
//     6x  java/lang/StringBuffer.toString
//     6x  javax/microedition/lcdui/Display.setCurrent
//     6x  javax/microedition/lcdui/Canvas.getKeyCode
//     6x  javax/microedition/lcdui/Canvas.getKeyName
//     6x  javax/microedition/lcdui/Graphics.fillRect
//     5x  java/lang/String.length
//     5x  java/lang/Object.getClass
//     5x  javax/microedition/lcdui/Command.<init>
//     5x  javax/microedition/lcdui/Displayable.removeCommand
//     5x  javax/microedition/lcdui/List.<init>
//     5x  javax/microedition/rms/RecordStore.openRecordStore
//     5x  javax/microedition/rms/RecordStore.closeRecordStore
//     5x  java/io/DataInputStream.read
//     4x  java/lang/String.substring
//     4x  java/lang/Class.getResourceAsStream
//     4x  java/io/DataInputStream.<init>

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
