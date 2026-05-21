import sys

def replace_in_file(filepath, replacements):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
            else:
                print(f"Target not found: {old[:50]}...")
                
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

replacements = [
    (
        '''        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(qfont("size_small",
                           weight=TYPOGRAPHY["weight_bold"]))''',
        '''        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(label)
        self.setFont(qfont("size_small",
                           weight=TYPOGRAPHY["weight_bold"]))'''
    ),
    (
        '''        self.setFixedHeight(32)
        self.setMinimumWidth(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(qfont("size_small",
                           weight=TYPOGRAPHY["weight_semibold"]))''',
        '''        self.setFixedHeight(36)
        self.setMinimumWidth(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(label)
        self.setFont(qfont("size_small",
                           weight=TYPOGRAPHY["weight_semibold"]))'''
    )
]

replace_in_file("app/modules/avisos_qt.py", replacements)

