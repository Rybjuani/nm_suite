"""exportar.py — Exportación de registros del paciente a PDF."""
import os
import threading
from datetime import datetime


def exportar_pdf(paciente_nombre: str, paciente_id: str, datos: dict,
                 on_done=None, on_error=None):
    """Genera el PDF en un hilo daemon. Llama on_done(ruta) o on_error(msg)."""
    def _run():
        try:
            ruta = _generar(paciente_nombre, paciente_id, datos)
            if on_done:
                on_done(ruta)
        except Exception as e:
            if on_error:
                on_error(str(e))

    threading.Thread(target=_run, daemon=True).start()


def _generar(nombre: str, pid: str, datos: dict) -> str:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
    except ImportError:
        raise RuntimeError("reportlab no está instalado.")

    nombre_seg = "".join(c for c in nombre if c.isalnum() or c in " _-")
    fecha_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"NeuroMood_{nombre_seg}_{fecha_str}.pdf"
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(downloads):
        downloads = os.path.expanduser("~")
    filepath = os.path.join(downloads, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    AC = "#00d4c8"
    titulo_st = ParagraphStyle("titulo", parent=styles["Title"],
                               fontSize=18, textColor=rl_colors.HexColor(AC))
    h2_st = ParagraphStyle("h2", parent=styles["Heading2"],
                           fontSize=12, textColor=rl_colors.HexColor(AC), spaceAfter=4)
    normal_st = styles["Normal"]
    caption_st = ParagraphStyle("cap", parent=styles["Normal"], fontSize=8,
                                textColor=rl_colors.HexColor("#555555"))

    story = []
    story.append(Paragraph(f"NeuroMood — Registro de {nombre}", titulo_st))
    story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", caption_st))
    story.append(HRFlowable(width="100%", thickness=1,
                            color=rl_colors.HexColor(AC), spaceAfter=12))

    def _seccion(titulo, filas, encabezados, row_fn, prom_txt=None):
        story.append(Paragraph(titulo, h2_st))
        if prom_txt:
            story.append(Paragraph(prom_txt, normal_st))
            story.append(Spacer(1, 4))
        if not filas:
            story.append(Paragraph("Sin registros.", caption_st))
            story.append(Spacer(1, 10))
            return
        tabla_data = [encabezados] + [row_fn(r) for r in filas]
        col_w = (A4[0] - 4*cm) / len(encabezados)
        t = Table(tabla_data, colWidths=[col_w] * len(encabezados), repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), rl_colors.HexColor(AC)),
            ("TEXTCOLOR",     (0, 0), (-1, 0), rl_colors.white),
            ("FONTSIZE",      (0, 0), (-1, 0), 9),
            ("FONTSIZE",      (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [rl_colors.HexColor("#F4F8FC"), rl_colors.white]),
            ("GRID",          (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#CCDDEE")),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    animo = datos.get("animo", [])
    puntajes = [r["puntaje"] for r in animo if r.get("puntaje") is not None]
    prom_txt = (f"Promedio: {round(sum(puntajes)/len(puntajes),1)}/10  |  "
                f"Total: {len(animo)} registros") if puntajes else None
    _seccion("Registros de ánimo", animo,
             ["Fecha", "Hora", "Puntaje", "Nota"],
             lambda r: [r.get("fecha","")[:10], r.get("hora","")[:5],
                        str(r.get("puntaje","")), (r.get("nota") or "")[:60]],
             prom_txt)
    _seccion("Sesiones de respiración", datos.get("resp", []),
             ["Fecha", "Hora", "Técnica", "Duración (min)"],
             lambda r: [r.get("fecha","")[:10], r.get("hora","")[:5],
                        r.get("tecnica","?"), str(r.get("duracion_minutos","?"))])
    _seccion("Registros de pensamientos", datos.get("pens", []),
             ["Fecha", "Emoción", "Intensidad", "Pensamiento"],
             lambda r: [r.get("fecha","")[:10], r.get("emocion","?"),
                        str(r.get("intensidad","?")), (r.get("pensamiento") or "")[:80]])
    all_check = datos.get("checklist", [])
    _seccion("Actividades de activación",
             [r for r in all_check if r.get("origen") == "activacion"],
             ["Fecha", "Categoría", "Actividad"],
             lambda r: [r.get("fecha","")[:10], r.get("categoria","?"),
                        (r.get("descripcion") or "")[:80]])
    _seccion("Checklist completadas",
             [r for r in all_check if r.get("origen") != "activacion"],
             ["Fecha", "Origen", "Categoría", "Descripción"],
             lambda r: [r.get("fecha","")[:10],
                        "Profesional" if r.get("origen") == "profesional" else "Paciente",
                        r.get("categoria","?"), (r.get("descripcion") or "")[:70]])
    _seccion("Sesiones de temporizador", datos.get("timer", []),
             ["Fecha", "Hora", "Actividad", "Duración (min)"],
             lambda r: [r.get("fecha","")[:10], r.get("hora","")[:5],
                        (r.get("nombre") or "Sin nombre")[:40],
                        str((r.get("duracion_real") or 0) // 60)])
    _seccion("Recordatorios disparados", datos.get("reclog", []),
             ["Fecha", "Hora", "Mensaje", "Estado"],
             lambda r: [r.get("fecha","")[:10], r.get("hora","")[:5],
                        (r.get("mensaje") or "")[:80],
                        "Cerrado" if r.get("cerrado") else "Pendiente"])

    doc.build(story)
    try:
        os.startfile(filepath)
    except Exception:
        pass
    return filepath
