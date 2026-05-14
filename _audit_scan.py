"""
Audit scanner for NeuroMood QA.
Scans all 27 critical files for bugs.
"""
import os, re, ast
from pathlib import Path

# Files to scan
dirs = ['shared', 'app', 'hub', 'installers']
files = []
for d in dirs:
    for f in Path(d).rglob('*.py'):
        files.append(str(f))
        
# Critical files to analyze first
critical = [
    'shared/components_qt.py',
    'shared/theme_qt.py', 
    'app/home_qt.py',
    'app/main_qt.py',
    'app/modules/animo_qt.py',
    'app/modules/respiracion_qt.py',
    'app/modules/registro_tcc_qt.py',
    'app/modules/rutina_qt.py',
    'app/modules/actividades_qt.py',
    'app/modules/timer_qt.py',
    'app/modules/avisos_qt.py',
    'hub/main_qt.py',
    'hub/pacientes_qt.py',
    'hub/ia_asistente.py',
    'installers/installer.py',
]

print('=' * 60)
print('AUDITORÍA TÉCNICA COMPLETA — NeuroMood Suite')
print('=' * 60)
print()

# Analysis results
results = {
    'critical': [],
    'visual': [],
    'tech_debt': [],
    'risks': [],
    'regression': [],
    'avoid': [],
}

# Scan for specific patterns
for f in critical:
    if not os.path.exists(f):
        continue
    print(f'SCANNING: {f}', flush=True)
    with open(f, 'r', encoding='utf-8') as fd:
        content = fd.read()
        
    # 1. Silent exceptions
    for match in re.finditer(r'except Exception.*?:\s*(?:pass|continue)', content):
        line_no = content[:match.start()].count('\n') + 1
        results['critical'].append(f'{f}:{line_no} - Silent exception swallowed')
        
    # 2. QWidget resources not cleaned
    for match in re.finditer(r'QTimer\(|QPropertyAnimation\(|QSequentialAnimationGroup\(', content):
        line_no = content[:match.start()].count('\n') + 1
        results['critical'].append(f'{f}:{line_no} - Qt resource (timer/animation) - verify cleanup')
        
    # 3. Direct stylesheet (vs paintEvent)
    for match in re.finditer(r'setStyleSheet\(', content):
        if 'background-color' in content[match.start():match.start()+100]:
            line_no = content[:match.start()].count('\n') + 1
            results['visual'].append(f'{f}:{line_no} - Direct stylesheet - consider paintEvent')
            
    # 4. Missing parent cleanup in widgets
    for match in re.finditer(r'def __init__\(self,.*?parent=None\)', content):
        if 'self.destroyed.connect' not in content[match.start():match.end()+500]:
            line_no = content[:match.start()].count('\n') + 1
            results['critical'].append(f'{f}:{line_no} - Widget parent destroy signal not connected')
            
    # 5. ThemeManager signals not disconnected
    for match in re.finditer(r'_tm\(\).theme_changed.connect', content):
        line_no = content[:match.start()].count('\n') + 1
        results['tech_debt'].append(f'{f}:{line_no} - ThemeManager signal - verify disconnect on destroy')
        
    # 6. Imports inconsistent
    for match in re.finditer(r'from shared.components_qt import.*?NM.*?\)', content):
        line_no = content[:match.start()].count('\n') + 1
        results['tech_debt'].append(f'{f}:{line_no} - Component import - verify compatibility')
        
    # 7. Duplicate code
    if 'def _apply_' in content and content.count('_apply_') >= 4:
        results['tech_debt'].append(f'{f} - Multiple _apply_theme functions - potential duplication')
        
    # 8. Missing error handling
    if 'try:' in content and 'except:' in content and 'Exception' not in content:
        results['critical'].append(f'{f} - Bare except found')
        
    # 9. Race conditions (threading)
    if 'threading' in content.lower() or 'qthread' in content.lower():
        results['critical'].append(f'{f} - Threading detected - verify race conditions')
        
    # 10. Memory leaks (QPixmap, QPainter, etc.)
    if 'QPixmap' in content and 'grab()' in content:
        results['critical'].append(f'{f} - QPixmap grab detected - verify cleanup')

print()
print('SCANNING COMPLETE')
print(f'  Critical: {len(results["critical"])}')
print(f'  Visual: {len(results["visual"])}')  
print(f'  Tech debt: {len(results["tech_debt"])}')
print()

# Print all findings
for cat, items in results.items():
    if items:
        print(f'\n--- {cat.upper()} ---')
        for item in items[:20]:  # Limit to 20 per category
            print(f'  {item}')
        if len(items) > 20:
            print(f'  ... and {len(items) - 20} more')