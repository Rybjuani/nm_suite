"""
_test_visual.py — Dashboard de verificación visual completa para el MASTER_PROMPT.

Ejecutar:  python _test_visual.py

Ejercita cada componente de las 5 fases del MASTER_PROMPT_NEUROMOOD_DESIGN:
  FASE 1 — Tokens: rich_gradient, noise_overlay, glass shadow
  FASE 2 — Componentes: NMButton (ripple/hover/press), NMCard (glow/noise/scale),
           NMProgressBar (shimmer), NMSkeleton, _SidebarItem (hover)
  FASE 3 — Navegación: fade entre "páginas" simuladas
  FASE 5 — Delight: breathing logo, MoodCelebration particles

Genera screenshots automáticos en _test_screens/ (si se ejecuta con --capture).
"""

import sys
import os

# Ensure project root in path
_proj = os.path.dirname(os.path.abspath(__file__))
if _proj not in sys.path:
    sys.path.insert(0, _proj)

from PyQt6.QtCore import (
    Qt, QTimer, QPointF, QRectF, QRect,
    pyqtSignal, QSize,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont,
    QPixmap, QPaintEvent, QMouseEvent, QResizeEvent,
    QIcon,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QFrame, QPushButton, QSizePolicy,
    QGraphicsOpacityEffect, QGridLayout, QTabWidget,
)

# ── Shared imports ────────────────────────────────────────────────────────────
from shared.theme_qt import (
    C, colors, norm_modo, qcolor, qfont, shadow_effect,
    rich_gradient, linear_gradient, noise_overlay, radial_glow,
    get_gradient, gradient_colors, interpolate_color,
    stylesheet_base, app_palette, stylesheet_scrollarea, stylesheet_tabwidget,
    RADIUS_CARD, RADIUS_BUTTON, PAD_CONTAINER, GAP_CARDS,
    aplicar_captionbar_qt, obtener_ruta_recurso,
)
from shared.components_qt import (
    ThemeManager, NMCard, NMButton, NMButtonOutline,
    NMProgressBar, NMSkeleton, NMHeader, NMFadeWidget,
    NMToast, NMInput, _LogoLabel, _SidebarItem,
)

# ── Theme ─────────────────────────────────────────────────────────────────────
MODO = "dark_hybrid"

# ── MoodCelebration duplicada para testing aislado ────────────────────────────
import random


class _TestParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-6, -2)
        self.alpha = 255
        self.radius = random.uniform(3, 6)
        self.color = QColor(color)


class _TestCelebration(QWidget):
    def __init__(self, parent, modo="dark_hybrid"):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(parent.size())
        self._particles = []
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)
        self.hide()

    def launch(self, origin_x: int, origin_y: int):
        parent = self.parentWidget()
        if parent:
            self.resize(parent.size())
        c = colors(self._modo)
        colors_pool = [c["accent"], c["teal"], c["violet"], c["cyan"]]
        self._particles = [
            _TestParticle(origin_x, origin_y, random.choice(colors_pool))
            for _ in range(28)
        ]
        self.raise_()
        self.show()
        self._timer.start()

    def _tick(self):
        alive = []
        for p in self._particles:
            p.x += p.vx
            p.y += p.vy
            p.vy += 0.3
            p.alpha = max(0, p.alpha - 6)
            if p.alpha > 0:
                alive.append(p)
        self._particles = alive
        self.update()
        if not alive:
            self._timer.stop()
            self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for part in self._particles:
            col = QColor(part.color)
            col.setAlpha(part.alpha)
            painter.setBrush(col)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(part.x - part.radius),
                int(part.y - part.radius),
                int(part.radius * 2),
                int(part.radius * 2),
            )
        painter.end()


# ── Página 1: Componentes base ────────────────────────────────────────────────


