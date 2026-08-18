from fastapi.testclient import TestClient

from app import models
from app.main import app

client = TestClient(app)


def test_directorio_pdf_sin_filtro_no_requiere_login(sede):
    """Pensado para imprimir en un mostrador -- tiene que ser público, sin token."""
    r = client.get("/api/v1/directorio.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-"


def test_directorio_pdf_sin_dependencias_publicadas_no_falla(db, sede):
    dep = models.Dependencia(
        tipo="administrativa", nombre="Todavía en revisión", sede_id=sede.id,
        area="Recursos Humanos", estado="revision",
    )
    db.add(dep)
    db.commit()

    r = client.get("/api/v1/directorio.pdf")
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"


def test_directorio_pdf_filtrado_por_sede_inexistente_da_404():
    r = client.get("/api/v1/directorio.pdf", params={"sede_id": 999999})
    assert r.status_code == 404


def test_directorio_pdf_filtrado_por_sede_devuelve_pdf(db, sede):
    dep = models.Dependencia(
        tipo="administrativa", nombre="Módulo de Pensiones", sede_id=sede.id,
        area="Recursos Humanos", estado="activo",
    )
    db.add(dep)
    db.commit()

    r = client.get("/api/v1/directorio.pdf", params={"sede_id": sede.id})
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"


def test_directorio_pdf_no_falla_con_caracteres_fuera_de_latin1(db, sede):
    """Regresión: fpdf2 con la fuente núcleo "helvetica" solo soporta Latin-1
    -- antes de _texto_seguro(), un solo carácter fuera de ese rango (rayas
    largas, comillas curvas de Word, emoji) en cualquier campo libre rompía
    la generación de TODO el directorio en un endpoint público sin login."""
    db.add(models.Dependencia(
        tipo="administrativa", nombre="Oficina — “Atención” 😀 al ciudadano", sede_id=sede.id,
        area="Recursos Humanos", estado="activo",
        horario="Lunes–Viernes, 8:00…17:00", telefono="Anexo 123 — externo",
    ))
    db.commit()

    r = client.get("/api/v1/directorio.pdf")
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"


def test_directorio_pdf_no_incluye_contenido_en_revision(db, sede):
    """El PDF es un canal público más -- las mismas reglas que la búsqueda:
    nada en revisión llega hasta que alguien lo aprueba."""
    import io

    import pdfplumber

    db.add(models.Dependencia(
        tipo="administrativa", nombre="Publicada De Verdad", sede_id=sede.id,
        area="Recursos Humanos", estado="activo",
    ))
    db.add(models.Dependencia(
        tipo="administrativa", nombre="Todavia Sin Aprobar", sede_id=sede.id,
        area="Recursos Humanos", estado="revision",
    ))
    db.commit()

    r = client.get("/api/v1/directorio.pdf")
    assert r.status_code == 200
    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        texto = "\n".join(p.extract_text() or "" for p in pdf.pages)
    assert "Publicada De Verdad" in texto
    assert "Todavia Sin Aprobar" not in texto
