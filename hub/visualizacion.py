"""visualizacion.py — Gráficos matplotlib integrados en el Hub."""
import customtkinter as ctk
from shared.theme import COLORS, TYPOGRAPHY, get_gradient
from shared.components import interpolate_color

# Inicializar backend matplotlib una sola vez al importar el módulo
try:
    import matplotlib
    matplotlib.use("TkAgg")
    _MATPLOTLIB_OK = True
except Exception:
    _MATPLOTLIB_OK = False


def _colores_matplotlib(modo: str) -> dict:
    c = COLORS.get(modo, COLORS["dark_hybrid"])
    grad = get_gradient(modo)
    return {
        "bg":       c["bg_surface"],
        "fg":       c["bg_primary"],
        "text":     c["text_secondary"],
        "grid":     c["border"],
        "line_a":   grad[0],
        "line_b":   grad[1],
        "fill_a":   grad[0] + "40",   # alpha hex
        "bar":      grad[0],
        "bar2":     grad[1],
    }


def _aplicar_estilo(ax, fig, modo: str):
    col = _colores_matplotlib(modo)
    fig.patch.set_facecolor(col["fg"])
    ax.set_facecolor(col["bg"])
    ax.tick_params(colors=col["text"], labelsize=8)
    ax.spines[:].set_color(col["grid"])
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)
    ax.yaxis.label.set_color(col["text"])
    ax.xaxis.label.set_color(col["text"])
    ax.title.set_color(col["text"])


def grafico_animo(parent, registros: list, modo: str = "dark_hybrid") -> ctk.CTkFrame:
    """Línea de ánimo con área rellena teal. registros: list[{fecha, puntaje}]"""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import numpy as np
    except ImportError:
        return _placeholder(parent, "matplotlib no instalado", modo)

    col = _colores_matplotlib(modo)
    c = COLORS.get(modo, COLORS["dark_hybrid"])

    fechas = [r.get("fecha", "")[:10] for r in registros]
    puntajes = [r.get("puntaje", 0) for r in registros]

    if not puntajes:
        return _placeholder(parent, "Sin registros de ánimo", modo)

    fig, ax = plt.subplots(figsize=(5.5, 2.8), dpi=96)
    _aplicar_estilo(ax, fig, modo)

    x = range(len(puntajes))
    ax.plot(list(x), puntajes, color=col["line_a"], linewidth=2, zorder=3)
    ax.fill_between(list(x), puntajes, alpha=0.18, color=col["line_a"])
    ax.set_ylim(0, 10.5)
    ax.set_yticks(range(0, 11, 2))

    # Mostrar solo cada N fechas para no sobrecargar
    step = max(1, len(fechas) // 6)
    ax.set_xticks(list(range(0, len(fechas), step)))
    ax.set_xticklabels([fechas[i] for i in range(0, len(fechas), step)],
                       rotation=30, ha="right", fontsize=7)

    if puntajes:
        prom = round(sum(puntajes) / len(puntajes), 1)
        ax.axhline(prom, color=col["line_b"], linewidth=1, linestyle="--", alpha=0.6)
        ax.text(len(puntajes) - 1, prom + 0.3, f"prom {prom}",
                color=col["line_b"], fontsize=7, ha="right")

    ax.set_title("Evolución del ánimo", fontsize=9, pad=6)
    fig.tight_layout(pad=0.8)

    frame = ctk.CTkFrame(parent, fg_color=c["bg_surface"], corner_radius=10)
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
    plt.close(fig)
    return frame


def grafico_rutina(parent, semanas: list, modo: str = "dark_hybrid") -> ctk.CTkFrame:
    """Barras de adherencia semanal. semanas: list[{semana, completadas, total}]"""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    except ImportError:
        return _placeholder(parent, "matplotlib no instalado", modo)

    col = _colores_matplotlib(modo)
    c = COLORS.get(modo, COLORS["dark_hybrid"])

    if not semanas:
        return _placeholder(parent, "Sin datos de rutina", modo)

    labels = [s.get("semana", "")[-5:] for s in semanas]
    completadas = [s.get("completadas", 0) for s in semanas]
    totales = [s.get("total", 1) or 1 for s in semanas]
    pcts = [c_ / t * 100 for c_, t in zip(completadas, totales)]

    fig, ax = plt.subplots(figsize=(5.5, 2.8), dpi=96)
    _aplicar_estilo(ax, fig, modo)

    bars = ax.bar(labels, pcts, color=col["bar"], width=0.6, zorder=3)
    ax.set_ylim(0, 110)
    ax.set_ylabel("%", fontsize=8)
    ax.set_title("Adherencia rutina semanal", fontsize=9, pad=6)
    ax.tick_params(axis="x", labelsize=7, rotation=30)

    for bar, pct in zip(bars, pcts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                f"{pct:.0f}%", ha="center", va="bottom",
                fontsize=7, color=col["text"])

    fig.tight_layout(pad=0.8)

    frame = ctk.CTkFrame(parent, fg_color=c["bg_surface"], corner_radius=10)
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
    plt.close(fig)
    return frame


def grafico_sesiones(parent, sesiones: list, titulo: str,
                     modo: str = "dark_hybrid") -> ctk.CTkFrame:
    """Línea de sesiones (respiración o timer). sesiones: list[{fecha}]"""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from collections import Counter
    except ImportError:
        return _placeholder(parent, "matplotlib no instalado", modo)

    col = _colores_matplotlib(modo)
    c = COLORS.get(modo, COLORS["dark_hybrid"])

    if not sesiones:
        return _placeholder(parent, f"Sin datos de {titulo.lower()}", modo)

    from collections import Counter
    conteo = Counter(r.get("fecha", "")[:10] for r in sesiones)
    fechas = sorted(conteo.keys())
    valores = [conteo[f] for f in fechas]

    fig, ax = plt.subplots(figsize=(5.5, 2.4), dpi=96)
    _aplicar_estilo(ax, fig, modo)

    ax.plot(range(len(fechas)), valores, color=col["line_b"], linewidth=2, marker="o",
            markersize=4, zorder=3)
    ax.fill_between(range(len(fechas)), valores, alpha=0.15, color=col["line_b"])

    step = max(1, len(fechas) // 5)
    ax.set_xticks(list(range(0, len(fechas), step)))
    ax.set_xticklabels([fechas[i] for i in range(0, len(fechas), step)],
                       rotation=30, ha="right", fontsize=7)
    ax.set_yticks(range(0, max(valores) + 2))
    ax.set_title(titulo, fontsize=9, pad=6)
    fig.tight_layout(pad=0.8)

    frame = ctk.CTkFrame(parent, fg_color=c["bg_surface"], corner_radius=10)
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)
    plt.close(fig)
    return frame


def _placeholder(parent, msg: str, modo: str) -> ctk.CTkFrame:
    c = COLORS.get(modo, COLORS["dark_hybrid"])
    frame = ctk.CTkFrame(parent, fg_color=c["bg_surface"], corner_radius=10)
    ctk.CTkLabel(
        frame, text=msg,
        font=(TYPOGRAPHY["font_family"], TYPOGRAPHY["size_small"]),
        text_color=c["text_tertiary"],
    ).pack(expand=True, pady=20)
    return frame
