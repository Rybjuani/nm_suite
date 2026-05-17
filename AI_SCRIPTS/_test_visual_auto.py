"""
_test_visual_auto.py — Test visual AUTOMATICO con ventana real.
Simula hover y click via eventos Qt directos. Cierra solo.
Todo encadenado con QTimer.singleShot — sin QTest.qWait bloqueante.
Salida: _test_screens/ con ~12 PNGs.
Ejecutar: python _test_visual_auto.py
"""
import sys, os

_proj = os.path.dirname(os.path.abspath(__file__))
if _proj not in sys.path:
    sys.path.insert(0, _proj)

from PyQt6.QtCore import (
    Qt, QTimer, QPoint, QEvent, QSize,
)
from PyQt6.QtGui import (
    QColor, QPixmap, QIcon, QEnterEvent, QMouseEvent, QFont,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QFrame, QTabWidget,
)

from shared.theme_qt import (
    C, colors, qfont, stylesheet_base, app_palette,
    stylesheet_scrollarea, stylesheet_tabwidget,
    RADIUS_CARD, RADIUS_BUTTON,
    PAD_CONTAINER, GAP_CARDS,
    aplicar_captionbar_qt, obtener_ruta_recurso, shadow_effect,
)
from shared.components_qt import (
    ThemeManager, NMCard, NMButton, NMButtonOutline,
    NMProgressBar, NMSkeleton, NMHeader, _LogoLabel, _SidebarItem,
    NMFadeWidget,
)

MODO = "dark_hybrid"
OUT = os.path.join(_proj, "_test_screens")
os.makedirs(OUT, exist_ok=True)


class AutoTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self._modo = MODO
        self.setWindowTitle("NeuroMood Visual AutoTest")
        self.resize(820, 700)
        try:
            geo = QApplication.primaryScreen().availableGeometry()
            self.move((geo.width() - 820) // 2, (geo.height() - 700) // 2)
        except Exception:
            pass
        ico = obtener_ruta_recurso("NM_icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))
        QApplication.instance().setPalette(app_palette(MODO))
        self.setStyleSheet(stylesheet_base(MODO) +
                           f"QMainWindow {{ background: {C('bg_primary', MODO)}; }}")
        ThemeManager.instance().switch_mode(MODO)
        self._build()
        QTimer.singleShot(120, lambda: aplicar_captionbar_qt(self, MODO))

        self._seq = []
        self._pos = 0

    def _build(self):
        c = colors(MODO)
        central = QWidget()
        self.setCentralWidget(central)
        vl = QVBoxLayout(central)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)
        vl.addWidget(NMHeader(central, modo=MODO, username="AutoTest"))
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(stylesheet_tabwidget(MODO))

        # ── Tab 0: Componentes ──
        p0 = QWidget()
        p0.setStyleSheet(f"background: {C('bg_primary', MODO)};")
        sc = QScrollArea(p0)
        sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet(stylesheet_scrollarea(MODO))
        p0_lay = QVBoxLayout(p0); p0_lay.setContentsMargins(0,0,0,0); p0_lay.addWidget(sc)
        cnt = QWidget(); cnt.setStyleSheet("background: transparent;"); sc.setWidget(cnt)
        L = QVBoxLayout(cnt)
        L.setContentsMargins(PAD_CONTAINER, 16, PAD_CONTAINER, 32); L.setSpacing(GAP_CARDS)

        def hdr(t):
            lb = QLabel(t); lb.setFont(qfont("size_h3", bold=True))
            lb.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            return lb

        # NMButton
        L.addWidget(hdr("NMButton — Gradiente 3-stop + Ripple"))
        self._btn = NMButton("Hover + Click me", modo=MODO, width=200, height=44)
        L.addWidget(self._btn)

        # NMButtonOutline
        L.addWidget(hdr("NMButtonOutline — Borde accent + hover fill"))
        self._obtn = NMButtonOutline("Outline hover", modo=MODO)
        self._obtn.setFixedSize(140, 38)
        L.addWidget(self._obtn)

        # NMCard
        L.addWidget(hdr("NMCard — Glow hover + Noise + Scale"))
        self._card = NMCard(modo=MODO)
        self._card.setMinimumHeight(80)
        ci = QVBoxLayout(self._card); ci.setContentsMargins(20, 14, 16, 14)
        ci.addWidget(QLabel("Card con glow hover + noise overlay"))
        L.addWidget(self._card)

        # Card disabled
        L.addWidget(hdr("NMCard disabled — Rayas diagonales"))
        cd = NMCard(modo=MODO, clickable=False); cd.setMinimumHeight(50); cd.setEnabled(False)
        cdi = QVBoxLayout(cd); cdi.setContentsMargins(20, 10, 16, 10)
        cdi.addWidget(QLabel("Disabled — rayas + alpha 0.4"))
        L.addWidget(cd)

        # Glass shadow
        L.addWidget(hdr("Glass Shadow — blur 48, offset Y=20"))
        self._glass = QFrame()
        self._glass.setFixedHeight(50)
        self._glass.setStyleSheet(
            f"background: {c['bg_glass']}; border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {c.get('border_card', c['border'])};"
        )
        self._glass.setGraphicsEffect(
            shadow_effect("glass", MODO, self._glass)
        )
        L.addWidget(self._glass)

        # ProgressBar + Skeleton
        L.addWidget(hdr("NMProgressBar + NMSkeleton — Shimmer"))
        pb = NMProgressBar(modo=MODO, height=10); pb.animate_to(0.7, 600); L.addWidget(pb)
        sr = QHBoxLayout(); sr.setSpacing(8)
        sr.addWidget(NMSkeleton(width=200, height=12, radius=6, modo=MODO))
        sr.addWidget(NMSkeleton(width=100, height=12, radius=6, modo=MODO)); sr.addStretch()
        L.addLayout(sr)

        # Sidebar
        L.addWidget(hdr("_SidebarItem — Hover animado"))
        sw = QWidget(); sw.setFixedSize(200, 48)
        sw.setStyleSheet(f"background: {c['bg_secondary']}; border-radius: {RADIUS_CARD}px;")
        sl = QVBoxLayout(sw); sl.setContentsMargins(0, 4, 0, 4)
        self._si = _SidebarItem("s", "🎭", "Animo", modo=MODO)
        sl.addWidget(self._si); L.addWidget(sw)
        L.addStretch()
        self._tabs.addTab(p0, "Componentes")

        # ── Tab 1: Delight ──
        p1 = QWidget()
        p1.setStyleSheet(f"background: {C('bg_primary', MODO)};")
        sc2 = QScrollArea(p1); sc2.setWidgetResizable(True); sc2.setFrameShape(QFrame.Shape.NoFrame)
        sc2.setStyleSheet(stylesheet_scrollarea(MODO))
        p1_lay = QVBoxLayout(p1); p1_lay.setContentsMargins(0,0,0,0); p1_lay.addWidget(sc2)
        cnt2 = QWidget(); cnt2.setStyleSheet("background: transparent;"); sc2.setWidget(cnt2)
        L2 = QVBoxLayout(cnt2)
        L2.setContentsMargins(PAD_CONTAINER, 16, PAD_CONTAINER, 32); L2.setSpacing(GAP_CARDS)

        L2.addWidget(hdr("_LogoLabel — Breathing animation"))
        self._logo = _LogoLabel(); self._logo.setFixedSize(200, 50)
        L2.addWidget(self._logo)

        L2.addWidget(hdr("MoodCelebration — Particulas"))
        self._celeb = NMButton("Animo 9/10 — Disparar", modo=MODO, width=200, height=44)
        L2.addWidget(self._celeb)
        L2.addStretch()
        self._tabs.addTab(p1, "Delight")

        vl.addWidget(self._tabs)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _cap(self, name):
        QApplication.processEvents()
        path = os.path.join(OUT, f"{name}.png")
        self.grab().save(path)
        print(f"  {name}.png", flush=True)

    def _tab(self, n):
        self._tabs.setCurrentIndex(n)
        QApplication.processEvents()

    def _hover(self, w, enter=True):
        try:
            from PyQt6.QtCore import QPointF as _QPF
            center = w.rect().center()
            gp = _QPF(w.mapTo(w.window(), center))
            if enter:
                ev = QEnterEvent(gp, gp, gp)
            else:
                ev = QEvent(QEvent.Type.Leave)
            QApplication.sendEvent(w, ev)
        except Exception as e:
            print(f"       (hover skip: {e})", flush=True)
        QApplication.processEvents()

    def _press(self, w):
        from PyQt6.QtCore import QPointF as _QPF
        rc = w.rect()
        c = _QPF(rc.center())
        g = _QPF(w.mapTo(w.window(), rc.center()))
        QApplication.sendEvent(w, QMouseEvent(
            QEvent.Type.MouseButtonPress, c, g,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier))
        QApplication.processEvents()

    def _release(self, w):
        from PyQt6.QtCore import QPointF as _QPF
        rc = w.rect()
        c = _QPF(rc.center())
        g = _QPF(w.mapTo(w.window(), rc.center()))
        QApplication.sendEvent(w, QMouseEvent(
            QEvent.Type.MouseButtonRelease, c, g,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier))
        QApplication.processEvents()

    def _click(self, w):
        self._press(w)
        self._release(w)
        try:
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
        except Exception as e:
            print(f"       (click skip: {e})", flush=True)
        QApplication.processEvents()

    # ── Secuencia ──────────────────────────────────────────────────────────────

    def start(self):
        self._seq = [
            # ---- Tab Componentes ----
            (1,     self._s01,  "01_base"),
            (400,   self._s02,  "02_btn_hover"),
            (100,   self._s02b, "02b_btn_hover_outline"),
            (300,   self._s03,  "03_btn_click_ripple"),
            (100,   self._s04,  "04_btn_press"),
            (300,   self._s05,  "05_card_default"),
            (400,   self._s06,  "06_card_hover_glow"),
            (100,   self._s07,  "07_card_click_scale"),
            (300,   self._s08,  "08_card_disabled"),
            (300,   self._s09,  "09_progress_skeleton"),
            (400,   self._s10,  "10_sidebar_hover"),
            (200,   self._s11,  "11_glass_shadow"),
            # ---- Tab Delight ----
            (200,   self._s12,  "12_logo_phase1"),
            (100,   self._s13,  "13_logo_phase2"),
            (400,   self._s14,  "14_celebration"),
            # ---- Tab Navegacion ----
            (300,   self._s_fin, None),
        ]
        self._run(0)

    def _run(self, i):
        if i >= len(self._seq):
            return
        delay, fn, label = self._seq[i]
        if label:
            print(f"  [{i+1}/{len(self._seq)-1}] {label}...", flush=True)
        QTimer.singleShot(delay, lambda idx=i: self._do_step(idx))

    def _do_step(self, i):
        _, fn, label = self._seq[i]
        fn()
        self._run(i + 1)

    def _s01(self): self._tab(0); self._cap("01_base")
    def _s02(self): self._tab(0); self._hover(self._btn, True); self._cap("02_btn_hover")
    def _s02b(self): self._tab(0); self._hover(self._btn, False); self._hover(self._obtn, True); self._cap("02b_outline_hover")
    def _s03(self): self._tab(0); self._hover(self._obtn, False); self._click(self._btn); self._cap("03_btn_click_ripple")
    def _s04(self): self._tab(0); self._press(self._btn); self._cap("04_btn_press")
    def _s05(self): self._tab(0); self._release(self._btn); self._cap("05_card_default")
    def _s06(self): self._tab(0); self._hover(self._card, True); self._cap("06_card_hover_glow")
    def _s07(self): self._tab(0); self._click(self._card); self._cap("07_card_click_scale")
    def _s08(self): self._tab(0); self._cap("08_card_disabled")
    def _s09(self): self._tab(0); self._cap("09_progress_skeleton")
    def _s10(self): self._tab(0); self._hover(self._si, True); self._cap("10_sidebar_hover")
    def _s11(self): self._tab(0); self._cap("11_glass_shadow")
    def _s12(self): self._tab(1); self._cap("12_logo_phase1")
    def _s13(self): self._tab(1); self._cap("13_logo_phase2")
    def _s14(self): self._tab(1); self._click(self._celeb); self._cap("14_celebration")
    def _s_fin(self):
        n = len(self._seq) - 1
        print(f"\n=== {n} capturas completadas ===")
        print(f"  {OUT}")
        QTimer.singleShot(200, self.close)


def main():
    print("=" * 50, flush=True)
    print("NeuroMood Visual AutoTest", flush=True)
    print("=" * 50, flush=True)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood_AutoTest")
    w = AutoTest()
    w.show()
    QTimer.singleShot(2000, w.start)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
