# -*- coding: utf-8 -*-
"""Carga el mapa interno (nodos y conexiones) del Nivel 1 de la Sede Javier
Alzamora Valdez -- interpretado de la planta arquitectonica real del
edificio (JAV_EDIFICIO.pdf, "PLANTA PRIMER NIVEL", digitalizacion BIM del
Ex Ministerio de Educacion, arq. Enrique Seoane Ros, 1956).

Uso:
    python -m app.cargar_mapa_jav_nivel1

Idempotente (como cargar_titulares.py y cargar_directorio_excel.py): correr
esto varias veces no duplica nodos ni conexiones -- si un nodo con el mismo
nombre ya existe en esa sede/piso, se reutiliza en vez de crear uno nuevo.

Nota de precision: las conexiones e instrucciones se infirieron de la
adyacencia visual en el plano 2D, no de una caminata real por el edificio.
Es un punto de partida razonable, no una verificacion de campo -- Coordinacion
de Informatica puede ajustar cualquier nodo o instruccion despues desde el
panel (pestaña "Mapa interno"), sin volver a correr este script.
"""
from app import models
from app.database import SessionLocal

SEDE_NOMBRE = "Sede Javier Alzamora Valdez"
NIVEL = "1"

# clave interna -> (nombre a mostrar, es punto de partida seleccionable)
NODOS = {
    "ingreso_principal": ("Ingreso principal", True),
    "hall_principal": ("Hall principal", True),
    "hall_ascensores_a": ("Hall de ascensores - Bloque A (lado Abancay)", True),
    "hall_ascensores_b": ("Hall de ascensores - Bloque B (lado Nicolás de Piérola)", True),
    "hall_a": ("Hall - Bloque A", False),
    "hall_b": ("Hall - Bloque B", False),
    "recepcion_a": ("Recepción del Bloque A", True),
    "recepcion_b": ("Recepción del Bloque B", True),
    "informes_a": ("Informes - Bloque A", True),
    "informes_b": ("Informes - Bloque B", True),
    "pagos_a": ("Pagos y servicios - Bloque A", True),
    "pagos_b": ("Pagos y servicios - Bloque B", True),
    "ingreso_vehicular": ("Ingreso vehicular (Av. Nicolás de Piérola)", True),
    "salida_vehicular": ("Salida vehicular (Av. Abancay)", True),
    "auditorio": ("Auditorio (escenario y sala de butacas)", True),
    "patio_a": ("Patio exterior - Bloque A", True),
    "patio_b": ("Patio exterior - Bloque B", True),
    "bancos": ("Zona de bancos (agencias de pago)", True),
    "oficinas_apurimac": ("Oficinas (lado Jr. Apurímac)", True),
    "deposito_a": ("Depósito - Bloque A", False),
    "deposito_b": ("Depósito - Bloque B", False),
}

