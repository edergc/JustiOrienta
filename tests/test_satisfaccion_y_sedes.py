from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _crear_dependencia_activa(db, sede):
    from app import crud

    data = dict(
        tipo="administrativa", nombre="Recursos Humanos", sede_id=sede.id,
        area="Recursos Humanos", estado="activo",
    )
    return crud.dependencias.crear(db, data, "rrhh, personal")


def test_buscar_devuelve_consulta_id(sede, admin_usuario):
    r = client.get("/api/v1/buscar", params={"q": "recursos humanos"})
    assert r.status_code == 200
    assert r.json()["consulta_id"] is not None


def test_registrar_satisfaccion_valida_y_actualiza_metricas(db, sede, admin_usuario):
    _crear_dependencia_activa(db, sede)

    r = client.get("/api/v1/buscar", params={"q": "recursos humanos"})
    consulta_id = r.json()["consulta_id"]
    assert consulta_id is not None

    r2 = client.post(f"/api/v1/satisfaccion/{consulta_id}", json={"valor": "si"})
    assert r2.status_code == 200

    atoken = client.post(
        "/api/v1/auth/login", data={"username": "10000001", "password": "clave123"}
    ).json()["access_token"]
    resumen = client.get(
        "/api/v1/admin/metricas/resumen", headers={"Authorization": f"Bearer {atoken}"}
    ).json()
    assert resumen["respuestas_satisfaccion"] == 1
    assert resumen["porcentaje_satisfaccion"] == 100.0


def test_registrar_satisfaccion_rechaza_valor_invalido(sede, admin_usuario):
    r = client.get("/api/v1/buscar", params={"q": "algo"})
    consulta_id = r.json()["consulta_id"]
    r2 = client.post(f"/api/v1/satisfaccion/{consulta_id}", json={"valor": "excelente"})
    assert r2.status_code == 404


def test_registrar_satisfaccion_rechaza_consulta_inexistente():
    r = client.post("/api/v1/satisfaccion/999999", json={"valor": "si"})
    assert r.status_code == 404


def test_listado_publico_de_sedes_no_requiere_login(sede):
    r = client.get("/api/v1/sedes")
    assert r.status_code == 200
    nombres = [s["nombre"] for s in r.json()]
    assert sede.nombre in nombres
