"""Find which private module-level names each target class uses."""
import ast

with open("shared/components_qt.py", encoding="utf-8") as f:
    src = f.read()
tree = ast.parse(src)

private_names = set()
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id.startswith("_"):
                private_names.add(t.id)
    elif isinstance(node, ast.FunctionDef) and node.name.startswith("_"):
        private_names.add(node.name)

targets = [
    "NMPanel", "NMFormRow", "NMSettingsSection", "NMSyncOrb",
    "NMListRow", "NMPageHeader", "NMStepper", "NMHeatBar", "NMWaveChart",
    "NMPlayButton", "NMSearchInput", "NMTextArea", "NMTabs",
]
classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
for cls in sorted(classes, key=lambda c: c.lineno):
    if cls.name not in targets:
        continue
    used = set()
    for node in ast.walk(cls):
        if isinstance(node, ast.Name) and node.id in private_names:
            used.add(node.id)
    label = sorted(used) if used else ["none"]
    print(f"{cls.name}: {label}")
