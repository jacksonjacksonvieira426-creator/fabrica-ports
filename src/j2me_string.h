#ifndef J2ME_STRING_H
#define J2ME_STRING_H

#include "j2me_vector.h"

// Retorna indice da primeira ocorrencia de 'c', ou -1
int  j2me_str_index_of(const char* s, char c);

// Retorna indice da ultima ocorrencia de 'c', ou -1
int  j2me_str_last_index_of(const char* s, char c);

// Split por delimitador. Retorna Vector de strings (alocadas)
J2MEVector* j2me_str_split(const char* s, char delim);

// Substring (aloca nova string)
char* j2me_str_substring(const char* s, int inicio, int fim);

// Trim (remove espacos nas pontas, aloca nova)
char* j2me_str_trim(const char* s);

// Converte inteiro para string (aloca)
char* j2me_str_from_int(int n);

// Compara strings
int  j2me_str_equals(const char* a, const char* b);

#endif
