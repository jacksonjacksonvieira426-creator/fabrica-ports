#ifndef J2ME_VECTOR_H
#define J2ME_VECTOR_H

typedef struct {
    void** itens;
    int    tamanho;
    int    capacidade;
} J2MEVector;

J2MEVector* j2me_vector_new(void);
void        j2me_vector_free(J2MEVector* v);
void        j2me_vector_add(J2MEVector* v, void* item);
void*       j2me_vector_get(J2MEVector* v, int i);
void*       j2me_vector_remove(J2MEVector* v, int i);
int         j2me_vector_size(J2MEVector* v);
void        j2me_vector_clear(J2MEVector* v);

#endif
