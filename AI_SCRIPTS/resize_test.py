"""
resize_test.py -- Automated responsive UI testing with layout problem detection.
Tests at multiple resolutions, detects clipping, overlaps, truncated text,
missing scrollbars, and other layout issues.
Uses REAL Windows rendering.
Usage: python resize_test.py [--app patient] [--resolutions 800x600,1920x1080]
"""
import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

_proj = str(Path(__file__).resolve().parent)
if _proj not in sys.path:
    sys.path.insert(0, _proj)

from PyQt6.QtCore import Qt, QTimer, QPointF, QEvent, QRect, QRectF, QSize
from PyQt6.QtGui import QEnterEvent, QMouseEvent, QPixmap, QPainter, QPen, QColor, QFontMetrics
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QScrollArea, QStackedWidget,
    QTabWidget, QMainWindow, QTextEdit, QLineEdit, QFrame, QComboBox,
)

OUT_DIR = os.path.join(_proj, "_test_screens", "resize")
os.makedirs(OUT_DIR, exist_ok=True)

DEFAULT_RESOLUTIONS = [
    (800,  600),
    (1024, 720),
    (1280, 720),
    (1366, 768),
    (1920, 1080),
]

REPORT = {
    "timestamp": datetime.now().isoformat(),
    "total_issues": 0,
    "resolutions": [],
}


class LayoutIssue:
    CLIPPING = "clipping"
    OVERLAP = "overlap"
    TRUNCATED = "truncated"
    OVERFLOW = "overflow"
    MISSING_SCROLLBAR = "missing_scrollbar"
    OFFSCREEN = "offscreen"


def _detect_clipping(widget, parent_rect: QRect, is_root: bool = False) -> list:
    """Detect if widget extends beyond parent boundaries."""
    if is_root:
        return []  # Root window position is intentionally off-origin (centered)
    issues = []
    try:
        wg = widget.geometry()
        wg_global = QRect(widget.mapTo(widget.window(), wg.topLeft()), wg.size())

        # Check if partially outside parent
        parent_global = parent_rect
        if not parent_global.contains(wg_global, proper=True):
            overlap = parent_global.intersected(wg_global)
            if overlap.isValid():
                clip_pct = (1.0 - (overlap.width() * overlap.height()) /
                           max(wg_global.width() * wg_global.height(), 1)) * 100
                if clip_pct > 5:
                    issues.append({
                        "type": LayoutIssue.CLIPPING,
                        "widget": widget.objectName() or widget.__class__.__name__,
                        "text": _safe_text(widget),
                        "clip_pct": round(clip_pct, 1),
                        "widget_geom": [wg_global.x(), wg_global.y(),
                                       wg_global.width(), wg_global.height()],
                        "parent_geom": [parent_global.x(), parent_global.y(),
                                       parent_global.width(), parent_global.height()],
                    })
    except Exception:
        pass
    return issues


def _detect_overlap(widget, siblings: list) -> list:
    """Detect if widget overlaps with sibling widgets unexpectedly."""
    issues = []
    try:
        wr = QRect(widget.mapTo(widget.window(), widget.rect().topLeft()),
                   widget.size())
        if not wr.isValid() or wr.width() < 10 or wr.height() < 10:
            return issues

        for sib in siblings:
            if sib is widget:
                continue
            try:
                sr = QRect(sib.mapTo(sib.window(), sib.rect().topLeft()),
                           sib.size())
                if not sr.isValid():
                    continue

                intersection = wr.intersected(sr)
                if intersection.isValid():
                    overlap_area = intersection.width() * intersection.height()
                    w_area = wr.width() * wr.height()
                    if w_area > 0 and overlap_area / w_area > 0.1:
                        issues.append({
                            "type": LayoutIssue.OVERLAP,
                            "widget": widget.objectName() or widget.__class__.__name__,
                            "overlapping": sib.objectName() or sib.__class__.__name__,
                            "overlap_pct": round(overlap_area / w_area * 100, 1),
                        })
            except Exception:
                continue
    except Exception:
        pass
    return issues


def _detect_truncated_text(widget) -> list:
    """Detect if QLabel text is truncated (ellipsis or cutoff)."""
    issues = []
    try:
        if not isinstance(widget, QLabel):
            return issues

        text = widget.text()
        if not text or len(text) < 3:
            return issues

        fm = QFontMetrics(widget.font())
        available_w = widget.width() - widget.contentsMargins().left() - widget.contentsMargins().right() - 4
        text_w = fm.horizontalAdvance(text)

        if text_w > available_w and widget.wordWrap() is False:
            # Text is truncated because wordWrap is off
            issues.append({
                "type": LayoutIssue.TRUNCATED,
                "widget": widget.objectName() or "QLabel",
                "text": text[:80],
                "text_width": text_w,
                "available_width": available_w,
                "truncated_by": text_w - available_w,
            })
        elif text_w > available_w * widget.height() / fm.height() * 0.8 and widget.wordWrap():
            # Even with wordWrap, text might overflow the height
            pass
    except Exception:
        pass
    return issues


