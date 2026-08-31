import re

import pytest
from fastapi.testclient import TestClient

from app import rate_limit
from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _limpiar_limite_de_intentos():
    # El limitador vive en memoria de proceso (ver app/rate_limit.py), no en
    # la base de datos -- sin limpiarlo, los intentos de un test contarían
    # para el límite del siguiente.
    rate_limit._intentos.clear()
    yield


def test_crear_solicitud_devuelve_codigo_con_formato_esperado(db):
    r = client.post(
        "/api/v1/solicitudes-atencion",
        json={"nombre_contacto": "María López", "telefono": "999888777", "motivo": "No sé a dónde ir"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert re.fullmatch(r"JO-\d{4}-\d{6}", data["codigo"])
    assert data["estado"] == "recibida"
    assert data["area"] is None


def test_crear_solicitud_sin_telefono_ni_correo_falla(db):
    r = client.post(
        "/api/v1/solicitudes-atencion",
        json={"nombre_contacto": "María López", "motivo": "No sé a dónde ir"},
    )
    assert r.status_code == 422


def test_crear_solicitud_con_motivo_vacio_falla(db):
    r = client.post(
        "/api/v1/solicitudes-atencion",
        json={"nombre_contacto": "María López", "telefono": "999888777", "motivo": "   "},
    )
    assert r.status_code == 422


def test_codigos_correlativos_dentro_del_mismo_anio(db):
    payload = {"nombre_contacto": "Ana", "telefono": "1", "motivo": "algo"}
    r1 = client.post("/api/v1/solicitudes-atencion", json=payload)
    r2 = client.post("/api/v1/solicitudes-atencion", json=payload)
    assert r1.json()["codigo"] != r2.json()["codigo"]
    n1 = int(r1.json()["codigo"].split("-")[-1])
    n2 = int(r2.json()["codigo"].split("-")[-1])
    assert n2 == n1 + 1


def test_consultar_por_codigo_existente(db):
    creada = client.post(
        "/api/v1/solicitudes-atencion",
        json={"nombre_contacto": "Ana", "correo": "ana@example.com", "motivo": "algo"},
    ).json()
    r = client.get(f"/api/v1/solicitudes-atencion/{creada['codigo']}")
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "recibida"
    # La consulta pública no expone el dato de contacto de vuelta.
    assert "correo" not in r.json()


def test_consultar_por_codigo_inexistente_da_404(db):
    r = client.get("/api/v1/solicitudes-atencion/JO-2026-999999")
    assert r.status_code == 404


def test_limite_de_solicitudes_por_ip(db):
    payload = {"nombre_contacto": "Ana", "telefono": "1", "motivo": "algo"}
    for _ in range(5):
        assert client.post("/api/v1/solicitudes-atencion", json=payload).status_code == 200
    r = client.post("/api/v1/solicitudes-atencion", json=payload)
    assert r.status_code == 429


def test_admin_puede_listar_y_actualizar(db, admin_usuario):
    creada = client.post(
        "/api/v1/solicitudes-atencion",
        json={"nombre_contacto": "Ana", "telefono": "1", "motivo": "algo"},
    ).json()

    atoken = _login("10000001", "clave123")
    r = client.get("/api/v1/admin/solicitudes-atencion", headers=_auth(atoken))
    assert r.status_code == 200, r.text
    assert any(s["codigo"] == creada["codigo"] for s in r.json())

    solicitud_id = next(s["id"] for s in r.json() if s["codigo"] == creada["codigo"])
    r = client.put(
        f"/api/v1/admin/solicitudes-atencion/{solicitud_id}",
        json={"area": "Recursos Humanos", "estado": "derivada"},
        headers=_auth(atoken),
    )
    assert r.status_code == 200, r.text
    assert r.json()["area"] == "Recursos Humanos"
    assert r.json()["estado"] == "derivada"

    # El cambio se refleja en la consulta pública por código.
    r = client.get(f"/api/v1/solicitudes-atencion/{creada['codigo']}")
    assert r.json()["estado"] == "derivada"
    assert r.json()["area"] == "Recursos Humanos"


def test_validador_no_puede_actualizar_una_solicitud(db, sede, validador_usuario):
    creada = client.post(
        "/api/v1/solicitudes-atencion",
        json={"nombre_contacto": "Ana", "telefono": "1", "motivo": "algo"},
    ).json()
    from app import crud

    solicitud = crud.solicitud_atencion.obtener_por_codigo(db, creada["codigo"])

    vtoken = _login("10000003", "clave123")
    r = client.put(
        f"/api/v1/admin/solicitudes-atencion/{solicitud.id}",
        json={"estado": "cerrada"},
        headers=_auth(vtoken),
    )
    assert r.status_code == 403


def test_actualizar_solicitud_inexistente_da_404(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.put(
        "/api/v1/admin/solicitudes-atencion/999999",
        json={"estado": "cerrada"},
        headers=_auth(atoken),
    )
    assert r.status_code == 404
