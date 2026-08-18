"""Auditoría de accesibilidad automatizada sobre el HTML estático servido --
una versión ligera de lo que haría axe-core, pero sin depender de Node ni de
un navegador headless: este piloto se instala con "pip install -r
requirements.txt" y nada más, así que la herramienta de auditoría tiene que
respetar esa misma regla.

Cubre las reglas de WCAG que sí se pueden verificar sobre el marcado estático
sin renderizar la página: idioma declarado, texto alternativo en imágenes,
controles de formulario con etiqueta programática, botones/enlaces con
nombre accesible, un solo <h1>, y diálogos modales con nombre accesible. NO
reemplaza una revisión real con lector de pantalla ni verifica contraste de
color (eso necesita render real) -- pero deja evidencia objetiva y repetible
en cada cambio de plantilla, y corre en cada `pytest` (ver
tests/test_accesibilidad_estatica.py).

Uso manual: `python -m app.auditoria_accesibilidad`
"""
from bs4 import BeautifulSoup

_TIPOS_SIN_LABEL_PROPIO = {"hidden", "submit", "button", "image"}


def _tiene_label(soup: BeautifulSoup, control) -> bool:
    if control.get("aria-label") or control.get("aria-labelledby"):
        return True
    id_ = control.get("id")
    if id_ and soup.find("label", attrs={"for": id_}):
        return True
    return control.find_parent("label") is not None


def auditar_html(html: str, nombre_pagina: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    problemas: list[str] = []

    html_tag = soup.find("html")
    if not html_tag or not (html_tag.get("lang") or "").strip():
        problemas.append(f"{nombre_pagina}: falta el atributo lang en <html>")

    if not soup.find("meta", attrs={"name": "viewport"}):
        problemas.append(f"{nombre_pagina}: falta <meta name=\"viewport\">")

    for img in soup.find_all("img"):
        if not (img.get("alt") or "").strip() and img.get("role") != "presentation":
            problemas.append(f"{nombre_pagina}: <img id={img.get('id')}> sin atributo alt")

    for control in soup.find_all(["input", "select", "textarea"]):
        tipo = (control.get("type") or "text").lower()
        if control.name == "input" and tipo in _TIPOS_SIN_LABEL_PROPIO:
            continue
        if not _tiene_label(soup, control):
            problemas.append(f"{nombre_pagina}: <{control.name} id={control.get('id')}> sin label asociado")

    for boton in soup.find_all(["button", "a"]):
        nombre_accesible = boton.get_text(strip=True) or boton.get("aria-label") or boton.get("title")
        if not nombre_accesible:
            problemas.append(f"{nombre_pagina}: <{boton.name} id={boton.get('id')}> sin texto ni aria-label")

    h1s = soup.find_all("h1")
    if len(h1s) > 1:
        problemas.append(f"{nombre_pagina}: hay {len(h1s)} <h1>, debería haber a lo sumo uno")

    for dialogo in soup.find_all(attrs={"role": "dialog"}):
        if not (dialogo.get("aria-label") or dialogo.get("aria-labelledby")):
            problemas.append(f"{nombre_pagina}: role=\"dialog\" sin aria-label/aria-labelledby")

    return problemas


if __name__ == "__main__":
    from pathlib import Path

    base = Path(__file__).resolve().parent / "static"
    encontrado_algo = False
    for nombre in ("index.html", "admin.html"):
        html = (base / nombre).read_text(encoding="utf-8")
        problemas = auditar_html(html, nombre)
        if problemas:
            encontrado_algo = True
            print(f"\n{nombre}: {len(problemas)} problema(s)")
            for p in problemas:
                print(f"  - {p}")
        else:
            print(f"{nombre}: sin problemas detectados")
    if not encontrado_algo:
        print("\nAuditoría estática completa, sin hallazgos.")
