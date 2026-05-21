import re
with open('shared/theme_qt.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Define pattern carefully to match across newlines
pattern = re.compile(r'def stylesheet_installer\(modo: str = \"dark_hybrid\"\) -> str:.*?QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical \{ height: 0; \}', re.DOTALL)

replacement = 'def stylesheet_installer(modo: str = "dark_hybrid") -> str:\\n    """Stylesheet premium v3 para ventanas de instalador.\\n\\n    Usa glassmorphism, tipografía Jakarta Sans y componentes v3.\\n    """\\n    c = colors("dark")\\n    rd = V3_RD\\n    sp = V3_SP\\n    \\n    return f"""\\n    QWidget#InstallerShell {\\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, \\n                                    stop:0 #0a0d1a, stop:1 #060912);\\n    }\\n    QLabel {\\n        color: {c["text_primary"]};\\n        font-family: "{TYPOGRAPHY["font_primary"]}";\\n        font-size: {TYPOGRAPHY["size_body"]}pt;\\n    }\\n    QTextEdit {\\n        background: {v3c("surface", "dark").name()};\\n        color: {c["teal"]};\\n        border: 1px solid {v3c("borderSoft", "dark").name()};\\n        border-radius: {rd["lg"]}px;\\n        padding: {sp["lg"]}px;\\n        font-family: "{TYPOGRAPHY["font_mono"]}";\\n        font-size: {TYPOGRAPHY["size_small"]}pt;\\n    }\\n    QProgressBar {\\n        background: {v3c("surfaceSolid", "dark").name()};\\n        border: 1px solid {v3c("borderSoft", "dark").name()};\\n        border-radius: {rd["lg"]}px;\\n        height: 8px;\\n        text-align: center;\\n    }\\n    QProgressBar::chunk {\\n        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, \\n                                    stop:0 {v3c("teal", "dark").name()}, \\n                                    stop:1 {v3c("accent", "dark").name()});\\n        border-radius: {rd["lg"]}px;\\n    }\\n    """'

new_text = pattern.sub(replacement, text)
with open('shared/theme_qt.py', 'w', encoding='utf-8') as f:
    f.write(new_text)
