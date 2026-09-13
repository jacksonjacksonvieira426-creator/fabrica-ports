# Fabrica de Ports J2ME -> PSP

Pipeline semiautomatico para portar jogos Java ME para PSP.

## Estrutura
- `tools/analisador.py` — analisa um .jar e lista APIs usadas
- `tools/analisar_lote.py` — analisa uma pasta de .jar
- `mapeamento.json` — tabela de traducao J2ME -> PSP
- `relatorios/` — resultado da analise de cada jogo
- `src/` — codigo C do runtime e dos ports
- `.github/workflows/` — build automatico via GitHub Actions

## Status
- [x] Fase 1: Analisador de bytecode
- [x] Fase 2: Classificador automatico
- [ ] Fase 3: Runtime base (j2me_runtime.c)
- [ ] Fase 4: Pipeline grafico (sceGu)
- [ ] Fase 5: Sistema de telas
- [ ] Fase 6: Traducao do primeiro jogo (funtetris)
- [ ] Fase 7: Build PSP

## Primeiro alvo
`funtetris.jar` — 4 classes, 34 metodos, 36 APIs, sem audio/threads
