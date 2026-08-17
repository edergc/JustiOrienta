"""Interpretación ligera de lenguaje natural para el buscador.

Deliberadamente simple: no es un modelo de lenguaje ni IA -- son reglas
explícitas y auditables, tal como exige el principio de "IA responsable" del
proyecto (nunca inventar, siempre poder explicar por qué se sugirió algo).
Sirve para que la persona no tenga que escribir el nombre oficial exacto.
"""
import re

from app.models import normalizar

# ── Frases de cortesía / relleno que no aportan a la búsqueda ──
FRASES_IGNORADAS = [
    "buenos dias", "buenas tardes", "buenas noches", "buenas",
    "por favor", "porfavor", "porfa", "disculpe", "disculpa", "disculpen",
    "oiga", "oye", "senor", "senora", "senorita",
    "me podria decir", "me puede decir", "me pueden decir",
    "podria decirme", "puede decirme", "sabe usted", "sabe donde",
    "sabes donde", "usted sabe", "me gustaria saber", "quisiera saber",
    "quisiera", "quiero saber", "quiero ir a", "necesito ir a",
    "donde esta", "donde queda", "donde puedo encontrar", "donde encuentro",
    "donde tramito", "donde presento", "donde hago", "en donde esta",
    "en donde queda", "a donde voy", "a donde debo ir", "como llego a",
    "como llegar a", "como hago para llegar a", "cual es la ubicacion de",
    "hola", "necesito", "quiero", "busco", "estoy buscando",
]

# ── Números en palabras -> dígitos (para "once civil" == "11 civil") ──
CARDINALES = {
    "cero": 0, "uno": 1, "una": 1, "un": 1, "dos": 2, "tres": 3, "cuatro": 4,
    "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
    "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
    "veinte": 20, "veintiuno": 21, "veintidos": 22, "veintitres": 23,
    "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26, "veintisiete": 27,
    "veintiocho": 28, "veintinueve": 29, "treinta": 30, "cuarenta": 40,
    "cincuenta": 50,
}

ORDINALES = {
    "primero": 1, "segundo": 2, "tercero": 3, "cuarto": 4, "quinto": 5,
    "sexto": 6, "septimo": 7, "setimo": 7, "octavo": 8, "noveno": 9,
    "decimo": 10, "undecimo": 11, "duodecimo": 12, "decimotercero": 13,
    "decimocuarto": 14, "decimoquinto": 15, "decimosexto": 16,
    "decimoseptimo": 17, "decimooctavo": 18, "decimonoveno": 19,
    "vigesimo": 20,
}

_UNIDADES_COMPUESTAS = {
    "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
}

# Sinónimos coloquiales -> término genérico. Solo vocabulario, no datos
# institucionales: no afirma a qué área corresponde, únicamente empareja
# palabras equivalentes antes de comparar contra el catálogo.
SINONIMOS = {
    "compu": "computadora", "pc": "computadora", "note": "laptop",
    "notebook": "laptop", "wifi": "internet", "wi fi": "internet",
    "correo electronico": "correo", "mail": "correo", "email": "correo",
    "cel": "telefono", "celular": "telefono",
    "rrhh": "recursos humanos", "rr hh": "recursos humanos",
    "mesa de partes virtual": "mesa de partes",
}


def _compuesto_treinta_cuarenta(match: re.Match) -> str:
    base = CARDINALES[match.group(1)]
    unidad = _UNIDADES_COMPUESTAS[match.group(2)]
    return str(base + unidad)


def convertir_numeros(texto_normalizado: str) -> str:
    """'juzgado civil once' -> 'juzgado civil 11'. También resuelve compuestos
    tipo 'treinta y dos' y sufijos coloquiales tipo 'onceavo'."""
    t = texto_normalizado

    # Compuestos: "treinta y dos", "cuarenta y uno"
    t = re.sub(
        r"\b(treinta|cuarenta)\s+y\s+(uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)\b",
        _compuesto_treinta_cuarenta,
        t,
    )

    palabras = t.split(" ")
    resultado = []
    for p in palabras:
        if p in CARDINALES:
            resultado.append(str(CARDINALES[p]))
            continue
        if p in ORDINALES:
            resultado.append(str(ORDINALES[p]))
            continue
        # Sufijo coloquial "-avo/-ava": onceavo, doceavo, veinteavo...
        if p.endswith("avo") or p.endswith("ava"):
            raiz = p[:-3]
            if raiz in CARDINALES:
                resultado.append(str(CARDINALES[raiz]))
                continue
        resultado.append(p)
    return " ".join(resultado)


def aplicar_sinonimos(texto_normalizado: str) -> str:
    t = f" {texto_normalizado} "
    for coloquial, canonico in SINONIMOS.items():
        t = t.replace(f" {coloquial} ", f" {canonico} ")
    return " ".join(t.split())


def quitar_frases_ignoradas(texto_normalizado: str) -> str:
    t = texto_normalizado
    # las frases más largas primero, para no dejar residuos de una frase corta
    # contenida dentro de una más larga
    for frase in sorted(FRASES_IGNORADAS, key=len, reverse=True):
        t = t.replace(frase, " ")
    return " ".join(t.split())


def interpretar(query: str) -> str:
    """Punto de entrada único: normaliza, resuelve números, sinónimos y
    quita relleno conversacional. Determinista y sin llamadas externas."""
    t = normalizar(query)
    t = convertir_numeros(t)
    t = aplicar_sinonimos(t)
    t = quitar_frases_ignoradas(t)
    return t


# Palabras/frases que indican que la persona pregunta por accesibilidad,
# no por una dependencia puntual. Sirve para dos cosas: (a) responder con la
# información de accesibilidad de la sede cuando no se nombra una dependencia
# específica, y (b) alimentar el indicador "consultas sobre rutas accesibles".
PALABRAS_ACCESIBILIDAD = {
    "rampa", "rampas", "ascensor", "ascensores", "accesible", "accesibilidad",
    "discapacidad", "discapacitados", "silla de ruedas", "sillas de ruedas",
    "movilidad reducida", "banio accesible", "ruta accesible",
}


def es_pregunta_de_accesibilidad(texto_normalizado: str) -> bool:
    t = f" {texto_normalizado} "
    return any(f" {palabra} " in t or t.strip() == palabra for palabra in PALABRAS_ACCESIBILIDAD)


def distancia_edicion(a: str, b: str) -> int:
    """Distancia de Levenshtein clásica (programación dinámica), sin
    dependencias externas -- para tolerar errores de tipeo menores."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    fila_anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        fila = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            costo = 0 if ca == cb else 1
            fila[j] = min(
                fila_anterior[j] + 1,      # borrar
                fila[j - 1] + 1,           # insertar
                fila_anterior[j - 1] + costo,  # sustituir
            )
        fila_anterior = fila
    return fila_anterior[-1]


def es_similar(a: str, b: str) -> bool:
    """Umbral de tolerancia a errores de tipeo, más laxo en palabras largas."""
    if a == b:
        return True
    tolerancia = 1 if len(a) <= 5 else 2
    return distancia_edicion(a, b) <= tolerancia
