import zipfile, io, sys
from jawa.cf import ClassFile

jar = sys.argv[1] if len(sys.argv) > 1 else "../jogos_teste/Snake.jar"

z = zipfile.ZipFile(jar)
classes = [n for n in z.namelist() if n.endswith(".class")]
print(f"Classes encontradas: {len(classes)}")

if classes:
    nome = classes[0]
    print(f"\n--- Analisando: {nome} ---")
    dados = z.read(nome)
    cf = ClassFile(io.BytesIO(dados))
    methods = list(cf.methods)
    print(f"Methods: {len(methods)}")
    for m in methods[:3]:
        print(f"\n  Metodo: {m.name.value} {m.descriptor.value}")
        if m.code:
            instrs = list(m.code.disassemble())
            print(f"  Instrucoes: {len(instrs)}")
            for i in instrs:
                if i.mnemonic in ("invokevirtual","invokestatic","invokespecial","invokeinterface"):
                    print(f"    {i.mnemonic} | operands: {i.operands}")
                    if i.operands:
                        idx = i.operands[0].value
                        print(f"      -> indice na pool: {idx}")
                        const = cf.constants.get(idx)
                        print(f"      -> constante: {const}")
                        if const and hasattr(const, 'class_') and hasattr(const, 'name_and_type'):
                            print(f"      -> classe: {const.class_.name.value}")
                            print(f"      -> metodo: {const.name_and_type.name.value}")
        else:
            print(f"  (sem code)")
