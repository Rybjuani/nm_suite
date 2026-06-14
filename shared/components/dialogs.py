"""Dialog components: NMDialog, nm_confirm, NMDialogScaffold."""

from __future__ import annotations

from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from shared.theme import TYPOGRAPHY
from shared.theme_manager import ThemeManager
from shared.theme_qt import (
    C,
    V3_RD,
    V3_SP,
    eyebrow_font,
    norm_modo,
    qfont,
    v3c,
)
from shared.components.buttons import (
    NMButton,
    _NM_CONTROL_FONT,
    _NM_CONTROL_HEIGHT,
    _NM_CONTROL_PILL_RADIUS,
    _NM_CONTROL_WEIGHT,
)


def _tm() -> ThemeManager:
    return ThemeManager.instance()


class NMDialog(QWidget):
    """Modal/Dialog overlay con header, body y footer estandarizados.

    Implementado como overlay sobre la ventana padre (no QDialog nativo) para
    mantener consistencia visual con el shell. Soporta close por click en
    backdrop o tecla Escape.

    Uso:
        dlg = NMDialog(title="Confirmar acción", parent=self)
        dlg.set_body_widget(QLabel("¿Estás seguro?"))
        dlg.add_footer_button("Cancelar", role="secondary",
                              callback=dlg.close)
        dlg.add_footer_button("Eliminar", role="danger",
                              callback=self._do_delete)
        dlg.show_centered()
    """

    closed = pyqtSignal()

    def __init__(self, title: str = "", modo: str = None, width: int = 480, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._dialog_width = width
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        # Overlay full-cover sobre el padre
        if parent is not None:
            self.setGeometry(parent.rect())

        # Container central
        self._panel = QFrame(self)
        self._panel.setFixedWidth(width)
        self._panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        panel_lay = QVBoxLayout(self._panel)
        panel_lay.setContentsMargins(V3_SP["xl"], V3_SP["xl"], V3_SP["xl"], V3_SP["lg"])
        panel_lay.setSpacing(V3_SP["md"])

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(V3_SP["sm"])
        self._title = QLabel(title or "")
        self._title.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        self._title.setWordWrap(True)
        header_row.addWidget(self._title, stretch=1)
        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setFlat(True)
        self._close_btn.clicked.connect(self.close)
        header_row.addWidget(self._close_btn)
        panel_lay.addLayout(header_row)

        # Body container
        self._body_holder = QVBoxLayout()
        self._body_holder.setSpacing(V3_SP["md"])
        panel_lay.addLayout(self._body_holder, stretch=1)

        # Footer
        self._footer_row = QHBoxLayout()
        self._footer_row.setSpacing(V3_SP["sm"])
        self._footer_row.addStretch()
        panel_lay.addLayout(self._footer_row)
        self._footer_buttons: list[QPushButton] = []

        # Layout root para centrar el panel
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch()
        center_row = QHBoxLayout()
        center_row.addStretch()
        center_row.addWidget(self._panel)
        center_row.addStretch()
        root.addLayout(center_row)
        root.addStretch()

        _tm().theme_changed.connect(self._apply_theme)
        self._apply_theme(self._modo)
        self.hide()

    # ── API ──────────────────────────────────────────────────────────────────

    def set_title(self, text: str):
        self._title.setText(text or "")

    def set_body_widget(self, widget: QWidget):
        # Limpiar body actual
        while self._body_holder.count():
            item = self._body_holder.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._body_holder.addWidget(widget)

    def add_footer_button(self, label: str, role: str = "secondary", callback=None) -> QPushButton:
        """role: 'primary' | 'secondary' | 'danger' | 'ghost'."""
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(_NM_CONTROL_HEIGHT)
        btn.setMinimumWidth(96)
        btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
        btn.setProperty("nm_role", role)
        if callback is not None:
            btn.clicked.connect(lambda _=False, cb=callback: cb())
        self._footer_row.addWidget(btn)
        self._footer_buttons.append(btn)
        self._style_footer()
        return btn

    def show_centered(self):
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        self.setFocus(Qt.FocusReason.PopupFocusReason)

    # ── Eventos ──────────────────────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Click fuera del panel cierra
        if not self._panel.geometry().contains(event.pos()):
            self.close()
            return
        super().mousePressEvent(event)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    # ── Paint ────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Backdrop semitransparente, theme-aware: en light un scrim negro duro se
        # ve roto (feedback). En dark mantenemos negro; en light usamos la tinta
        # profunda del tema a baja alpha para atenuar sin ennegrecer.
        if "dark" in self._modo:
            scrim = QColor(0, 0, 0, 150)
        else:
            ink = v3c("text", self._modo)
            scrim = QColor(ink.red(), ink.green(), ink.blue(), 90)
        p.fillRect(self.rect(), scrim)
        # El panel se pinta como QFrame con su stylesheet
        p.end()

    # ── Theme ────────────────────────────────────────────────────────────────

    def _apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        border = C("border", self._modo)
        self._panel.setStyleSheet(
            f"QFrame {{ background-color: {bg}; "
            f"border: 1px solid {border}; border-radius: {V3_RD['xl']}px; }}"
        )
        self._title.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        c_ink_secondary = v3c("ink_secondary", self._modo).name()
        self._close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {c_ink_secondary}; "
            f"border: none; border-radius: 12px; padding: 0px; }}"
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; "
            f"color: {v3c('text', self._modo).name()}; }}"
        )
        self._style_footer()

    def _style_footer(self):
        accent = v3c("accent", self._modo).name()
        danger = v3c("danger", self._modo).name()
        text_on_acc = v3c("primary_ink", self._modo).name()
        text = v3c("text", self._modo).name()
        text_muted = v3c("text2", self._modo).name()
        accent_soft = v3c("accentSoft", self._modo)
        soft = (
            f"rgba({accent_soft.red()},{accent_soft.green()},"
            f"{accent_soft.blue()},{accent_soft.alpha()})"
        )
        for btn in self._footer_buttons:
            role = btn.property("nm_role") or "secondary"
            btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
            if role == "primary":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('cyan', self._modo).name()}; }}"
                )
            elif role == "danger":
                btn.setStyleSheet(
                    f"QPushButton {{ background: {danger}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('warm', self._modo).name()}; }}"
                )
            elif role == "ghost":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {text_muted}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ color: {text}; background: {soft}; }}"
                )
            else:  # secondary
                btn.setStyleSheet(
                    f"QPushButton {{ background: {soft}; color: {accent}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('tealSoftSolid' if 'dark' in self._modo else 'tealSoft', self._modo).name()}; }}"
                )


