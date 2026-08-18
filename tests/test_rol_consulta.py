from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_consulta_puede_ver_el_resumen_de_metricas(consulta_usuario):
    token = _login("10000004", "clave123")
    r = client.get("/api/v1/admin/metricas/resumen", headers=_auth(token))
    assert r.status_code == 200, r.text


def test_consulta_puede_descargar_el_reporte(consulta_usuario):
    token = _login("10000004", "clave123")
    r = client.get("/api/v1/admin/metricas/reporte.xlsx", headers=_auth(token))
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert r.content[:2] == b"PK"  # firma de archivo zip/xlsx


def test_consulta_no_puede_ver_la_auditoria_detallada(consulta_usuario):
    token = _login("10000004", "clave123")
    r = client.get("/api/v1/admin/auditoria", headers=_auth(token))
    assert r.status_code == 403


def test_gestor_no_puede_descargar_el_reporte(gestor_usuario):
    token = _login("10000002", "clave123")
    r = client.get("/api/v1/admin/metricas/reporte.xlsx", headers=_auth(token))
    assert r.status_code == 403


def test_consulta_no_puede_crear_ni_editar_dependencias(sede, consulta_usuario):
    token = _login("10000004", "clave123")
    r = client.post(
        "/api/v1/admin/dependencias",
        json={"tipo": "administrativa", "nombre": "Intento", "sede_id": sede.id, "area": "X", "alias": ""},
        headers=_auth(token),
    )
    assert r.status_code == 403


def test_consulta_no_puede_crear_usuarios(consulta_usuario):
    token = _login("10000004", "clave123")
    r = client.post(
        "/api/v1/admin/usuarios",
        json={"nombre": "Intento", "dni": "10000099", "password": "clave123", "rol": "gestor", "area": "X"},
        headers=_auth(token),
    )
    assert r.status_code == 403


def test_admin_puede_crear_usuario_con_rol_consulta(admin_usuario):
    token = _login("10000001", "clave123")
    r = client.post(
        "/api/v1/admin/usuarios",
        json={"nombre": "Nueva Consulta", "dni": "10000005", "password": "clave123", "rol": "consulta"},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["rol"] == "consulta"
