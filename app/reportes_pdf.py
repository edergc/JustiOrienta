"""Directorio público en PDF -- para imprimir en un mostrador o llevarse sin
conexión, sin depender de que la pantalla del sitio público esté disponible
en ese momento. Generado 100% local con fpdf2 (LGPL, sin costo de licencia,
sin dependencias nativas), igual que el reporte en Excel del panel usa
openpyxl y el QR usa la librería `qrcode`."""
from datetime import datetime
from typing import Optional

from fpdf import FPDF

from app import models

_ANCHO_UTIL = 190  # mm útiles en A4 con márgenes de 10mm por lado

# Reemplazos comunes antes de la red de seguridad de más abajo -- para que
# rayas, comillas curvas y elipsis (frecuentes si alguien pega texto desde
# Word) se vean bien en vez de aparecer como "?".
_REEMPLAZOS_UNICODE = {
    "—": "-", "–": "-",  # raya larga/corta
    "‘": "'", "’": "'",  # comillas simples curvas
    "“": '"', "”": '"',  # comillas dobles curvas
    "…": "...",  # elipsis
    " ": " ",  # espacio duro
}


def _texto_seguro(valor) -> str:
    """Las fuentes núcleo de fpdf2 (helvetica) solo soportan Latin-1 -- sin
    esto, un solo carácter fuera de ese rango en cualquier campo de texto
    libre (nombre, horario, dirección...) hacía fallar la generación de TODO
    el directorio, no solo esa fila, en un endpoint público sin login. Como
    red de seguridad final, cualquier otro carácter no soportado se
    reemplaza en vez de romper la respuesta."""
    if valor is None:
        return ""
    texto = str(valor)
    for buscado, reemplazo in _REEMPLAZOS_UNICODE.items():
        texto = texto.replace(buscado, reemplazo)
    return texto.encode("latin-1", errors="replace").decode("latin-1")


class _DirectorioPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 14)
        self.set_text_color(20, 30, 60)
        self.cell(0, 10, "Justicia Orienta -- Directorio", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(20, 30, 60)
        self.line(10, 20, 200, 20)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def _accesibilidad_texto(dep: models.Dependencia) -> str:
    # Prioriza lo confirmado en la dependencia; si no hay dato ahí, cae al de
    # la sede -- mismo criterio que ya usa la tarjeta pública (public.js).
    items = []
    if dep.rampa or (dep.sede and dep.sede.rampa):
        items.append("rampa")
    if dep.ascensor or (dep.sede and dep.sede.ascensor):
        items.append("ascensor")
    if dep.banio_accesible or (dep.sede and dep.sede.banio_accesible):
        items.append("baño accesible")
    return ", ".join(items) if items else "sin dato confirmado -- consulta en el módulo de orientación"


def generar_directorio_pdf(dependencias: list[models.Dependencia], sede_nombre: Optional[str]) -> bytes:
    pdf = _DirectorioPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    subtitulo = _texto_seguro(sede_nombre) or "Todas las sedes publicadas"
    pdf.cell(0, 6, f"{subtitulo} -- generado {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if not dependencias:
        pdf.set_font("helvetica", "", 11)
        pdf.multi_cell(_ANCHO_UTIL, 6, "No hay dependencias publicadas todavía para este filtro.")
        return bytes(pdf.output())

    sede_actual = None
    for dep in dependencias:
        nombre_sede = _texto_seguro(dep.sede.nombre) if dep.sede else "Sede no registrada"
        if nombre_sede != sede_actual:
            sede_actual = nombre_sede
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(20, 30, 60)
            pdf.ln(3)
            pdf.cell(0, 8, nombre_sede, new_x="LMARGIN", new_y="NEXT")
            if dep.sede and dep.sede.direccion:
                pdf.set_font("helvetica", "", 9)
                pdf.set_text_color(90, 90, 90)
                pdf.cell(0, 5, _texto_seguro(dep.sede.direccion), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)
            pdf.ln(3)

        ubicacion = " / ".join(
            p for p in [
                _texto_seguro(dep.edificio.nombre) if dep.edificio else None,
                f"Piso {_texto_seguro(dep.piso)}" if dep.piso else None,
                f"Oficina {_texto_seguro(dep.oficina)}" if dep.oficina else None,
            ] if p
        )
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(_ANCHO_UTIL, 5, _texto_seguro(dep.nombre) + (f"  ({ubicacion})" if ubicacion else ""))

        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(70, 70, 70)
        if dep.horario:
            pdf.multi_cell(_ANCHO_UTIL, 5, f"Horario: {_texto_seguro(dep.horario)}")
        if dep.telefono:
            pdf.multi_cell(_ANCHO_UTIL, 5, f"Teléfono: {_texto_seguro(dep.telefono)}")
        pdf.multi_cell(_ANCHO_UTIL, 5, f"Accesibilidad: {_accesibilidad_texto(dep)}")
        pdf.ln(2)

    return bytes(pdf.output())
