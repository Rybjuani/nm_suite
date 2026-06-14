"""Temporary: find module-level functions/constants in components_qt.py."""
import ast

with open("shared/components_qt.py", encoding="utf-8") as f:
    src = f.read()
tree = ast.parse(src)

print("=== MODULE-LEVEL FUNCTIONS (non-class) ===")
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        print(f"  ln={node.lineno}  {node.name}")

print("\n=== MODULE-LEVEL ASSIGNMENTS (constants/vars) ===")
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                print(f"  ln={node.lineno}  {t.id}")
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        print(f"  ln={node.lineno}  {node.target.id} (annotated)")

print("\n=== PRIVATE HELPERS (used inside classes) ===")
# Find private functions referenced by classes
class_names = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        class_names.add(node.name)

func_names = set()
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        func_names.add(node.name)

# Check which functions are referenced in which classes
classes_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
for cls in classes_nodes:
    for node in ast.walk(cls):
        if isinstance(node, ast.Name) and node.id in func_names:
            print(f"  {cls.name} uses function: {node.id}")
