#!/bin/bash
cd ~/fabrica-ports/ports
printf "%-12s %6s %8s %8s %8s %8s\n" "JOGO" "APIs" "IMAGES" "THREADS" "FORM" "CANVAS"
printf "%-12s %6s %8s %8s %8s %8s\n" "----" "----" "------" "-------" "----" "------"
for d in */; do
    n="${d%/}"
    r="$n/README.md"
    [ -f "$r" ] || continue
    apis=$(grep -c "^- \`" "$r" 2>/dev/null)
    imgs=$(grep -c "Image\." "$r" 2>/dev/null)
    thrs=$(grep -c "Thread\." "$r" 2>/dev/null)
    form=$(grep -c "Form\." "$r" 2>/dev/null)
    canv=$(grep -c "Canvas\." "$r" 2>/dev/null)
    printf "%-12s %6s %8s %8s %8s %8s\n" "$n" "$apis" "$imgs" "$thrs" "$form" "$canv"
done
