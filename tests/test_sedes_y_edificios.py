from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_crear_y_actualizar_sede(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.post("/api/v1/admin/sedes", json={"nombre": "Sede Nueva"}, headers=_auth(atoken))
    assert r.status_code == 200, r.text
    sede = r.json()
    assert sede["estado"] == "activo"

    r2 = client.put(
        f"/api/v1/admin/sedes/{sede['id']}",
        json={"nombre": "Sede Nueva", "estado": "inactivo"},
        headers=_auth(atoken),
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["estado"] == "inactivo"


def test_gestor_no_puede_crear_sede(gestor_usuario):
    gtoken = _login("10000002", "clave123")
    r = client.post("/api/v1/admin/sedes", json={"nombre": "Intento"}, headers=_auth(gtoken))
    assert r.status_code == 403


def test_actualizar_sede_inexistente_da_404(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.put(
        "/api/v1/admin/sedes/999999", json={"nombre": "X"}, headers=_auth(atoken)
    )
    assert r.status_code == 404


def test_crear_y_actualizar_edificio(sede, admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.post(
        "/api/v1/admin/edificios",
        json={"sede_id": sede.id, "nombre": "Torre Norte", "pisos": 5},
        headers=_auth(atoken),
    )
    assert r.status_code == 200, r.text
    edificio = r.json()
    assert edificio["nombre"] == "Torre Norte"

    r2 = client.put(
        f"/api/v1/admin/edificios/{edificio['id']}",
        json={"sede_id": sede.id, "nombre": "Torre Norte Renombrada", "pisos": 6},
        headers=_auth(atoken),
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["nombre"] == "Torre Norte Renombrada"


def test_crear_edificio_rechaza_sede_inexistente(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.post(
        "/api/v1/admin/edificios",
        json={"sede_id": 999999, "nombre": "Huérfano"},
        headers=_auth(atoken),
    )
    assert r.status_code == 404


def test_actualizar_edificio_rechaza_sede_inexistente(db, sede, admin_usuario):
    from app import crud, schemas

    atoken = _login("10000001", "clave123")
    edificio = crud.edificios.crear(db, schemas.EdificioCreate(sede_id=sede.id, nombre="Torre"))
    r = client.put(
        f"/api/v1/admin/edificios/{edificio.id}",
        json={"sede_id": 999999, "nombre": "Torre"},
        headers=_auth(atoken),
    )
    assert r.status_code == 404


def test_actualizar_edificio_inexistente_da_404(sede, admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.put(
        "/api/v1/admin/edificios/999999",
        json={"sede_id": sede.id, "nombre": "X"},
        headers=_auth(atoken),
    )
    assert r.status_code == 404


def test_gestor_no_puede_crear_edificio(sede, gestor_usuario):
    gtoken = _login("10000002", "clave123")
    r = client.post(
        "/api/v1/admin/edificios",
        json={"sede_id": sede.id, "nombre": "Intento"},
        headers=_auth(gtoken),
    )
    assert r.status_code == 403


def test_listar_edificios_filtra_por_sede(db, sede, admin_usuario):
    from app import crud, models, schemas

    otra_sede = models.Sede(nombre="Otra Sede Distinta")
    db.add(otra_sede)
    db.commit()
    db.refresh(otra_sede)

    crud.edificios.crear(db, schemas.EdificioCreate(sede_id=sede.id, nombre="De esta sede"))
    crud.edificios.crear(db, schemas.EdificioCreate(sede_id=otra_sede.id, nombre="De la otra"))

    atoken = _login("10000001", "clave123")
    r = client.get("/api/v1/admin/edificios", params={"sede_id": sede.id}, headers=_auth(atoken))
    assert r.status_code == 200, r.text
    nombres = [e["nombre"] for e in r.json()]
    assert nombres == ["De esta sede"]
