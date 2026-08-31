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


def test_pregunta_de_accesibilidad_reconoce_la_frase_exacta():
    assert nlp.es_pregunta_de_accesibilidad(nlp.interpretar("hay rampa de acceso"))
    assert nlp.es_pregunta_de_accesibilidad(nlp.interpretar("tienen ascensor"))
    assert not nlp.es_pregunta_de_accesibilidad(nlp.interpretar("recursos humanos"))


def test_pregunta_de_accesibilidad_tolera_errores_de_tipeo():
    # igual que el resto del buscador -- no debería ser la única parte
    # que exige ortografía perfecta
    assert nlp.es_pregunta_de_accesibilidad(nlp.interpretar("hay rrampa"))
    assert nlp.es_pregunta_de_accesibilidad(nlp.interpretar("es acesible"))


def test_detecta_senales_de_perfil_dentro_de_una_busqueda_normal():
    # A diferencia de es_pregunta_de_accesibilidad (toda la consulta ES
    # sobre accesibilidad), esto detecta la señal aunque venga junto con
    # una búsqueda real de una dependencia.
    t = nlp.interpretar("recursos humanos, mi mama usa silla de ruedas")
    assert nlp.detectar_senales_perfil(t) == ["motora"]

    t = nlp.interpretar("juzgado de familia para un adulto mayor")
    assert nlp.detectar_senales_perfil(t) == ["adulto_mayor"]

    t = nlp.interpretar("recursos humanos")
    assert nlp.detectar_senales_perfil(t) == []


def test_detecta_varias_senales_de_perfil_a_la_vez():
    t = nlp.interpretar("soy adulto mayor y tengo dificultad visual")
    assert set(nlp.detectar_senales_perfil(t)) == {"adulto_mayor", "visual"}


def test_senales_de_perfil_no_se_disparan_con_palabras_sueltas_sin_relacion():
    t = nlp.interpretar("mesa de partes")
    assert nlp.detectar_senales_perfil(t) == []
