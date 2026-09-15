#!/usr/bin/env python3
"""
Extrai cada metodo do bytecode como um arquivo .txt legivel.
Uso: python extrair_metodos.py <jogo.jar> <pasta_saida>
Gera: pasta_saida/<classe>/<metodo>.txt com bytecode limpo
"""
import sys, os, zipfile, io, json
from jawa.cf import ClassFile

def traduzir_instr_basico(instr, cf, classes_internas):
    """Traduz uma instrucao pra texto legivel (nao C, so descritivo)."""
    mn = instr.mnemonic
    ops = instr.operands
    if mn in ("invokevirtual","invokestatic","invokespecial","invokeinterface"):
        if ops:
            try:
                const = cf.constants.get(ops[0].value)
                owner = const.class_.name.value
                nome = const.name_and_type.name.value
                return f"{mn} {owner}.{nome}"
            except: pass
    if mn in ("getfield","putfield","getstatic","putstatic") and ops:
        try:
            const = cf.constants.get(ops[0].value)
            cls = const.class_.name.value.split("/")[-1]
            campo = const.name_and_type.name.value
            return f"{mn} {cls}.{campo}"
        except: pass
    if ops:
        try:
            return f"{mn} {ops[0].value}"
        except: pass
    return mn

def extrair(jar, pasta):
    z = zipfile.ZipFile(jar)
    classes = [n for n in z.namelist() if n.endswith(".class")]
    internas = {n[:-6] for n in classes}
    total = 0
    
    for n in classes:
        nome_cls = n[:-6].split("/")[-1]
        try:
            cf = ClassFile(io.BytesIO(z.read(n)))
        except: continue
        
        pasta_cls = os.path.join(pasta, nome_cls)
        os.makedirs(pasta_cls, exist_ok=True)
        
        for m in list(cf.methods):
            if m.name.value == "<clinit>": continue
            if not m.code: continue
            try:
                instrs = list(m.code.disassemble())
            except: continue
            
            nome_metodo = m.name.value.replace("<init>", "constructor").replace("/", "_")
            # Remove _ inicial (padroniza)
            if nome_metodo.startswith("_"):
                nome_metodo = "f" + nome_metodo[1:]
            descricao = m.descriptor.value
            
            # Monta arquivo com: header + instrucoes legiveis
            linhas = []
            linhas.append(f"// Classe: {nome_cls}")
            linhas.append(f"// Metodo: {m.name.value}")
            linhas.append(f"// Descritor: {descricao}")
            linhas.append(f"// Instrucoes: {len(instrs)}")
            linhas.append("")
            for i, ins in enumerate(instrs):
                linha = traduzir_instr_basico(ins, cf, internas)
                linhas.append(f"[{i:4d}] {linha}")
            
            arq_saida = os.path.join(pasta_cls, f"{nome_metodo}.txt")
            with open(arq_saida, "w") as f:
                f.write("\n".join(linhas))
            total += 1
    
    print(f"Extraidos {total} metodos de {len(classes)} classes")
    print(f"Salvos em: {pasta}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python extrair_metodos.py <jogo.jar> <pasta_saida>")
        sys.exit(1)
    extrair(sys.argv[1], sys.argv[2])
