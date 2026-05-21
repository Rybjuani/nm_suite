"""Editor visual de plantillas TCC para el Hub."""

import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QTabWidget, QTextEdit, QComboBox,
)

from shared.components_qt import (
    NMButton, NMButtonOutline, NMCard, NMInput, NMToast, NMTCCStepper,
)
from shared.theme import TYPOGRAPHY
from shared.theme_qt import norm_modo, qfont, stylesheet_textedit, v3c, V3_SP


DEFAULT_TEMPLATE = {
    "steps": ["Situación", "Emoción", "Pensamiento", "Respuesta"],
    "emotions": [
        "Ansiedad", "Tristeza", "Enojo", "Miedo",
        "Culpa", "Vergüenza", "Soledad", "Otro",
    ],
    "distortions": [
        "Catastrofización", "Lectura mental", "Filtro mental", "Etiquetado",
        "Debería", "Personalización", "Sobregeneralización",
        "Descalificación", "Pensamiento dicotómico", "Magnificación",
    ],
    "tip": "Buscá una respuesta alternativa más equilibrada y amable.",
}


class TCCTemplateEditor(QWidget):
    def __init__(self, sb, patient_id: str = "", modo: str = "dark_hybrid", parent=None):
        super().__init__(parent)
        self._sb = sb
        self._pid = patient_id
        self._modo = norm_modo(modo)
        self._templates: list[dict] = []
        self._current_id = None
        self._build()
        self._load_templates()

    def _build(self):
        self.setWindowTitle("Editor de plantillas TCC")
        self.resize(1120, 720)
        self.setStyleSheet(f"background: {v3c('bg', self._modo).name()};")

        root = QHBoxLayout(self)
        root.setContentsMargins(V3_SP["lg"], V3_SP["lg"], V3_SP["lg"], V3_SP["lg"])
        root.setSpacing(V3_SP["lg"])

        side = NMCard(modo=self._modo, clickable=False)
        side_lay = QVBoxLayout(side)
        side_lay.setContentsMargins(V3_SP["md"], V3_SP["md"], V3_SP["md"], V3_SP["md"])
        title = QLabel("Plantillas")
        title.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_bold"]))
        title.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        side_lay.addWidget(title)
        self._list = QListWidget()
        self._list.setMinimumWidth(240)
        self._list.setStyleSheet(self._list_style())
        self._list.currentRowChanged.connect(self._select_template)
        side_lay.addWidget(self._list)
        root.addWidget(side)

        main = NMCard(modo=self._modo, clickable=False)
        main_lay = QVBoxLayout(main)
        main_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"], V3_SP["lg"], V3_SP["lg"])
        main_lay.setSpacing(V3_SP["md"])

        meta = QHBoxLayout()
        self._name = NMInput("Nombre de plantilla", modo=self._modo)
        meta.addWidget(self._name, stretch=2)
        self._scope = QComboBox()
        scopes = ["global"]
        if self._pid:
            scopes.append(f"patient:{self._pid}")
        self._scope.addItems(scopes)
        self._scope.setStyleSheet(self._combo_style())
        meta.addWidget(self._scope)
        main_lay.addLayout(meta)

        content = QHBoxLayout()
        self._tabs = QTabWidget()
        self._tabs.currentChanged.connect(lambda _: self._refresh_preview())
        self._tabs.addTab(self._list_tab("steps", "Paso"), "Pasos (4)")
        self._tabs.addTab(self._list_tab("emotions", "Emoción"), "Emociones (8 default)")
        self._tabs.addTab(self._list_tab("distortions", "Distorsión"), "Distorsiones (10 default)")
        self._tabs.addTab(self._tip_tab(), "Tip terapéutico")
        content.addWidget(self._tabs, stretch=2)

        preview = NMCard(modo=self._modo, clickable=False, glow=False)
        preview_lay = QVBoxLayout(preview)
        preview_lay.setContentsMargins(V3_SP["md"], V3_SP["md"], V3_SP["md"], V3_SP["md"])
        lbl = QLabel("Preview")
        lbl.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        lbl.setStyleSheet(f"color: {v3c('text3', self._modo).name()}; background: transparent;")
        preview_lay.addWidget(lbl)
        self._stepper_holder = QVBoxLayout()
        preview_lay.addLayout(self._stepper_holder)
        self._preview_text = QLabel("")
        self._preview_text.setWordWrap(True)
        self._preview_text.setStyleSheet(f"color: {v3c('text2', self._modo).name()}; background: transparent;")
        preview_lay.addWidget(self._preview_text)
        preview_lay.addStretch()
        content.addWidget(preview, stretch=1)
        main_lay.addLayout(content, stretch=1)

        actions = QHBoxLayout()
        actions.addStretch()
        btn_defaults = NMButtonOutline("Restaurar default", modo=self._modo)
        btn_defaults.setFixedSize(140, 32)
        btn_defaults.clicked.connect(self._restore_default)
        actions.addWidget(btn_defaults)
        btn_assign = NMButton("Asignar a paciente", modo=self._modo, width=150, height=32)
        btn_assign.clicked.connect(self._assign_patient)
        actions.addWidget(btn_assign)
        btn_save = NMButton("Guardar", modo=self._modo, width=110, height=32)
        btn_save.clicked.connect(self._save)
        actions.addWidget(btn_save)
        main_lay.addLayout(actions)

        root.addWidget(main, stretch=1)
        self._restore_default()

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

    def _list_tab(self, key: str, label: str) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(tab)
        lw = QListWidget()
        lw.setObjectName(key)
        lw.setStyleSheet(self._list_style())
        lw.currentItemChanged.connect(lambda *_: self._load_item_to_input(key))
        lay.addWidget(lw, stretch=1)
        row = QHBoxLayout()
        inp = NMInput(label, modo=self._modo)
        setattr(self, f"_{key}_input", inp)
        setattr(self, f"_{key}_list", lw)
        row.addWidget(inp, stretch=1)
        add = NMButton("Agregar/Actualizar", modo=self._modo, width=150, height=32)
        add.clicked.connect(lambda: self._upsert_item(key))
        row.addWidget(add)
        remove = NMButtonOutline("Quitar", modo=self._modo)
        remove.setFixedSize(70, 32)
        remove.clicked.connect(lambda: self._remove_item(key))
        row.addWidget(remove)
        lay.addLayout(row)
        return tab

    def _tip_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(tab)
        self._tip = QTextEdit()
        self._tip.setPlaceholderText("Tip terapéutico")
        self._tip.setStyleSheet(stylesheet_textedit(self._modo))
        self._tip.textChanged.connect(self._refresh_preview)
        lay.addWidget(self._tip)
        return tab

    def _load_templates(self):
        self._templates = []
        self._list.clear()
        if not self._sb:
            return
        scopes = ["global"]
        if self._pid:
            scopes.append(f"patient:{self._pid}")
        try:
            res = (self._sb.table("tcc_templates")
                   .select("id,scope,name,payload,version")
                   .in_("scope", scopes)
                   .order("scope")
                   .execute())
            self._templates = res.data or []
        except Exception as exc:
            NMToast.display(self, str(exc)[:80], variant="error")
            return
        for tmpl in self._templates:
            self._list.addItem(f"{tmpl.get('name', 'Sin nombre')} ({tmpl.get('scope', 'global')})")

    def _select_template(self, row: int):
        if row < 0 or row >= len(self._templates):
            return
        tmpl = self._templates[row]
        self._current_id = tmpl.get("id")
        self._name.setText(tmpl.get("name") or "")
        scope_idx = self._scope.findText(tmpl.get("scope") or "global")
        self._scope.setCurrentIndex(max(0, scope_idx))
        payload = self._decode_payload(tmpl.get("payload"))
        self._set_payload(payload)

    def _decode_payload(self, payload) -> dict:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        if not isinstance(payload, dict):
            payload = {}
        return {**DEFAULT_TEMPLATE, **payload}

    def _set_payload(self, payload: dict):
        for key in ("steps", "emotions", "distortions"):
            lw: QListWidget = getattr(self, f"_{key}_list")
            lw.clear()
            for item in payload.get(key, []):
                lw.addItem(str(item))
        self._tip.setPlainText(str(payload.get("tip", "")))
        self._refresh_preview()

    def _payload(self) -> dict:
        data = {}
        for key in ("steps", "emotions", "distortions"):
            lw: QListWidget = getattr(self, f"_{key}_list")
            data[key] = [lw.item(i).text() for i in range(lw.count())]
        data["tip"] = self._tip.toPlainText().strip()
        return data

    def _load_item_to_input(self, key: str):
        lw: QListWidget = getattr(self, f"_{key}_list")
        inp: NMInput = getattr(self, f"_{key}_input")
        item = lw.currentItem()
        inp.setText(item.text() if item else "")

    def _upsert_item(self, key: str):
        lw: QListWidget = getattr(self, f"_{key}_list")
        inp: NMInput = getattr(self, f"_{key}_input")
        text = inp.text().strip()
        if not text:
            return
        item = lw.currentItem()
        if item:
            item.setText(text)
        else:
            lw.addItem(text)
        inp.clear()
        lw.clearSelection()
        self._refresh_preview()

    def _remove_item(self, key: str):
        lw: QListWidget = getattr(self, f"_{key}_list")
        row = lw.currentRow()
        if row >= 0:
            lw.takeItem(row)
            self._refresh_preview()

    def _restore_default(self):
        self._current_id = None
        self._name.setText("TCC base")
        self._scope.setCurrentIndex(0)
        self._set_payload(DEFAULT_TEMPLATE)

    def _refresh_preview(self):
        if not all(hasattr(self, f"_{key}_list")
                   for key in ("steps", "emotions", "distortions")):
            return
        if not hasattr(self, "_stepper_holder"):
            return
        steps = self._payload().get("steps") or DEFAULT_TEMPLATE["steps"]
        while self._stepper_holder.count():
            item = self._stepper_holder.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        stepper = NMTCCStepper(steps, modo=self._modo)
        stepper.set_step(min(1, max(0, len(steps) - 1)))
        self._stepper_holder.addWidget(stepper)
        payload = self._payload()
        self._preview_text.setText(
            f"{len(payload['steps'])} pasos · "
            f"{len(payload['emotions'])} emociones · "
            f"{len(payload['distortions'])} distorsiones\n\n"
            f"Tip: {payload['tip'] or 'Sin tip'}"
        )

    def _row_payload(self, scope: str | None = None) -> dict:
        return {
            "scope": scope or self._scope.currentText(),
            "name": self._name.text().strip() or "TCC base",
            "payload": json.dumps(self._payload(), ensure_ascii=False),
            "version": 1,
        }

    def _save(self):
        if not self._sb:
            return
        payload = self._row_payload()
        try:
            if self._current_id:
                payload["id"] = self._current_id
                self._sb.table("tcc_templates").upsert(payload).execute()
            else:
                self._sb.table("tcc_templates").upsert(
                    payload, on_conflict="scope,name"
                ).execute()
            self._load_templates()
            NMToast.display(self, "Plantilla TCC guardada.", variant="success")
        except Exception as exc:
            NMToast.display(self, str(exc)[:80], variant="error")

    def _assign_patient(self):
        if not self._sb or not self._pid:
            NMToast.display(self, "Seleccioná un paciente.", variant="warning")
            return
        try:
            self._sb.table("tcc_templates").upsert(
                self._row_payload(scope=f"patient:{self._pid}"),
                on_conflict="scope,name",
            ).execute()
            self._load_templates()
            NMToast.display(self, "Plantilla asignada al paciente.", variant="success")
        except Exception as exc:
            NMToast.display(self, str(exc)[:80], variant="error")
