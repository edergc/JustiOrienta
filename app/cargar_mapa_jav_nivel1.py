# -*- coding: utf-8 -*-
"""Carga el mapa interno (nodos y conexiones) de la Sede Javier Alzamora
Valdez: el Nivel 1 en detalle, y un "hall de ascensores" por piso del 2 al
20 para el resto del edificio.

Fuentes:
- Nivel 1 (planta, accesos, zonificación y circulación real): JAV_EDIFICIO.pdf
  (digitalización BIM) y JAV_DiSEÑO.pdf (Universidad Privada del Norte,
  "Análisis de caso" del edificio -- trabajo académico, no un documento
  oficial del Poder Judicial, pero con planos y circulación reales que
  confirmaron y afinaron el trazado del Nivel 1 ya cargado).
- Pisos 2 al 20: JAV_DiSEÑO.pdf confirma que los ascensores van del sótano 2
  al último piso (la circulación vertical principal) y que el piso 4 al 11 y
  12 al 20 repiten el mismo patrón de planta. No hay dato de qué oficina
  exacta ocupa cada piso, así que solo se agrega un punto "Hall de
  ascensores, piso N": suficiente para llevar a alguien al piso y ascensor
  correctos de cualquier dependencia del catálogo (que sí trae el piso),
  aunque no hasta la puerta exacta de la oficina.

Uso:
    python -m app.cargar_mapa_jav_nivel1

Idempotente (como cargar_titulares.py y cargar_directorio_excel.py): correr
esto varias veces no duplica nodos ni conexiones -- si un nodo con el mismo
nombre ya existe en esa sede/piso, se reutiliza en vez de crear uno nuevo.

Nota de precision: las conexiones e instrucciones del Nivel 1 se infirieron
de la adyacencia visual en planos 2D (uno BIM, otro de un análisis de caso
universitario), no de una caminata real por el edificio. Es un punto de
partida razonable, no una verificación de campo -- Coordinación de
Informática puede ajustar cualquier nodo o instrucción después desde el
panel (pestaña "Mapa interno"), sin volver a correr este script.
"""
from app import models
from app.database import SessionLocal

SEDE_NOMBRE = "Sede Javier Alzamora Valdez"
NIVEL_1 = "1"
PRIMER_PISO_SUPERIOR = 2
# JAV_DiSEÑO.pdf documenta en detalle el patrón repetido de los pisos 4 al 20
# (y JAV_EDIFICIO.pdf, que el edificio tiene 21 niveles) -- el 21 no tiene
# planta propia en ninguna de las dos fuentes, pero el catálogo real (piso
# registrado en las dependencias ya cargadas) confirma que existe y tiene
# oficinas activas, así que se incluye igual: incorrecto dejarlo sin ruta
# solo porque no hay planta de ese piso en particular.
ULTIMO_PISO_SUPERIOR = 21

