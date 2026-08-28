from fastapi.testclient import TestClient

from app import correo
from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_crear_dependencia_en_revision_notifica_al_validador(db, sede, gestor_usuario, validador_usuario, monkeypatch):
    validador_usuario.email = "validador@example.com"
    db.commit()

    llamados = []
    monkeypatch.setattr(
        correo, "enviar_correo_pendiente_aprobacion",
        lambda destino, nombre, dep_nombre, area: llamados.append((destino, dep_nombre, area)),
    )

    gtoken = _login("10000002", "clave123")
    payload = {
        "tipo": "administrativa", "nombre": "Módulo de Pensiones", "sede_id": sede.id,
        "area": "Recursos Humanos", "estado": "activo", "alias": "",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(gtoken))
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "revision"

    assert llamados == [("validador@example.com", "Módulo de Pensiones", "Recursos Humanos")]


def test_editar_publicado_por_gestor_notifica_al_volver_a_revision(db, sede, gestor_usuario, validador_usuario, monkeypatch):
    from app import models

    validador_usuario.email = "validador@example.com"
    dep = models.Dependencia(
        tipo="administrativa", nombre="Recursos Humanos", sede_id=sede.id,
        area="Recursos Humanos", estado="activo", horario="8 a 16",
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)

    llamados = []
    monkeypatch.setattr(
        correo, "enviar_correo_pendiente_aprobacion",
        lambda destino, nombre, dep_nombre, area: llamados.append(dep_nombre),
    )

    gtoken = _login("10000002", "clave123")
    payload = {
        "tipo": "administrativa", "nombre": "Recursos Humanos", "sede_id": sede.id,
        "area": "Recursos Humanos", "estado": "activo", "horario": "8 a 17", "alias": "",
    }
    r = client.put(f"/api/v1/admin/dependencias/{dep.id}", json=payload, headers=_auth(gtoken))
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "revision"
    assert llamados == ["Recursos Humanos"]


def test_editar_algo_que_ya_estaba_en_revision_no_reenvia_el_correo(db, sede, gestor_usuario, validador_usuario, monkeypatch):
    """Regresión: un(a) gestor(a) guardando varias veces seguidas el mismo
    contenido en revisión no debe generar un correo por cada guardado -- solo
    la transición REAL hacia "revisión" es lo que amerita avisar."""
    from app import models

    validador_usuario.email = "validador@example.com"
    dep = models.Dependencia(
        tipo="administrativa", nombre="Ya en revisión", sede_id=sede.id,
        area="Recursos Humanos", estado="revision", horario="8 a 16",
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)

    llamados = []
    monkeypatch.setattr(
        correo, "enviar_correo_pendiente_aprobacion",
        lambda destino, nombre, dep_nombre, area: llamados.append(dep_nombre),
    )

    gtoken = _login("10000002", "clave123")
    payload = {
        "tipo": "administrativa", "nombre": "Ya en revisión", "sede_id": sede.id,
        "area": "Recursos Humanos", "estado": "revision", "horario": "8 a 18", "alias": "",
    }
    r = client.put(f"/api/v1/admin/dependencias/{dep.id}", json=payload, headers=_auth(gtoken))
    assert r.status_code == 200, r.text
    assert not llamados


def test_admin_crea_y_publica_directo_no_notifica(sede, admin_usuario, validador_usuario, monkeypatch):
    """admin nunca pasa por revisión, así que no hay a quién avisar -- de
    haber un(a) validador(a) igual no debe recibir nada."""
    llamados = []
    monkeypatch.setattr(
        correo, "enviar_correo_pendiente_aprobacion",
        lambda destino, nombre, dep_nombre, area: llamados.append(dep_nombre),
    )

    atoken = _login("10000001", "clave123")
    payload = {
        "tipo": "administrativa", "nombre": "Publicado directo", "sede_id": sede.id,
        "area": "Recursos Humanos", "estado": "activo", "alias": "",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(atoken))
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "activo"
    assert not llamados


def test_validador_sin_correo_no_rompe_el_guardado(db, sede, gestor_usuario, validador_usuario):
    """validador_usuario no tiene email por defecto -- el guardado del(a)
    gestor(a) debe seguir funcionando igual, sin intentar mandar nada."""
    gtoken = _login("10000002", "clave123")
    payload = {
        "tipo": "administrativa", "nombre": "Sin validador con correo", "sede_id": sede.id,
        "area": "Recursos Humanos", "estado": "activo", "alias": "",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(gtoken))
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "revision"


def test_fallo_al_enviar_el_correo_no_rompe_el_guardado(db, sede, gestor_usuario, validador_usuario, monkeypatch):
    """Un problema de SMTP es un problema de notificación, no del catálogo --
    el guardado del(a) gestor(a) no debe fallar por eso."""
    validador_usuario.email = "validador@example.com"
    db.commit()

    def _falla(*args, **kwargs):
        raise RuntimeError("SMTP caído")

    monkeypatch.setattr(correo, "enviar_correo_pendiente_aprobacion", _falla)

    gtoken = _login("10000002", "clave123")
    payload = {
        "tipo": "administrativa", "nombre": "A pesar del SMTP caído", "sede_id": sede.id,
        "area": "Recursos Humanos", "estado": "activo", "alias": "",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(gtoken))
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "revision"
