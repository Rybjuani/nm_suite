"""Temporary analysis script - not for commit."""
import ast

with open("shared/components_qt.py", encoding="utf-8") as f:
    src = f.read()
tree = ast.parse(src)

nodes = sorted([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)], key=lambda n: n.lineno)
classes = {}
for i, n in enumerate(nodes):
    end = nodes[i+1].lineno - 1 if i+1 < len(nodes) else 99999
    bases = [b.id if isinstance(b, ast.Name) else ast.unparse(b) for b in n.bases]
    classes[n.name] = {"start": n.lineno, "end": end, "bases": bases}

class_names = set(classes.keys())
refs = {name: set() for name in class_names}

for n in nodes:
    name = n.name
    for node in ast.walk(n):
        if isinstance(node, ast.Name) and node.id in class_names and node.id != name:
            refs[name].add(node.id)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in class_names and node.value.id != name:
                refs[name].add(node.value.id)

dependents = {name: set() for name in class_names}
for name, deps in refs.items():
    for dep in deps:
        dependents[dep].add(name)

print("=== LEAF CLASSES (nothing in file depends on them) ===")
leaves = [name for name in class_names if not dependents[name]]
for name in sorted(leaves):
    b = classes[name]["bases"]
    r = sorted(refs[name])
    print(f"  {name}  ln={classes[name]['start']}  bases={b}  refs={r}")

print(f"\nTotal leaves: {len(leaves)}")

print("\n=== INTERNAL DEPENDENCIES (used by others) ===")
for name in sorted(class_names):
    if dependents[name]:
        d = sorted(dependents[name])
        b = classes[name]["bases"]
        print(f"  {name}  ln={classes[name]['start']}  bases={b}  <- used by: {d}")
