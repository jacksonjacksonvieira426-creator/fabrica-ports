#ifndef J2ME_RUNTIME_H
#define J2ME_RUNTIME_H

#include <stdint.h>

// Tempo
int64_t j2me_time_ms(void);

// Random
void    j2me_random_init(void);
int     j2me_random_next(int max);

// Integer
void*   j2me_int_new(int valor);
char*   j2me_int_to_string(int valor);
int     j2me_int_parse(const char* s);

// Utilitarios
void    j2me_noop(void);

// Timer (simulado - para jogos que usam Timer/TimerTask)
typedef void (*j2me_timer_cb)(void*);
void    j2me_timer_init(void);
void    j2me_timer_schedule(int delay_ms, int period_ms, j2me_timer_cb cb, void* arg);
void    j2me_timer_cancel(void);

#endif
