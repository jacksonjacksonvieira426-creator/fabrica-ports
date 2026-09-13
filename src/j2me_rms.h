#ifndef J2ME_RMS_H
#define J2ME_RMS_H

// Record Management System (equivale ao javax.microedition.rms do J2ME)
typedef struct RecordStore RecordStore;

// Abre/cria um RecordStore. Se create=0 e nao existir, retorna NULL.
RecordStore* j2me_rms_open(const char* nome, int create);

// Fecha e salva
void j2me_rms_close(RecordStore* rs);

// Apaga um RecordStore inteiro
void j2me_rms_delete(const char* nome);

// Adiciona um registro. Retorna o ID (>0) ou -1 em erro.
int  j2me_rms_add(RecordStore* rs, const unsigned char* dados, int offset, int tam);

// Le um registro. Retorna o tamanho em bytes ou -1 em erro.
int  j2me_rms_get(RecordStore* rs, int id, unsigned char* saida, int max_tam);

// Tamanho de um registro. Retorna -1 em erro.
int  j2me_rms_get_size(RecordStore* rs, int id);

// Substitui um registro. Retorna o novo tamanho ou -1.
int  j2me_rms_set(RecordStore* rs, int id, const unsigned char* dados, int offset, int tam);

// Apaga um registro
void j2me_rms_del(RecordStore* rs, int id);

// Numero de registros
int  j2me_rms_count(RecordStore* rs);

// Retorna o menor ID ainda em uso (>0) ou -1 se vazio
int  j2me_rms_first_id(RecordStore* rs);

// Retorna o proximo ID em uso a partir de 'id' (>0) ou -1
int  j2me_rms_next_id(RecordStore* rs, int id);

#endif
