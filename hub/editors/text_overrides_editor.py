"""Editor key/value para overrides text.* en hub_config."""

import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QComboBox,
)

from shared.components_qt import NMButton, NMCard, NMInput, NMToast
from shared.theme import TYPOGRAPHY
from shared.theme_qt import norm_modo, qfont, v3c, V3_SP


TEXT_KEYS = [
    ("text.home.greeting", "Hola", "Saludo principal del Home"),
    ("text.home.subtitle", "¿Cómo estás hoy?", "Subtítulo del Home"),
    ("text.home.modules_eyebrow", "MÓDULOS", "Eyebrow de módulos"),
    ("text.module.animo.title", "Ánimo", "Título módulo ánimo"),
    ("text.module.animo.desc", "Registrá cómo te sentís.", "Descripción ánimo"),
    ("text.module.rutina.title", "Rutina", "Título módulo rutina"),
    ("text.module.rutina.desc", "Completá tu rutina diaria.", "Descripción rutina"),
    ("text.module.timer.title", "Timer", "Título módulo timer"),
    ("text.module.timer.desc", "Enfocate por bloques breves.", "Descripción timer"),
    ("text.module.avisos.title", "Avisos", "Título módulo avisos"),
    ("text.module.avisos.desc", "Recordatorios de apoyo.", "Descripción avisos"),
    ("text.module.tcc.title", "Registro TCC", "Título módulo TCC"),
    ("text.module.tcc.desc", "Revisá pensamientos difíciles.", "Descripción TCC"),
    ("text.common.save", "Guardar", "Texto botón guardar"),
    ("text.common.cancel", "Cancelar", "Texto botón cancelar"),
]


