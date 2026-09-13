# Ports J2ME -> PSP

Cada pasta contem o main.c de um port especifico.

- funtetris/main.c — Tetris jogavel (traduzido de funtetris.jar)
- cod_psp/main.c — Call of Duty MVP (sprites originais + mapa manual)

## Como compilar

Copie o main.c do port desejado para src/:

    cp ports/funtetris/main.c src/main.c
    git add . && git commit -m "build: funtetris" && git push

A biblioteca compartilhada (j2me_*.c/h) fica em src/ e eh usada por todos os ports.
