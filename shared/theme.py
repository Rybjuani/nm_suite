COLORS = {
    "dark": {
        "bg_primary":       "#0B1928",
        "bg_secondary":     "#0D2137",
        "bg_surface":       "#112740",
        "bg_input":         "#112740",
        "bg_hover":         "#1A3050",
        "bg_list_item":     "#1A3050",

        "accent":           "#1EC8D4",
        "accent_hover":     "#2EDDE9",
        "accent_subtle":    "#0F3040",

        "text_primary":     "#FFFFFF",
        "text_secondary":   "#E8EEF4",
        "text_tertiary":    "#8BA4BE",
        "text_on_accent":   "#FFFFFF",

        "border":           "#1A3050",
        "border_accent":    "#1EC8D4",
        "border_focus":     "#1EC8D4",

        "success":          "#22D47E",
        "warning":          "#F0A500",
        "error":            "#E8505B",
        "info":             "#1EC8D4",

        "progress_track":   "#1A3050",
        "progress_fill":    "#1EC8D4",
    },

    "light": {
        # Fondos — paleta Notion light mode
        "bg_primary":       "#E3E2DE",   # Notion Cream — body + header
        "bg_secondary":     "#D8D7D3",   # barra inferior — un tono más oscuro
        "bg_surface":       "#F7F7F5",   # cards — Notion Light Gray (más claro que body)
        "bg_input":         "#FFFFFF",   # inputs blancos — más elevados
        "bg_hover":         "#C0BFBC",   # hover en items de lista
        "bg_list_item":     "#FFFFFF",   # filas de historial — elevadas sobre surface

        # Interactivos — charcoal suave (no negro puro)
        "accent":           "#404040",   # gris carbón — más pastel que #191919
        "accent_hover":     "#5C5C5C",   # más claro en hover → interactividad visible
        "accent_subtle":    "#DDDCDA",

        # Texto — escala Notion
        "text_primary":     "#191919",   # Notion Text Default
        "text_secondary":   "#4A4A4A",
        "text_tertiary":    "#6B6B6B",   # Notion Dark Gray
        "text_on_accent":   "#FFFFFF",

        # Bordes — Notion Mid Gray (#CBCAC7), visibles sin ser agresivos
        "border":           "#CBCAC7",
        "border_accent":    "#404040",
        "border_focus":     "#404040",

        # Estados funcionales — colores Notion de contenido
        "success":          "#5A9E82",   # verde pastel
        "warning":          "#C87C40",   # ámbar pastel
        "error":            "#D46868",   # rosa-rojo pastel
        "info":             "#4A7EA5",   # azul petróleo pastel

        "progress_track":   "#CBCAC7",
        "progress_fill":    "#404040",
    }
}

TYPOGRAPHY = {
    "font_family":      "Segoe UI",
    "font_fallback":    "Arial",
    "size_h1":          28,
    "size_h2":          22,
    "size_h3":          17,
    "size_body":        14,
    "size_small":       12,
    "size_caption":     11,
    "weight_regular":   "normal",
    "weight_medium":    "bold",
}

LAYOUT = {
    "padding_container":    24,
    "padding_card":         20,
    "padding_button_x":     24,
    "padding_button_y":     10,
    "gap_cards":            16,
    "gap_elements":         12,
    "radius_button":        8,
    "radius_card":          12,
    "radius_modal":         16,
    "radius_input":         8,
    "radius_badge":         20,
    "border_width":         1,
    "border_card_width":    2,
    "border_accent_width":  2,
    "border_button_width":  2,
    "header_height":        68,
    "min_touch_target":     44,
}
