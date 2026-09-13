#include "j2me_string.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int j2me_str_index_of(const char* s, char c) {
    if (!s) return -1;
    for (int i = 0; s[i]; i++) if (s[i] == c) return i;
    return -1;
}

int j2me_str_last_index_of(const char* s, char c) {
    if (!s) return -1;
    int ultimo = -1;
    for (int i = 0; s[i]; i++) if (s[i] == c) ultimo = i;
    return ultimo;
}

J2MEVector* j2me_str_split(const char* s, char delim) {
    J2MEVector* v = j2me_vector_new();
    if (!s) return v;

    int inicio = 0;
    for (int i = 0; ; i++) {
        if (s[i] == delim || s[i] == 0) {
            int tam = i - inicio;
            char* pedaco = (char*)malloc(tam + 1);
            for (int j = 0; j < tam; j++) pedaco[j] = s[inicio + j];
            pedaco[tam] = 0;
            j2me_vector_add(v, pedaco);
            if (s[i] == 0) break;
            inicio = i + 1;
        }
    }
    return v;
}

char* j2me_str_substring(const char* s, int inicio, int fim) {
    if (!s) return 0;
    int n = strlen(s);
    if (inicio < 0) inicio = 0;
    if (fim > n) fim = n;
    if (fim <= inicio) {
        char* vazio = (char*)malloc(1);
        vazio[0] = 0;
        return vazio;
    }
    int tam = fim - inicio;
    char* r = (char*)malloc(tam + 1);
    for (int i = 0; i < tam; i++) r[i] = s[inicio + i];
    r[tam] = 0;
    return r;
}

char* j2me_str_trim(const char* s) {
    if (!s) return 0;
    int i = 0, j = strlen(s) - 1;
    while (s[i] == ' ' || s[i] == '\t') i++;
    while (j > i && (s[j] == ' ' || s[j] == '\t')) j--;
    return j2me_str_substring(s, i, j + 1);
}

char* j2me_str_from_int(int n) {
    char* buf = (char*)malloc(16);
    snprintf(buf, 16, "%d", n);
    return buf;
}

int j2me_str_equals(const char* a, const char* b) {
    if (!a || !b) return 0;
    return strcmp(a, b) == 0;
}
