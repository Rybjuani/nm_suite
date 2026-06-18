"""Pantalla del Hub para textos globales de Suite.

La vista lee exclusivamente `shared.suite_text_catalog`; no importa ni instancia
modulos de paciente y no construye previews de la Suite.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
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
)
from shared.suite_text_catalog import SuiteTextEntry, suite_text_entries, suite_text_sections
from shared.theme import TYPOGRAPHY
from shared.theme_qt import norm_modo, qfont, stylesheet_combobox, stylesheet_scrollarea, v3c, V3_SP


class _TextEntryRow(NMCard):
    def __init__(self, entry: SuiteTextEntry, modo: str, parent=None):
        super().__init__(parent=parent, modo=modo, clickable=False, glow=False)
        self.entry = entry
        self._modo = norm_modo(modo)
        self._build()
        self._apply_row_theme()

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
            self.editor.textChanged.connect(self._sync_counter)
        else:
            self.editor = NMInput("", modo=self._modo, max_length=self.entry.max_chars)
            self.editor.textChanged.connect(self._sync_counter)
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

    def value(self) -> str:
        if isinstance(self.editor, NMTextArea):
            return self.editor.toPlainText()
        return self.editor.text()

    def restore(self) -> None:
        if isinstance(self.editor, NMTextArea):
            self.editor.setPlainText("")
        else:
            self.editor.setText("")
        self._sync_counter()

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

    def apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self._apply_theme(self._modo)
        self._apply_row_theme()
        self._sync_counter()


class TextosGlobalesSuiteView(QWidget):
    def __init__(self, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._modo = norm_modo(modo)
        self._rows: list[_TextEntryRow] = []
        self._build()
        self._apply_theme(self._modo)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], V3_SP["sm"], V3_SP["lg"], 0)
        root.setSpacing(V3_SP["sm"])

        top = QHBoxLayout()
        top.setSpacing(V3_SP["sm"])
        self._title_lbl = QLabel("Textos globales de Suite")
        self._title_lbl.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))
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
        self._list_lay.setSpacing(V3_SP["xs"])
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll, stretch=1)

        for entry in suite_text_entries():
            row = _TextEntryRow(entry, self._modo, parent=self._content)
            row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._rows.append(row)
            self._list_lay.addWidget(row)
        self._list_lay.addStretch(1)

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, V3_SP["xs"])
        bottom.addStretch()
        self._restore_all = NMButtonOutline("Restaurar todos", modo=self._modo, size="sm")
        self._restore_all.clicked.connect(self._restore_all_rows)
        bottom.addWidget(self._restore_all)
        self._save = NMButton("Guardar cambios", modo=self._modo, size="sm", width=150)
        self._save.setEnabled(False)
        bottom.addWidget(self._save)
        root.addLayout(bottom)

        self._apply_filters()

    def _restore_all_rows(self) -> None:
        for row in self._rows:
            row.restore()

    def _apply_filters(self) -> None:
        query = self._search.text().strip() if hasattr(self, "_search") else ""
        section = self._section_filter.currentData() if hasattr(self, "_section_filter") else ""
        visible = 0
        for row in self._rows:
            is_visible = row.matches(query, section)
            row.setVisible(is_visible)
            if is_visible:
                visible += 1
        suffix = "s" if visible != 1 else ""
        self._count.setText(f"{visible} texto{suffix}")

    def _apply_theme(self, modo: str) -> None:
        self._modo = norm_modo(modo)
        self._title_lbl.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; background: transparent;"
        )
        self._section_filter.setStyleSheet(stylesheet_combobox(self._modo))
        self._scroll.setStyleSheet(stylesheet_scrollarea(self._modo))
        for row in self._rows:
            row.apply_theme(self._modo)

    def apply_theme(self, modo: str) -> None:
        self._apply_theme(modo)
