"""Importa la plantilla Excel de levantamiento del catálogo hacia la base de datos.

Uso:
    python -m app.import_excel "JusticiaOrienta_04_Plantilla_Catalogo_Piloto.xlsx"

Empareja filas por 'Nombre oficial': si ya existe una dependencia con ese nombre
la actualiza, si no, la crea. Las filas sin nombre se ignoran.
"""
import sys
from pathlib import Path

from openpyxl import load_workbook

from app import crud, models
from app.database import Base, SessionLocal, engine

COLUMNAS = [
    "id_hoja", "tipo", "categoria", "nombre", "alias",
    "sede", "edificio", "piso", "oficina", "horario",
    "servicios", "requisitos", "telefono", "correo",
    "rampa", "ascensor", "banio_accesible", "ruta_accesible",
    "estado", "responsable_validar",
]

SI_NO = {"sí": True, "si": True, "no": False, "no aplica": False, "": False}


def _bool(v) -> bool:
    return SI_NO.get(str(v or "").strip().lower(), False)


def _texto(v) -> str:
    return str(v).strip() if v is not None else ""


def importar(ruta_excel: str) -> None:
    wb = load_workbook(ruta_excel, data_only=True)
    ws = wb["Catálogo"]

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    creadas, actualizadas, omitidas = 0, 0, 0

    try:
        for fila in ws.iter_rows(min_row=2, values_only=True):
            valores = dict(zip(COLUMNAS, fila))
            nombre = _texto(valores.get("nombre"))
            if not nombre:
                omitidas += 1
                continue

            tipo_map = {"jurisdiccional": "jurisdiccional", "administrativa": "administrativa", "servicio": "servicio"}
            tipo = tipo_map.get(_texto(valores.get("tipo")).lower(), "servicio")
            estado_map = {"activo": "activo", "en revisión": "revision", "en revision": "revision", "inactivo": "inactivo"}
            estado = estado_map.get(_texto(valores.get("estado")).lower(), "revision")

            data = {
                "tipo": tipo,
                "categoria": _texto(valores.get("categoria")) or None,
                "nombre": nombre,
                "sede": _texto(valores.get("sede")) or None,
                "edificio": _texto(valores.get("edificio")) or None,
                "piso": _texto(valores.get("piso")) or None,
                "oficina": _texto(valores.get("oficina")) or None,
                "horario": _texto(valores.get("horario")) or None,
                "servicios": _texto(valores.get("servicios")) or None,
                "requisitos": _texto(valores.get("requisitos")) or None,
                "telefono": _texto(valores.get("telefono")) or None,
                "correo": _texto(valores.get("correo")) or None,
                "rampa": _bool(valores.get("rampa")),
                "ascensor": _bool(valores.get("ascensor")),
                "banio_accesible": _bool(valores.get("banio_accesible")),
                "ruta_accesible": _bool(valores.get("ruta_accesible")),
                "estado": estado,
                "area": _texto(valores.get("categoria")) or _texto(valores.get("tipo")),
                "responsable_validar": _texto(valores.get("responsable_validar")) or None,
            }
            alias_csv = _texto(valores.get("alias"))

            existente = db.query(models.Dependencia).filter(models.Dependencia.nombre == nombre).first()
            if existente:
                crud.actualizar_dependencia(db, existente, data, alias_csv)
                actualizadas += 1
            else:
                crud.crear_dependencia(db, data, alias_csv)
                creadas += 1

        print(f"Importación completa: {creadas} creadas, {actualizadas} actualizadas, {omitidas} filas vacías omitidas.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m app.import_excel <ruta_al_excel.xlsx>")
        sys.exit(1)
    ruta = Path(sys.argv[1])
    if not ruta.exists():
        print(f"No se encontró el archivo: {ruta}")
        sys.exit(1)
    importar(str(ruta))
