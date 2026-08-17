from app import nlp


def test_numeros_en_palabras_a_digitos():
    assert nlp.convertir_numeros("juzgado civil once") == "juzgado civil 11"
    assert nlp.convertir_numeros("juzgado civil onceavo") == "juzgado civil 11"
    assert nlp.convertir_numeros("sala treinta y dos") == "sala 32"
    assert nlp.convertir_numeros("recursos humanos") == "recursos humanos"


def test_quitar_frases_de_cortesia():
    t = nlp.interpretar("buenas tardes, ¿me podría decir dónde queda recursos humanos?")
    assert "recursos humanos" in t
    assert "buenas" not in t
    assert "podria" not in t


def test_interpretar_completo_frase_larga():
    t = nlp.interpretar("hola, quisiera saber donde puedo encontrar el once civil por favor")
    assert "11 civil" in t
    assert "hola" not in t
    assert "favor" not in t
    assert "quisiera" not in t


def test_similitud_tolera_errores_de_tipeo_menores():
    assert nlp.es_similar("informatika", "informatica")
    assert nlp.es_similar("discapasidad", "discapacidad")
    assert not nlp.es_similar("informatica", "recursos")


def test_similitud_exige_mas_cercania_en_palabras_cortas():
    # con solo 1 de tolerancia en palabras <=5, "casa" y "caja" (dist=1) son similares
    assert nlp.es_similar("casa", "caja")
    # pero "casa" y "mesa" (dist=2) no deberían serlo
    assert not nlp.es_similar("casa", "mesa")
