from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(dni: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", data={"username": dni, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_login_incorrecto_devuelve_401(admin_usuario):
    r = client.post("/api/v1/auth/login", data={"username": "10000001", "password": "mala"})
    assert r.status_code == 401


def test_login_se_bloquea_tras_varios_intentos_fallidos(db, admin_usuario):
    """El DNI es un dato público en el Perú, no un secreto -- la protección
    real contra fuerza bruta tiene que ser esta, no la existencia del usuario."""
    from app.crud.usuarios import MAX_INTENTOS_FALLIDOS

    for _ in range(MAX_INTENTOS_FALLIDOS):
        r = client.post("/api/v1/auth/login", data={"username": "10000001", "password": "mala"})
        assert r.status_code == 401

    # Ahora incluso con la contraseña CORRECTA, el bloqueo sigue vigente --
    # si no fuera así, protegería solo al atacante que no adivinó a tiempo.
    r = client.post("/api/v1/auth/login", data={"username": "10000001", "password": "clave123"})
    assert r.status_code == 403
    assert "bloqueada" in r.json()["detail"].lower()


def test_login_correcto_resetea_el_contador_de_intentos_fallidos(admin_usuario):
    from app.crud.usuarios import MAX_INTENTOS_FALLIDOS

    for _ in range(MAX_INTENTOS_FALLIDOS - 1):
        r = client.post("/api/v1/auth/login", data={"username": "10000001", "password": "mala"})
        assert r.status_code == 401

    r = client.post("/api/v1/auth/login", data={"username": "10000001", "password": "clave123"})
    assert r.status_code == 200, r.text

    # Un intento fallido más no debe bloquear: el login correcto ya reseteó el contador.
    r = client.post("/api/v1/auth/login", data={"username": "10000001", "password": "mala"})
    assert r.status_code == 401
    r = client.post("/api/v1/auth/login", data={"username": "10000001", "password": "clave123"})
    assert r.status_code == 200, r.text


def test_admin_guarda_la_ficha_y_eso_desbloquea_al_usuario(db, admin_usuario, gestor_usuario):
    from app.crud.usuarios import MAX_INTENTOS_FALLIDOS

    for _ in range(MAX_INTENTOS_FALLIDOS):
        r = client.post("/api/v1/auth/login", data={"username": "10000002", "password": "mala"})
        assert r.status_code == 401
    r = client.post("/api/v1/auth/login", data={"username": "10000002", "password": "clave123"})
    assert r.status_code == 403

    atoken = _login("10000001", "clave123")
    r = client.put(
        f"/api/v1/admin/usuarios/{gestor_usuario.id}",
        json={"nombre": gestor_usuario.nombre, "rol": "gestor", "area": gestor_usuario.area, "activo": True},
        headers=_auth(atoken),
    )
    assert r.status_code == 200, r.text

    r = client.post("/api/v1/auth/login", data={"username": "10000002", "password": "clave123"})
    assert r.status_code == 200, r.text


def test_flujo_completo_de_publicacion(sede, admin_usuario, gestor_usuario, validador_usuario):
    gtoken = _login("10000002", "clave123")
    vtoken = _login("10000003", "clave123")

    # 1. El gestor crea contenido; aunque mande estado=activo, el servidor lo fuerza a revisión.
    payload = {
        "tipo": "administrativa",
        "nombre": "Módulo de Pensiones",
        "sede_id": sede.id,
        "area": "Recursos Humanos",
        "estado": "activo",
        "alias": "pensiones, jubilacion",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(gtoken))
    assert r.status_code == 200, r.text
    dep = r.json()
    assert dep["estado"] == "revision"
    dep_id = dep["id"]

    # 2. Todavía no aparece en la búsqueda pública.
    r = client.get("/api/v1/buscar", params={"q": "pensiones"})
    assert r.json()["fallback"] is True

    # 3. El gestor no puede autopublicarse: aunque su guardado incluya
    # estado='activo', el servidor lo mantiene en revisión en vez de publicarlo.
    r = client.put(
        f"/api/v1/admin/dependencias/{dep_id}",
        json={**payload, "estado": "activo"},
        headers=_auth(gtoken),
    )
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "revision"

    r = client.post(f"/api/v1/admin/dependencias/{dep_id}/aprobar", headers=_auth(gtoken))
    assert r.status_code == 403

    # 4. El validador de la misma área sí puede aprobar.
    r = client.post(f"/api/v1/admin/dependencias/{dep_id}/aprobar", headers=_auth(vtoken))
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "activo"

    # 5. Ahora sí aparece en la búsqueda pública.
    r = client.get("/api/v1/buscar", params={"q": "pensiones"})
    body = r.json()
    assert body["fallback"] is False
    assert body["resultados"][0]["nombre"] == "Módulo de Pensiones"

    # 6. No se puede aprobar dos veces algo que ya está activo.
    r = client.post(f"/api/v1/admin/dependencias/{dep_id}/aprobar", headers=_auth(vtoken))
    assert r.status_code == 400


def test_validador_no_puede_aprobar_fuera_de_su_area(db, sede, validador_usuario):
    from app import models

    otra = models.Dependencia(
        tipo="jurisdiccional", nombre="11.º Juzgado Civil", sede_id=sede.id,
        area="Juzgado civil", estado="revision",
    )
    db.add(otra)
    db.commit()
    db.refresh(otra)

    vtoken = _login("10000003", "clave123")
    r = client.post(f"/api/v1/admin/dependencias/{otra.id}/aprobar", headers=_auth(vtoken))
    assert r.status_code == 403


def test_gestor_no_lee_auditoria_pero_admin_si(admin_usuario, gestor_usuario):
    atoken = _login("10000001", "clave123")
    gtoken = _login("10000002", "clave123")

    assert client.get("/api/v1/admin/auditoria", headers=_auth(atoken)).status_code == 200
    assert client.get("/api/v1/admin/auditoria", headers=_auth(gtoken)).status_code == 403


def test_editar_publicado_por_gestor_lo_regresa_a_revision_sin_403(db, sede, gestor_usuario):
    """Regresión: si el formulario reenvía estado='activo' porque así estaba
    la dependencia, un(a) gestor(a) corrigiendo otro campo no debe recibir un
    403 -- el guardado se acepta y el contenido vuelve a revisión."""
    from app import models

    dep = models.Dependencia(
        tipo="administrativa", nombre="Recursos Humanos", sede_id=sede.id,
        area="Recursos Humanos", estado="activo", horario="8 a 16",
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)

    gtoken = _login("10000002", "clave123")
    payload = {
        "tipo": "administrativa",
        "nombre": "Recursos Humanos",
        "sede_id": sede.id,
        "area": "Recursos Humanos",
        "estado": "activo",  # el formulario reenvía el valor actual, sin cambiarlo
        "horario": "8 a 17",  # esto sí cambia
        "alias": "",
    }
    r = client.put(f"/api/v1/admin/dependencias/{dep.id}", json=payload, headers=_auth(gtoken))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["horario"] == "8 a 17"
    assert body["estado"] == "revision"


def test_gestor_no_puede_crear_fuera_de_su_area(sede, gestor_usuario):
    gtoken = _login("10000002", "clave123")
    payload = {
        "tipo": "jurisdiccional",
        "nombre": "Intento fuera de área",
        "sede_id": sede.id,
        "area": "Juzgado civil",  # el gestor de pruebas es de "Recursos Humanos"
        "alias": "",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(gtoken))
    assert r.status_code == 403


def test_gestor_no_puede_reasignar_area_de_su_dependencia(db, sede, gestor_usuario):
    """Regresión: puede_editar_area() solo valida el área ACTUAL de la
    dependencia -- sin este chequeo, el gestor de "Recursos Humanos" podía
    editar una dependencia propia y, en el mismo payload, cambiarle el campo
    "area" hacia "Juzgado civil", transfiriéndola fuera de su área sin que
    nadie de "Juzgado civil" lo autorizara."""
    from app import models

    dep = models.Dependencia(
        tipo="administrativa", nombre="Recursos Humanos", sede_id=sede.id,
        area="Recursos Humanos", estado="activo",
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)

    gtoken = _login("10000002", "clave123")
    payload = {
        "tipo": "administrativa",
        "nombre": "Recursos Humanos",
        "sede_id": sede.id,
        "area": "Juzgado civil",  # intenta moverla fuera de su propia área
        "estado": "activo",
        "alias": "",
    }
    r = client.put(f"/api/v1/admin/dependencias/{dep.id}", json=payload, headers=_auth(gtoken))
    assert r.status_code == 403

    db.refresh(dep)
    assert dep.area == "Recursos Humanos"  # no debe haber cambiado


def test_admin_si_puede_reasignar_area_de_una_dependencia(db, sede, admin_usuario):
    from app import models

    dep = models.Dependencia(
        tipo="administrativa", nombre="Módulo Compartido", sede_id=sede.id,
        area="Recursos Humanos", estado="activo",
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)

    atoken = _login("10000001", "clave123")
    payload = {
        "tipo": "administrativa",
        "nombre": "Módulo Compartido",
        "sede_id": sede.id,
        "area": "Juzgado civil",
        "estado": "activo",
        "alias": "",
    }
    r = client.put(f"/api/v1/admin/dependencias/{dep.id}", json=payload, headers=_auth(atoken))
    assert r.status_code == 200, r.text
    assert r.json()["area"] == "Juzgado civil"


def test_crear_dependencia_rechaza_sede_inexistente(admin_usuario):
    atoken = _login("10000001", "clave123")
    payload = {
        "tipo": "administrativa", "nombre": "Huérfana", "sede_id": 999999,
        "area": "Recursos Humanos", "alias": "",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(atoken))
    assert r.status_code == 404


def test_crear_dependencia_rechaza_edificio_de_otra_sede(db, sede, admin_usuario):
    from app import models

    otra_sede = models.Sede(nombre="Otra Sede")
    db.add(otra_sede)
    db.commit()
    db.refresh(otra_sede)
    edificio_ajeno = models.Edificio(sede_id=otra_sede.id, nombre="Torre Ajena")
    db.add(edificio_ajeno)
    db.commit()
    db.refresh(edificio_ajeno)

    atoken = _login("10000001", "clave123")
    payload = {
        "tipo": "administrativa", "nombre": "Mal Ubicada", "sede_id": sede.id,
        "edificio_id": edificio_ajeno.id, "area": "Recursos Humanos", "alias": "",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(atoken))
    assert r.status_code == 400


def test_crear_dependencia_rechaza_tipo_invalido(sede, admin_usuario):
    atoken = _login("10000001", "clave123")
    payload = {
        "tipo": "inventado", "nombre": "Tipo Raro", "sede_id": sede.id,
        "area": "Recursos Humanos", "alias": "",
    }
    r = client.post("/api/v1/admin/dependencias", json=payload, headers=_auth(atoken))
    assert r.status_code == 422


def test_crear_sede_rechaza_estado_invalido(admin_usuario):
    atoken = _login("10000001", "clave123")
    r = client.post(
        "/api/v1/admin/sedes",
        json={"nombre": "Sede Rara", "estado": "publicada"},
        headers=_auth(atoken),
    )
    assert r.status_code == 422
