#include "j2me_runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#ifdef __PSP__
#include <pspkernel.h>
#endif

// ===== TEMPO =====
int64_t j2me_time_ms(void) {
#ifdef __PSP__
    // PSP: tempo desde o boot em microssegundos
    return (int64_t)(sceKernelGetSystemTimeWide() / 1000);
#else
    // Linux/Termux: clock monotônico
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
#endif
}

// ===== RANDOM =====
static unsigned int rng_state = 0;

void j2me_random_init(void) {
#ifdef __PSP__
    rng_state = (unsigned int)sceKernelGetSystemTimeWide();
#else
    rng_state = (unsigned int)time(NULL);
#endif
}

int j2me_random_next(int max) {
    if (max <= 0) return 0;
    rng_state = rng_state * 1103515245 + 12345;
    return (int)((rng_state >> 16) % (unsigned int)max);
}

// ===== INTEGER =====
void* j2me_int_new(int valor) {
    int* p = (int*)malloc(sizeof(int));
    if (p) *p = valor;
    return p;
}

char* j2me_int_to_string(int valor) {
    char* buf = (char*)malloc(16);
    if (buf) snprintf(buf, 16, "%d", valor);
    return buf;
}

int j2me_int_parse(const char* s) {
    if (!s) return 0;
    return atoi(s);
}

// ===== UTILITARIOS =====
void j2me_noop(void) { }

// ===== TIMER (stub por enquanto) =====
void j2me_timer_init(void) { }

void j2me_timer_schedule(int delay_ms, int period_ms, j2me_timer_cb cb, void* arg) {
    (void)delay_ms; (void)period_ms; (void)cb; (void)arg;
}

void j2me_timer_cancel(void) { }
