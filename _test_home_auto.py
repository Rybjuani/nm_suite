"""
_test_home_auto.py — Test visual automático del HomeView real con ModuleCards.
Verifica: sombra, hover glow, scale click, márgenes PAD_CONTAINER, barra 3px.
Auto-captura y cierra solo.
Ejecutar: python _test_home_auto.py
"""
import sys, os

_proj = os.path.dirname(os.path.abspath(__file__))
if _proj not in sys.path:
    sys.path.insert(0, _proj)

from PyQt6.QtCore import (
    Qt, QTimer, QPointF, QEvent, QPoint,
)
from PyQt6.QtGui import (
    QEnterEvent, QMouseEvent, QPixmap,
)
from PyQt6.QtWidgets import QApplication

OUT = os.path.join(_proj, "_test_screens")
os.makedirs(OUT, exist_ok=True)

print("=" * 50, flush=True)
print("NeuroMood HomeView AutoTest — ModuleCard fixes", flush=True)
print("=" * 50, flush=True)

app = QApplication.instance() or QApplication(sys.argv)
app.setApplicationName("NeuroMood_HomeTest")

from app.main_qt import NeuroMoodApp
window = NeuroMoodApp()
window.show()

from app.home_qt import ModuleCard


def _cap(name):
    QApplication.processEvents()
    path = os.path.join(OUT, f"home_{name}.png")
    window.grab().save(path)
    print(f"  home_{name}.png", flush=True)


def _find_cards():
    """Encuentra todas las ModuleCard en el HomeView."""
    cards = []
    home = window._home
    for card in home._cards.values():
        if isinstance(card, ModuleCard):
            cards.append(card)
    return cards


def _hover(w, enter=True):
    from PyQt6.QtCore import QPointF as _QPF
    rc = w.rect()
    gp = _QPF(w.mapTo(w.window(), rc.center()))
    if enter:
        QApplication.sendEvent(w, QEnterEvent(gp, gp, gp))
    else:
        QApplication.sendEvent(w, QEvent(QEvent.Type.Leave))
    QApplication.processEvents()


def _click(w):
    from PyQt6.QtCore import QPointF as _QPF
    rc = w.rect()
    c = _QPF(rc.center())
    g = _QPF(w.mapTo(w.window(), rc.center()))
    QApplication.sendEvent(w, QMouseEvent(
        QEvent.Type.MouseButtonPress, c, g,
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier))
    QApplication.processEvents()
    QApplication.sendEvent(w, QMouseEvent(
        QEvent.Type.MouseButtonRelease, c, g,
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier))
    QApplication.processEvents()


def _step(seq, i, cards):
    if i >= len(seq):
        print(f"\n=== {len(seq)} capturas completadas ===")
        print(f"  {OUT}")
        QTimer.singleShot(200, window.close)
        return
    delay, fn, label = seq[i]
    print(f"  [{i+1}/{len(seq)}] {label}...", flush=True)
    QTimer.singleShot(delay, lambda idx=i: _run_step(idx, seq, cards))


def _run_step(i, seq, cards):
    _, fn, _ = seq[i]
    fn(cards)
    _step(seq, i + 1, cards)


# ── Secuencia ──────────────────────────────────────────────────────────────────

def _s01(cards):
    """Home completo — verificar márgenes 24px + cards con sombra."""
    _cap("01_home_full")
    if cards:
        c0 = cards[0]
        print(f"       {len(cards)} cards | card0: {c0.width()}x{c0.height()}px", flush=True)


def _s02(cards):
    """Hover en primera card — verificar glow indigo en sombra."""
    if cards:
        _hover(cards[0], True)
    _cap("02_card_hover_glow")


def _s03(cards):
    """Dejar de hover — restaurar sombra normal."""
    if cards:
        _hover(cards[0], False)
    _cap("03_card_hover_out")


def _s04(cards):
    """Click en segunda card — verificar escala 97%."""
    if len(cards) > 1:
        _click(cards[1])
    _cap("04_card_click_scale")


def _s05(cards):
    """Hover en última card (avisos, centrada sola)."""
    if len(cards) >= 7:
        _hover(cards[6], True)
    _cap("05_card7_hover")
    if len(cards) >= 7:
        _hover(cards[6], False)


def _s06(cards):
    """Vista general después de interacciones."""
    _cap("06_home_after_interactions")


# ── Iniciar tras carga ────────────────────────────────────────────────────────

def _start():
    cards = _find_cards()
    print(f"  Found {len(cards)} ModuleCard(s)", flush=True)

    seq = [
        (100,   _s01, "01_home_full"),
        (800,   _s02, "02_card_hover_glow"),
        (200,   _s03, "03_card_hover_out"),
        (600,   _s04, "04_card_click_scale"),
        (200,   _s05, "05_card7_hover"),
        (300,   _s06, "06_home_final"),
    ]
    _step(seq, 0, cards)


QTimer.singleShot(2500, _start)
sys.exit(app.exec())
