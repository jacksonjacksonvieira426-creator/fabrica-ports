import sys, zipfile, io
from jawa.cf import ClassFile

jar = sys.argv[1]
z = zipfile.ZipFile(jar)
for n in sorted(z.namelist()):
    if not n.endswith(".class"): continue
    try:
        cf = ClassFile(io.BytesIO(z.read(n)))
    except: continue
    nome = n[:-6].split("/")[-1]
    print(f"\n=== {nome} ===")
    # Superclasse
    try:
        super_name = cf.super_class.name.value.split("/")[-1]
        print(f"  extends {super_name}")
    except: pass
    # Campos
    campos = [(c.name.value, c.descriptor.value) for c in list(cf.fields)]
    if campos:
        print("  CAMPOS:")
        for nome_c, desc in campos:
            print(f"    {nome_c} {desc}")
    # Métodos
    print("  METODOS:")
    for m in list(cf.methods):
        print(f"    {m.name.value} {m.descriptor.value}")
