"""
ui_crawler.py — PyQt6 UI introspection engine.
Walks widget trees, exports to JSON, detects interactive elements.
Autonomous: discovers QApplication, MainWindow, launchers, dialogs.
Usage: python ui_crawler.py [--app app.main_qt] [--hub hub.main_qt]
"""
import sys, os, json, gc
from pathlib import Path

_proj = str(Path(__file__).resolve().parent)
if _proj not in sys.path:
    sys.path.insert(0, _proj)

OUT_DIR = os.path.join(_proj, "_test_screens", "crawl")
os.makedirs(OUT_DIR, exist_ok=True)

# Known entrypoints
ENTRYPOINTS = {
    "patient": ("app.main_qt", "NeuroMoodApp"),
    "hub": ("hub.main_qt", "NeuroMoodHub"),
}


def _safe_text(widget) -> str:
    """Get text from any widget type safely."""
    for attr in ("text", "windowTitle", "title", "placeholderText", "toolTip"):
        try:
            val = getattr(widget, attr, None)
            if callable(val):
                val = val()
            if isinstance(val, str) and val.strip():
                return val.strip()[:120]
        except (RuntimeError, AttributeError):
            continue
    return ""


def _safe_geom(widget) -> dict:
    """Get widget geometry safely."""
    try:
        g = widget.geometry()
        return {"x": g.x(), "y": g.y(), "w": g.width(), "h": g.height()}
    except (RuntimeError, AttributeError):
        return {"x": 0, "y": 0, "w": 0, "h": 0}


def _safe_visible(widget) -> bool:
    """Check if widget is visible."""
    try:
        return bool(widget.isVisible())
    except (RuntimeError, AttributeError):
        return False


def _safe_children(widget) -> list:
    """Get children safely."""
    try:
        return widget.findChildren(type(widget).__bases__[0] if widget.__class__.__bases__ else type(widget))
    except (RuntimeError, AttributeError):
        return []


def crawl_widget(widget, depth: int = 0, max_depth: int = 8) -> dict:
    """Recursively crawl a QWidget tree."""
    if depth > max_depth or widget is None:
        return {}

    node = {
        "class": widget.__class__.__name__,
        "objectName": widget.objectName() or "",
        "text": _safe_text(widget),
        "geometry": _safe_geom(widget),
        "visible": _safe_visible(widget),
        "enabled": widget.isEnabled() if hasattr(widget, "isEnabled") else True,
        "depth": depth,
        "children": [],
    }

    # Gather child widgets
    for attr_name in ("children", "widgets"):
        try:
            getter = getattr(widget, attr_name, None)
        except Exception:
            continue
        if callable(getter):
            try:
                kids = getter()
                for child in kids:
                    cn = crawl_widget(child, depth + 1, max_depth)
                    if cn:
                        node["children"].append(cn)
                if node["children"]:
                    break
            except Exception:
                continue

    # If no children found via method, try findChildren
    if not node["children"] and hasattr(widget, "findChildren"):
        try:
            for child in widget.findChildren(type(widget.__class__)):
                if child is widget:
                    continue
                cn = crawl_widget(child, depth + 1, max_depth)
                if cn:
                    node["children"].append(cn)
        except Exception:
            pass

    return node


def crawl_app(app_name: str = "patient") -> dict:
    """Launch an app and crawl its widget tree."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer

    if app_name not in ENTRYPOINTS:
        return {"error": f"Unknown app: {app_name}. Known: {list(ENTRYPOINTS.keys())}"}

    mod_path, cls_name = ENTRYPOINTS[app_name]
    app = QApplication.instance() or QApplication(sys.argv)

    import importlib
    module = importlib.import_module(mod_path)
    WindowClass = getattr(module, cls_name)
    window = WindowClass()
    window.show()

    # Process events to populate widget tree
    for _ in range(5):
        QApplication.processEvents()

    # Crawl
    tree = crawl_widget(window)

    # Also crawl top-level widgets
    toplevels = []
    for w in QApplication.topLevelWidgets():
        if w is not window and _safe_visible(w):
            toplevels.append(crawl_widget(w, max_depth=4))

    result = {
        "app": app_name,
        "window_class": cls_name,
        "window_title": window.windowTitle(),
        "window_geometry": _safe_geom(window),
        "widget_tree": tree,
        "toplevel_widgets": toplevels,
    }

    # Save to JSON
    path = os.path.join(OUT_DIR, f"{app_name}_tree.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Saved: {path}", flush=True)

    # Find interactive widgets
    interactive = extract_interactive(window)
    inter_path = os.path.join(OUT_DIR, f"{app_name}_interactive.json")
    with open(inter_path, "w", encoding="utf-8") as f:
        json.dump(interactive, f, indent=2, ensure_ascii=False, default=str)
    print(f"  Interactive: {len(interactive)} widgets -> {inter_path}", flush=True)

    QTimer.singleShot(500, app.quit)
    app.exec()
    return result


def extract_interactive(widget, depth: int = 0, max_depth: int = 6) -> list:
    """Find all interactive widgets (buttons, tabs, inputs, toggles)."""
    from PyQt6.QtWidgets import QPushButton, QAbstractButton, QLineEdit, QTextEdit
    from PyQt6.QtWidgets import QComboBox, QSlider, QCheckBox, QTabBar, QSpinBox
    from PyQt6.QtWidgets import QWidget

    TARGETS = ("QPushButton", "QAbstractButton", "QCheckBox",
                "QComboBox", "QSlider", "QTabBar",
                "QLineEdit", "QTextEdit", "QSpinBox")

    results = []

    def _walk(w, d):
        if d > max_depth or w is None:
            return
        cls = w.__class__.__name__
        if cls in TARGETS or "Button" in cls or "Toggle" in cls or "Input" in cls:
            if _safe_visible(w):
                results.append({
                    "class": cls,
                    "objectName": w.objectName() or "",
                    "text": _safe_text(w),
                    "geometry": _safe_geom(w),
                    "depth": d,
                })
        try:
            for child in w.findChildren(QWidget):
                if child is w:
                    continue
                _walk(child, d + 1)
        except Exception:
            pass

    _walk(widget, 0)
    return results


def crawl_all() -> dict:
    """Crawl all known apps."""
    results = {}
    for name in ENTRYPOINTS:
        try:
            results[name] = crawl_app(name)
        except Exception as e:
            results[name] = {"error": str(e)}
    return results


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="PyQt6 UI Crawler")
    p.add_argument("--app", default="patient", help="App to crawl (patient/hub/all)")
    p.add_argument("--max-depth", type=int, default=6, help="Max crawl depth")
    args = p.parse_args()

    if args.app == "all":
        result = crawl_all()
        print(f"\nCrawled {len(result)} apps: {list(result.keys())}")
    else:
        crawl_app(args.app)
