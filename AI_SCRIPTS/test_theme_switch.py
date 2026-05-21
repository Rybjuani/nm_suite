import traceback
import sys
import os
import time

# Add root to sys.path
sys.path.insert(0, os.getcwd())

from PyQt6.QtWidgets import QApplication
from app.main_qt import NeuroMoodApp
from shared.components_qt import ThemeManager

app = QApplication(sys.argv)
try:
    print("Initializing NeuroMoodApp...")
    window = NeuroMoodApp()
    print("Init OK")
    
    # Test theme switching across modules
    for mid in ["animo", "respiracion", "registro", "rutina", "actividades", "timer", "avisos"]:
        print(f"Testing module '{mid}'...")
        window._open_module(mid)
        
        print(f"Switching to light mode for '{mid}'...")
        ThemeManager.instance().switch_mode("light")
        app.processEvents()
        time.sleep(0.5)
        
        print(f"Switching to dark mode for '{mid}'...")
        ThemeManager.instance().switch_mode("dark_hybrid")
        app.processEvents()
        time.sleep(0.5)
        print(f"{mid} theme switch OK")

except Exception:
    traceback.print_exc()
finally:
    app.quit()
