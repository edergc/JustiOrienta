from app import crud, models


def _crear_dependencia(db, sede, **overrides):
    data = dict(
        tipo="jurisdiccional",
        nombre="11.º Juzgado Civil",
        sede_id=sede.id,
        area="Juzgado civil",
        estado="activo",
    )
    data.update(overrides)
    alias_csv = data.pop("alias", "")
    return crud.dependencias.crear(db, data, alias_csv)


def test_busqueda_encuentra_por_alias_exacto(db, sede):
    _crear_dependencia(db, sede, alias="11 civil, once civil, onceavo civil")
    resultados = crud.busqueda.buscar_dependencias(db, "once civil")
    assert len(resultados) == 1
    assert resultados[0].nombre == "11.º Juzgado Civil"


def test_busqueda_no_confunde_palabras_cortas(db, sede):
    """Regresión: 'no' no debía matchear por estar dentro de 'informaNOs' /
    'funciONa', causando falsos positivos con consultas irrelevantes."""
    _crear_dependencia(
        db, sede,
        tipo="administrativa", nombre="Coordinación de Informática", area="Informática",
        alias="informatica, soporte tecnico, mi computadora no funciona",
    )
    _crear_dependencia(
        db, sede,
        tipo="administrativa", nombre="Recursos Humanos", area="Unidad",
        alias="rrhh, personal",
    )
    resultados = crud.busqueda.buscar_dependencias(db, "mi computadora no funciona")
    nombres = [d.nombre for d in resultados]
    assert nombres == ["Coordinación de Informática"]


def test_busqueda_sin_coincidencia_no_devuelve_nada(db, sede):
    _crear_dependencia(db, sede, alias="11 civil")
    assert crud.busqueda.buscar_dependencias(db, "quiero un cafe") == []


def test_busqueda_solo_considera_dependencias_activas(db, sede):
    _crear_dependencia(db, sede, estado="revision", alias="11 civil")
    assert crud.busqueda.buscar_dependencias(db, "11 civil") == []


def test_busqueda_tolera_error_de_tipeo_como_respaldo(db, sede):
    _crear_dependencia(
        db, sede, tipo="administrativa", nombre="Coordinación de Informática",
        area="Informática", alias="informatica, soporte tecnico",
    )
    resultados = crud.busqueda.buscar_dependencias(db, "informatika")
    assert len(resultados) == 1
    assert resultados[0].nombre == "Coordinación de Informática"


def test_busqueda_por_numero_no_confunde_juzgados_similares(db, sede):
    """Regresión: al filtrar tokens de menos de 3 letras se descartaba el
    número del juzgado ("11" por ejemplo), y buscar "11 juzgado civil"
    devolvía CUALQUIER "Juzgado Civil Transitorio" en vez de nada o del
    juzgado correcto -- justo el dato más específico se estaba ignorando."""
    for i in range(1, 6):
        _crear_dependencia(
            db, sede, nombre=f"{i}.º Juzgado Civil Transitorio",
            area="Juzgado civil", alias="",
        )
    _crear_dependencia(db, sede, nombre="11.º Juzgado Civil", area="Juzgado civil", alias="")

    resultados = crud.busqueda.buscar_dependencias(db, "11 juzgado civil")
    nombres = [d.nombre for d in resultados]
    assert nombres == ["11.º Juzgado Civil"]

    # Y sigue sin confundir "5" con el "15" o el "25" de otro nombre.
    _crear_dependencia(db, sede, nombre="15.º Juzgado Civil", area="Juzgado civil", alias="")
    _crear_dependencia(db, sede, nombre="25.º Juzgado Civil", area="Juzgado civil", alias="")
    resultados5 = crud.busqueda.buscar_dependencias(db, "5 juzgado civil")
    nombres5 = [d.nombre for d in resultados5]
    assert "15.º Juzgado Civil" not in nombres5
    assert "25.º Juzgado Civil" not in nombres5


def test_busqueda_por_servicio_estructurado(db, sede):
    dep = _crear_dependencia(db, sede, tipo="administrativa", nombre="Recursos Humanos", area="Unidad")
    servicio = models.Servicio(dependencia_id=dep.id, nombre="Constancia de trabajo", estado="activo")
    db.add(servicio)
    db.commit()

    resultados = crud.busqueda.buscar_dependencias(db, "necesito una constancia de trabajo")
    assert len(resultados) == 1
    assert resultados[0].nombre == "Recursos Humanos"
