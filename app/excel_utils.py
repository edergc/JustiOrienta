"""Helpers de Excel compartidos entre los reportes de indicadores
(admin_metricas.py) y la exportación del catálogo (admin_dependencias.py) --
antes cada uno tenía su propia copia del ajuste de ancho de columna, con
límites que ya se habían desalineado entre sí (10-50 en uno, 12-60 en el
otro) por ser copias pegadas y modificadas por separado."""
from openpyxl.styles import Font

# "Inyección de fórmulas": nombre, horario, instrucciones_internas, etc. son
# texto libre que cualquier gestor(a) de área puede escribir, y terminan en
# estas mismas celdas cuando alguien exporta el catálogo. Si algo empieza con
# uno de estos caracteres, Excel/LibreOffice puede interpretarlo como fórmula
# al abrir el archivo (en la máquina de quien lo abre, no en el servidor) --
# antepone una comilla para forzar texto literal, igual que hace Excel mismo
# cuando alguien escribe "=..." a mano en una celda de texto.
_CARACTERES_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def celda_segura(valor):
    if isinstance(valor, str) and valor.startswith(_CARACTERES_FORMULA):
        return "'" + valor
    return valor


def fila_segura(fila) -> list:
    return [celda_segura(v) for v in fila]


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
        ws.append(fila_segura(fila))
    autoajustar_columnas(ws)
    return ws
