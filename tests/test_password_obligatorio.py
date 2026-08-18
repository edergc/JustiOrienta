from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_usuario_nuevo_debe_cambiar_password_antes_de_usar_el_resto(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.post(
        "/api/v1/admin/usuarios",
        json={"nombre": "Nuevo", "dni": "10000009", "password": "clave123", "rol": "auditor"},
        headers=_auth(atoken),
    )
    assert r.status_code == 200, r.text
    assert r.json()["debe_cambiar_password"] is True

    ntoken = _login("10000009", "clave123")

    # /auth/yo y /auth/mi-password siguen disponibles con el cambio pendiente...
    r = client.get("/api/v1/auth/yo", headers=_auth(ntoken))
    assert r.status_code == 200
    assert r.json()["debe_cambiar_password"] is True

    # ...pero cualquier otro endpoint queda bloqueado hasta que cambie la clave.
    r = client.get("/api/v1/admin/metricas/resumen", headers=_auth(ntoken))
    assert r.status_code == 403

    r = client.put(
        "/api/v1/auth/mi-password",
        json={"password_actual": "clave123", "password_nueva": "otraclave456"},
        headers=_auth(ntoken),
    )
    assert r.status_code == 200, r.text

    # Ya cambiada, el resto del sistema queda disponible con normalidad.
    r = client.get("/api/v1/admin/metricas/resumen", headers=_auth(ntoken))
    assert r.status_code == 200
    assert client.get("/api/v1/auth/yo", headers=_auth(ntoken)).json()["debe_cambiar_password"] is False


def test_admin_restablece_password_y_vuelve_a_exigir_el_cambio(admin_usuario, gestor_usuario):
    atoken = _login("10000001", "clave123")
    gtoken = _login("10000002", "clave123")

    # El gestor de pruebas ya viene con la clave "propia" (no marcada pendiente).
    r = client.get("/api/v1/admin/metricas/resumen", headers=_auth(gtoken))
    assert r.status_code == 200

    r = client.put(
        f"/api/v1/admin/usuarios/{gestor_usuario.id}",
        json={
            "nombre": gestor_usuario.nombre, "rol": "gestor", "area": gestor_usuario.area,
            "activo": True, "nueva_password": "restablecida1",
        },
        headers=_auth(atoken),
    )
    assert r.status_code == 200, r.text
    assert r.json()["debe_cambiar_password"] is True

    gtoken2 = _login("10000002", "restablecida1")
    r = client.get("/api/v1/admin/metricas/resumen", headers=_auth(gtoken2))
    assert r.status_code == 403


def test_editar_usuario_sin_restablecer_password_no_marca_el_cambio_pendiente(admin_usuario, gestor_usuario):
    atoken = _login("10000001", "clave123")
    r = client.put(
        f"/api/v1/admin/usuarios/{gestor_usuario.id}",
        json={"nombre": "Nuevo Nombre", "rol": "gestor", "area": gestor_usuario.area, "activo": True},
        headers=_auth(atoken),
    )
    assert r.status_code == 200, r.text
    assert r.json()["debe_cambiar_password"] is False

    gtoken = _login("10000002", "clave123")
    assert client.get("/api/v1/admin/metricas/resumen", headers=_auth(gtoken)).status_code == 200
