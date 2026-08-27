from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from app import correo
from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _pedir_token_de_reset(monkeypatch, dni: str) -> str:
    """Intercepta el enlace que se mandaría por correo (sin depender de un
    servidor SMTP real -- el propio módulo hace lo mismo cuando smtp_host no
    está configurado, ver app/correo.py) y devuelve solo el token."""
    capturado = {}

    def _fingido(destino, nombre, enlace, minutos):
        capturado["enlace"] = enlace

    monkeypatch.setattr(correo, "enviar_correo_restablecer", _fingido)
    r = client.post("/api/v1/auth/olvide-password", json={"dni": dni})
    assert r.status_code == 200, r.text
    token = parse_qs(urlparse(capturado["enlace"]).query)["reset"][0]
    assert token
    return token


def test_dni_sin_cuenta_da_error_claro(db):
    r = client.post("/api/v1/auth/olvide-password", json={"dni": "99999999"})
    assert r.status_code == 404


def test_cuenta_sin_correo_registrado_no_manda_nada_y_avisa(db, admin_usuario):
    assert admin_usuario.email is None
    r = client.post("/api/v1/auth/olvide-password", json={"dni": admin_usuario.dni})
    assert r.status_code == 409


def test_flujo_completo_de_restablecer_password(db, admin_usuario, monkeypatch):
    admin_usuario.email = "admin@example.com"
    db.commit()

    token = _pedir_token_de_reset(monkeypatch, admin_usuario.dni)

    r = client.post("/api/v1/auth/restablecer-password", json={"token": token, "nueva_password": "nuevaClave1"})
    assert r.status_code == 200, r.text

    # La nueva contraseña ya funciona para iniciar sesión...
    nuevo_token = _login(admin_usuario.dni, "nuevaClave1")
    assert client.get("/api/v1/auth/yo", headers={"Authorization": f"Bearer {nuevo_token}"}).status_code == 200

    # ...y la vieja ya no.
    r = client.post("/api/v1/auth/login", data={"username": admin_usuario.dni, "password": "clave123"})
    assert r.status_code == 401


def test_token_de_reset_es_de_un_solo_uso(db, admin_usuario, monkeypatch):
    admin_usuario.email = "admin@example.com"
    db.commit()
    token = _pedir_token_de_reset(monkeypatch, admin_usuario.dni)

    r = client.post("/api/v1/auth/restablecer-password", json={"token": token, "nueva_password": "primeraClave1"})
    assert r.status_code == 200, r.text

    # El mismo token no debe volver a servir para cambiarla otra vez.
    r = client.post("/api/v1/auth/restablecer-password", json={"token": token, "nueva_password": "segundaClave1"})
    assert r.status_code == 400


def test_token_invalido_no_funciona(db, admin_usuario):
    r = client.post(
        "/api/v1/auth/restablecer-password",
        json={"token": "token-que-nunca-se-generó", "nueva_password": "cualquierClave1"},
    )
    assert r.status_code == 400


def test_restablecer_password_no_deja_pendiente_el_cambio_obligatorio(db, admin_usuario, monkeypatch):
    """Quien restablece su propia contraseña por este flujo ya la eligió
    ella/él mismo/a -- no debe quedar forzado/a a cambiarla de nuevo al
    entrar, a diferencia de cuando un(a) admin se la restablece por otra
    persona (ver tests/test_password_obligatorio.py)."""
    admin_usuario.email = "admin@example.com"
    db.commit()
    token = _pedir_token_de_reset(monkeypatch, admin_usuario.dni)
    client.post("/api/v1/auth/restablecer-password", json={"token": token, "nueva_password": "miPropiaClave1"})

    nuevo_token = _login(admin_usuario.dni, "miPropiaClave1")
    r = client.get("/api/v1/auth/yo", headers={"Authorization": f"Bearer {nuevo_token}"})
    assert r.json()["debe_cambiar_password"] is False
