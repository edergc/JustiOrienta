from fastapi.testclient import TestClient

from app import models
from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_login_devuelve_el_dni_del_usuario(admin_usuario):
    r = client.post(
        "/api/v1/auth/login", data={"username": "10000001", "password": "clave123"}
    )
    assert r.status_code == 200, r.text
    assert r.json()["usuario"]["dni"] == "10000001"


def test_crear_usuario_rechaza_dni_con_formato_invalido(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.post(
        "/api/v1/admin/usuarios",
        json={"nombre": "Alguien", "dni": "123", "password": "clave123", "rol": "gestor", "area": "X"},
        headers=_auth(atoken),
    )
    assert r.status_code == 422


def test_crear_usuario_rechaza_password_corta(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.post(
        "/api/v1/admin/usuarios",
        json={"nombre": "Alguien", "dni": "10000009", "password": "abc", "rol": "gestor", "area": "X"},
        headers=_auth(atoken),
    )
    assert r.status_code == 422


def test_admin_no_puede_restablecer_a_password_corta(admin_usuario, gestor_usuario):
    atoken = _login("10000001", "clave123")
    r = client.put(
        f"/api/v1/admin/usuarios/{gestor_usuario.id}",
        json={
            "nombre": gestor_usuario.nombre, "rol": "gestor", "area": gestor_usuario.area,
            "activo": True, "nueva_password": "123",
        },
        headers=_auth(atoken),
    )
    assert r.status_code == 422


def test_crear_usuario_rechaza_dni_duplicado(admin_usuario, gestor_usuario):
    atoken = _login("10000001", "clave123")
    r = client.post(
        "/api/v1/admin/usuarios",
        json={
            "nombre": "Otro Nombre", "dni": gestor_usuario.dni, "password": "clave123",
            "rol": "gestor", "area": "X",
        },
        headers=_auth(atoken),
    )
    assert r.status_code == 409


def test_cambiar_mi_password_exitoso_y_login_con_la_nueva(admin_usuario):
    token = _login("10000001", "clave123")
    r = client.put(
        "/api/v1/auth/mi-password",
        json={"password_actual": "clave123", "password_nueva": "nuevaClave456"},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text

    assert client.post(
        "/api/v1/auth/login", data={"username": "10000001", "password": "clave123"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", data={"username": "10000001", "password": "nuevaClave456"}
    ).status_code == 200


def test_cambiar_mi_password_rechaza_password_actual_incorrecta(admin_usuario):
    token = _login("10000001", "clave123")
    r = client.put(
        "/api/v1/auth/mi-password",
        json={"password_actual": "no-es-esta", "password_nueva": "nuevaClave456"},
        headers=_auth(token),
    )
    assert r.status_code == 401


def test_admin_edita_usuario_y_restablece_password(admin_usuario, gestor_usuario):
    atoken = _login("10000001", "clave123")
    r = client.put(
        f"/api/v1/admin/usuarios/{gestor_usuario.id}",
        json={
            "nombre": "Gestor Renombrado", "rol": "validador", "area": "Otra Área",
            "activo": True, "nueva_password": "otraClave789",
        },
        headers=_auth(atoken),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["nombre"] == "Gestor Renombrado"
    assert body["rol"] == "validador"
    assert body["area"] == "Otra Área"

    # la contraseña vieja ya no sirve, la nueva sí
    assert client.post(
        "/api/v1/auth/login", data={"username": "10000002", "password": "clave123"}
    ).status_code == 401
    assert client.post(
        "/api/v1/auth/login", data={"username": "10000002", "password": "otraClave789"}
    ).status_code == 200


def test_admin_no_puede_desactivar_su_propia_cuenta(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.put(
        f"/api/v1/admin/usuarios/{admin_usuario.id}",
        json={"nombre": admin_usuario.nombre, "rol": "admin", "area": None, "activo": False},
        headers=_auth(atoken),
    )
    assert r.status_code == 400


def test_admin_no_puede_quitarse_a_si_mismo_el_rol_de_admin(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.put(
        f"/api/v1/admin/usuarios/{admin_usuario.id}",
        json={"nombre": admin_usuario.nombre, "rol": "gestor", "area": "X", "activo": True},
        headers=_auth(atoken),
    )
    assert r.status_code == 400


def test_gestor_no_puede_editar_usuarios(admin_usuario, gestor_usuario):
    gtoken = _login("10000002", "clave123")
    r = client.put(
        f"/api/v1/admin/usuarios/{admin_usuario.id}",
        json={"nombre": "Hackeado", "rol": "admin", "area": None, "activo": True},
        headers=_auth(gtoken),
    )
    assert r.status_code == 403


def test_listado_de_dependencias_pagina_y_filtra_por_nombre(db, sede, admin_usuario):
    from app import crud

    for i in range(3):
        crud.dependencias.crear(
            db,
            dict(tipo="administrativa", nombre=f"Oficina {i}", sede_id=sede.id, area="X", estado="activo"),
            "",
        )

    atoken = _login("10000001", "clave123")

    r = client.get("/api/v1/admin/dependencias", params={"limite": 2}, headers=_auth(atoken))
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2

    r2 = client.get("/api/v1/admin/dependencias", params={"skip": 2, "limite": 2}, headers=_auth(atoken))
    assert len(r2.json()["items"]) == 1

    r3 = client.get("/api/v1/admin/dependencias", params={"q": "oficina 1"}, headers=_auth(atoken))
    nombres = [d["nombre"] for d in r3.json()["items"]]
    assert nombres == ["Oficina 1"]