# (clave_a, clave_b, distancia, instruccion_a_a_b, instruccion_b_a_a)
CONEXIONES = [
    ("ingreso_principal", "hall_principal", 1,
     "Entra por la puerta central, de frente a la plaza.",
     "Sal hacia la plaza principal."),
    ("hall_principal", "hall_ascensores_a", 2,
     "Camina hacia la derecha (lado Av. Abancay) hasta los ascensores.",
     "Regresa al hall principal."),
    ("hall_principal", "hall_ascensores_b", 2,
     "Camina hacia la izquierda (lado Av. Nicolás de Piérola) hasta los ascensores.",
     "Regresa al hall principal."),
    ("hall_ascensores_a", "hall_a", 1,
     "Sigue de frente hacia el hall del Bloque A.",
     "Regresa hacia el hall de ascensores del Bloque A."),
    ("hall_ascensores_b", "hall_b", 1,
     "Sigue de frente hacia el hall del Bloque B.",
     "Regresa hacia el hall de ascensores del Bloque B."),
    ("hall_a", "recepcion_a", 1,
     "La recepción del Bloque A está al fondo del hall.",
     "Regresa hacia el hall del Bloque A."),
    ("hall_a", "informes_a", 1,
     "Informes está junto a la recepción del Bloque A.",
     "Regresa hacia el hall del Bloque A."),
    ("hall_a", "pagos_a", 1,
     "Pagos y servicios está junto a la recepción del Bloque A.",
     "Regresa hacia el hall del Bloque A."),
    ("hall_b", "recepcion_b", 1,
     "La recepción del Bloque B está al fondo del hall.",
     "Regresa hacia el hall del Bloque B."),
    ("hall_b", "informes_b", 1,
     "Informes está junto a la recepción del Bloque B.",
     "Regresa hacia el hall del Bloque B."),
    ("hall_b", "pagos_b", 1,
     "Pagos y servicios está junto a la recepción del Bloque B.",
     "Regresa hacia el hall del Bloque B."),
    ("hall_principal", "auditorio", 2,
     "Sube hacia el foyer, el auditorio está detrás del hall principal.",
     "Baja hacia el hall principal."),
    ("auditorio", "patio_b", 1,
     "El patio exterior del Bloque B está a un costado del escenario.",
     "Regresa hacia el auditorio."),
    ("auditorio", "patio_a", 1,
     "El patio exterior del Bloque A está a un costado del escenario.",
     "Regresa hacia el auditorio."),
    ("patio_a", "bancos", 2,
     "La zona de bancos está hacia el lado de Jr. Apurímac.",
     "Regresa hacia el patio exterior del Bloque A."),
    ("bancos", "oficinas_apurimac", 1,
     "Las oficinas están junto a la zona de bancos.",
     "Regresa hacia la zona de bancos."),
    ("ingreso_vehicular", "deposito_b", 1,
     "El depósito del Bloque B está junto al ingreso vehicular.",
     "El ingreso vehicular (Av. Nicolás de Piérola) está junto al depósito."),
    ("deposito_b", "hall_b", 2,
     "El hall del Bloque B está hacia el interior, pasando el depósito.",
     "El depósito y el ingreso vehicular están hacia la fachada."),
    ("salida_vehicular", "deposito_a", 1,
     "El depósito del Bloque A está junto a la salida vehicular.",
     "La salida vehicular (Av. Abancay) está junto al depósito."),
    ("deposito_a", "hall_a", 2,
     "El hall del Bloque A está hacia el interior, pasando el depósito.",
     "El depósito y la salida vehicular están hacia la fachada."),
]


def aplicar(db) -> dict:
    sede = db.query(models.Sede).filter(models.Sede.nombre == SEDE_NOMBRE).first()
    if not sede:
        raise SystemExit(f"No se encontró la sede '{SEDE_NOMBRE}'. ¿Está bien escrito el nombre?")

    creados_nodo = 0
    reusados_nodo = 0
    ids = {}
    for clave, (nombre, es_punto_partida) in NODOS.items():
        existente = (
            db.query(models.NodoUbicacion)
            .filter(
                models.NodoUbicacion.sede_id == sede.id,
                models.NodoUbicacion.piso == NIVEL,
                models.NodoUbicacion.nombre == nombre,
            )
            .first()
        )
        if existente:
            ids[clave] = existente.id
            reusados_nodo += 1
            continue
        nodo = models.NodoUbicacion(
            sede_id=sede.id, piso=NIVEL, nombre=nombre, es_punto_partida=es_punto_partida
        )
        db.add(nodo)
        db.flush()
        ids[clave] = nodo.id
        creados_nodo += 1

    creados_conexion = 0
    reusadas_conexion = 0
    for clave_a, clave_b, distancia, instr_ab, instr_ba in CONEXIONES:
        nodo_a_id, nodo_b_id = ids[clave_a], ids[clave_b]
        existente = (
            db.query(models.ConexionNodo)
            .filter(
                (
                    (models.ConexionNodo.nodo_a_id == nodo_a_id)
                    & (models.ConexionNodo.nodo_b_id == nodo_b_id)
                )
                | (
                    (models.ConexionNodo.nodo_a_id == nodo_b_id)
                    & (models.ConexionNodo.nodo_b_id == nodo_a_id)
                )
            )
            .first()
        )
        if existente:
            reusadas_conexion += 1
            continue
        db.add(
            models.ConexionNodo(
                nodo_a_id=nodo_a_id,
                nodo_b_id=nodo_b_id,
                distancia=distancia,
                instruccion_a_b=instr_ab,
                instruccion_b_a=instr_ba,
            )
        )
        creados_conexion += 1

    db.commit()
    return {
        "nodos_creados": creados_nodo,
        "nodos_reusados": reusados_nodo,
        "conexiones_creadas": creados_conexion,
        "conexiones_reusadas": reusadas_conexion,
    }


if __name__ == "__main__":
    db = SessionLocal()
    try:
        resumen = aplicar(db)
    finally:
        db.close()
    print(f"Nodos creados: {resumen['nodos_creados']} (ya existían: {resumen['nodos_reusados']})")
    print(f"Conexiones creadas: {resumen['conexiones_creadas']} (ya existían: {resumen['conexiones_reusadas']})")