# clave interna -> (nombre a mostrar, piso, es punto de partida seleccionable, pos_x %, pos_y %)
#
# pos_x/pos_y ubican el punto sobre el mapa visual del Nivel 1 (ver
# renderMapaSVG en public.js) -- 0-100, x de izquierda a derecha, y de atrás
# (auditorio) hacia adelante (plaza/ingreso). Estimadas a ojo comparando la
# posición relativa de cada ambiente en la lámina "Zonificación - Micro,
# primer piso" de JAV_DiSEÑO.pdf: no son coordenadas topográficas, solo
# sitúan cada punto en el lugar aproximado correcto dentro del edificio.
# El resto de pisos no tiene mapa visual, así que quedan en None.
NODOS = {
    "ingreso_principal": ("Ingreso principal", NIVEL_1, True, 50, 88),
    "hall_principal": ("Hall principal", NIVEL_1, True, 50, 68),
    "hall_ascensores_a": ("Hall de ascensores - Bloque A (lado Abancay)", NIVEL_1, True, 61, 51),
    "hall_ascensores_b": ("Hall de ascensores - Bloque B (lado Nicolás de Piérola)", NIVEL_1, True, 39, 51),
    "hall_a": ("Hall - Bloque A", NIVEL_1, False, 64, 63),
    "hall_b": ("Hall - Bloque B", NIVEL_1, False, 36, 63),
    "recepcion_a": ("Recepción del Bloque A", NIVEL_1, True, 73, 64),
    "recepcion_b": ("Recepción del Bloque B", NIVEL_1, True, 27, 64),
    "informes_a": ("Informes - Bloque A", NIVEL_1, True, 67, 62),
    "informes_b": ("Informes - Bloque B", NIVEL_1, True, 33, 62),
    "pagos_a": ("Pagos y servicios - Bloque A", NIVEL_1, True, 67, 73),
    "pagos_b": ("Pagos y servicios - Bloque B", NIVEL_1, True, 33, 73),
    "ingreso_vehicular": ("Ingreso vehicular (Av. Nicolás de Piérola)", NIVEL_1, True, 23, 37),
    "salida_vehicular": ("Salida vehicular (Jr. Santa Rosa)", NIVEL_1, True, 81, 37),
    "auditorio": ("Auditorio (escenario y sala de butacas)", NIVEL_1, True, 50, 28),
    "patio_a": ("Patio exterior - Bloque A", NIVEL_1, True, 70, 32),
    "patio_b": ("Patio exterior - Bloque B", NIVEL_1, True, 30, 32),
    "bancos": ("Zona de bancos (agencias de pago)", NIVEL_1, True, 68, 22),
    "oficinas_apurimac": ("Oficinas (lado Jr. Apurímac)", NIVEL_1, True, 79, 20),
    "deposito_a": ("Depósito - Bloque A", NIVEL_1, False, 88, 49),
    "deposito_b": ("Depósito - Bloque B", NIVEL_1, False, 16, 49),
    # SS.HH confirmados en JAV_DiSEÑO.pdf (lámina "Zonificación - Micro",
    # primer piso): dos junto al foyer del auditorio, dos junto a los halls
    # de ascensores -- no estaban en la primera carga del Nivel 1.
    "ss_hh_auditorio_a": ("SS.HH - Auditorio, lado Bloque A", NIVEL_1, True, 62, 18),
    "ss_hh_auditorio_b": ("SS.HH - Auditorio, lado Bloque B", NIVEL_1, True, 38, 18),
    "ss_hh_ascensores_a": ("SS.HH - Hall de ascensores, Bloque A", NIVEL_1, True, 67, 47),
    "ss_hh_ascensores_b": ("SS.HH - Hall de ascensores, Bloque B", NIVEL_1, True, 33, 47),
}
# Un "hall de ascensores" por cada piso superior -- ver nota de fuentes arriba.
# Sin mapa visual propio, así que sin posición (None, None).
for _piso in range(PRIMER_PISO_SUPERIOR, ULTIMO_PISO_SUPERIOR + 1):
    NODOS[f"hall_ascensores_piso_{_piso}"] = (f"Hall de ascensores - piso {_piso}", str(_piso), True, None, None)

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
    ("hall_ascensores_a", "ss_hh_ascensores_a", 1,
     "El baño está junto al hall de ascensores.",
     "Regresa hacia el hall de ascensores."),
    ("hall_ascensores_b", "ss_hh_ascensores_b", 1,
     "El baño está junto al hall de ascensores.",
     "Regresa hacia el hall de ascensores."),
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
    ("auditorio", "ss_hh_auditorio_a", 1,
     "El baño está a un costado del escenario, junto al foyer (lado Bloque A).",
     "Regresa hacia el auditorio."),
    ("auditorio", "ss_hh_auditorio_b", 1,
     "El baño está a un costado del escenario, junto al foyer (lado Bloque B).",
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
     "La salida vehicular (Jr. Santa Rosa) está junto al depósito."),
    ("deposito_a", "hall_a", 2,
     "El hall del Bloque A está hacia el interior, pasando el depósito.",
     "El depósito y la salida vehicular están hacia la fachada."),
]
# Cada piso superior se conecta por ascensor desde AMBOS halls del Nivel 1 --
# no sabemos si un piso en particular lo sirve el banco de ascensores del
# Bloque A o el del Bloque B, así que se ofrecen los dos.
for _piso in range(PRIMER_PISO_SUPERIOR, ULTIMO_PISO_SUPERIOR + 1):
    _clave_piso = f"hall_ascensores_piso_{_piso}"
    for _bloque in ("a", "b"):
        CONEXIONES.append((
            f"hall_ascensores_{_bloque}", _clave_piso, 3,
            f"Toma el ascensor y sube al piso {_piso}.",
            "Toma el ascensor y baja al Nivel 1.",
        ))

# clave de nodo -> nombre exacto de la dependencia ya cargada en el catálogo
# (confirmado por búsqueda real: es la única "Mesa de Partes" en el piso 1).
# Nunca sobrescribe un vínculo que ya se haya puesto a mano desde el panel.
VINCULOS = {
    "recepcion_a": "Mesa de Partes (Ubicación de Expedientes y Recepción de Solicitudes)",
}

