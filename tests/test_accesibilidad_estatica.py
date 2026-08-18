from fastapi.testclient import TestClient

from app.auditoria_accesibilidad import auditar_html
from app.main import app

client = TestClient(app)


def test_pagina_publica_pasa_la_auditoria_estatica():
    html = client.get("/").text
    problemas = auditar_html(html, "index.html")
    assert problemas == []


def test_panel_admin_pasa_la_auditoria_estatica():
    html = client.get("/admin").text
    problemas = auditar_html(html, "admin.html")
    assert problemas == []


def test_detecta_input_sin_label():
    html = '<html lang="es"><meta name="viewport" content=""><body><input id="x"></body></html>'
    problemas = auditar_html(html, "prueba")
    assert any("sin label" in p for p in problemas)


def test_detecta_boton_sin_nombre_accesible():
    html = '<html lang="es"><meta name="viewport" content=""><body><button></button></body></html>'
    problemas = auditar_html(html, "prueba")
    assert any("sin texto ni aria-label" in p for p in problemas)


def test_detecta_falta_de_lang():
    html = '<html><meta name="viewport" content=""><body></body></html>'
    problemas = auditar_html(html, "prueba")
    assert any("lang" in p for p in problemas)


def test_input_con_aria_label_no_marca_problema():
    html = (
        '<html lang="es"><meta name="viewport" content=""><body>'
        '<input id="x" aria-label="Buscar"></body></html>'
    )
    assert auditar_html(html, "prueba") == []


def test_checkbox_envuelto_en_label_no_marca_problema():
    html = (
        '<html lang="es"><meta name="viewport" content=""><body>'
        '<label><input type="checkbox" id="c"> Activo</label></body></html>'
    )
    assert auditar_html(html, "prueba") == []
