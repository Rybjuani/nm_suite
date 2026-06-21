"""Pantalla del Hub para textos globales de Suite.

La vista lee exclusivamente `shared.suite_text_catalog`; no importa ni instancia
modulos de paciente y no construye previews de la Suite.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QEvent, QPoint, QRect, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen
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
from shared.theme_qt import norm_modo, qfont, stylesheet_combobox, stylesheet_scrollarea, v3_font, v3c, V3_SP


class _TextEntryRow(NMCard):
    changed = pyqtSignal()

    def __init__(self, entry: SuiteTextEntry, modo: str, parent=None):
        self._dirty = False
        self._interactive_controls_visible = True
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False, radius=16)
        self.entry = entry
        self._modo = norm_modo(modo)
        self._build()
        self._apply_row_theme()
        self._apply_dirty_shadow()
        QTimer.singleShot(0, self._stabilize_height)

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(V3_SP["md"], V3_SP["sm"], V3_SP["md"], V3_SP["sm"])
        lay.setSpacing(V3_SP["md"])

        meta_col = QVBoxLayout()
        meta_col.setSpacing(2)
        self._section_lbl = QLabel(self.entry.section)
        self._section_lbl.setFont(qfont("size_caption_xs", weight=TYPOGRAPHY["weight_semibold"]))
        meta_col.addWidget(self._section_lbl)

        self._field_lbl = QLabel(self.entry.field)
        self._field_lbl.setWordWrap(True)
        self._field_lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
        meta_col.addWidget(self._field_lbl)
        lay.addLayout(meta_col, stretch=1)

        self._default_lbl = QLabel(self.entry.default)
        self._default_lbl.setWordWrap(True)
        self._default_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._default_lbl.setFont(qfont("size_caption"))
        self._default_lbl.setMinimumWidth(210)
        self._default_lbl.setMaximumWidth(300)
        lay.addWidget(self._default_lbl, stretch=2)

        if self.entry.multiline:
            self.editor = NMTextArea("", modo=self._modo, min_height=64, max_length=self.entry.max_chars)
            self.editor.setMaximumHeight(82)
            self.editor.textChanged.connect(self._on_text_changed)
        else:
            self.editor = NMInput("", modo=self._modo, max_length=self.entry.max_chars)
            self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setMinimumWidth(230)
        lay.addWidget(self.editor, stretch=2)

        side = QVBoxLayout()
        side.setSpacing(V3_SP["xs"])
        self._count_lbl = QLabel()
        self._count_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._count_lbl.setFont(qfont("size_caption_xs"))
        side.addWidget(self._count_lbl)

        self._restore_btn = NMButtonOutline("Restaurar", modo=self._modo, size="sm")
        self._restore_btn.setFixedHeight(30)
        self._restore_btn.clicked.connect(self.restore)
        side.addWidget(self._restore_btn)
        side.addStretch()
        lay.addLayout(side)

        self._sync_counter()

    def _stabilize_height(self) -> None:
        self.setMinimumHeight(max(self.minimumHeight(), self.sizeHint().height()))

    def set_interactive_controls_visible(self, visible: bool) -> None:
        visible = bool(visible)
        if visible == self._interactive_controls_visible:
            return
        self._interactive_controls_visible = visible
        self.editor.setVisible(visible)
        self._restore_btn.setVisible(visible)
        if not visible:
            if self.editor.hasFocus():
                self.editor.clearFocus()
            if self._restore_btn.hasFocus():
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
        self.set_value("")
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
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        self._field_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._default_lbl.setStyleSheet(
            f"color: {v3c('text2', self._modo).name()}; background: transparent;"
        )

    def _apply_dirty_shadow(self) -> None:
        if not self._dirty:
            self._apply_card_shadow()
            return
        if self._card_shadow is None:
            self._card_shadow = QGraphicsDropShadowEffect(self)
        glow = v3c("brandSoft", self._modo)
        self._card_shadow.setBlurRadius(10)
        self._card_shadow.setOffset(0, 0)
        self._card_shadow.setColor(glow)
        self.setGraphicsEffect(self._card_shadow)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._dirty:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(v3c("brandLine", self._modo), 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 16, 16)
        p.end()

    def apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self._apply_theme(self._modo)
        self._apply_row_theme()
        self._apply_dirty_shadow()
        self._sync_counter()


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
        root.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], 0)
        root.setSpacing(V3_SP["sm"])

        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        self._title_lbl = QLabel("Textos globales de Suite")
        self._title_lbl.setFont(v3_font("size_heading_l", weight=TYPOGRAPHY["weight_semibold"], serif=True))
        top.addWidget(self._title_lbl)

        self._search = NMSearchInput("Buscar textos", modo=self._modo)
        self._search.text_changed.connect(self._apply_filters)
        self._search.setMinimumWidth(220)
        top.addWidget(self._search, stretch=1)

        self._section_filter = QComboBox()
        self._section_filter.setMinimumHeight(32)
        self._section_filter.setMinimumWidth(210)
        self._section_filter.addItem("Todos los módulos", "")
        for section in suite_text_sections():
            self._section_filter.addItem(section, section)
        self._section_filter.currentIndexChanged.connect(self._apply_filters)
        top.addWidget(self._section_filter)

        self._count = NMBadge("0 textos", tone="info", modo=self._modo)
        top.addWidget(self._count, alignment=Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(top)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._list_lay = QVBoxLayout(self._content)
        self._list_lay.setContentsMargins(0, 0, 0, V3_SP["sm"])
        self._list_lay.setSpacing(V3_SP["md"] + 2)
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

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, V3_SP["xs"])
        self._pending_badge = NMBadge("Sin cambios", tone="neutral", modo=self._modo)
        bottom.addWidget(self._pending_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        bottom.addStretch()
        self._restore_all = NMButtonOutline("Restaurar todos", modo=self._modo, size="sm")
        self._restore_all.clicked.connect(self._restore_all_rows)
        bottom.addWidget(self._restore_all)
        self._save = NMButton("Guardar cambios", modo=self._modo, size="sm", width=150)
        self._save.setEnabled(False)
        self._save.clicked.connect(self._save_changes)
        bottom.addWidget(self._save)
        root.addLayout(bottom)

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
                row.set_value(values.get(row.entry.key, ""))
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
            self._pending_badge.setText("Revisar limites")
            self._pending_badge.set_tone("danger")
        elif pending:
            self._pending_badge.setText("Cambios pendientes")
            self._pending_badge.set_tone("warning")
        else:
            self._pending_badge.setText("Sin cambios")
            self._pending_badge.set_tone("neutral")
        self._save.setEnabled(pending and not invalid)

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

    def _apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._section_filter.setStyleSheet(stylesheet_combobox(self._modo))
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        if hasattr(self, "_pending_badge"):
            self._pending_badge._apply_theme(self._modo)
        for row in self._rows:
            row.apply_theme(self._modo)

    def apply_theme(self, modo: str) -> None:
        self._apply_theme(modo)
