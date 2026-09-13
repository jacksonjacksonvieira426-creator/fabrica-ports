#!/bin/bash
cd ~/storage/shared/jogos_java/'828 Java Games'
for jogo in MetalSlug Castlevania1 superMario SonicCafe PrinceOfPersia splinterCell2 call_of_duty MightAndMagic; do
    jar=$(ls "${jogo}.jar" 2>/dev/null | head -1)
    [ -z "$jar" ] && jar=$(ls "${jogo}"*.jar 2>/dev/null | head -1)
    if [ -n "$jar" ]; then
        echo "=== $jar ==="
        python ~/fabrica-ports/tools/mapa.py "$jar" 2>&1 | grep "^===" | wc -l
        python ~/fabrica-ports/tools/analisar_lote.py . /tmp/rel_tmp 2>/dev/null | grep "$jar" | head -1
        echo ""
    fi
done
