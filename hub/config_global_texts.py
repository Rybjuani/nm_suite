"""Pantalla del Hub para textos globales de Suite.

La vista lee exclusivamente `shared.suite_text_catalog`; no importa ni instancia
modulos de paciente y no construye previews de la Suite.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QEvent, QPoint, QRect, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from shared.components import (
    NMBadge,
    NMButton,
    NMButtonOutline,
    NMCard,
    NMInput,
    NMSearchInput,
    NMTextArea,
    NMToast,
    nm_confirm,
)
from shared.suite_text_catalog import (
    SuiteTextEntry,
    suite_text_by_key,
    suite_text_entries,
    suite_text_sections,
)
from shared.theme import TYPOGRAPHY
from shared.theme_qt import (
    norm_modo,
    paint_screen_frame_bg,
    qcolor_to_rgba_css,
    qfont,
    stylesheet_combobox,
    stylesheet_scrollarea,
    v3_font,
    v3c,
    V3_SP,
)


class _TextEntryRow(NMCard):
    changed = pyqtSignal()

    def __init__(self, entry: SuiteTextEntry, modo: str, parent=None):
        self._dirty = False
        self._interactive_controls_visible = True
        # `padding` explícito: NMCard re-sincroniza los margins del layout a su
        # `_padding_margins` (20px default) vía _sync_layout_padding — pasarlo
        # acá evita que pise el padding canónico 12px 14px de `.tg-row`.
        super().__init__(
            parent=parent,
            modo=modo,
            clickable=False,
            glow=False,
            radius=16,
            padding=(14, 12, 14, 12),
        )
        # `.tg-row` NO es una card elevada (bg surface-2, sin sombra) — el
        # objectName propio la saca del contrato de sombra de cards (VAS) y
        # scopea el QSS de fila sin heredar los estilos #NMCard.
        self.setObjectName("TgRow")
        self.entry = entry
        self._modo = norm_modo(modo)
        self._build()
        self._apply_row_theme()
        self._apply_dirty_shadow()
        QTimer.singleShot(0, self._stabilize_height)

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        # `.tg-row` (L428): padding 12px 14px, gap 16.
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(16)

        # `.tg-label` (L431): columna fija de 150px.
        meta_wrap = QWidget()
        meta_wrap.setStyleSheet("background: transparent; border: none;")
        meta_wrap.setFixedWidth(150)
        meta_col = QVBoxLayout(meta_wrap)
        meta_col.setContentsMargins(0, 0, 0, 0)
        meta_col.setSpacing(2)
        self._section_lbl = QLabel(self.entry.section.upper())  # mockup: eyebrow en mayúsculas
        # `.tg-mod`: 10.5px letter-spacing .1em semibold ink-3.
        _mod_f = qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"])
        _mod_f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.1)
        self._section_lbl.setFont(_mod_f)
        meta_col.addWidget(self._section_lbl)

        self._field_lbl = QLabel(self.entry.field)
        self._field_lbl.setWordWrap(True)
        # `.tg-name`: 13.5px weight 600.
        self._field_lbl.setFont(qfont(13, weight=TYPOGRAPHY["weight_semibold"]))
        meta_col.addWidget(self._field_lbl)
        lay.addWidget(meta_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        # El editor lleva el VALOR actual (override si existe, sino el default),
        # como en el mockup canonico: no hay un label de "valor por defecto" aparte.
        # El valor se setea ANTES de conectar textChanged para no marcar dirty.
        if self.entry.multiline:
            self.editor = NMTextArea("", modo=self._modo, min_height=64, max_length=self.entry.max_chars)
            self.editor.setMaximumHeight(82)
            self.editor.setPlainText(self.entry.default)
            self.editor.textChanged.connect(self._on_text_changed)
        else:
            self.editor = NMInput("", modo=self._modo, max_length=self.entry.max_chars)
            self.editor.setText(self.entry.default)
            self.editor.textChanged.connect(self._on_text_changed)
            # `.input` (L301): padding 12px vertical + texto 13.5 ≈ 39px de
            # alto en `.tg-row` (fila canónica de 65px). El default de NMInput
            # (44, _NM_CONTROL_HEIGHT) es de los forms del Suite.
            self.editor.setFixedHeight(39)
        self.editor.setMinimumWidth(230)
        lay.addWidget(self.editor, stretch=1)

        # Mockup: el contador y "Restaurar" van INLINE (contador a la izquierda
        # del botón), ambos centrados verticalmente en la fila. Antes era un
        # QVBoxLayout que los apilaba (contador arriba, botón abajo) + addStretch,
        # lo que inflaba la altura de la fila (~112px vs ~64px del mockup) y
        # rompía la alineación. HBox compacto.
        side = QHBoxLayout()
        # `.tg-meta` (L435): gap 10; contador 11.5px min-width 48 right-aligned.
        side.setSpacing(10)
        self._count_lbl = QLabel()
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._count_lbl.setFont(qfont("size_caption"))
        self._count_lbl.setMinimumWidth(48)
        side.addWidget(self._count_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        self._restore_btn = NMButtonOutline("Restaurar", modo=self._modo, size="sm")
        self._restore_btn.setFixedHeight(30)
        self._restore_btn.clicked.connect(self.restore)
        side.addWidget(self._restore_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(side)

        self._sync_counter()

    def _stabilize_height(self) -> None:
        self.setMinimumHeight(max(self.minimumHeight(), self.sizeHint().height()))

    def set_interactive_controls_visible(self, visible: bool) -> None:
        visible = bool(visible)
        if visible == self._interactive_controls_visible:
            return
        self._interactive_controls_visible = visible
        # El editor permanece SIEMPRE visible: ahora porta el valor (ya no hay un
        # label de default aparte que lo cubra fuera del viewport). Solo el boton
        # Restaurar se oculta fuera de vista (optimizacion menor).
        self._restore_btn.setVisible(visible)
        if not visible and self._restore_btn.hasFocus():
            self._restore_btn.clearFocus()

    def value(self) -> str:
        if isinstance(self.editor, NMTextArea):
            return self.editor.toPlainText()
        return self.editor.text()

    def set_value(self, value: str) -> None:
        if isinstance(self.editor, NMTextArea):
            self.editor.setPlainText(value or "")
        else:
            self.editor.setText(value or "")
        self._sync_counter()

    def effective_value(self) -> str:
        value = self.value().strip()
        if not value or value == self.entry.default:
            return ""
        return value

    def is_over_limit(self) -> bool:
        return len(self.value()) > self.entry.max_chars

    def restore(self) -> None:
        # Restaurar = volver al default visible en el input (effective_value()
        # devolvera "" porque value == default, asi no se persiste override).
        self.set_value(self.entry.default)
        self.changed.emit()

    def set_dirty(self, dirty: bool) -> None:
        dirty = bool(dirty)
        if dirty == self._dirty:
            return
        self._dirty = dirty
        self._apply_dirty_shadow()
        self.update()

    def matches(self, query: str, section: str) -> bool:
        if section and self.entry.section != section:
            return False
        if not query:
            return True
        haystack = " ".join(
            [self.entry.key, self.entry.section, self.entry.field, self.entry.default]
        ).lower()
        return query.lower() in haystack

    def _sync_counter(self) -> None:
        n = len(self.value())
        self._count_lbl.setText(f"{n} / {self.entry.max_chars}")
        color_key = "danger" if n > self.entry.max_chars else "ink_secondary"
        self._count_lbl.setStyleSheet(
            f"color: {v3c(color_key, self._modo).name()}; background: transparent;"
        )

    def _on_text_changed(self, *_args) -> None:
        self._sync_counter()
        self.changed.emit()

    def _apply_row_theme(self) -> None:
        self._section_lbl.setStyleSheet(
            f"color: {v3c('text3', self._modo).name()}; background: transparent; border: none;"
        )
        self._field_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent; border: none;"
        )

    def _apply_theme(self, modo: str) -> None:
        # El signal de ThemeManager llega directo a NMCard._apply_theme y
        # resetea el QSS → sin este override la fila vuelve al surface default
        # (blanco) en vez del surface-2 de `.tg-row`.
        super()._apply_theme(modo)
        self._modo = norm_modo(modo)
        self._apply_row_theme()
        self._apply_dirty_shadow()

    def _apply_dirty_shadow(self) -> None:
        if not self._dirty:
            # `.tg-row` no tiene sombra en reposo (NMCard sí, shadow_1).
            self.setGraphicsEffect(None)
            self._card_shadow = None
            return
        if self._card_shadow is None:
            self._card_shadow = QGraphicsDropShadowEffect(self)
        glow = v3c("brandSoft", self._modo)
        self._card_shadow.setBlurRadius(10)
        self._card_shadow.setOffset(0, 0)
        self._card_shadow.setColor(glow)
        self.setGraphicsEffect(self._card_shadow)

    def paintEvent(self, event) -> None:
        # `.tg-row` (L428): bg surface-2 + border 1px --line + radius 16 — NO
        # es la superficie de card de NMCard (surface + lift + border card),
        # así que se pinta acá sin delegar en NMCard.paintEvent. Dirty:
        # border brand-line (el halo brand-soft lo pone _apply_dirty_shadow).
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setBrush(QBrush(v3c("surface_2", self._modo)))
        if self._dirty:
            border = v3c("brandLine", self._modo)
        else:
            # Mockup: `border:1px solid var(--line)` sobre surface-2. El render
            # del navegador difumina ese border (subpixel) y queda casi
            # imperceptible; el QPen opaco con el token `line` lo marcaba
            # demasiado. Una versión con alpha baja (~6%) replica el efecto
            # visual del canónico sin tocar el token compartido.
            line = QColor(v3c("line", self._modo))
            line.setAlpha(10 if "light" in self._modo else 16)
            border = line
        p.setPen(QPen(border, 1.0))
        p.drawRoundedRect(rect, 16, 16)
        p.end()

    def apply_theme(self, modo: str) -> None:
        self._apply_theme(norm_modo(modo))
        self._sync_counter()


class _TgSearchInput(NMSearchInput):
    """`NMSearchInput` con bg `surface_3` para el topbar de Textos Globales.

    El mockup canónico muestra el search input del `.tg-top` sobre la zona
    central del radial del `.screen-frame`, donde el composite del navegador
    (radial `.screen-frame` + radial `.screen` apilados) satura `surface_2` a un
    tono intermedio entre `surface_2` y `surface_3`. El `NMSearchInput` base
    pinta `surface_2` opaco, que en esa posición queda claro de más. Esta
    subclase local (sólo Textos Globales) usa `surface_3` para acercarse al
    canónico sin tocar el componente compartido (Pacientes y otras vistas siguen
    usando `surface_2`).
    """

    def __init__(self, placeholder: str = "Buscar...", modo: str | None = None, parent=None):
        super().__init__(placeholder, modo=modo, parent=parent)
        # En el search global compartido se reserva un margen de 3px para el
        # halo de foco; en `.tg-top` el mockup captura el input sin foco y el
        # fill ocupa todo el control. Si dejamos ese margen, se ve el `surface`
        # del topbar como un marco claro y sube el changed_ratio de light.
        self.setContentsMargins(0, 0, 0, 0)

    def paintEvent(self, event) -> None:
        # Mismo dibujo que NMSearchInput.paintEvent pero con bg surface_3.
        from shared.components.buttons import _NM_CONTROL_RADIUS
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = float(_NM_CONTROL_RADIUS)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        bg = v3c("surface_3", self._modo)
        focused = self._edit.hasFocus()
        if focused:
            from PyQt6.QtGui import QPen as _QPen
            from PyQt6.QtCore import Qt as _Qt
            brand_soft = QColor(v3c("primary_soft", self._modo))
            brand_line = QColor(v3c("brandLine", self._modo))
            halo_rect = rect.adjusted(0, 0, 0, 0)
            p.setBrush(QBrush(brand_soft))
            p.setPen(_Qt.PenStyle.NoPen)
            p.drawRoundedRect(halo_rect, r, r)
            p.setBrush(QBrush(bg))
            p.setPen(_QPen(brand_line, 1.0))
            p.drawRoundedRect(rect, r, r)
        else:
            border = v3c("border", self._modo)
            p.setBrush(QBrush(bg))
            p.setPen(QPen(border, 1.0))
            p.drawRoundedRect(rect, r, r)
        p.end()


class _TgTopBar(QWidget):
    """Contenedor del header `.tg-top` con fondo local surface.

    El mockup canónico muestra `.tg-top` sobre el fondo del `.screen-frame` con
    el radial ya fadeado a `surface` en su padding-bottom (la zona entre los
    controles y el border-bottom de la lista). El radial compartido del frame
    no replica ese fade exactamente (diferencia de render Qt vs Chromium), así
    que este widget pinta `surface` localmente en toda su área; los controles
    opacos (search, combo, badge) se dibujan encima y muestran su propio bg
    `surface_2`, mientras que la padding-bottom queda `surface` limpio como en
    el canónico.
    """

    def __init__(self, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QBrush(v3c("surface", self._modo)))
        p.end()


class _TgFoot(QWidget):
    """Footer local de Textos Globales.

    El canónico deja el footer principal en `surface`, pero la banda inmediata
    bajo la lista queda en `surface_2` y lleva el hairline superior. Pintarlo
    localmente evita mover `paint_screen_frame_bg`, que ya está compartido con
    Pacientes.
    """

    def __init__(self, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self.setObjectName("TgFoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QBrush(v3c("surface", self._modo)))
        p.fillRect(QRect(0, 0, self.width(), 12), QBrush(v3c("surface_2", self._modo)))
        line = QColor(v3c("line", self._modo))
        line.setAlpha(18 if "light" in self._modo else 24)
        p.setPen(QPen(line, 1.0))
        p.drawLine(0, 0, self.width(), 0)
        p.end()


class TextosGlobalesSuiteView(QWidget):
    def __init__(self, modo: str = "dark_hybrid", sb=None, parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._rows: list[_TextEntryRow] = []
        self._rows_by_key: dict[str, _TextEntryRow] = {}
        self._catalog_by_key = suite_text_by_key()
        self._original_values: dict[str, str] = {}
        self._sb = sb
        self._loading = False
        self._build()
        self._apply_theme(self._modo)
        self.refresh_overrides(silent=True)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        # Mockup `.screen.tg-body` (L255/1989): padding 24; el foot llega hasta
        # ~12px del borde inferior de la ventana.
        root.setContentsMargins(24, 24, 24, 12)
        root.setSpacing(0)

        top = QHBoxLayout()
        # `.tg-top` (L426): gap 12.
        top.setSpacing(12)
        self._title_lbl = QLabel("Textos globales")
        # Mockup L1991: h2 h-serif 19px 600.
        self._title_lbl.setFont(v3_font(19, weight=TYPOGRAPHY["weight_semibold"], serif=True))
        top.addWidget(self._title_lbl)

        self._search = _TgSearchInput("Buscar textos", modo=self._modo)
        self._search.text_changed.connect(self._apply_filters)
        # `.tg-search`: flex:1, min-width 160; alto canónico ~38
        # (input 9px padding + 15px de línea + borde) vs 44 del control Suite.
        self._search.setMinimumWidth(160)
        self._search.setFixedHeight(38)
        top.addWidget(self._search, stretch=1)

        self._section_filter = QComboBox()
        self._section_filter.setFixedHeight(38)
        # Mockup: `select` con width:auto → ~140px con "Todos los módulos"
        # a 13px (el QSS base de combobox lo inflaba a ~280).
        self._section_filter.setFixedWidth(140)
        self._section_filter.addItem("Todos los módulos", "")
        for section in suite_text_sections():
            self._section_filter.addItem(section, section)
        self._section_filter.currentIndexChanged.connect(self._apply_filters)
        top.addWidget(self._section_filter)

        # Mockup L1999: `badge brand`.
        self._count = NMBadge("0 textos", tone="brand", modo=self._modo)
        top.addWidget(self._count, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Mockup l.383: .tg-top tiene padding-bottom 16px + border-bottom 1px
        # var(--line). Antes el row de búsqueda/filtro estaba pegado a la lista
        # sin separador — el mockup define una línea sutil que ancla el bloque
        # de controles y le da aire a la lista de cards debajo.
        top_wrap = _TgTopBar(modo=self._modo)
        top_wrap.setObjectName("TextosGlobalesTopBar")
        self._top_wrap = top_wrap
        top_wrap_lay = QVBoxLayout(top_wrap)
        top_wrap_lay.setContentsMargins(0, 0, 0, 0)
        top_wrap_lay.setSpacing(0)
        top_wrap_lay.addLayout(top)
        # Padding-bottom 16 + border-bottom 1 (mockup).
        sep = QFrame(top_wrap)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setObjectName("TextosGlobalesSeparator")
        sep.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._top_sep = sep  # para _apply_theme
        top_wrap_lay.addSpacing(16)
        top_wrap_lay.addWidget(sep)
        root.addWidget(top_wrap)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Mockup `.tg-list`: overflow-y auto sin rail visible (el wheel sigue
        # scrolleando; mismo criterio que la lista de PacientesView).
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._list_lay = QVBoxLayout(self._content)
        # `.tg-list` (L427): padding 14px 2px, gap 8.
        self._list_lay.setContentsMargins(2, 14, 2, 14)
        self._list_lay.setSpacing(8)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._content)
        self._scroll.verticalScrollBar().valueChanged.connect(
            lambda _value: self._queue_row_control_visibility_refresh()
        )
        self._scroll.viewport().installEventFilter(self)
        root.addWidget(self._scroll, stretch=1)

        for entry in suite_text_entries():
            row = _TextEntryRow(entry, self._modo, parent=self._content)
            row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row.changed.connect(self._on_row_changed)
            self._rows.append(row)
            self._rows_by_key[entry.key] = row
            self._list_lay.addWidget(row)
        self._list_lay.addStretch(1)

        # `.tg-foot` (L437): border-top 1px --line + padding 14px 2px 4px;
        # status como TEXTO plano 12.5px ink-3 (el mockup no usa pill acá).
        foot_wrap = _TgFoot(modo=self._modo)
        self._foot_wrap = foot_wrap
        bottom = QHBoxLayout(foot_wrap)
        bottom.setContentsMargins(2, 14, 2, 4)
        bottom.setSpacing(10)
        self._pending_status = QLabel("Sin cambios")
        self._pending_status.setFont(qfont("size_caption"))
        self._status_tone = "neutral"
        bottom.addWidget(self._pending_status, alignment=Qt.AlignmentFlag.AlignVCenter)
        bottom.addStretch()
        self._restore_all = NMButtonOutline("Restaurar todos", modo=self._modo, size="sm")
        self._restore_all.clicked.connect(self._restore_all_rows)
        bottom.addWidget(self._restore_all)
        self._save = NMButton("Guardar cambios", modo=self._modo, size="sm", width=150)
        # Mockup `.btn:disabled { opacity:.5 }`: el botón Guardar arranca
        # deshabilitado y el canónico lo muestra con brand al 50% sobre surface
        # (verde sage ~148,170,153). El default de NMButton es 0.65 (tuneado
        # para el mockup "Animo"), que acá da un verde demasiado saturado.
        self._save._disabled_opacity = 0.5
        self._save.setEnabled(False)
        self._save.clicked.connect(self._save_changes)
        bottom.addWidget(self._save)
        root.addWidget(foot_wrap)

        self._apply_filters()
        self._update_pending_state()

    def eventFilter(self, obj, event) -> bool:
        if (
            hasattr(self, "_scroll")
            and obj is self._scroll.viewport()
            and event.type()
            in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.Move)
        ):
            self._queue_row_control_visibility_refresh()
        return super().eventFilter(obj, event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._queue_row_control_visibility_refresh()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._queue_row_control_visibility_refresh()

    def _restore_all_rows(self) -> None:
        nm_confirm(
            self,
            "Restaurar todos",
            "Se quitaran todos los reemplazos globales de texto de Suite.",
            self._restore_all_rows_confirmed,
            confirm_text="Restaurar",
            modo=self._modo,
        )

    def _restore_all_rows_confirmed(self) -> None:
        for row in self._rows:
            row.restore()
        self._update_pending_state()

    def set_supabase_client(self, sb) -> None:
        self._sb = sb
        if not self.has_pending_changes():
            self.refresh_overrides(silent=True)
        self._update_pending_state()

    def has_pending_changes(self) -> bool:
        return self._current_effective_values() != self._original_values

    def refresh_overrides(self, silent: bool = False) -> None:
        if self._sb is None:
            self._update_pending_state()
            return
        try:
            query = self._sb.table("hub_config").select("key,value").eq("scope", "global")
            if hasattr(query, "like"):
                query = query.like("key", "text.%")
            res = query.execute()
        except Exception as exc:
            if not silent:
                NMToast.display(
                    self.window(),
                    f"No se pudieron cargar los textos: {str(exc)[:80]}",
                    variant="error",
                )
            return

        loaded: dict[str, str] = {}
        for item in res.data or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "")
            entry = self._catalog_by_key.get(key)
            if entry is None:
                continue
            value = self._coerce_text_value(item.get("value")).strip()
            if value and value != entry.default:
                loaded[key] = value
        self._set_loaded_values(loaded)

    def _apply_filters(self) -> None:
        query = self._search.text().strip() if hasattr(self, "_search") else ""
        section = self._section_filter.currentData() if hasattr(self, "_section_filter") else ""
        visible = 0
        for row in self._rows:
            is_visible = row.matches(query, section)
            row.setVisible(is_visible)
            if not is_visible:
                row.set_interactive_controls_visible(False)
            if is_visible:
                visible += 1
        suffix = "s" if visible != 1 else ""
        self._count.setText(f"{visible} texto{suffix}")
        self._queue_row_control_visibility_refresh()

    def _queue_row_control_visibility_refresh(self) -> None:
        if hasattr(self, "_scroll"):
            QTimer.singleShot(0, self._refresh_row_control_visibility)

    def _refresh_row_control_visibility(self) -> None:
        if not hasattr(self, "_scroll") or not hasattr(self, "_content"):
            return
        viewport = self._scroll.viewport()
        view_rect = QRect(viewport.rect())
        view_rect.moveTopLeft(self._content.mapFrom(viewport, QPoint(0, 0)))
        top = view_rect.top()
        bottom = view_rect.bottom()
        for row in self._rows:
            row_rect = row.geometry()
            row_fully_inside = row_rect.top() >= top and row_rect.bottom() <= bottom
            row.set_interactive_controls_visible(row.isVisible() and row_fully_inside)

    def _current_effective_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for row in self._rows:
            value = row.effective_value()
            if value:
                values[row.entry.key] = value
        return values

    def _set_loaded_values(self, values: dict[str, str]) -> None:
        self._loading = True
        try:
            for row in self._rows:
                row.set_value(values.get(row.entry.key) or row.entry.default)
            self._original_values = {
                key: value
                for key, value in values.items()
                if key in self._catalog_by_key and value
            }
        finally:
            self._loading = False
        self._update_pending_state()

    def _on_row_changed(self) -> None:
        if self._loading:
            return
        self._update_pending_state()

    def _invalid_rows(self) -> list[_TextEntryRow]:
        return [row for row in self._rows if row.is_over_limit()]

    def _update_pending_state(self) -> None:
        if not hasattr(self, "_save"):
            return
        for row in self._rows:
            original = self._original_values.get(row.entry.key, "")
            row.set_dirty(row.effective_value() != original)
        invalid = bool(self._invalid_rows())
        pending = self.has_pending_changes()
        if invalid:
            self._set_status("Revisar limites", "danger")
        elif pending:
            self._set_status("Cambios pendientes", "warning")
        else:
            self._set_status("Sin cambios", "neutral")
        self._save.setEnabled(pending and not invalid)

    def _set_status(self, text: str, tone: str) -> None:
        self._status_tone = tone
        self._pending_status.setText(text)
        color_key = {"danger": "danger", "warning": "amber"}.get(tone, "text3")
        self._pending_status.setStyleSheet(
            f"color: {v3c(color_key, self._modo).name()}; background: transparent;"
        )

    def _save_changes(self) -> None:
        invalid = self._invalid_rows()
        if invalid:
            NMToast.display(
                self.window(),
                "Hay textos que superan el limite permitido.",
                variant="error",
            )
            self._update_pending_state()
            return
        if self._sb is None:
            NMToast.display(
                self.window(),
                "No hay conexion con Supabase para guardar los textos.",
                variant="error",
            )
            return

        desired = self._current_effective_values()
        changed_keys = set(self._original_values) | set(desired)
        delete_keys = sorted(key for key in changed_keys if key not in desired)
        upsert_rows = [
            {"scope": "global", "key": key, "value": desired[key]}
            for key in sorted(desired)
            if key in self._catalog_by_key
        ]
        try:
            for key in delete_keys:
                if key not in self._catalog_by_key:
                    continue
                (
                    self._sb.table("hub_config")
                    .delete()
                    .eq("scope", "global")
                    .eq("key", key)
                    .execute()
                )
            if upsert_rows:
                (
                    self._sb.table("hub_config")
                    .upsert(upsert_rows, on_conflict="scope,key")
                    .execute()
                )
        except Exception as exc:
            NMToast.display(
                self.window(),
                f"No se pudieron guardar los textos: {str(exc)[:80]}",
                variant="error",
            )
            return

        self._original_values = desired
        self._update_pending_state()
        NMToast.display(self.window(), "Textos globales guardados.", variant="success")

    @staticmethod
    def _coerce_text_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        return ""

    def paintEvent(self, event) -> None:
        # Mockup `.window` + `.screen-frame`: surface + radial surface-2 del
        # tope + anillo de borde/esquinas del tramo de contenido.
        p = QPainter(self)
        paint_screen_frame_bg(p, QRectF(self.rect()), self._modo)
        p.end()

    def _apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        # Select del mockup: texto 13px, padding 8/12 (el control base Suite
        # usa 14px + padding ancho y no entra en los ~140px canónicos).
        self._section_filter.setStyleSheet(
            stylesheet_combobox(self._modo)
            + " QComboBox { font-size: 13px; padding: 6px 12px; min-height: 20px; }"
        )
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        # Separador bajo la fila de controles: color v3c('line', modo) — el
        # mismo token que el resto de las cards/listas usan como border.
        line_css = qcolor_to_rgba_css(v3c("line", self._modo))
        if hasattr(self, "_top_sep"):
            self._top_sep.setStyleSheet(
                f"QFrame#TextosGlobalesSeparator {{ background: {line_css}; border: none; }}"
            )
        if hasattr(self, "_foot_wrap"):
            self._foot_wrap.setStyleSheet("")
            self._foot_wrap.apply_theme(self._modo)
        if hasattr(self, "_pending_status"):
            self._set_status(self._pending_status.text(), self._status_tone)
        if hasattr(self, "_top_wrap"):
            self._top_wrap.apply_theme(self._modo)
        for row in self._rows:
            row.apply_theme(self._modo)
        self.update()

    def apply_theme(self, modo: str) -> None:
        self._apply_theme(modo)
