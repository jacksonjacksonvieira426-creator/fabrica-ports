#include <pspkernel.h>
#include "j2me_gfx.h"
#include "j2me_font.h"
#include "j2me_input.h"

PSP_MODULE_INFO("snakeii", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

// === APIs usadas pelo jogo original (para traduzir) ===
//    18x  java/lang/StringBuffer.append
//    18x  javax/microedition/lcdui/List.append
//    15x  javax/microedition/lcdui/Graphics.drawImage
//    15x  java/io/DataInputStream.readInt
//    13x  java/io/DataOutputStream.writeInt
//    12x  javax/microedition/lcdui/Graphics.setClip
//    11x  javax/microedition/lcdui/Image.createImage
//    10x  java/io/PrintStream.println
//     9x  java/lang/StringBuffer.<init>
//     9x  java/lang/Throwable.toString
//     9x  java/lang/StringBuffer.toString
//     9x  com/nokia/mid/ui/DirectGraphics.drawPixels
//     7x  java/util/Random.nextInt
//     7x  javax/microedition/lcdui/Image.getHeight
//     6x  java/lang/Math.abs
//     5x  javax/microedition/rms/RecordStore.openRecordStore
//     5x  javax/microedition/rms/RecordStore.closeRecordStore
//     4x  java/lang/Object.getClass
//     4x  java/lang/Class.getResourceAsStream
//     4x  java/io/DataInputStream.<init>
//     4x  java/io/DataInputStream.close
//     4x  javax/microedition/lcdui/Graphics.setColor
//     4x  javax/microedition/rms/RecordStore.deleteRecordStore
//     4x  javax/microedition/lcdui/List.<init>
//     3x  javax/microedition/lcdui/Graphics.fillRect
//     3x  javax/microedition/lcdui/Display.setCurrent
//     3x  javax/microedition/lcdui/Displayable.addCommand
//     3x  java/io/InputStream.read
//     2x  javax/microedition/lcdui/Image.getGraphics
//     2x  java/io/DataInputStream.skipBytes

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
