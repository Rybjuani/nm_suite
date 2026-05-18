import os

# Configuración de la auditoría
OUTPUT_FILE = "neuromood_completo.txt"
# Carpetas e historias que ignoramos por completo para no inflar el archivo
EXCLUDE_DIRS = {
    '.git', 'venv', '.venv', 'env', '__pycache__', 
    'build', 'dist', '.pytest_cache', '.idea', '.vscode'
}
# Extensiones de texto clave que necesitamos auditar de forma profunda
INCLUDE_EXTENSIONS = {
    '.py', '.spec', '.bat', '.ini', '.json', '.yaml', '.yml', '.txt', '.md'
}
# Archivos específicos que no queremos meter en el dump de código
EXCLUDE_FILES = {OUTPUT_FILE, "unificar.py", "package-lock.json"}

def generar_dump():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"=== Iniciando empaquetado en: {root_dir} ===")
    
    contador_archivos = 0
    
    with open(os.path.join(root_dir, OUTPUT_FILE), 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(root_dir):
            # Filtrar carpetas excluidas en el camino
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                    
                _, ext = os.path.splitext(file)
                if ext.lower() in INCLUDE_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    # Guardamos la ruta relativa para mantener limpia la estructura en la IA
                    rel_path = os.path.relpath(full_path, root_dir)
                    
                    print(f"[+] Procesando: {rel_path}")
                    
                    outfile.write(f"\n\n=========================================\n")
                    outfile.write(f"=== ARCHIVO: {rel_path} ===\n")
                    outfile.write(f"=========================================\n\n")
                    
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as infile:
                            outfile.write(infile.read())
                        contador_archivos += 1
                    except Exception as e:
                        outfile.write(f"// ERROR AL LEER EL ARCHIVO: {str(e)}\n")
                        
    print(f"\n=== ¡Listo! Se procesaron {contador_archivos} archivos. ===")
    print(f"=== Archivo generado: {os.path.join(root_dir, OUTPUT_FILE)} ===")

if __name__ == "__main__":
    generar_dump()