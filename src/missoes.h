#ifndef MISSOES_H
#define MISSOES_H

typedef struct {
    const char* titulo;
    const char* briefing;
    unsigned int seed;      // seed do mapa procedural
    int         n_inimigos;
    int         dificuldade; // 1-9
} Missao;

static const Missao MISSOES[9] = {
    {
        "MISSAO 1",
        "Desembarque na Normandia. Abra caminho ate a cidade e chegue ao ponto de encontro.",
        0x12345678, 3, 1
    },
    {
        "MISSAO 2",
        "Avance pelas fazendas. Cuidado com emboscadas nas estradas.",
        0x23456789, 4, 2
    },
    {
        "MISSAO 3",
        "Atravesse a ponte. Destrua as defesas antiaereas no caminho.",
        0x34567890, 5, 3
    },
    {
        "MISSAO 4",
        "Infiltrar na vila ocupada. Elimine os franco-atiradores.",
        0x45678901, 6, 4
    },
    {
        "MISSAO 5",
        "Resgate os aliados capturados. Fuja antes do reforco chegar.",
        0x56789012, 7, 5
    },
    {
        "MISSAO 6",
        "Sabotar o deposito de municao. Explosivos no caminho.",
        0x67890123, 8, 6
    },
    {
        "MISSAO 7",
        "Escalar a colina. Tome o posto de observacao inimigo.",
        0x78901234, 9, 7
    },
    {
        "MISSAO 8",
        "Cruzar o rio sob fogo. Chegue ao outro lado da linha inimiga.",
        0x89012345, 10, 8
    },
    {
        "MISSAO 9",
        "Assalto final. Chegue ao comando inimigo e termine a missao.",
        0x90123456, 12, 9
    },
};

#endif
