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


def test_detecta_mismo_nombre_repetido_en_la_misma_sede_entre_areas(db, sede, admin_usuario):
    db.add(models.Dependencia(
        tipo="administrativa", nombre="Mesa de Partes", sede_id=sede.id,
        area="Bienestar Social", estado="activo",
    ))
    db.add(models.Dependencia(
        tipo="administrativa", nombre="Mesa de Partes", sede_id=sede.id,
        area="Control de Asistencia", estado="revision",
    ))
    db.commit()

    atoken = _login("10000001", "clave123")
    r = client.get("/api/v1/admin/dependencias/duplicados", headers=_auth(atoken))
    assert r.status_code == 200, r.text
    grupos = r.json()
    assert len(grupos) == 1
    assert grupos[0]["nombre"] == "Mesa de Partes"
    assert grupos[0]["sede"] == sede.nombre
    areas = {d["area"] for d in grupos[0]["dependencias"]}
    assert areas == {"Bienestar Social", "Control de Asistencia"}


def test_no_agrupa_el_mismo_nombre_en_sedes_distintas(db, sede, admin_usuario):
    otra_sede = models.Sede(nombre="Otra Sede")
    db.add(otra_sede)
    db.commit()
    db.refresh(otra_sede)

    db.add(models.Dependencia(
        tipo="administrativa", nombre="Mesa de Partes", sede_id=sede.id, area="X", estado="activo",
    ))
    db.add(models.Dependencia(
        tipo="administrativa", nombre="Mesa de Partes", sede_id=otra_sede.id, area="X", estado="activo",
    ))
    db.commit()

    atoken = _login("10000001", "clave123")
    grupos = client.get("/api/v1/admin/dependencias/duplicados", headers=_auth(atoken)).json()
    assert grupos == []


def test_no_marca_falso_positivo_entre_juzgados_numerados_distintos(db, sede, admin_usuario):
    """Regresión a propósito: "10.º Juzgado Civil" y "11.º Juzgado Civil" son
    oficinas legítimamente distintas que solo difieren en un carácter -- el
    detector exige nombre normalizado IDÉNTICO, nunca "parecido", para no
    generar ruido con justo el caso más común de este catálogo."""
    db.add(models.Dependencia(
        tipo="jurisdiccional", nombre="10.º Juzgado Civil", sede_id=sede.id, area="Civil", estado="activo",
    ))
    db.add(models.Dependencia(
        tipo="jurisdiccional", nombre="11.º Juzgado Civil", sede_id=sede.id, area="Civil", estado="activo",
    ))
    db.commit()

    atoken = _login("10000001", "clave123")
    grupos = client.get("/api/v1/admin/dependencias/duplicados", headers=_auth(atoken)).json()
    assert grupos == []


def test_excluye_dependencias_inactivas(db, sede, admin_usuario):
    db.add(models.Dependencia(
        tipo="administrativa", nombre="Mesa de Partes", sede_id=sede.id, area="X", estado="activo",
    ))
    db.add(models.Dependencia(
        tipo="administrativa", nombre="Mesa de Partes", sede_id=sede.id, area="Y", estado="inactivo",
    ))
    db.commit()

    atoken = _login("10000001", "clave123")
    grupos = client.get("/api/v1/admin/dependencias/duplicados", headers=_auth(atoken)).json()
    assert grupos == []


def test_gestor_no_puede_ver_duplicados(gestor_usuario):
    gtoken = _login("10000002", "clave123")
    r = client.get("/api/v1/admin/dependencias/duplicados", headers=_auth(gtoken))
    assert r.status_code == 403


def test_consulta_no_puede_ver_duplicados(consulta_usuario):
    token = _login("10000004", "clave123")
    r = client.get("/api/v1/admin/dependencias/duplicados", headers=_auth(token))
    assert r.status_code == 403