def _detect_missing_scrollbar(widget) -> list:
    """Detect if QScrollArea needs scrollbars but doesn't show them."""
    issues = []
    try:
        if not isinstance(widget, QScrollArea):
            return issues

        content = widget.widget()
        if not content:
            return issues

        viewport = widget.viewport()
        if not viewport:
            return issues

        content_h = content.sizeHint().height()
        viewport_h = viewport.height()

        if content_h > viewport_h + 10:
            vsb = widget.verticalScrollBar()
            if vsb and not vsb.isVisible():
                issues.append({
                    "type": LayoutIssue.MISSING_SCROLLBAR,
                    "widget": widget.objectName() or "QScrollArea",
                    "content_height": content_h,
                    "viewport_height": viewport_h,
                    "overflow": content_h - viewport_h,
                })
    except Exception:
        pass
    return issues


def _detect_offscreen(widget, screen_rect: QRect) -> list:
    """Detect if widget is completely off screen."""
    issues = []
    try:
        wg = widget.geometry()
        top_left = widget.mapToGlobal(wg.topLeft())
        wr = QRect(top_left, wg.size())

        if not screen_rect.intersects(wr):
            issues.append({
                "type": LayoutIssue.OFFSCREEN,
                "widget": widget.objectName() or widget.__class__.__name__,
                "position": [top_left.x(), top_left.y()],
            })
    except Exception:
        pass
    return issues


def _safe_text(widget) -> str:
    for attr in ("text", "windowTitle"):
        try:
            val = getattr(widget, attr, None)
            if callable(val):
                val = val()
            if isinstance(val, str):
                return val.strip()[:100]
        except Exception:
            continue
    return ""


def _audit_widget(widget, parent_rect: QRect, screen_rect: QRect, depth: int = 0,
                  max_depth: int = 5, is_root: bool = False) -> list:
    """Recursively audit a widget tree for layout issues."""
    if depth > max_depth or widget is None:
        return []

    issues = []

    try:
        # Get widget geometry in window coordinates
        w_geom = widget.geometry()
        w_global_rect = QRect(widget.mapTo(widget.window(), w_geom.topLeft()), w_geom.size())
    except Exception:
        w_global_rect = QRect()

    # Run detectors
    issues.extend(_detect_clipping(widget, parent_rect, is_root))
    issues.extend(_detect_truncated_text(widget))
    issues.extend(_detect_missing_scrollbar(widget))
    issues.extend(_detect_offscreen(widget, screen_rect))

    # Get siblings for overlap detection
    try:
        parent = widget.parentWidget()
        if parent:
            siblings = parent.findChildren(type(widget.__class__), options=0)
            issues.extend(_detect_overlap(widget, siblings[:20]))
    except Exception:
        pass

    # Recurse children
    try:
        for child in widget.findChildren(type(widget.__class__), options=0):
            if child is widget:
                continue
            try:
                cg = child.geometry()
                cr = QRect(child.mapTo(child.window(), cg.topLeft()), cg.size())
            except Exception:
                cr = w_global_rect
            issues.extend(_audit_widget(child, cr, screen_rect, depth + 1, max_depth))
    except Exception:
        pass

    return issues