# nombre viejo -> nombre nuevo, para cuando se corrige un nombre ya cargado
# en producción -- sin esto, cambiar NODOS[clave][0] simplemente crea un
# nodo nuevo con el nombre corregido y deja el viejo huérfano en la base.
RENOMBRES = {
    "Salida vehicular (Av. Abancay)": "Salida vehicular (Jr. Santa Rosa)",
}


def aplicar(db) -> dict:
    sede = db.query(models.Sede).filter(models.Sede.nombre == SEDE_NOMBRE).first()
    if not sede:
        raise SystemExit(f"No se encontró la sede '{SEDE_NOMBRE}'. ¿Está bien escrito el nombre?")

    renombrados = 0
    for nombre_viejo, nombre_nuevo in RENOMBRES.items():
        ya_existe_nuevo = (
            db.query(models.NodoUbicacion)
            .filter(models.NodoUbicacion.sede_id == sede.id, models.NodoUbicacion.nombre == nombre_nuevo)
            .first()
        )
        if ya_existe_nuevo:
            continue
        viejo = (
            db.query(models.NodoUbicacion)
            .filter(models.NodoUbicacion.sede_id == sede.id, models.NodoUbicacion.nombre == nombre_viejo)
            .first()
        )
        if viejo:
            viejo.nombre = nombre_nuevo
            renombrados += 1
    if renombrados:
        db.flush()

    creados_nodo = 0
    reusados_nodo = 0
    posiciones_completadas = 0
    ids = {}
    for clave, (nombre, piso, es_punto_partida, pos_x, pos_y) in NODOS.items():
        existente = (
            db.query(models.NodoUbicacion)
            .filter(
                models.NodoUbicacion.sede_id == sede.id,
                models.NodoUbicacion.piso == piso,
                models.NodoUbicacion.nombre == nombre,
            )
            .first()
        )
        if existente:
            ids[clave] = existente.id
            reusados_nodo += 1
            # Rellena la posición solo si el nodo todavía no tiene una --
            # así una corrida vieja (de antes de que existiera pos_x/pos_y)
            # se pone al día, sin pisar un ajuste que alguien ya hizo a mano
            # desde el panel.
            if existente.pos_x is None and existente.pos_y is None and pos_x is not None:
                existente.pos_x = pos_x
                existente.pos_y = pos_y
                posiciones_completadas += 1
            continue
        nodo = models.NodoUbicacion(
            sede_id=sede.id, piso=piso, nombre=nombre, es_punto_partida=es_punto_partida,
            pos_x=pos_x, pos_y=pos_y,
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

    vinculados = 0
    sin_encontrar = []
    for clave, nombre_dependencia in VINCULOS.items():
        nodo = db.query(models.NodoUbicacion).filter(models.NodoUbicacion.id == ids[clave]).first()
        if nodo.dependencia_id is not None:
            continue  # ya vinculado (a mano o en una corrida previa) -- no se pisa
        dep = (
            db.query(models.Dependencia)
            .filter(models.Dependencia.sede_id == sede.id, models.Dependencia.nombre == nombre_dependencia)
            .first()
        )
        if not dep:
            sin_encontrar.append(nombre_dependencia)
            continue
        nodo.dependencia_id = dep.id
        vinculados += 1

    db.commit()
    return {
        "renombrados": renombrados,
        "nodos_creados": creados_nodo,
        "nodos_reusados": reusados_nodo,
        "posiciones_completadas": posiciones_completadas,
        "conexiones_creadas": creados_conexion,
        "conexiones_reusadas": reusadas_conexion,
        "vinculados": vinculados,
        "sin_encontrar": sin_encontrar,
    }


if __name__ == "__main__":
    db = SessionLocal()
    try:
        resumen = aplicar(db)
    finally:
        db.close()
    if resumen["renombrados"]:
        print(f"Nodos renombrados: {resumen['renombrados']}")
    print(f"Nodos creados: {resumen['nodos_creados']} (ya existían: {resumen['nodos_reusados']})")
    if resumen["posiciones_completadas"]:
        print(f"Posiciones en el mapa completadas en nodos ya existentes: {resumen['posiciones_completadas']}")
    print(f"Conexiones creadas: {resumen['conexiones_creadas']} (ya existían: {resumen['conexiones_reusadas']})")
    print(f"Nodos vinculados a una dependencia: {resumen['vinculados']}")
    if resumen["sin_encontrar"]:
        print("Dependencias no encontradas para vincular (revisar el nombre exacto):")
        for nombre in resumen["sin_encontrar"]:
            print(f"  - {nombre}")