# Alias semántico
NMModal = NMDialog


def nm_confirm(
    parent: QWidget,
    titulo: str,
    mensaje: str,
    on_confirm,
    confirm_text: str = "Restablecer",
    modo: str = None,
) -> NMDialog:
    """Confirmación estándar sobre NMDialog (patrón único del producto).

    La usan todos los "Restablecer por defecto" de los configurables del Hub:
    overlay child de la ventana (sin ventana top-level), Cancelar ghost +
    acción danger. `on_confirm` corre solo si el profesional confirma.
    """
    win = parent.window() if parent is not None else None
    dlg = NMDialog(title=titulo, modo=modo, parent=win)
    body = QLabel(mensaje)
    body.setWordWrap(True)
    body.setFont(qfont("size_small"))
    body.setStyleSheet(
        f"color: {v3c('text2', norm_modo(modo or _tm().modo)).name()}; background: transparent;"
    )
    dlg.set_body_widget(body)
    dlg.add_footer_button("Cancelar", role="ghost", callback=dlg.close)

    def _go():
        dlg.close()
        on_confirm()

    dlg.add_footer_button(confirm_text, role="danger", callback=_go)
    dlg.show_centered()
    return dlg


class NMDialogScaffold(QWidget):
    """Ventana auxiliar standalone con header, cuerpo y footer de acciones.

    Para editores y ventanas secundarias (no overlay). Incluye:
      - Header fijo: eyebrow opcional + título + botón cerrar
      - Cuerpo: widget principal (flexible, con stretch)
      - Footer fijo: action bar con botones alineados a la derecha

    Uso::
        win = NMDialogScaffold("Editor de textos", modo=modo)
        win.set_body(editor_widget)
        win.add_action("Cancelar", role="ghost", callback=win.close)
        win.add_action("Guardar", role="primary", callback=on_save)
        win.show()
    """

    def __init__(
        self,
        title: str = "",
        eyebrow: str = "",
        modo: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._modo = norm_modo(modo or _tm().modo)
        self._action_buttons: list[QPushButton] = []
        # Flags de ventana SOLO standalone. Con parent (embebido en un QDialog
        # via addWidget) el flag Window NO se limpia porque el parent ya
        # coincide y addChildWidget saltea el setParent → el scaffold quedaba
        # como top-level invisible y el diálogo medía 360×0 (la "mini ventana"
        # de Olvidé mi PIN / Quitar paciente / Exportar informe).
        if parent is None:
            self.setWindowFlags(
                Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint
            )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], V3_SP["md"])
        root.setSpacing(0)

        # Header row
        hdr = QHBoxLayout()
        hdr.setSpacing(V3_SP["sm"])
        hdr.setContentsMargins(0, 0, 0, V3_SP["sm"])

        vtext = QVBoxLayout()
        vtext.setSpacing(2)
        # Parent explícito pre-addWidget: setVisible(True) sobre un QLabel
        # huérfano lo muestra como top-level fugaz (AGENTS §10.9).
        self._eyebrow_lbl = QLabel(eyebrow or "", self)
        self._eyebrow_lbl.setFont(eyebrow_font())
        self._eyebrow_lbl.setVisible(bool(eyebrow))
        vtext.addWidget(self._eyebrow_lbl)

        self._title_lbl = QLabel(title or "")
        try:
            from shared.theme_qt import v3_font as _v3f
            self._title_lbl.setFont(_v3f("size_h2", weight=600, serif=True))
        except Exception:
            self._title_lbl.setFont(qfont("size_h2", weight=TYPOGRAPHY["weight_semibold"]))
        vtext.addWidget(self._title_lbl)
        hdr.addLayout(vtext, stretch=1)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(30, 30)
        self._close_btn.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_medium"]))
        self._close_btn.setFlat(True)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.clicked.connect(self.close)
        hdr.addWidget(self._close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(hdr)

        # Body slot
        self._body_slot = QVBoxLayout()
        self._body_slot.setContentsMargins(0, 0, 0, 0)
        self._body_slot.setSpacing(0)
        root.addLayout(self._body_slot, stretch=1)

        # Footer
        self._footer_sep = QWidget()
        self._footer_sep.setFixedHeight(1)
        root.addWidget(self._footer_sep)

        footer = QHBoxLayout()
        footer.setSpacing(V3_SP["sm"])
        footer.setContentsMargins(0, V3_SP["sm"], 0, 0)
        footer.addStretch()
        root.addLayout(footer)
        self._footer_lay = footer

        _tm().theme_changed.connect(self._apply_scaffold_theme)
        self._apply_scaffold_theme(self._modo)

    def set_title(self, text: str) -> None:
        self._title_lbl.setText(text or "")

    def set_eyebrow(self, text: str) -> None:
        self._eyebrow_lbl.setText(text or "")
        self._eyebrow_lbl.setVisible(bool(text))

    def set_body(self, widget: QWidget) -> None:
        while self._body_slot.count():
            item = self._body_slot.takeAt(0)
            if item.widget() and item.widget() is not widget:
                item.widget().setParent(None)
        self._body_slot.addWidget(widget)

    def add_action(self, label: str, role: str = "secondary", callback=None) -> QPushButton:
        variant = {
            "primary": "primary",
            "secondary": "secondary",
            "ghost": "ghost",
            "danger": "danger",
        }.get(role, "secondary")
        btn = NMButton(label, variant=variant, size="md", modo=self._modo, width=90)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(_NM_CONTROL_HEIGHT)
        btn.setMinimumWidth(90)
        btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
        btn.setProperty("nm_role", role)
        if callback is not None:
            btn.clicked.connect(lambda _=False, cb=callback: cb())
        self._footer_lay.addWidget(btn)
        self._action_buttons.append(btn)
        self._style_scaffold_actions()
        return btn

    def _style_scaffold_actions(self) -> None:
        accent = v3c("accent", self._modo).name()
        danger = v3c("danger", self._modo).name()
        text_m = v3c("text2", self._modo).name()
        text = v3c("text", self._modo).name()
        accent_soft = v3c("accentSoft", self._modo)
        soft = (
            f"rgba({accent_soft.red()},{accent_soft.green()},"
            f"{accent_soft.blue()},{accent_soft.alpha()})"
        )
        for btn in self._action_buttons:
            role = btn.property("nm_role") or "secondary"
            btn.setFont(qfont(_NM_CONTROL_FONT, weight=_NM_CONTROL_WEIGHT))
            if isinstance(btn, NMButton):
                btn.set_variant(
                    "primary"
                    if role == "primary"
                    else "danger"
                    if role == "danger"
                    else "ghost"
                    if role == "ghost"
                    else "secondary"
                )
                btn._apply_theme(self._modo)
                continue
            if role == "primary":
                text_on_acc = v3c("text_on_accent", self._modo).name()
                btn.setStyleSheet(
                    f"QPushButton {{ background: {accent}; color: {text_on_acc}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('cyan', self._modo).name()}; color: {text_on_acc}; }}"
                )
            elif role == "danger":
                text_on_danger = v3c("primary_ink", self._modo).name()
                btn.setStyleSheet(
                    f"QPushButton {{ background: {danger}; color: {text_on_danger}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                )
            elif role == "ghost":
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; color: {text_m}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ color: {text}; background: {soft}; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {soft}; color: {accent}; "
                    f"border: none; border-radius: {_NM_CONTROL_PILL_RADIUS}px; "
                    f"padding: 0 14px; min-height: {_NM_CONTROL_HEIGHT}px; }}"
                    f"QPushButton:hover {{ background: {v3c('tealSoftSolid' if 'dark' in self._modo else 'tealSoft', self._modo).name()}; }}"
                )

    def _apply_scaffold_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        is_dark = "dark" in self._modo
        bg = v3c("surfaceSolid" if is_dark else "surface", self._modo).name()
        ink1 = v3c("ink_primary", self._modo).name()
        ink2 = v3c("ink_secondary", self._modo).name()
        self.setStyleSheet(f"QWidget {{ background: {bg}; }}")
        self._eyebrow_lbl.setStyleSheet(f"color: {ink2}; background: transparent;")
        self._title_lbl.setStyleSheet(f"color: {ink1}; background: transparent;")
        self._close_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {ink2}; "
            f"border: none; border-radius: 12px; padding: 0px; }}"
            f"QPushButton:hover {{ background: {C('bg_hover', self._modo)}; color: {ink1}; }}"
        )
        sep_c = v3c("border", self._modo)
        self._footer_sep.setStyleSheet(
            f"background: rgba({sep_c.red()},{sep_c.green()},{sep_c.blue()},60);"
        )
        self._style_scaffold_actions()

