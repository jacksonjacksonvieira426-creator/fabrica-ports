#include "j2me_rms.h"
#include <pspkernel.h>
#include <pspiofilemgr.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define RMS_DIR       "ms0:/PSP/RMS"
#define MAX_RECORDS   256
#define MAGIC         "RMS1"

typedef struct {
    int            id;
    int            tam;
    unsigned char* dados;
} Registro;

struct RecordStore {
    char      nome[64];
    Registro  registros[MAX_RECORDS];
    int       count;
    int       nextId;
};

// Caminho do arquivo do RecordStore
static void caminho(const char* nome, char* out, int max) {
    snprintf(out, max, RMS_DIR "/%s.rms", nome);
}

// Garante que a pasta existe
static void garantir_pasta(void) {
    sceIoMkdir("ms0:/PSP", 0777);
    sceIoMkdir(RMS_DIR, 0777);
}

// ===== Persistencia =====
static int salvar(RecordStore* rs) {
    garantir_pasta();
    char path[128];
    caminho(rs->nome, path, sizeof(path));

    SceUID fd = sceIoOpen(path, PSP_O_WRONLY | PSP_O_CREAT | PSP_O_TRUNC, 0777);
    if (fd < 0) return 0;

    // Header: MAGIC(4) + nextId(4) + count(4)
    char header[12];
    memcpy(header, MAGIC, 4);
    memcpy(header + 4, &rs->nextId, 4);
    memcpy(header + 8, &rs->count,  4);
    sceIoWrite(fd, header, 12);

    // Cada registro: id(4) + tam(4) + dados(tam)
    for (int i = 0; i < rs->count; i++) {
        Registro* r = &rs->registros[i];
        char rh[8];
        memcpy(rh, &r->id,  4);
        memcpy(rh + 4, &r->tam, 4);
        sceIoWrite(fd, rh, 8);
        if (r->tam > 0 && r->dados) sceIoWrite(fd, r->dados, r->tam);
    }

    sceIoClose(fd);
    return 1;
}

static int carregar(RecordStore* rs) {
    char path[128];
    caminho(rs->nome, path, sizeof(path));

    SceUID fd = sceIoOpen(path, PSP_O_RDONLY, 0);
    if (fd < 0) return 0;

    char header[12];
    if (sceIoRead(fd, header, 12) != 12) { sceIoClose(fd); return 0; }
    if (memcmp(header, MAGIC, 4) != 0)   { sceIoClose(fd); return 0; }

    memcpy(&rs->nextId, header + 4, 4);
    memcpy(&rs->count,  header + 8, 4);
    if (rs->count < 0) rs->count = 0;
    if (rs->count > MAX_RECORDS) rs->count = MAX_RECORDS;

    for (int i = 0; i < rs->count; i++) {
        char rh[8];
        if (sceIoRead(fd, rh, 8) != 8) { rs->count = i; break; }
        Registro* r = &rs->registros[i];
        memcpy(&r->id,  rh,     4);
        memcpy(&r->tam, rh + 4, 4);
        if (r->tam < 0) r->tam = 0;
        r->dados = NULL;
        if (r->tam > 0) {
            r->dados = (unsigned char*)malloc(r->tam);
            if (r->dados) {
                if (sceIoRead(fd, r->dados, r->tam) != r->tam) {
                    free(r->dados);
                    r->dados = NULL;
                    r->tam = 0;
                    rs->count = i;
                    break;
                }
            }
        }
    }

    sceIoClose(fd);
    return 1;
}

// ===== API publica =====
RecordStore* j2me_rms_open(const char* nome, int create) {
    garantir_pasta();
    RecordStore* rs = (RecordStore*)calloc(1, sizeof(RecordStore));
    if (!rs) return NULL;

    strncpy(rs->nome, nome, sizeof(rs->nome) - 1);
    rs->nextId = 1;

    if (!carregar(rs)) {
        if (!create) {
            free(rs);
            return NULL;
        }
        // Nao existia; fica em branco
    }
    return rs;
}

void j2me_rms_close(RecordStore* rs) {
    if (!rs) return;
    salvar(rs);
    for (int i = 0; i < rs->count; i++) {
        if (rs->registros[i].dados) free(rs->registros[i].dados);
    }
    free(rs);
}

void j2me_rms_delete(const char* nome) {
    char path[128];
    caminho(nome, path, sizeof(path));
    sceIoRemove(path);
}

static Registro* achar(RecordStore* rs, int id) {
    for (int i = 0; i < rs->count; i++) {
        if (rs->registros[i].id == id) return &rs->registros[i];
    }
    return NULL;
}

int j2me_rms_add(RecordStore* rs, const unsigned char* dados, int offset, int tam) {
    if (!rs || rs->count >= MAX_RECORDS) return -1;
    if (tam < 0) tam = 0;

    Registro* r = &rs->registros[rs->count];
    r->id = rs->nextId++;
    r->tam = tam;
    r->dados = NULL;
    if (tam > 0) {
        r->dados = (unsigned char*)malloc(tam);
        if (!r->dados) return -1;
        memcpy(r->dados, dados + offset, tam);
    }
    rs->count++;
    salvar(rs);
    return r->id;
}

int j2me_rms_get(RecordStore* rs, int id, unsigned char* saida, int max_tam) {
    Registro* r = achar(rs, id);
    if (!r) return -1;
    int n = (r->tam < max_tam) ? r->tam : max_tam;
    if (r->dados && saida) memcpy(saida, r->dados, n);
    return r->tam;
}

int j2me_rms_get_size(RecordStore* rs, int id) {
    Registro* r = achar(rs, id);
    return r ? r->tam : -1;
}

int j2me_rms_set(RecordStore* rs, int id, const unsigned char* dados, int offset, int tam) {
    Registro* r = achar(rs, id);
    if (!r) return -1;
    if (r->dados) free(r->dados);
    r->dados = NULL;
    r->tam = tam;
    if (tam > 0) {
        r->dados = (unsigned char*)malloc(tam);
        if (!r->dados) { r->tam = 0; return -1; }
        memcpy(r->dados, dados + offset, tam);
    }
    salvar(rs);
    return tam;
}

void j2me_rms_del(RecordStore* rs, int id) {
    for (int i = 0; i < rs->count; i++) {
        if (rs->registros[i].id == id) {
            if (rs->registros[i].dados) free(rs->registros[i].dados);
            for (int j = i; j < rs->count - 1; j++) {
                rs->registros[j] = rs->registros[j + 1];
            }
            rs->count--;
            salvar(rs);
            return;
        }
    }
}

int j2me_rms_count(RecordStore* rs) {
    return rs ? rs->count : 0;
}

int j2me_rms_first_id(RecordStore* rs) {
    if (!rs || rs->count == 0) return -1;
    int menor = rs->registros[0].id;
    for (int i = 1; i < rs->count; i++) {
        if (rs->registros[i].id < menor) menor = rs->registros[i].id;
    }
    return menor;
}

int j2me_rms_next_id(RecordStore* rs, int id) {
    if (!rs) return -1;
    int prox = -1;
    for (int i = 0; i < rs->count; i++) {
        int rid = rs->registros[i].id;
        if (rid > id && (prox == -1 || rid < prox)) prox = rid;
    }
    return prox;
}
