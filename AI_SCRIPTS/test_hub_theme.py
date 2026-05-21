import traceback
import sys
import os
import time

# Add root to sys.path
sys.path.insert(0, os.getcwd())

from PyQt6.QtWidgets import QApplication
from hub.main_qt import NeuroMoodHub
from shared.components_qt import ThemeManager

app = QApplication(sys.argv)
try:
    print("Initializing NeuroMoodHub...")
    window = NeuroMoodHub()
    print("Hub Init OK")
    
    # Test switching views and themes
    # Views: dashboard, pacientes, config
    for view_id in ["dashboard", "pacientes", "config"]:
        print(f"Testing view '{view_id}'...")
        window._on_nav(view_id)
        
        print(f"Switching theme to light for '{view_id}'...")
        ThemeManager.instance().switch_mode("light")
        app.processEvents()
        time.sleep(0.5)
        
        print(f"Switching theme to dark for '{view_id}'...")
        ThemeManager.instance().switch_mode("dark_hybrid")
        app.processEvents()
        time.sleep(0.5)
        print(f"Theme switch OK for '{view_id}'")

except Exception:
    traceback.print_exc()
finally:
    app.quit()