def _annotate_screenshot(app, issues: list, path: str):
    """Draw issue markers on a screenshot copy."""
    pix = app.grab()
    if pix.isNull():
        return

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    for issue in issues:
        if "widget_geom" in issue:
            g = issue["widget_geom"]
            r = QRect(g[0], g[1], g[2], g[3])
            if issue["type"] == LayoutIssue.CLIPPING:
                painter.setPen(QPen(QColor(255, 80, 80, 180), 2, Qt.PenStyle.DashLine))
            elif issue["type"] == LayoutIssue.TRUNCATED:
                painter.setPen(QPen(QColor(255, 200, 50, 180), 2, Qt.PenStyle.DashLine))
            else:
                painter.setPen(QPen(QColor(80, 200, 255, 180), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(r)
            from PyQt6.QtCore import QPointF as _QPF
            painter.drawText(_QPF(r.topLeft()) + _QPF(2.0, -4.0),
                           issue["type"][:3].upper())

    painter.end()
    annotated_path = path.replace(".png", "_annotated.png")
    pix.save(annotated_path)


def run_resize_test(app_name: str = "patient", resolutions: list = None) -> dict:
    """Run resize test at multiple resolutions."""
    if resolutions is None:
        resolutions = DEFAULT_RESOLUTIONS

    print("=" * 60, flush=True)
    print(f"Resize Test -- {app_name}", flush=True)
    print(f"Resolutions: {len(resolutions)}", flush=True)
    print("=" * 60, flush=True)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood_ResizeTest")

    if app_name == "patient":
        from app.main_qt import NeuroMoodApp
        window = NeuroMoodApp()
    elif app_name == "hub":
        from hub.main_qt import NeuroMoodHub
        window = NeuroMoodHub()
    else:
        print(f"Unknown app: {app_name}", flush=True)
        return REPORT

    window.show()
    QApplication.processEvents()
    QApplication.processEvents()

    for w, h in resolutions:
        print(f"\n  Resolution: {w}x{h}", flush=True)
        window.resize(QSize(w, h))
        QApplication.processEvents()
        QApplication.processEvents()

        # Get screen rect for offscreen detection
        screen = app.primaryScreen()
        screen_rect = screen.geometry() if screen else QRect(0, 0, w, h)

        # Audit widget tree
        window_rect = QRect(0, 0, w, h)
        issues = _audit_widget(window, window_rect, screen_rect, is_root=True)

        # Classify issues
        clipping = [i for i in issues if i["type"] == LayoutIssue.CLIPPING]
        truncated = [i for i in issues if i["type"] == LayoutIssue.TRUNCATED]
        overlaps = [i for i in issues if i["type"] == LayoutIssue.OVERLAP]
        scrollbar = [i for i in issues if i["type"] == LayoutIssue.MISSING_SCROLLBAR]
        offscreen = [i for i in issues if i["type"] == LayoutIssue.OFFSCREEN]

        total = len(issues)
        REPORT["total_issues"] += total

        res_entry = {
            "resolution": f"{w}x{h}",
            "total_issues": total,
            "clipping": len(clipping),
            "truncated": len(truncated),
            "overlaps": len(overlaps),
            "missing_scrollbar": len(scrollbar),
            "offscreen": len(offscreen),
            "issues": issues[:50],  # limit for JSON size
        }
        REPORT["resolutions"].append(res_entry)

        # Log summary
        flags = []
        if clipping:
            flags.append(f"CUT:{len(clipping)}")
        if truncated:
            flags.append(f"TRUNC:{len(truncated)}")
        if overlaps:
            flags.append(f"OVERLAP:{len(overlaps)}")
        if scrollbar:
            flags.append(f"SCROLL:{len(scrollbar)}")

        status = "[WARN]" if flags else "[OK]"
        flag_str = " | ".join(flags) if flags else "CLEAN"
        print(f"    {status} {total} issues [{flag_str}]", flush=True)

        # Capture screenshot
        prefix = app_name[:3]
        cap_path = os.path.join(OUT_DIR, f"resize_{prefix}_{w}x{h}.png")
        window.grab().save(cap_path)
        print(f"    Screenshot: {os.path.basename(cap_path)}", flush=True)

        # Annotate if there are issues
        if issues:
            _annotate_screenshot(window, issues, cap_path)

        # Print detailed issues
        for iss in issues[:10]:
            loc = ""
            if "widget_geom" in iss:
                g = iss["widget_geom"]
                loc = f" @ ({g[0]},{g[1]} {g[2]}x{g[3]})"
            print(f"      {iss['type']:12s} | {iss.get('widget', '?'):20s} {loc}", flush=True)

    # Save report
    report_path = os.path.join(OUT_DIR, f"resize_report_{app_name}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n  Report: {report_path}", flush=True)
    print(f"  Total issues across all resolutions: {REPORT['total_issues']}", flush=True)

    QTimer.singleShot(500, lambda: window.close())
    QTimer.singleShot(800, app.quit)
    app.exec()
    return REPORT


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Resize Test with Layout Detection")
    p.add_argument("--app", default="patient", help="patient/hub")
    p.add_argument("--resolutions", default=None,
                   help="Comma-separated: 800x600,1920x1080")
    args = p.parse_args()

    resolutions = DEFAULT_RESOLUTIONS
    if args.resolutions:
        resolutions = []
        for r in args.resolutions.split(","):
            parts = r.strip().split("x")
            if len(parts) == 2:
                resolutions.append((int(parts[0]), int(parts[1])))

    run_resize_test(args.app, resolutions)
