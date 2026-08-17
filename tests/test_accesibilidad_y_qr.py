from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _crear_dependencia_activa(db, sede, **extra):
    from app import crud

    data = dict(
        tipo="administrativa", nombre="Recursos Humanos", sede_id=sede.id,
        area="Recursos Humanos", estado="activo",
    )
    data.update(extra)
    return crud.dependencias.crear(db, data, "rrhh, personal")


def _token_admin():
    return client.post(
        "/api/v1/auth/login", data={"username": "10000001", "password": "clave123"}
    ).json()["access_token"]


def test_pregunta_de_accesibilidad_responde_desde_la_sede(db, sede, admin_usuario):
    sede.rampa = True
    sede.ascensor = True
    db.add(sede)
    db.commit()

    r = client.get("/api/v1/buscar", params={"q": "hay rampa de acceso", "sede_contexto": sede.id})
    assert r.status_code == 200
    data = r.json()
    assert data["sede_accesibilidad"] is not None
    assert data["sede_accesibilidad"]["rampa"] is True
    # No es un callejón sin salida aunque no haya dependencias que coincidan.
    assert data["fallback"] is False


def test_pregunta_de_accesibilidad_sin_sede_contexto_no_responde_sede(sede, admin_usuario):
    r = client.get("/api/v1/buscar", params={"q": "hay rampa de acceso"})
    assert r.status_code == 200
    assert r.json()["sede_accesibilidad"] is None


def test_indicadores_de_consulta_se_reflejan_en_metricas(db, sede, admin_usuario):
    _crear_dependencia_activa(db, sede)

    client.get(
        "/api/v1/buscar",
        params={"q": "recursos humanos", "modo_accesible": "true", "via_voz": "true"},
    )
    client.get("/api/v1/buscar", params={"q": "hay ascensor", "sede_contexto": sede.id})

    token = _token_admin()
    resumen = client.get(
        "/api/v1/admin/metricas/resumen", headers={"Authorization": f"Bearer {token}"}
    ).json()
    assert resumen["porcentaje_modo_accesible"] == 50.0
    assert resumen["porcentaje_via_voz"] == 50.0
    assert resumen["porcentaje_sobre_accesibilidad"] == 50.0
    assert any(c["sede"] == sede.nombre for c in resumen["consultas_por_sede"])


def test_instrucciones_internas_se_guarda_y_se_devuelve(db, sede, admin_usuario):
    dep = _crear_dependencia_activa(db, sede, instrucciones_internas="Sube al piso 5 por el ascensor.")
    token = _token_admin()
    r = client.get(
        f"/api/v1/admin/dependencias", headers={"Authorization": f"Bearer {token}"}
    )
    encontrada = next(d for d in r.json()["items"] if d["id"] == dep.id)
    assert encontrada["instrucciones_internas"] == "Sube al piso 5 por el ascensor."


def test_qr_de_sede_requiere_autenticacion(sede):
    r = client.get(f"/api/v1/admin/qr/sede/{sede.id}")
    assert r.status_code == 401


def test_qr_de_sede_genera_imagen_png(sede, admin_usuario):
    token = _token_admin()
    r = client.get(f"/api/v1/admin/qr/sede/{sede.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_qr_de_sede_inexistente_da_404(admin_usuario):
    token = _token_admin()
    r = client.get("/api/v1/admin/qr/sede/999999", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_qr_de_dependencia_genera_imagen_png(db, sede, admin_usuario):
    dep = _crear_dependencia_activa(db, sede)
    token = _token_admin()
    r = client.get(f"/api/v1/admin/qr/dependencia/{dep.id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
