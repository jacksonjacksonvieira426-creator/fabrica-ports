// main.c — ponto de entrada do port
// Este arquivo sera reescrito a partir do bytecode do funtetris.jar

#include <pspkernel.h>
#include <pspdebug.h>

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    pspDebugScreenInit();
    pspDebugScreenPrintf("Funtetris PSP\n");
    pspDebugScreenPrintf("Aguardando implementacao...\n");
    sceKernelSleepThread();
    return 0;
}
