from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _crear_dependencia(db, sede, area="Recursos Humanos"):
    from app import crud

    data = dict(tipo="administrativa", nombre="Recursos Humanos", sede_id=sede.id, area=area, estado="activo")
    return crud.dependencias.crear(db, data, "")


def test_crear_listar_desactivar_y_reactivar_servicio(db, sede, admin_usuario):
    dep = _crear_dependencia(db, sede)
    token = _login("10000001", "clave123")

    r = client.post(
        f"/api/v1/admin/dependencias/{dep.id}/servicios",
        json={"nombre": "Presentación de escritos", "canal": "presencial"},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text
    servicio_id = r.json()["id"]

    # Visible en el listado normal.
    r2 = client.get(f"/api/v1/admin/dependencias/{dep.id}/servicios", headers=_auth(token))
    assert any(s["id"] == servicio_id for s in r2.json())

    # Se desactiva -- desaparece del listado normal (comportamiento ya existente).
    r3 = client.delete(f"/api/v1/admin/servicios/{servicio_id}", headers=_auth(token))
    assert r3.status_code == 200
    r4 = client.get(f"/api/v1/admin/dependencias/{dep.id}/servicios", headers=_auth(token))
    assert not any(s["id"] == servicio_id for s in r4.json())

    # Pero sigue siendo visible (y recuperable) con incluir_inactivos=true.
    r5 = client.get(
        f"/api/v1/admin/dependencias/{dep.id}/servicios",
        params={"incluir_inactivos": "true"},
        headers=_auth(token),
    )
    encontrado = next(s for s in r5.json() if s["id"] == servicio_id)
    assert encontrado["estado"] == "inactivo"

    # Reactivar lo devuelve al listado normal.
    r6 = client.post(f"/api/v1/admin/servicios/{servicio_id}/reactivar", headers=_auth(token))
    assert r6.status_code == 200, r6.text
    assert r6.json()["estado"] == "activo"
    r7 = client.get(f"/api/v1/admin/dependencias/{dep.id}/servicios", headers=_auth(token))
    assert any(s["id"] == servicio_id for s in r7.json())


def test_gestor_no_puede_gestionar_servicios_de_otra_area(db, sede, gestor_usuario):
    dep = _crear_dependencia(db, sede, area="Otra Área")
    token = _login("10000002", "clave123")
    r = client.post(
        f"/api/v1/admin/dependencias/{dep.id}/servicios",
        json={"nombre": "Intento"},
        headers=_auth(token),
    )
    assert r.status_code == 403


def test_reactivar_servicio_inexistente_da_404(admin_usuario):
    token = _login("10000001", "clave123")
    r = client.post("/api/v1/admin/servicios/999999/reactivar", headers=_auth(token))
    assert r.status_code == 404


def test_crear_servicio_rechaza_estado_invalido(db, sede, admin_usuario):
    dep = _crear_dependencia(db, sede)
    token = _login("10000001", "clave123")
    r = client.post(
        f"/api/v1/admin/dependencias/{dep.id}/servicios",
        json={"nombre": "Raro", "estado": "publicado"},
        headers=_auth(token),
    )
    assert r.status_code == 422


def test_consulta_no_puede_listar_dependencias_de_gestion(sede, consulta_usuario):
    token = _login("10000004", "clave123")
    r = client.get("/api/v1/admin/dependencias", headers=_auth(token))
    assert r.status_code == 403