class TextOverridesEditor(QWidget):
    MAX_LEN = 200

    def __init__(self, sb, modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._sb = sb
        self._modo = norm_modo(modo)
        self._patients: list[dict] = []
        self._values: dict[tuple[str, str], str] = {}
        self._build()
        self._load_patients()
        self._load_values()
        self._select_key(0)

    def _build(self):
        self.setWindowTitle("Editor de textos")
        self.resize(1080, 680)
        self.setStyleSheet(f"background: {v3c('bg', self._modo).name()};")
        root = QHBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], V3_SP["lg"], V3_SP["lg"], V3_SP["lg"])
        root.setSpacing(V3_SP["lg"])

        side = NMCard(modo=self._modo, clickable=False)
        side_lay = QVBoxLayout(side)
        side_lay.setContentsMargins(V3_SP["md"], V3_SP["md"], V3_SP["md"], V3_SP["md"])
        title = QLabel("Keys text.*")
        title.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_bold"]))
        title.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        side_lay.addWidget(title)
        self._keys = QListWidget()
        self._keys.setMinimumWidth(280)
        self._keys.setStyleSheet(self._list_style())
        for key, _, _ in TEXT_KEYS:
            self._keys.addItem(key)
        self._keys.currentRowChanged.connect(self._select_key)
        side_lay.addWidget(self._keys)
        root.addWidget(side)

        main = NMCard(modo=self._modo, clickable=False)
        lay = QVBoxLayout(main)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"], V3_SP["lg"], V3_SP["lg"])
        lay.setSpacing(V3_SP["md"])

        self._key_lbl = QLabel("")
        self._key_lbl.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_bold"]))
        self._key_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        lay.addWidget(self._key_lbl)

        self._desc_lbl = QLabel("")
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setStyleSheet(f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        lay.addWidget(self._desc_lbl)

        self._default_lbl = QLabel("")
        self._default_lbl.setWordWrap(True)
        self._default_lbl.setStyleSheet(f"color: {v3c('text2', self._modo).name()}; background: transparent;")
        lay.addWidget(self._default_lbl)

        self._global = NMInput("Override global", modo=self._modo)
        self._global.textChanged.connect(self._update_preview)
        lay.addWidget(self._global)

        patient_row = QHBoxLayout()
        self._patient = QComboBox()
        self._patient.setStyleSheet(self._combo_style())
        self._patient.currentIndexChanged.connect(self._load_patient_value)
        patient_row.addWidget(self._patient)
        self._patient_value = NMInput("Override por paciente", modo=self._modo)
        self._patient_value.textChanged.connect(self._update_preview)
        patient_row.addWidget(self._patient_value, stretch=1)
        lay.addLayout(patient_row)

        preview_title = QLabel("Preview")
        preview_title.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        preview_title.setStyleSheet(f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        lay.addWidget(preview_title)
        self._preview = QLabel("")
        self._preview.setWordWrap(True)
        self._preview.setMinimumHeight(120)
        self._preview.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._preview.setStyleSheet(
            f"color: {v3c('text', self._modo).name()}; "
            f"border: 1px solid {v3c('borderSoft', self._modo).name()}; "
            "border-radius: 12px; padding: 16px; background: transparent;"
        )
        lay.addWidget(self._preview)
        lay.addStretch()

        actions = QHBoxLayout()
        actions.addStretch()
        save = NMButton("Guardar", modo=self._modo, width=120, height=32)
        save.clicked.connect(self._save)
        actions.addWidget(save)
        lay.addLayout(actions)
        root.addWidget(main, stretch=1)

    def _list_style(self) -> str:
        return (
            f"QListWidget {{ background: {v3c('bg', self._modo).name()}; "
            f"color: {v3c('text', self._modo).name()}; "
            f"border: 1px solid {v3c('borderSoft', self._modo).name()}; "
            "border-radius: 10px; padding: 4px; }}"
            f"QListWidget::item:selected {{ background: {v3c('teal', self._modo).name()}; }}"
        )

    def _combo_style(self) -> str:
        return (
            f"QComboBox {{ background: {v3c('bg', self._modo).name()}; "
            f"color: {v3c('text', self._modo).name()}; "
            f"border: 1px solid {v3c('borderStrong', self._modo).name()}; "
            "border-radius: 10px; padding: 6px 10px; min-height: 30px; }}"
        )

    def _load_patients(self):
        self._patient.clear()
        self._patient.addItem("Sin paciente", "")
        if not self._sb:
            return
        try:
            res = self._sb.table("patients").select("patient_id,patient_name").execute()
            self._patients = res.data or []
        except Exception:
            self._patients = []
        for p in self._patients:
            self._patient.addItem(
                p.get("patient_name") or p.get("patient_id", ""),
                p.get("patient_id", ""),
            )

    def _load_values(self):
        self._values = {}
        if not self._sb:
            return
        keys = [k for k, _, _ in TEXT_KEYS]
        scopes = ["global"]
        scopes.extend(f"patient:{p.get('patient_id')}" for p in self._patients if p.get("patient_id"))
        try:
            res = (self._sb.table("hub_config")
                   .select("scope,key,value")
                   .in_("key", keys)
                   .in_("scope", scopes)
                   .execute())
        except Exception:
            return
        for row in res.data or []:
            self._values[(row.get("scope"), row.get("key"))] = self._decode_value(row.get("value"))

    def _decode_value(self, value) -> str:
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
                return str(decoded)
            except Exception:
                return value
        if value is None:
            return ""
        return str(value)

    def _current_key_data(self):
        row = max(0, self._keys.currentRow())
        return TEXT_KEYS[row]

    def _select_key(self, row: int):
        if row < 0:
            return
        key, default, desc = TEXT_KEYS[row]
        self._key_lbl.setText(key)
        self._desc_lbl.setText(desc)
        self._default_lbl.setText(f"Default: {default}")
        self._global.blockSignals(True)
        self._global.setText(self._values.get(("global", key), ""))
        self._global.blockSignals(False)
        self._load_patient_value()
        self._update_preview()

    def _load_patient_value(self):
        if not hasattr(self, "_patient_value"):
            return
        key, _, _ = self._current_key_data()
        pid = self._patient.currentData()
        scope = f"patient:{pid}" if pid else ""
        self._patient_value.blockSignals(True)
        self._patient_value.setText(self._values.get((scope, key), "") if scope else "")
        self._patient_value.setEnabled(bool(pid))
        self._patient_value.blockSignals(False)
        self._update_preview()

    def _valid_text(self, text: str) -> bool:
        return len(text) <= self.MAX_LEN

    def _update_preview(self):
        key, default, _ = self._current_key_data()
        global_text = self._global.text().strip()
        patient_text = self._patient_value.text().strip() if self._patient_value.isEnabled() else ""
        effective = patient_text or global_text or default
        self._preview.setText(
            f"{key}\n\n{effective}\n\n"
            f"Global: {global_text or '(sin override)'}\n"
            f"Paciente: {patient_text or '(sin override)'}"
        )

    def _save(self):
        if not self._sb:
            return
        key, _, _ = self._current_key_data()
        rows = []
        global_text = self._global.text().strip()
        patient_text = self._patient_value.text().strip() if self._patient_value.isEnabled() else ""
        if not self._valid_text(global_text) or not self._valid_text(patient_text):
            NMToast.display(self, "Máximo 200 caracteres.", variant="warning")
            return
        if global_text:
            rows.append({"scope": "global", "key": key, "value": global_text})
        pid = self._patient.currentData()
        if pid and patient_text:
            rows.append({"scope": f"patient:{pid}", "key": key, "value": patient_text})
        if not rows:
            NMToast.display(self, "No hay overrides para guardar.", variant="warning")
            return
        try:
            self._sb.table("hub_config").upsert(rows, on_conflict="scope,key").execute()
            for row in rows:
                self._values[(row["scope"], row["key"])] = row["value"]
            NMToast.display(self, "Textos guardados.", variant="success")
        except Exception as exc:
            NMToast.display(self, str(exc)[:80], variant="error")