class PageComponents(QWidget):
    def __init__(self, modo, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setStyleSheet(f"background: {C('bg_primary', modo)};")
        self._setup()

    def _setup(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(PAD_CONTAINER, 16, PAD_CONTAINER, 32)
        layout.setSpacing(GAP_CARDS)

        c = colors(self._modo)

        def section(title: str, desc: str):
            lbl = QLabel(title)
            lbl.setFont(qfont("size_h3", bold=True))
            lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            layout.addWidget(lbl)
            sub = QLabel(desc)
            sub.setFont(qfont("size_caption"))
            sub.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            layout.addWidget(sub)

        # ── 1. NMButton con ripple + hover/press ───────────────────────────────
        section(
            "🔘 NMButton — Gradiente 3-stop + Ripple + Hover/Press",
            "Verificá: gradiente indigo→teal→violet. Al hacer hover, se aclara. "
            "Al clickear, ripple blanco + oscurece 15%. "
            "El ripple debe ser fluido a 60fps (16ms timer)."
        )
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn1 = NMButton("Hover me", modo=self._modo, width=140, height=44)
        btn_row.addWidget(btn1)
        btn2 = NMButton("Click me", modo=self._modo, width=140, height=44)
        btn_row.addWidget(btn2)
        btn3 = NMButton("Disabled", modo=self._modo, width=140, height=44)
        btn3.setEnabled(False)
        btn_row.addWidget(btn3)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── 2. NMButtonOutline ─────────────────────────────────────────────────
        section(
            "🔲 NMButtonOutline — Borde accent + fill hover",
            "Verificá: borde 2px accent. Hover: fill 15% accent."
        )
        out_row = QHBoxLayout()
        out_row.setSpacing(12)
        obtn1 = NMButtonOutline("Outline", modo=self._modo)
        obtn1.setFixedSize(120, 40)
        out_row.addWidget(obtn1)
        obtn2 = NMButtonOutline("Active", modo=self._modo)
        obtn2.setFixedSize(120, 40)
        obtn2.set_active(True)
        out_row.addWidget(obtn2)
        out_row.addStretch()
        layout.addLayout(out_row)

        # ── 3. NMCard — glow + noise + scale ──────────────────────────────────
        section(
            "🃏 NMCard — Glow hover + Noise overlay + Scale press",
            "Verificá: barra izquierda 5px con gradiente vertical accent→violet. "
            "Hover: la sombra cambia al color accent (glow indigo). "
            "Click: escala 97% con animación de 100ms OutCubic. "
            "Textura noise sutil en el área derecha de la barra."
        )
        card1 = NMCard(modo=self._modo)
        card1.setMinimumHeight(80)
        card_lay = QVBoxLayout(card1)
        card_lay.setContentsMargins(20, 12, 16, 12)
        card_lbl = QLabel("Card con glow hover + noise overlay")
        card_lbl.setFont(qfont("size_small", bold=True))
        card_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        card_lay.addWidget(card_lbl)
        card_subl = QLabel("Hacé hover para ver el glow indigo. Clickeá para escala.")
        card_subl.setFont(qfont("size_caption"))
        card_subl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        card_lay.addWidget(card_subl)
        layout.addWidget(card1)

        # Card disabled
        card2 = NMCard(modo=self._modo, clickable=False)
        card2.setMinimumHeight(50)
        card2.setEnabled(False)
        card2_lay = QVBoxLayout(card2)
        card2_lay.setContentsMargins(20, 10, 16, 10)
        card2_lbl = QLabel("Card disabled — debe mostrar rayas diagonales")
        card2_lbl.setFont(qfont("size_caption"))
        card2_lbl.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        card2_lay.addWidget(card2_lbl)
        layout.addWidget(card2)

        # ── 4. NMProgressBar — shimmer ────────────────────────────────────────
        section(
            "📊 NMProgressBar — Shimmer animado",
            "Verificá: barra de progreso con gradiente 3-stop horizontal + "
            "shimmer (banda blanca deslizante) a 60fps. "
            "El shimmer recorre la barra de izquierda a derecha."
        )
        pb1 = NMProgressBar(modo=self._modo, height=10)
        pb1.animate_to(0.75, duration=800)
        layout.addWidget(pb1)

        pb2 = NMProgressBar(modo=self._modo, height=6)
        pb2.animate_to(0.40, duration=800)
        layout.addWidget(pb2)

        pb3 = NMProgressBar(modo=self._modo, height=4)
        pb3.animate_to(0.95, duration=800)
        layout.addWidget(pb3)

        # ── 5. NMSkeleton ─────────────────────────────────────────────────────
        section(
            "💀 NMSkeleton — Carga animada",
            "Verificá: rectángulos con shimmer deslizante continuo. "
            "Base bg_elevated + banda blanca fina."
        )
        skel_row = QHBoxLayout()
        skel_row.setSpacing(12)
        skel1 = NMSkeleton(width=200, height=12, radius=6, modo=self._modo)
        skel_row.addWidget(skel1)
        skel2 = NMSkeleton(width=140, height=12, radius=6, modo=self._modo)
        skel_row.addWidget(skel2)
        skel3 = NMSkeleton(width=100, height=12, radius=6, modo=self._modo)
        skel_row.addWidget(skel3)
        skel_row.addStretch()
        layout.addLayout(skel_row)

        # ── 6. SidebarItem hover ──────────────────────────────────────────────
        section(
            "📂 _SidebarItem — Hover animado",
            "Verificá: fondo se aclara suavemente al hover con animación de 120ms. "
            "Barra izquierda accent aparece/desaparece con animación 150ms."
        )
        sid_widget = QWidget()
        sid_widget.setFixedSize(200, 160)
        sid_widget.setStyleSheet(f"background: {c['bg_secondary']}; border-radius: {RADIUS_CARD}px;")
        sid_lay = QVBoxLayout(sid_widget)
        sid_lay.setContentsMargins(0, 8, 0, 8)
        sid_lay.setSpacing(0)
        for i, (icon, label) in enumerate([("🎭", "Ánimo"), ("🌬️", "Respirar"), ("📝", "TCC")]):
            item = _SidebarItem(f"test_{i}", icon, label, modo=self._modo)
            if i == 0:
                item.set_active(True)
            sid_lay.addWidget(item)
        layout.addWidget(sid_widget)

        # ── 7. Glass shadow demo ──────────────────────────────────────────────
        section(
            "🪟 Glass Shadow — Sombra tipo glass",
            "Verificá: sombra con blur 48, offset Y=20, color accent alpha=20."
        )
        glass_card = QFrame()
        glass_card.setFixedHeight(60)
        glass_card.setStyleSheet(
            f"background: {c['bg_glass']}; border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {c.get('border_card', c['border'])};"
        )
        glass_lay = QVBoxLayout(glass_card)
        glass_lbl = QLabel("Glass card — shadow accent (blur 48, offset Y 20)")
        glass_lbl.setFont(qfont("size_caption"))
        glass_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        glass_lay.addWidget(glass_lbl)
        glass_shadow = shadow_effect("glass", self._modo, glass_card)
        glass_card.setGraphicsEffect(glass_shadow)
        layout.addWidget(glass_card)

        layout.addStretch()


# ── Página 2: Delight ─────────────────────────────────────────────────────────


class PageDelight(QWidget):
    particles_triggered = pyqtSignal(int, int)

    def __init__(self, modo, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setStyleSheet(f"background: {C('bg_primary', modo)};")
        self._setup()

    def _setup(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(stylesheet_scrollarea(self._modo))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(PAD_CONTAINER, 16, PAD_CONTAINER, 32)
        layout.setSpacing(GAP_CARDS)

        c = colors(self._modo)

        def section(title: str, desc: str):
            lbl = QLabel(title)
            lbl.setFont(qfont("size_h3", bold=True))
            lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
            layout.addWidget(lbl)
            sub = QLabel(desc)
            sub.setFont(qfont("size_caption"))
            sub.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
            layout.addWidget(sub)

        # ── 1. Breathing logo ──────────────────────────────────────────────────
        section(
            "🌊 Logo con Breathing Animation",
            "Verificá: glow radial indigo que pulsa suavemente (3s ciclo, "
            "SineCurve, loop infinito). El glow crece y se reduce. "
            "NO debe parpadear ni saltar. Debe ser hipnótico, fluido."
        )
        logo_container = QWidget()
        logo_container.setFixedHeight(50)
        logo_lay = QHBoxLayout(logo_container)
        logo_lay.setContentsMargins(0, 0, 0, 0)
        logo = _LogoLabel()
        logo_lay.addWidget(logo)
        logo_lay.addStretch()
        layout.addWidget(logo_container)

        # ── 2. MoodCelebration ─────────────────────────────────────────────────
        section(
            "✨ MoodCelebration — Partículas (puntaje ≥ 7)",
            "Verificá: 28 partículas con colores accent/teal/violet/cyan. "
            "Explosión hacia arriba con gravedad. 60fps. "
            "Click en 'Animo 9/10' para disparar."
        )
        celeb_container = QWidget()
        celeb_container.setFixedHeight(80)
        celeb_container.setStyleSheet(
            f"background: {c['bg_surface']}; border-radius: {RADIUS_CARD}px; "
            f"border: 1px solid {c.get('border_card', c['border'])};"
        )
        celeb_lay = QHBoxLayout(celeb_container)
        celeb_lay.setContentsMargins(20, 0, 20, 0)
        celeb_lbl = QLabel("Registraste ánimo 9/10")
        celeb_lbl.setFont(qfont("size_body", bold=True))
        celeb_lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        celeb_lay.addWidget(celeb_lbl)
        celeb_lay.addStretch()
        celeb_btn = NMButton("Disparar partículas ✨", modo=self._modo, width=180, height=36)
        celeb_btn.clicked.connect(
            lambda: self._trigger_particles(celeb_btn)
        )
        celeb_lay.addWidget(celeb_btn)
        layout.addWidget(celeb_container)

        self._celebration = _TestCelebration(container, self._modo)

        # ── 3. Gradiente 3-stop visual ─────────────────────────────────────────
        section(
            "🎨 Gradiente 3-stop — Indigo → Teal → Violet",
            "Verificá: barra horizontal con transición suave entre los 3 colores. "
            "Posiciones: indigo 0%, teal 45%, violet 100%."
        )
        grad_widget = _GradientPreview(self._modo)
        grad_widget.setFixedHeight(50)
        layout.addWidget(grad_widget)

        # ── 4. Noise overlay preview ───────────────────────────────────────────
        section(
            "🔮 Noise Overlay — Textura de material",
            "Verificá: textura de ruido fino sobre fondo bg_surface. "
            "Debe ser sutil (opacidad 3.5%). Mirá de cerca."
        )
        noise_widget = _NoisePreview(self._modo)
        noise_widget.setFixedHeight(60)
        layout.addWidget(noise_widget)

        layout.addStretch()

    def _trigger_particles(self, btn):
        origin = btn.mapTo(self, btn.rect().center())
        parent = self.findChild(QScrollArea).widget()
        self._celebration.setParent(parent)
        self._celebration.launch(origin.x(), origin.y())


# ── Gradient preview widget ───────────────────────────────────────────────────


class _GradientPreview(QWidget):
    def __init__(self, modo):
        super().__init__()
        self._modo = norm_modo(modo)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        grad = rich_gradient(rect, self._modo, angle=0)
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, RADIUS_BUTTON, RADIUS_BUTTON)
        p.end()


class _NoisePreview(QWidget):
    def __init__(self, modo):
        super().__init__()
        self._modo = norm_modo(modo)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = colors(self._modo)
        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        p.setBrush(QColor(c["bg_surface"]))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rect, RADIUS_CARD, RADIUS_CARD)
        noise_overlay(p, rect, opacity=0.035, modo=self._modo)
        p.end()


# ── Página 3: Navegación ──────────────────────────────────────────────────────


class PageNavigation(QWidget):
    go_home = pyqtSignal()
    go_module = pyqtSignal()

    def __init__(self, modo, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._setup()

    def _setup(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAD_CONTAINER, 16, PAD_CONTAINER, 32)
        layout.setSpacing(GAP_CARDS)
        c = colors(self._modo)

        lbl = QLabel("🗂️ Navegación — Fade entre páginas")
        lbl.setFont(qfont("size_h3", bold=True))
        lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        layout.addWidget(lbl)

        desc = QLabel(
            "Verificá: transición fade-out del snapshot anterior (200ms OutCubic) "
            "mientras carga la nueva vista. Sin saltos ni flicker."
        )
        desc.setFont(qfont("size_caption"))
        desc.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(12)
        btn_home = NMButton("← Home (simulado)", modo=self._modo, width=160, height=40)
        btn_home.clicked.connect(self.go_home.emit)
        nav_row.addWidget(btn_home)
        btn_mod = NMButton("→ Módulo (simulado)", modo=self._modo, width=160, height=40)
        btn_mod.clicked.connect(self.go_module.emit)
        nav_row.addWidget(btn_mod)
        nav_row.addStretch()
        layout.addLayout(nav_row)

        status = QLabel("Página actual: Home")
        status.setFont(qfont("size_small"))
        status.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
        layout.addWidget(status)
        self._status_lbl = status

        layout.addStretch()

    def set_page_name(self, name: str):
        self._status_lbl.setText(f"Página actual: {name}")


# ── Ventana principal ─────────────────────────────────────────────────────────


class VisualTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._modo = "dark_hybrid"
        self.setWindowTitle("NeuroMood MASTER_PROMPT — Test Visual")
        self.setMinimumSize(620, 480)
        self.resize(780, 680)
        self._center()

        # Icon
        ico = obtener_ruta_recurso("NM_icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        # Theme
        self._tm = ThemeManager.instance()
        self._tm.switch_mode(self._modo)

        # Global style
        QApplication.instance().setPalette(app_palette(self._modo))
        self.setStyleSheet(
            stylesheet_base(self._modo)
            + f"QMainWindow {{ background: {C('bg_primary', self._modo)}; }}"
        )

        # UI
        self._build_ui()

        # Caption bar
        QTimer.singleShot(100, lambda: aplicar_captionbar_qt(self, self._modo))

        # Capture screenshot after UI settles
        self._capture_timer = QTimer(self)
        self._capture_timer.setSingleShot(True)

        def _do_captures():
            self._capture_all()
            manual = os.environ.get("NM_TEST_NO_AUTO_CLOSE", "") == "1"
            if not manual:
                QTimer.singleShot(500, self.close)

        self._capture_timer.timeout.connect(_do_captures)
        self._capture_timer.start(2500)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self._header = NMHeader(
            central, modo=self._modo,
            username="Visual Test",
        )
        self._header.theme_toggle.connect(self._toggle_theme)
        main_layout.addWidget(self._header)

        # Tabs para cada fase
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(stylesheet_tabwidget(self._modo))

        self._page_components = PageComponents(self._modo)
        self._page_delight = PageDelight(self._modo)
        self._page_nav = PageNavigation(self._modo)

        # Fade stack para navegación
        self._fade = NMFadeWidget()
        self._page_nav.go_home.connect(self._show_home_fade)
        self._page_nav.go_module.connect(self._show_module_fade)

        # Home simulado para navegación
        self._fake_home = self._make_fake_page("Home", "Página de inicio simulada")
        self._fake_module = self._make_fake_page("Módulo", "Módulo de paciente simulado")
        self._fade.addWidget(self._fake_home)
        self._fade.addWidget(self._page_nav)
        self._fade.addWidget(self._fake_module)
        self._fade.setCurrentWidget(self._page_nav)

        self._tabs.addTab(self._page_components, "🔘 FASE 2 — Componentes")
        self._tabs.addTab(self._page_delight, "✨ FASE 5 — Delight")
        self._tabs.addTab(self._fade, "🗂️ FASE 3 — Navegación")

        main_layout.addWidget(self._tabs)

    def _make_fake_page(self, title: str, desc: str):
        w = QWidget()
        w.setStyleSheet(f"background: {C('bg_primary', self._modo)};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(PAD_CONTAINER, 40, PAD_CONTAINER, 40)
        c = colors(self._modo)
        lbl = QLabel(title)
        lbl.setFont(qfont("size_h1", bold=True))
        lbl.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
        lay.addWidget(lbl)
        sub = QLabel(desc)
        sub.setFont(qfont("size_body"))
        sub.setStyleSheet(f"color: {c['text_tertiary']}; background: transparent;")
        lay.addWidget(sub)
        lay.addStretch()
        return w

    def _show_home_fade(self):
        self._fade.setCurrentWidget(self._fake_home)
        self._page_nav.set_page_name("Home")

    def _show_module_fade(self):
        self._fade.setCurrentWidget(self._fake_module)
        self._page_nav.set_page_name("Módulo")

    def _toggle_theme(self):
        if "dark" in self._modo:
            self._modo = "light_hybrid"
        else:
            self._modo = "dark_hybrid"
        self._tm.switch_mode(self._modo)
        QApplication.instance().setPalette(app_palette(self._modo))
        self.setStyleSheet(
            stylesheet_base(self._modo)
            + f"QMainWindow {{ background: {C('bg_primary', self._modo)}; }}"
        )
        QTimer.singleShot(50, lambda: aplicar_captionbar_qt(self, self._modo))

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # ── Screenshot capture ────────────────────────────────────────────────────

    def _capture_all(self):
        """Captura screenshots de cada pestaña y los guarda en _test_screens/"""
        out_dir = os.path.join(_proj, "_test_screens")
        os.makedirs(out_dir, exist_ok=True)
        QApplication.processEvents()

        pages = [
            ("01_componentes", self._page_components),
            ("02_delight",      self._page_delight),
            ("03_navegacion",   self._page_nav),
        ]

        for name, page in pages:
            self._tabs.setCurrentWidget(page)
            QApplication.processEvents()
            QApplication.processEvents()
            pm = page.grab()
            path = os.path.join(out_dir, f"{name}.png")
            pm.save(path)
            print(f"  [OK] {path}")

        print(f"\nScreenshots guardados en: {out_dir}")
        print("Abrí la carpeta _test_screens/ para revisar cada captura.")


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    print("NeuroMood MASTER_PROMPT — Test Visual")
    print("  Abarcando FASE 2 (Componentes), FASE 5 (Delight), FASE 3 (Navegacion)")
    manual = os.environ.get("NM_TEST_NO_AUTO_CLOSE", "") == "1"
    print(f"  Manual (no cerrar): {'SI' if manual else 'NO (auto-cierre en 3s)'}")
    if manual:
        print("  Modo manual: cerra la ventana con la X cuando termines.")
    print()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NeuroMood_VisualTest")
    window = VisualTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
