#include "j2me_vector.h"
#include <stdlib.h>

J2MEVector* j2me_vector_new(void) {
    J2MEVector* v = (J2MEVector*)malloc(sizeof(J2MEVector));
    if (!v) return 0;
    v->capacidade = 8;
    v->tamanho = 0;
    v->itens = (void**)malloc(v->capacidade * sizeof(void*));
    return v;
}

void j2me_vector_free(J2MEVector* v) {
    if (!v) return;
    free(v->itens);
    free(v);
}

static void crescer(J2MEVector* v) {
    if (v->tamanho < v->capacidade) return;
    v->capacidade *= 2;
    void** novo = (void**)malloc(v->capacidade * sizeof(void*));
    for (int i = 0; i < v->tamanho; i++) novo[i] = v->itens[i];
    free(v->itens);
    v->itens = novo;
}

void j2me_vector_add(J2MEVector* v, void* item) {
    if (!v) return;
    crescer(v);
    v->itens[v->tamanho++] = item;
}

void* j2me_vector_get(J2MEVector* v, int i) {
    if (!v || i < 0 || i >= v->tamanho) return 0;
    return v->itens[i];
}

void* j2me_vector_remove(J2MEVector* v, int i) {
    if (!v || i < 0 || i >= v->tamanho) return 0;
    void* item = v->itens[i];
    for (int j = i; j < v->tamanho - 1; j++) v->itens[j] = v->itens[j+1];
    v->tamanho--;
    return item;
}

int j2me_vector_size(J2MEVector* v) {
    return v ? v->tamanho : 0;
}

void j2me_vector_clear(J2MEVector* v) {
    if (v) v->tamanho = 0;
}
