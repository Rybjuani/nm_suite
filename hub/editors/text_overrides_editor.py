"""
hub/editors/text_overrides_editor.py — Vista de Personalización de Textos (TextosView)
Permite customizar copys de la Suite globalmente o por paciente con límites de longitud y preview visual.
"""

import json
import logging

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QComboBox,
    QSplitter,
    QSizePolicy,
)

from shared.adaptive_layout_qt import BP_AUX_PANEL
from shared.components import (
    NMButton,
    NMButtonOutline,
    NMCard,
    NMInput,
    NMToast,
    NMBadge,
    NMDivider,
    nm_confirm,
)
from shared.theme import TYPOGRAPHY
from shared.theme_qt import (
    norm_modo,
    qfont,
    qfont_mono,
    qcolor_to_rgba_css,
    stylesheet_combobox,
    _clinical_scrollbar_qss,
    v3c,
    V3_SP,
    v3_font,
    eyebrow_font,
)

_log = logging.getLogger(__name__)

# Reconstruido con las claves t() reales cableadas en el Suite, límites de caracteres y categoría.
TEXT_KEYS = [
    # (key, default, desc, max_len, category)
    ("text.home.greeting_morning", "Buenos días,", "Saludo matutino en el Home", 20, "Home"),
    ("text.home.greeting_afternoon", "Buenas tardes,", "Saludo vespertino en el Home", 20, "Home"),
    ("text.home.greeting_evening", "Buenas noches,", "Saludo nocturno en el Home", 20, "Home"),
    ("text.home.brand", "NeuroMood Suite", "Nombre de la aplicación en la Titlebar", 30, "Home"),
    ("text.home.wellbeing_eyebrow", "Bienestar hoy", "Etiqueta de bienestar en Home", 20, "Home"),
    ("text.home.wellbeing_default", "Registrá tu ánimo\npara comenzar", "Texto de estado vacío de bienestar", 60, "Home"),
    ("text.home.next_session_eyebrow", "Próxima sesión", "Etiqueta de próxima sesión", 20, "Home"),
    ("text.home.next_session_default", "Sin sesión\nprogramada", "Texto de estado vacío de sesión", 60, "Home"),
    ("text.home.sync_idle", "Listo", "Etiqueta de sincronización en reposo", 16, "Home"),
    
    ("text.module.animo.note_placeholder", "¿Qué influyó en tu estado hoy?", "Placeholder de notas", 100, "Termómetro Emocional"),
    ("text.module.animo.save_btn", "Guardar registro", "Texto del botón guardar", 30, "Termómetro Emocional"),

    ("text.module.respiracion.guide_title", "Bio-guía", "Título de la bio-guía", 20, "Guía de Respiración"),
    ("text.module.respiracion.empty_state", "Sin sesiones.", "Texto de historial vacío", 60, "Guía de Respiración"),
    
    ("text.module.registro.tip_eyebrow", "Tip terapéutico", "Etiqueta de tip terapéutico", 20, "Registro TCC"),
    ("text.module.registro.empty_state", "Aún no hay registros previos.", "Texto de historial vacío", 60, "Registro TCC"),
    
    ("text.module.rutina.eyebrow", "Progreso del día", "Etiqueta de progreso", 20, "Checklist de Rutina"),
    ("text.module.rutina.no_tasks_title", "Sin tareas configuradas", "Título sin tareas", 40, "Checklist de Rutina"),
    ("text.module.rutina.no_tasks_desc", "Tu rutina se va construyendo paso a paso.", "Ayuda sin tareas", 150, "Checklist de Rutina"),
    
    ("text.module.actividades.categories_eyebrow", "Categorías", "Etiqueta de categorías", 20, "Activación Conductual"),
    ("text.module.actividades.categories_help", "Elegí una familia de actividades", "Ayuda de filtros", 60, "Activación Conductual"),
    ("text.module.actividades.filter_all", "Todas", "Filtro todas", 16, "Activación Conductual"),
    ("text.module.actividades.category_autocuidado", "Autocuidado", "Familia autocuidado", 18, "Activación Conductual"),
    ("text.module.actividades.category_fisica", "Física", "Familia física", 18, "Activación Conductual"),
    ("text.module.actividades.category_cognitiva", "Cognitiva", "Familia cognitiva", 18, "Activación Conductual"),
    ("text.module.actividades.category_placer", "Placer", "Familia placer", 18, "Activación Conductual"),
    ("text.module.actividades.category_social", "Social", "Familia social", 18, "Activación Conductual"),
    ("text.module.actividades.category_maestria", "Maestría", "Familia maestría", 18, "Activación Conductual"),
    
    ("text.module.timer.eyebrow", "Timer de enfoque", "Etiqueta del timer", 20, "Temporizador"),
    ("text.module.timer.empty_state", "Sin sesiones todavía hoy.", "Texto de historial vacío", 60, "Temporizador"),
    
    ("text.module.avisos.eyebrow", "Recordatorios", "Etiqueta de recordatorios", 20, "Recordatorios de Bienestar"),
    
    ("text.module.evolucion.eyebrow", "Evolución anímica", "Etiqueta de evolución", 20, "Evolución Anímica"),
    ("text.module.evolucion.weekly_title", "Variación del Humor Semanal", "Título de vista semanal", 40, "Evolución Anímica"),
    ("text.module.evolucion.monthly_title", "Variación del Humor Mensual (30 Días)", "Título de vista mensual", 40, "Evolución Anímica"),
]


