#!/bin/bash
# Produção em lote com V12
# Uso: bash batch_v12.sh

BASE=~/fabrica-ports
JOGOS=$BASE/jogos_prod2
PORTS=$BASE/ports
FAB8=$BASE/tools/fabrica_v8
GH_USER="jacksonjacksonvieira426-creator"

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== PRODUCAO EM LOTE V12 ==="
echo ""

cd "$JOGOS"
for jar in *.jar; do
    nome=$(basename "$jar" .jar | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -d '[]')
    echo -e "${YELLOW}=== $nome ===${NC}"

    # 1. Gera projeto V5
    python "$BASE/tools/portador.py" "$jar" > /dev/null 2>&1
    
    if [ ! -d "$PORTS/$nome" ]; then
        echo -e "${RED}  ✗ Portador falhou${NC}"
        continue
    fi
    
    # 2. Gera main.c V12
    cd "$PORTS/$nome"
    if [ -f estrutura.json ]; then
        python "$FAB8/4_injetar/gerador_v12.py" estrutura.json "$jar" > /dev/null 2>&1
        if [ -f ~/main_v12.c ]; then
            cp ~/main_v12.c src/main.c
            
            # 3. Adiciona PSP_MODULE_INFO
            if ! grep -q "PSP_MODULE_INFO" src/main.c; then
                sed -i "s|#include \"j2me_runtime.h\"|#include \"j2me_runtime.h\"\n\nPSP_MODULE_INFO(\"$nome\", 0, 1, 0);\nPSP_MAIN_THREAD_ATTR(THREAD_ATTR_USER);|" src/main.c
            fi
            echo -e "${GREEN}  ✓ main.c V12 gerado${NC}"
        else
            echo -e "${RED}  ✗ V12 falhou${NC}"
            continue
        fi
    fi
    
    # 4. Git init + push
    if [ ! -d .git ]; then
        git init -q
        git config user.name "$GH_USER"
        git config user.email "$GH_USER@users.noreply.github.com"
    fi
    
    git add . 2>/dev/null
    git commit -m "V12 auto" 2>/dev/null
    
    if ! git remote | grep -q origin; then
        gh repo create "${nome}-psp" --public --source=. --remote=origin --push 2>&1 | tail -1
        echo -e "${GREEN}  ✓ repo criado${NC}"
    else
        git push 2>&1 | tail -1
    fi
    cd "$JOGOS"
done

echo ""
echo "=== AGUARDANDO BUILDS (60s) ==="
sleep 60

echo ""
echo "=== RESULTADO FINAL ==="
for jar in *.jar; do
    nome=$(basename "$jar" .jar | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -d '[]')
    cd "$PORTS/$nome" 2>/dev/null || continue
    status=$(gh run list --limit 1 --json status,conclusion -q '.[0] | "\(.status) \(.conclusion // "")"' 2>/dev/null)
    if echo "$status" | grep -q "success"; then
        echo -e "${GREEN}  ✓ $nome${NC}"
    elif echo "$status" | grep -q "failure"; then
        echo -e "${RED}  ✗ $nome${NC}"
    else
        echo -e "${YELLOW}  ? $nome ($status)${NC}"
    fi
    cd "$JOGOS"
done
