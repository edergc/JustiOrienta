"""Helpers de Excel compartidos entre los reportes de indicadores
(admin_metricas.py) y la exportación del catálogo (admin_dependencias.py) --
antes cada uno tenía su propia copia del ajuste de ancho de columna, con
límites que ya se habían desalineado entre sí (10-50 en uno, 12-60 en el
otro) por ser copias pegadas y modificadas por separado."""
from openpyxl.styles import Font


def autoajustar_columnas(ws, minimo: int = 12, maximo: int = 60) -> None:
    """default=minimo en el max() es necesario: una hoja sin filas de datos
    (o una columna donde todos los valores son None) daría max() sobre un
    generador vacío y lanzaría ValueError -- la fila de encabezado sola ya
    lo evita en la práctica, pero no vale la pena depender de eso."""
    for col in ws.columns:
        ancho = max((len(str(c.value)) for c in col if c.value is not None), default=minimo) + 2
        ws.column_dimensions[col[0].column_letter].width = min(max(ancho, minimo), maximo)


def hoja_con_tabla(wb, titulo: str, encabezados: list[str], filas) -> "Worksheet":
    ws = wb.create_sheet(titulo)
    ws.append(encabezados)
    for celda in ws[1]:
        celda.font = Font(bold=True)
    for fila in filas:
        ws.append(fila)
    autoajustar_columnas(ws)
    return ws
