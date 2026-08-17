# -*- coding: utf-8 -*-
"""Carga el directorio oficial de la CSJ Lima (PDF publicado por el Poder
Judicial) hacia la base de datos de Justicia Orienta.

Fuente: https://www.pj.gob.pe -- "Directorio CSJLI" (directorio telefónico
oficial, actualizado periódicamente por la propia Corte). Se extrae con
pdfplumber -- lee las tablas reales del PDF, no transcripción a mano -- para
no introducir errores de tipeo en cientos de filas.

Uso:
    python -m app.cargar_directorio_pj [ruta_al_pdf]

Si no se indica ruta, usa la última descargada en fuentes/.

Reglas seguidas (consistentes con "nunca inventar información"):
- Solo se cargan campos presentes en el documento: sede, dirección, central
  telefónica, dependencia, piso, anexo. Horario, requisitos, accesibilidad y
  alias quedan en blanco -- nadie los ha confirmado todavía; es trabajo para
  cada área durante la revisión.
- Solo la sede piloto (Javier Alzamora Valdez) se publica como "activo". Las
  demás sedes quedan en "revision": cargadas y listas para que cada área las
  revise antes de publicarlas -- carga masiva no es lo mismo que validación.
- No se sobrescriben registros ya cargados: si una dependencia con el mismo
  nombre y sede ya existe, se deja tal cual (para no pisar ediciones que
  alguna área ya haya hecho a mano).
"""
import re
import sys
from pathlib import Path

import pdfplumber
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal

BASE_DIR = Path(__file__).resolve().parent.parent
FUENTES_DIR = BASE_DIR / "fuentes"
SEDE_PILOTO = "Sede Javier Alzamora Valdez"

CONECTORES = {"de", "del", "la", "las", "los", "y", "en", "con"}
ACRONIMOS = {"JPL"}

# El documento fuente repite el nombre genérico "Mesa de Partes" para tres
# oficinas distintas dentro de la misma sede piloto (Bienestar Social,
# Control de Asistencia, Escalafón y Registro) -- ya se corrigieron a mano
# con el contexto real que sí figura en el documento (ver auditoría). Se
# identifican por (sede, piso, anexo) para que una relectura del PDF no las
# vuelva a duplicar con el nombre genérico.
YA_DESAMBIGUADAS = {
    (SEDE_PILOTO, "12", "13203"),
    (SEDE_PILOTO, "13", "13155"),
    (SEDE_PILOTO, "10", "13144"),
}


def limpiar(texto: str) -> str:
    return " ".join((texto or "").replace("\n", " ").split())


def categoria_de(nombre: str) -> str:
    return re.sub(r"^\d+[°º]\s*", "", nombre).strip()


def formatear_nombre_sede(bruto: str) -> str:
    """'CAMPODONICO - JPL LA VICTORIA Y SAN LUIS' -> 'Campodonico - JPL la Victoria y San Luis'"""
    resultado = []
    for i, palabra in enumerate(bruto.strip().split(" ")):
        if palabra in ACRONIMOS:
            resultado.append(palabra)
        elif palabra.lower() in CONECTORES and i != 0:
            resultado.append(palabra.lower())
        else:
            resultado.append(palabra.capitalize())
    return "Sede " + " ".join(resultado)


def extraer_registros(pdf_path: str):
    """Devuelve (sedes: {nombre: {direccion, central}}, filas: [dict])."""
    sedes: dict[str, dict] = {}
    filas: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for tabla in page.extract_tables():
                if not tabla or not tabla[0] or not tabla[0][0]:
                    continue
                sede_bruto = limpiar(tabla[0][0])
                if not sede_bruto.upper().startswith("SEDE"):
                    continue
                sede_nombre = formatear_nombre_sede(sede_bruto[len("SEDE"):].strip())

                fila_direccion = tabla[1] if len(tabla) > 1 else None
                if fila_direccion and fila_direccion[0] and "Direcci" in fila_direccion[0]:
                    direccion = limpiar(fila_direccion[0]).split(":", 1)[-1].strip()
                    central = limpiar(fila_direccion[1]) if len(fila_direccion) > 1 else ""
                    if sede_nombre not in sedes:
                        sedes[sede_nombre] = {"direccion": direccion, "central": central}
                    inicio = 2
                else:
                    inicio = 1

                tipo_actual = None
                for row in tabla[inicio:]:
                    if not row or not row[0]:
                        continue
                    c0 = limpiar(row[0])
                    c1 = limpiar(row[1]) if len(row) > 1 else ""
                    c2 = limpiar(row[2]) if len(row) > 2 else ""

                    if c1.upper() == "PISO" and c2.upper() == "ANEXO":
                        tipo_actual = "administrativa" if "ADMINISTRATIVA" in c0.upper() else "jurisdiccional"
                        continue
                    if tipo_actual is None or not c0:
                        continue
                    if c0 == "Mesa de Partes" and (sede_nombre, c1, c2) in YA_DESAMBIGUADAS:
                        continue

                    filas.append({
                        "sede": sede_nombre, "tipo": tipo_actual,
                        "nombre": c0, "piso": c1, "anexo": c2,
                    })
    return sedes, filas


def cargar(db: Session, sedes: dict, filas: list) -> int:
    demo = db.query(models.Sede).filter(models.Sede.nombre == "Sede Alzamora Valdez").first()
    if demo:
        demo.nombre = SEDE_PILOTO
        db.flush()
        for dep in list(demo.dependencias):
            db.delete(dep)
        db.flush()

    sede_por_nombre = {}
    for nombre, datos in sedes.items():
        sede = db.query(models.Sede).filter(models.Sede.nombre == nombre).first()
        if not sede:
            sede = models.Sede(nombre=nombre)
            db.add(sede)
        sede.direccion = datos["direccion"] or sede.direccion
        sede.telefono = datos["central"] or sede.telefono
        sede.estado = "activo"
        db.flush()
        sede_por_nombre[nombre] = sede

    creadas = 0
    for fila in filas:
        sede = sede_por_nombre.get(fila["sede"])
        if not sede:
            continue
        existente = (
            db.query(models.Dependencia)
            .filter(models.Dependencia.nombre == fila["nombre"], models.Dependencia.sede_id == sede.id)
            .first()
        )
        if existente:
            continue
        estado = "activo" if fila["sede"] == SEDE_PILOTO else "revision"
        db.add(models.Dependencia(
            tipo=fila["tipo"],
            categoria=categoria_de(fila["nombre"]),
            nombre=fila["nombre"],
            sede_id=sede.id,
            piso=fila["piso"] or None,
            telefono=(f"Anexo {fila['anexo']}" if fila["anexo"] else None),
            area=fila["sede"],
            estado=estado,
        ))
        creadas += 1
    db.commit()
    return creadas


def _pdf_mas_reciente() -> Path:
    candidatos = sorted(FUENTES_DIR.glob("Directorio_CSJLI*.pdf"))
    if not candidatos:
        raise SystemExit(f"No se encontró ningún PDF de directorio en {FUENTES_DIR}")
    return candidatos[-1]


if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else _pdf_mas_reciente()
    print(f"Leyendo: {ruta}")
    sedes, filas = extraer_registros(str(ruta))
    print(f"Sedes detectadas: {len(sedes)}")
    print(f"Filas de dependencias detectadas: {len(filas)}")

    db = SessionLocal()
    try:
        creadas = cargar(db, sedes, filas)
        print(f"Dependencias nuevas creadas: {creadas}")
    finally:
        db.close()
