// main.c — ponto de entrada do port
#include <pspkernel.h>
#include <pspdebug.h>
#include "j2me_runtime.h"

PSP_MODULE_INFO("funtetris", 0, 1, 0);
PSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);

int main(void) {
    pspDebugScreenInit();

    j2me_random_init();
    int64_t t = j2me_time_ms();

    pspDebugScreenPrintf("Funtetris PSP\n");
    pspDebugScreenPrintf("Runtime OK\n");
    pspDebugScreenPrintf("Tempo: %lld ms\n", (long long)t);
    pspDebugScreenPrintf("Random: %d\n", j2me_random_next(100));
    pspDebugScreenPrintf("Random: %d\n", j2me_random_next(100));
    pspDebugScreenPrintf("Random: %d\n", j2me_random_next(100));

    sceKernelSleepThread();
    return 0;
}