class TextOverridesEditor(QWidget):
    """Editor de textos GLOBALES de la Suite (reorganización owner v1.0).

    Un solo scope: "global" (aplica a todos los pacientes). El scope por
    paciente fue ELIMINADO de la UI — lo por-paciente del Plan terapéutico es
    el asignado de recordatorios/temporizador/rutina/activación, no textos.

    Args:
        fixed_category: si se pasa, el editor queda FIJO a ese módulo
            (categoría de TEXT_KEYS) y no muestra el filtro de módulos —
            es el modo que usan los 8 botones de Personalización.
    """

    def __init__(
        self,
        sb,
        modo: str = "dark_hybrid",
        parent=None,
        fixed_category: str | None = None,
    ):
        super().__init__(parent)
        self._sb = sb
        self._modo = norm_modo(modo)
        self._fixed_category = fixed_category
        self._values: dict[tuple[str, str], str] = {}

        self._setup_ui()
        self._load_values()
        self._filter_keys()

    def _setup_ui(self):
        # Layout principal de la vista
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Contenedor de contenido
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_lay = QVBoxLayout(content)
        # M3 premium: aire alrededor del contenido sin robar ancho a las columnas.
        content_lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["lg"])
        content_lay.setSpacing(0)

        # Splitter. M3 premium: handle algo más ancho = separación entre las 3
        # columnas (antes pegadas como cajas) sin truncar el texto.
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(V3_SP["md"])
        content_lay.addWidget(self._splitter)
        main_lay.addWidget(content)

        # 1. Biblioteca (Left Panel)
        side = NMCard(modo=self._modo, clickable=False)
        side.setMinimumWidth(240)
        side.setMaximumWidth(320)
        side_lay = QVBoxLayout(side)
        side_lay.setContentsMargins(V3_SP["md"], V3_SP["md"], V3_SP["md"], V3_SP["md"])
        side_lay.setSpacing(V3_SP["md"])

        title = QLabel(self._fixed_category or "Textos de la Suite")
        title.setFont(qfont("size_body", weight=TYPOGRAPHY["weight_semibold"]))
        title.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        side_lay.addWidget(title)

        # Filtro de módulo — solo en modo navegable; con fixed_category el
        # módulo ya está elegido desde Personalización (un botón por módulo).
        self._module_filter = None
        if not self._fixed_category:
            self._module_filter = QComboBox()
            self._module_filter.setStyleSheet(stylesheet_combobox(self._modo))
            self._module_filter.addItem("Todos los módulos", "Todos")
            categories = sorted(list({k[4] for k in TEXT_KEYS}))
            for cat in categories:
                self._module_filter.addItem(cat, cat)
            self._module_filter.currentIndexChanged.connect(self._filter_keys)
            side_lay.addWidget(self._module_filter)

        self._keys = QListWidget()
        self._keys.setStyleSheet(self._list_style())
        # Elide a la derecha en vez de scroll horizontal duro: las claves largas
        # ("Nombre de la aplicación en la Titlebar…") se recortan con … en lugar
        # de mostrar una barra de scroll horizontal que se ve "herramienta interna".
        self._keys.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._keys.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._keys.currentRowChanged.connect(self._on_key_selection_changed)
        side_lay.addWidget(self._keys)
        self._splitter.addWidget(side)

        # 2. Editor Panel (Center)
        self._editor_card = NMCard(modo=self._modo, clickable=False)
        lay = QVBoxLayout(self._editor_card)
        lay.setContentsMargins(V3_SP["lg"], V3_SP["md"], V3_SP["lg"], V3_SP["md"])
        lay.setSpacing(V3_SP["md"])

        eyebrow = QLabel("Personalizar texto")
        eyebrow.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        eyebrow.setStyleSheet(
            f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;"
        )
        lay.addWidget(eyebrow)

        self._key_lbl = QLabel("")
        self._key_lbl.setFont(qfont("size_h3", weight=TYPOGRAPHY["weight_semibold"]))
        self._key_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()}; background: transparent;")
        lay.addWidget(self._key_lbl)

        self._desc_lbl = QLabel("")
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;")
        lay.addWidget(self._desc_lbl)

        self._default_lbl = QLabel("")
        self._default_lbl.setWordWrap(True)
        self._default_lbl.setStyleSheet(f"color: {v3c('text2', self._modo).name()}; background: transparent;")
        lay.addWidget(self._default_lbl)

        # Texto general (único scope editable)
        global_header = QHBoxLayout()
        global_lbl = QLabel("Texto general (todos los pacientes)")
        global_lbl.setFont(qfont("size_caption", weight=TYPOGRAPHY["weight_semibold"]))
        global_lbl.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;")
        global_header.addWidget(global_lbl)

        self._global_count = QLabel("0/200")
        self._global_count.setFont(qfont_mono(10))
        self._global_count.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;")
        global_header.addWidget(self._global_count, alignment=Qt.AlignmentFlag.AlignRight)
        lay.addLayout(global_header)

        self._global = NMInput("Texto para todos los pacientes…", modo=self._modo)
        self._global.textChanged.connect(self._on_global_text_changed)
        lay.addWidget(self._global)

        # Acciones alineadas en una sola fila al pie del formulario: Restablecer
        # (secundario, izquierda) y Guardar cambios (primario, derecha). En
        # Personalización el preview va oculto → la columna del editor es ancha y
        # la fila entra cómoda; antes los botones iban apilados a la derecha y
        # "flotaban" sobre el vacío. Alturas igualadas (32) para una base limpia.
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(V3_SP["sm"])
        self._reset_btn = NMButtonOutline("Restablecer por defecto", modo=self._modo, size="sm")
        self._reset_btn.setFixedHeight(32)
        self._reset_btn.clicked.connect(self._ask_reset)
        btn_lay.addWidget(self._reset_btn)
        btn_lay.addStretch()
        self._save_btn = NMButton("Guardar cambios", modo=self._modo, width=150, height=32)
        self._save_btn.clicked.connect(self._save_changes)
        btn_lay.addWidget(self._save_btn)
        lay.addLayout(btn_lay)
        lay.addStretch()

        self._splitter.addWidget(self._editor_card)

        # 3. Preview Panel (Right)
        self._preview_card = NMCard(modo=self._modo, clickable=False, glow=False)
        self._preview_card.setMinimumWidth(300)
        self._preview_card.setMaximumWidth(400)
        preview_lay = QVBoxLayout(self._preview_card)
        preview_lay.setContentsMargins(V3_SP["lg"], V3_SP["lg"], V3_SP["lg"], V3_SP["lg"])
        preview_lay.setSpacing(V3_SP["md"])

        p_title = QLabel("Vista previa Suite")
        p_title.setFont(eyebrow_font())
        p_title.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;")
        preview_lay.addWidget(p_title)

        # Card container simulating the Suite UI element
        self._suite_element_container = QWidget()
        self._suite_element_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._suite_element_layout = QVBoxLayout(self._suite_element_container)
        self._suite_element_layout.setContentsMargins(0, 0, 0, 0)
        self._suite_element_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_lay.addWidget(self._suite_element_container)

        self._splitter.addWidget(self._preview_card)

        # Splitter sizing ratio
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 2)
        self._splitter.setStretchFactor(2, 2)

        # Preview responsive: a 960×600 las 3 columnas quedaban comprimidas. El
        # preview es auxiliar → solo se muestra cuando hay ancho suficiente
        # (≥BP_AUX_PANEL). En modo angosto: biblioteca + editor (2 zonas).
        self._preview_card.setVisible(False)

    def resizeEvent(self, e):  # noqa: N802 (Qt override)
        super().resizeEvent(e)
        self._apply_preview_responsive(e.size().width())

    def _apply_preview_responsive(self, width: int) -> None:
        card = getattr(self, "_preview_card", None)
        if card is None:
            return
        show = width >= BP_AUX_PANEL
        if card.isVisible() != show:
            card.setVisible(show)

    def _list_style(self) -> str:
        # Selección suavizada: antes un teal pleno con texto blanco (muy fuerte,
        # "grita" en dark). Ahora un fondo accent translúcido con el texto del
        # tema, más un realce de hover sutil.
        sel_bg = qcolor_to_rgba_css(v3c("accentSoft", self._modo))
        hover_bg = qcolor_to_rgba_css(v3c("borderSoft", self._modo))
        return (
            f"QListWidget {{ background: {v3c('bg', self._modo).name()}; "
            f"color: {v3c('text', self._modo).name()}; "
            f"border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
            "border-radius: 8px; padding: 4px; outline: none; }}"
            "QListWidget::item { padding: 5px 6px; border-radius: 6px; }"
            f"QListWidget::item:hover {{ background: {hover_bg}; }}"
            f"QListWidget::item:selected {{ background: {sel_bg}; "
            f"color: {v3c('text', self._modo).name()}; }}"
            + _clinical_scrollbar_qss(self._modo)
        )

    def _filter_keys(self):
        from PyQt6.QtWidgets import QListWidgetItem

        if self._fixed_category:
            selected_cat = self._fixed_category
        else:
            selected_cat = self._module_filter.currentData()
        self._keys.clear()

        self._filtered_keys = []
        for item in TEXT_KEYS:
            if selected_cat == "Todos" or item[4] == selected_cat:
                self._filtered_keys.append(item)
                lw_item = QListWidgetItem(item[2])
                # El nombre completo en tooltip: la lista elide con "…" los
                # nombres largos (informe owner v1.0, Textos).
                lw_item.setToolTip(f"{item[2]} · {item[4]}")
                self._keys.addItem(lw_item)

        if self._filtered_keys:
            self._keys.setCurrentRow(0)

    def _load_values(self):
        self._values = {}
        if not self._sb:
            return
        keys = [item[0] for item in TEXT_KEYS]
        scopes = ["global"]
        try:
            res = (
                self._sb.table("hub_config")
                .select("scope,key,value")
                .in_("key", keys)
                .in_("scope", scopes)
                .execute()
            )
            for row in res.data or []:
                val = row.get("value")
                if isinstance(val, str):
                    try:
                        val = json.loads(val)
                    except Exception:
                        pass
                self._values[(row["scope"], row["key"])] = str(val or "")
        except Exception:
            _log.exception("Error al cargar valores de remote_config")

    def _get_selected_key_info(self):
        row = self._keys.currentRow()
        if 0 <= row < len(self._filtered_keys):
            return self._filtered_keys[row]
        return None

    def _on_key_selection_changed(self, row: int):
        info = self._get_selected_key_info()
        if not info:
            return
        key, default, desc, max_len, category = info
        self._key_lbl.setText(desc)
        self._key_lbl.setToolTip(f"Clave técnica: {key}")
        self._desc_lbl.setText(f"Categoría: {category}")
        self._default_lbl.setText(f"Valor predeterminado: {default}")

        # Block signals to update without triggering textChanged events
        self._global.blockSignals(True)
        global_val = self._values.get(("global", key), "")
        # Tope físico por clave (auditoría v1.0): pegar texto masivo
        # superaba la validación visual y rompía el responsive de la Suite.
        self._global.setMaxLength(int(max_len))
        self._global.setText(global_val)
        self._global_count.setText(f"{len(global_val)}/{max_len}")
        self._global.blockSignals(False)

        self._update_preview()

    def _on_global_text_changed(self, val: str):
        info = self._get_selected_key_info()
        if not info:
            return
        max_len = info[3]
        self._global_count.setText(f"{len(val)}/{max_len}")
        
        if len(val) > max_len:
            self._global_count.setStyleSheet(
                f"color: {v3c('danger', self._modo).name()}; background: transparent;"
            )
            self._save_btn.setEnabled(False)
        else:
            self._global_count.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()}; background: transparent;")
            self._save_btn.setEnabled(True)

        self._update_preview()

    def _update_preview(self):
        # Clear preview container
        while self._suite_element_layout.count():
            item = self._suite_element_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        info = self._get_selected_key_info()
        if not info:
            return
        key, default, desc, max_len, category = info

        # Valor activo: texto general editado, o el default.
        active_val = self._global.text() or default

        # Render preview mock based on key
        preview_widget = QWidget()
        preview_widget.setStyleSheet("background: transparent;")
        pl = QVBoxLayout(preview_widget)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if "greeting" in key:
            # greeting mock
            mock_lbl = QLabel(f'{active_val} Laura Gómez')
            mock_lbl.setFont(v3_font("size_display_m", weight=500, serif=True))
            mock_lbl.setWordWrap(True)
            mock_lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
            pl.addWidget(mock_lbl)
        elif "brand" in key:
            # brand mockbar
            mock_bar = QFrame()
            mock_bar.setFrameShape(QFrame.Shape.StyledPanel)
            # 6.2: borderSoft rgba — preservar alpha.
            mock_bar.setStyleSheet(
                f"background: {v3c('surface', self._modo).name()}; "
                f"border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
                "border-radius: 6px;"
            )
            mock_bar.setFixedSize(260, 40)
            mbl = QHBoxLayout(mock_bar)
            mbl.setContentsMargins(8, 0, 8, 0)
            lbl = QLabel(active_val)
            lbl.setFont(qfont("size_small", weight=TYPOGRAPHY["weight_semibold"]))
            lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
            mbl.addWidget(lbl)
            mbl.addStretch()
            # Mini-dots del mock de titlebar — neutros (F3): el semáforo
            # rojo/amarillo/verde era jerga macOS con hex web fuera de paleta.
            _dot_css = qcolor_to_rgba_css(v3c("borderStrong", self._modo))
            for _ in range(3):
                dot = QFrame()
                dot.setFixedSize(8, 8)
                dot.setStyleSheet(f"background: {_dot_css}; border-radius: 4px;")
                mbl.addWidget(dot)
            pl.addWidget(mock_bar)
        elif "save_btn" in key:
            # save button mock
            btn = NMButton(active_val, modo=self._modo, variant="gradient", width=140, height=32)
            pl.addWidget(btn)
        elif "eyebrow" in key:
            # eyebrow mock
            lbl = QLabel(active_val)
            lbl.setFont(eyebrow_font())
            lbl.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()};")
            pl.addWidget(lbl)
        elif "placeholder" in key:
            # placeholder text area mock
            textarea = QFrame()
            # 6.2: borderSoft rgba — preservar alpha.
            textarea.setStyleSheet(
                f"background: {v3c('bg', self._modo).name()}; "
                f"border: 1px solid {qcolor_to_rgba_css(v3c('borderSoft', self._modo))}; "
                "border-radius: 8px;"
            )
            textarea.setFixedSize(260, 80)
            tl = QVBoxLayout(textarea)
            tl.setContentsMargins(8, 8, 8, 8)
            lbl = QLabel(active_val)
            lbl.setFont(qfont("size_small"))
            lbl.setStyleSheet(f"color: {v3c('textMuted', self._modo).name()};")
            lbl.setWordWrap(True)
            tl.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignTop)
            pl.addWidget(textarea)
        else:
            # generic card/label mock
            card = NMCard(modo=self._modo, clickable=False)
            card.setFixedSize(260, 90)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 10, 12, 10)
            
            lbl_type = QLabel(category)
            lbl_type.setFont(eyebrow_font())
            lbl_type.setStyleSheet(f"color: {v3c('ink_secondary', self._modo).name()};")
            cl.addWidget(lbl_type)
            
            lbl = QLabel(active_val)
            lbl.setFont(qfont("size_small"))
            lbl.setStyleSheet(f"color: {v3c('text', self._modo).name()};")
            lbl.setWordWrap(True)
            cl.addWidget(lbl)
            pl.addWidget(card)

        self._suite_element_layout.addWidget(preview_widget)

    def _save_changes(self):
        info = self._get_selected_key_info()
        if not info or not self._sb:
            return
        key = info[0]
        try:
            global_val = self._global.text()
            if global_val:
                self._upsert_value("global", key, global_val)
                self._values[("global", key)] = global_val
            else:
                self._delete_value("global", key)
                self._values.pop(("global", key), None)

            NMToast.display(self.window(), "Textos guardados correctamente", variant="success")
            self._update_preview()
        except Exception as e:
            _log.exception("Error al guardar textos")
            NMToast.display(self.window(), f"Error al guardar: {str(e)[:50]}", variant="error")

    def _ask_reset(self):
        info = self._get_selected_key_info()
        if not info:
            return
        nm_confirm(
            self,
            "Restablecer por defecto",
            f"Se quitará el texto general para «{info[2]}». La Suite volverá a "
            f"mostrar el valor por defecto: “{info[1]}”.",
            self._reset_current_key,
            modo=self._modo,
        )

    def _reset_current_key(self):
        """Borra el override global de la clave activa y vuelve al default."""
        info = self._get_selected_key_info()
        if not info:
            return
        key, default, _desc, max_len, _cat = info
        try:
            if self._sb:
                self._delete_value("global", key)
            self._values.pop(("global", key), None)
            self._global.blockSignals(True)
            self._global.setText("")
            self._global_count.setText(f"0/{max_len}")
            self._global.blockSignals(False)
            self._update_preview()
            NMToast.display(
                self.window(), "Texto restablecido al valor por defecto.", variant="success"
            )
        except Exception as e:
            _log.exception("Error al restablecer texto")
            NMToast.display(self.window(), f"Error: {str(e)[:50]}", variant="error")

    def _upsert_value(self, scope: str, key: str, value: str):
        payload = {
            "scope": scope,
            "key": key,
            "value": json.dumps(value),
        }
        self._sb.table("hub_config").upsert(payload, on_conflict="scope,key").execute()

    def _delete_value(self, scope: str, key: str):
        self._sb.table("hub_config").delete().eq("scope", scope).eq("key", key).execute()

    def apply_theme(self, modo: str):
        self._modo = norm_modo(modo)
        if self._module_filter is not None:
            self._module_filter.setStyleSheet(stylesheet_combobox(self._modo))
        self._keys.setStyleSheet(self._list_style())
        self._update_preview()
