import zipfile, os

root = r"C:\Users\nosom\Desktop\Neuromood V3"
dirs = ["shared", "app", "hub", "installers"]
out = os.path.join(root, "neuromood_audit.zip")

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for d in dirs:
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, d)):
            dirnames[:] = [dn for dn in dirnames if dn != "__pycache__"]
            for fn in filenames:
                if fn.endswith((".pyc", ".png", ".ico", ".json")):
                    continue
                fp = os.path.join(dirpath, fn)
                arcname = os.path.relpath(fp, root)
                z.write(fp, arcname)
    z.write(os.path.join(root, "CLAUDE.md"), "CLAUDE.md")

total = os.path.getsize(out)
count = len(zipfile.ZipFile(out).namelist())
print(f"ZIP: {count} archivos, {total} bytes")
for f in sorted(zipfile.ZipFile(out).namelist()):
    print(f"  {f}")
