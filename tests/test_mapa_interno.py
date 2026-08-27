from fastapi.testclient import TestClient

from app import models
from app.main import app

client = TestClient(app)


def _crear_nodo(db, sede, nombre, piso="1", pos_x=None, pos_y=None, dependencia_id=None, es_punto_partida=True):
    n = models.NodoUbicacion(
        sede_id=sede.id, piso=piso, nombre=nombre, es_punto_partida=es_punto_partida,
        dependencia_id=dependencia_id, pos_x=pos_x, pos_y=pos_y,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def _conectar(db, a, b, distancia=1, instr_ab="Sigue de frente.", instr_ba="Regresa."):
    c = models.ConexionNodo(
        nodo_a_id=a.id, nodo_b_id=b.id, distancia=distancia,
        instruccion_a_b=instr_ab, instruccion_b_a=instr_ba,
    )
    db.add(c)
    db.commit()
    return c


def _crear_dependencia(db, sede, nombre, piso="1"):
    d = models.Dependencia(
        tipo="administrativa", nombre=nombre, sede_id=sede.id, piso=piso, estado="activo",
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def test_calcula_ruta_directa_cuando_la_dependencia_tiene_su_propio_nodo(db, sede):
    ingreso = _crear_nodo(db, sede, "Ingreso principal", pos_x=50, pos_y=88)
    hall = _crear_nodo(db, sede, "Hall principal", pos_x=50, pos_y=68)
    _conectar(db, ingreso, hall, instr_ab="Entra por la puerta central.", instr_ba="Sal hacia la plaza.")
    dep = _crear_dependencia(db, sede, "Mesa de Partes")
    hall.dependencia_id = dep.id
    db.commit()

    r = client.get(f"/api/v1/ruta?origen_id={ingreso.id}&dependencia_id={dep.id}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["aproximada"] is False
    assert data["dependencia_nombre"] == "Mesa de Partes"
    assert [p["nombre"] for p in data["pasos"]] == ["Ingreso principal", "Hall principal"]
    assert data["pasos"][1]["instruccion"] == "Entra por la puerta central."


def test_ruta_aproximada_cuando_la_dependencia_no_tiene_nodo_propio(db, sede):
    """Sin nodo propio vinculado, la ruta debe llegar hasta un punto de
    referencia del mismo piso (ej. el hall de ascensores) y marcarse
    explícitamente como aproximada -- nunca debe fingir precisión que no
    tiene."""
    ingreso = _crear_nodo(db, sede, "Ingreso principal", pos_x=50, pos_y=88)
    hall_piso_7 = _crear_nodo(db, sede, "Hall de ascensores - piso 7", piso="7")
    _conectar(db, ingreso, hall_piso_7, instr_ab="Sube al piso 7.", instr_ba="Baja al piso 1.")
    dep = _crear_dependencia(db, sede, "Oficina de Administración Piso 7", piso="7")

    r = client.get(f"/api/v1/ruta?origen_id={ingreso.id}&dependencia_id={dep.id}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["aproximada"] is True
    assert data["dependencia_nombre"] == "Oficina de Administración Piso 7"
    assert data["pasos"][-1]["nombre"] == "Hall de ascensores - piso 7"


def test_sin_ningun_punto_de_referencia_en_el_piso_no_hay_ruta(db, sede):
    ingreso = _crear_nodo(db, sede, "Ingreso principal", pos_x=50, pos_y=88)
    dep = _crear_dependencia(db, sede, "Oficina sin mapa cargado", piso="15")

    r = client.get(f"/api/v1/ruta?origen_id={ingreso.id}&dependencia_id={dep.id}")
    assert r.status_code == 404


def test_sin_camino_conectado_entre_los_puntos_no_hay_ruta(db, sede):
    ingreso = _crear_nodo(db, sede, "Ingreso principal", pos_x=50, pos_y=88)
    aislado = _crear_nodo(db, sede, "Nodo aislado sin conexiones")
    dep = _crear_dependencia(db, sede, "Dependencia aislada")
    aislado.dependencia_id = dep.id
    db.commit()

    r = client.get(f"/api/v1/ruta?origen_id={ingreso.id}&dependencia_id={dep.id}")
    assert r.status_code == 404


def test_pasos_traen_piso_y_posicion_para_que_el_frontend_decida_si_dibuja_el_mapa(db, sede):
    ingreso = _crear_nodo(db, sede, "Ingreso principal", pos_x=50, pos_y=88)
    hall = _crear_nodo(db, sede, "Hall principal", pos_x=50, pos_y=68)
    _conectar(db, ingreso, hall)
    dep = _crear_dependencia(db, sede, "Recepción")
    hall.dependencia_id = dep.id
    db.commit()

    r = client.get(f"/api/v1/ruta?origen_id={ingreso.id}&dependencia_id={dep.id}")
    data = r.json()
    for paso in data["pasos"]:
        assert paso["piso"] == "1"
        assert paso["pos_x"] is not None
        assert paso["pos_y"] is not None


def test_puntos_partida_solo_devuelve_los_marcados_como_reconocibles(db, sede):
    _crear_nodo(db, sede, "Ingreso principal", es_punto_partida=True)
    _crear_nodo(db, sede, "Cruce de pasillo interno", es_punto_partida=False)

    r = client.get(f"/api/v1/sedes/{sede.id}/puntos-partida")
    assert r.status_code == 200
    nombres = [n["nombre"] for n in r.json()]
    assert "Ingreso principal" in nombres
    assert "Cruce de pasillo interno" not in nombres


def test_admin_no_puede_guardar_una_posicion_fuera_de_rango(db, sede, admin_usuario):
    r = client.post("/api/v1/auth/login", data={"username": "10000001", "password": "clave123"})
    token = r.json()["access_token"]
    r = client.post(
        "/api/v1/admin/mapa/nodos",
        json={"sede_id": sede.id, "nombre": "Nodo con posición inválida", "pos_x": 150, "pos_y": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422
