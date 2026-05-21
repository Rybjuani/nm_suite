import sys

def replace_in_file(filepath, replacements):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
            else:
                print(f"Target not found: {old[:50]}...")
                
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

replacements = [
    (
        '''def responsive_columns(available_width: int, min_card_width: int = 280,
                       max_columns: int = 3) -> int:
    """Devuelve el número óptimo de columnas según ancho disponible."""
    cols = max(1, min(max_columns, available_width // min_card_width))
    return cols''',
        '''# Breakpoints documentados (ancho de viewport)
BREAKPOINTS = {"xs": 640, "sm": 960, "md": 1280, "lg": 1600}

def responsive_columns(available_width: int, min_card_width: int = 280,
                       max_columns: int = 3) -> int:
    """Devuelve el número óptimo de columnas según ancho disponible.
    
    Breakpoints documentados:
        xs < 640   → 1 columna (móvil / ventana muy pequeña)
        sm < 960   → hasta 2 columnas
        md < 1280  → hasta 3 columnas
        lg < 1600  → hasta max_columns
        xl >= 1600 → max_columns
    """
    if available_width < BREAKPOINTS["xs"]:
        return 1
    if available_width < BREAKPOINTS["sm"]:
        return min(2, max_columns)
    cols = max(1, min(max_columns, available_width // min_card_width))
    return cols

def responsive_breakpoint(width: int) -> str:
    """Devuelve el nombre del breakpoint activo para el ancho dado."""
    if width < BREAKPOINTS["xs"]:
        return "xs"
    if width < BREAKPOINTS["sm"]:
        return "sm"
    if width < BREAKPOINTS["md"]:
        return "md"
    if width < BREAKPOINTS["lg"]:
        return "lg"
    return "xl"'''
    ),
    (
        '''        eff_height = height if height is not None else _NM_BUTTON_HEIGHT[self._size]
        self.setFixedHeight(eff_height)
        if width:
            self.setMinimumWidth(width)
        self.setFont(qfont(_NM_BUTTON_FONT[self._size],
                           weight=TYPOGRAPHY["weight_semibold"]))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)''',
        '''        eff_height = height if height is not None else _NM_BUTTON_HEIGHT[self._size]
        self.setFixedHeight(eff_height)
        if width:
            self.setMinimumWidth(width)
        self.setFont(qfont(_NM_BUTTON_FONT[self._size],
                           weight=TYPOGRAPHY["weight_semibold"]))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setAccessibleName(text)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)'''
    ),
    (
        '''        self.setFont(qfont(_NM_BUTTON_FONT[self._size],
                           weight=TYPOGRAPHY["weight_medium"]))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setMinimumHeight(_NM_BUTTON_HEIGHT[self._size])
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))

        _tm().theme_changed.connect(self._apply_theme)''',
        '''        self.setFont(qfont(_NM_BUTTON_FONT[self._size],
                           weight=TYPOGRAPHY["weight_medium"]))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFlat(True)
        self.setMinimumHeight(_NM_BUTTON_HEIGHT[self._size])
        self.setAccessibleName(text)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setStyleSheet(focus_ring_stylesheet(self._modo))

        _tm().theme_changed.connect(self._apply_theme)

    def setText(self, text: str):
        super().setText(text)
        self.setAccessibleName(text)
        self.update()'''
    ),
    (
        '''        self._modo = norm_modo(modo or _tm().modo)
        self._focus_glow: QGraphicsDropShadowEffect | None = None
        self.setPlaceholderText(placeholder)
        self.setFont(qfont("size_body"))
        self.setMinimumHeight(LAYOUT["min_touch_target"])''',
        '''        self._modo = norm_modo(modo or _tm().modo)
        self._focus_glow: QGraphicsDropShadowEffect | None = None
        self.setPlaceholderText(placeholder)
        self.setAccessibleName(placeholder)
        self.setFont(qfont("size_body"))
        self.setMinimumHeight(LAYOUT["min_touch_target"])'''
    ),
    (
        '''        self.setCheckable(True)
        self.setFixedSize(self._track_w, self._track_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)''',
        '''        self.setCheckable(True)
        self.setFixedSize(self._track_w, self._track_h)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName("Toggle")'''
    ),
    (
        '''        for label, value in choices:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=True)
            btn.setFixedHeight(30)
            btn.setMinimumWidth(72)
            btn.clicked.connect(lambda checked=False, v=value, b=btn: self._select(v, b))
            layout.addWidget(btn)
            self._btns[value] = btn''',
        '''        for label, value in choices:
            btn = NMButtonOutline(label, modo=self._modo, toggleable=True)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(72)
            btn.clicked.connect(lambda checked=False, v=value, b=btn: self._select(v, b))
            layout.addWidget(btn)
            self._btns[value] = btn'''
    ),
    (
        '''        self._checked = checked
        self._strike_on_check = strike_on_check
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QHBoxLayout(self)''',
        '''        self._checked = checked
        self._strike_on_check = strike_on_check
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(44)
        lay = QHBoxLayout(self)'''
    ),
    (
        '''        self._label = QLabel(text)
        self._label.setFont(qfont("size_small"))
        self._label.setWordWrap(True)
        lay.addWidget(self._label, stretch=1)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)''',
        '''        self._label = QLabel(text)
        self._label.setFont(qfont("size_small"))
        self._label.setWordWrap(True)
        lay.addWidget(self._label, stretch=1)
        self.setAccessibleName(text)
        self._apply_theme(self._modo)
        _tm().theme_changed.connect(self._apply_theme)'''
    ),
    (
        '''        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(40)''',
        '''        self._modo = norm_modo(modo or _tm().modo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(44)
        self.setAccessibleName("Buscar")'''
    ),
    (
        '''        self._modo = norm_modo(modo or _tm().modo)
        self.setPlaceholderText(placeholder or "")
        self.setMinimumHeight(min_height)
        self.setAcceptRichText(False)''',
        '''        self._modo = norm_modo(modo or _tm().modo)
        self.setPlaceholderText(placeholder or "")
        self.setAccessibleName(placeholder or "Text area")
        self.setMinimumHeight(min_height)
        self.setAcceptRichText(False)'''
    )
]

replace_in_file("shared/components_qt.py", replacements)

