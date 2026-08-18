"""CRUD de dependencias + flujo de publicación (revisión -> aprobación) +
servicios anidados. Mount point: /api/v1/admin (ver app/main.py)."""
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from app import crud, schemas, security
from app.database import get_db
from app.deteccion_duplicados import detectar_duplicados
from app.models import Rol
from app.models.base import ahora_utc

router = APIRouter()


def _validar_referencias(db: Session, sede_id: int, edificio_id: Optional[int]) -> None:
    """SQLite no aplica las llaves foráneas de este proyecto (ver migraciones) --
    sin este chequeo, un sede_id/edificio_id inválido o de otra sede crea
    silenciosamente una dependencia huérfana que en el sitio público se ve
    como 'Sede no registrada', sin ningún error que apunte a la causa."""
    sede = crud.sedes.obtener(db, sede_id)
    if not sede:
        raise HTTPException(404, "La sede indicada no existe")
    if edificio_id is not None:
        edificio = crud.edificios.obtener(db, edificio_id)
        if not edificio:
            raise HTTPException(404, "El edificio indicado no existe")
        if edificio.sede_id != sede_id:
            raise HTTPException(400, "El edificio indicado no pertenece a la sede seleccionada")


# ── Dependencias ──────────────────────────────────────────────

@router.get("/dependencias", response_model=schemas.DependenciaListaOut)
def listar_dependencias(
    estado: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limite: int = 20,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    if usuario.rol == Rol.consulta:
        # El rol "consulta" es de indicadores/reportes, no de gestión del
        # catálogo -- sin este chequeo, cualquiera con esa cuenta podía pedir
        # este endpoint directo y ver el catálogo completo de todas las áreas,
        # incluido contenido "en revisión" todavía no publicado, aunque la
        # pestaña correspondiente esté oculta en el panel.
        raise HTTPException(403, "El rol de consulta no tiene acceso a la gestión del catálogo")
    area = None if usuario.rol == Rol.admin else usuario.area
    limite = min(limite, 100)
    deps = crud.dependencias.listar(db, area=area, estado=estado, q_nombre=q, skip=skip, limite=limite)
    total = crud.dependencias.contar(db, area=area, estado=estado, q_nombre=q)
    return schemas.DependenciaListaOut(
        items=[schemas.DependenciaOut.model_validate(d) for d in deps],
        total=total, skip=skip, limite=limite,
    )


@router.get("/dependencias/duplicados")
def duplicados_del_catalogo(
    db: Session = Depends(get_db),
    usuario=Depends(security.requiere_lectura_auditoria),
):
    """Posibles duplicados: mismo nombre (normalizado) repetido dentro de la
    misma sede, sin importar el área -- justo el patrón que ya se documentó
    y corrigió a mano una vez en 'De dónde salen los datos reales' del
    README. Es una herramienta de auditoría de calidad de datos, no de
    gestión del catálogo: mismo alcance que /admin/auditoria (admin/auditor),
    no el de gestor/validador -- el objetivo es ver duplicados ENTRE áreas,
    algo que la vista por área nunca mostraría."""
    return detectar_duplicados(db)


_ENCABEZADOS_EXPORTACION = [
    "ID interno", "Tipo", "Categoría", "Nombre oficial", "Alias",
    "Sede", "Edificio", "Piso", "Oficina", "Horario",
    "Servicios", "Requisitos", "Teléfono", "Correo",
    "Rampa", "Ascensor", "Baño accesible", "Ruta accesible",
    "Estado", "Responsable de validar", "Área", "Instrucciones internas",
]


def _si_no(v: bool) -> str:
    return "Sí" if v else "No"


@router.get("/dependencias/exportar.xlsx")
def exportar_catalogo(
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    """Todo lo cargado (no solo lo publicado), para respaldo, edición offline,
    o portarlo a otra instalación -- el complemento natural de
    `python -m app.import_excel`, que ya sabe leer estas mismas 19 primeras
    columnas en este mismo orden posicional (las columnas de más, como "Área"
    e "Instrucciones internas", las ignora sin problema al reimportar).
    Mismo alcance por área que la gestión del catálogo: nadie exporta
    contenido de un área que no podría ver en /admin/dependencias."""
    if usuario.rol == Rol.consulta:
        raise HTTPException(403, "El rol de consulta no tiene acceso a la gestión del catálogo")
    area = None if usuario.rol == Rol.admin else usuario.area
    deps = crud.dependencias.listar(db, area=area, limite=1_000_000)

    wb = Workbook()
    ws = wb.active
    ws.title = "Catálogo"
    ws.append(_ENCABEZADOS_EXPORTACION)
    for celda in ws[1]:
        celda.font = Font(bold=True)
    for dep in deps:
        ws.append([
            dep.id, dep.tipo, dep.categoria or "", dep.nombre, ", ".join(a.alias for a in dep.alias),
            dep.sede.nombre if dep.sede else "", dep.edificio.nombre if dep.edificio else "",
            dep.piso or "", dep.oficina or "", dep.horario or "",
            dep.servicios or "", dep.requisitos or "", dep.telefono or "", dep.correo or "",
            _si_no(dep.rampa), _si_no(dep.ascensor), _si_no(dep.banio_accesible), _si_no(dep.ruta_accesible),
            dep.estado, dep.responsable_validar or "", dep.area or "", dep.instrucciones_internas or "",
        ])
    for col in ws.columns:
        ancho = max((len(str(c.value)) for c in col if c.value is not None), default=10) + 2
        ws.column_dimensions[col[0].column_letter].width = min(max(ancho, 10), 50)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nombre_archivo = f"catalogo_justicia_orienta_{ahora_utc().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@router.post("/dependencias", response_model=schemas.DependenciaOut)
def crear_dependencia(
    payload: schemas.DependenciaCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    if not security.puede_editar_area(usuario, payload.area):
        raise HTTPException(403, "Solo puedes crear dependencias dentro de tu propia área")
    _validar_referencias(db, payload.sede_id, payload.edificio_id)

    data = payload.model_dump(exclude={"alias"})
    if usuario.rol != Rol.admin:
        # Nadie que no sea admin publica directamente: toda creación entra a revisión.
        data["estado"] = "revision"

    dep = crud.dependencias.crear(db, data, payload.alias)
    crud.auditoria.registrar(db, usuario.dni, "dependencia", dep.id, "CREATE", f"Creó '{dep.nombre}'")
    return schemas.DependenciaOut.model_validate(dep)


@router.put("/dependencias/{dep_id}", response_model=schemas.DependenciaOut)
def actualizar_dependencia(
    dep_id: int,
    payload: schemas.DependenciaUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar esta dependencia")
    if payload.area != dep.area and usuario.rol != Rol.admin:
        # puede_editar_area() solo valida el área ACTUAL de la dependencia --
        # sin este chequeo, un(a) gestor(a) o validador(a) podía reescribir el
        # campo "area" del payload hacia un área ajena y así "transferir" una
        # dependencia fuera de su propia área sin autorización de nadie del
        # área destino, rompiendo "cada área es dueña de su información".
        # Reasignar de área es una decisión editorial que solo admin toma.
        raise HTTPException(403, "Solo un(a) administrador(a) puede cambiar el área de una dependencia")
    _validar_referencias(db, payload.sede_id, payload.edificio_id)

    data = payload.model_dump(exclude={"alias"})
    if data.get("estado") == "activo" and not security.puede_aprobar(usuario, dep.area):
        # No se rechaza el guardado por esto: un(a) gestor(a) corrigiendo un
        # dato de algo ya publicado no debería toparse con un 403 solo porque
        # el formulario reenvía el estado actual. En cambio, cualquier edición
        # de gestor(a) vuelve a pasar por revisión -- así ningún cambio de
        # contenido llega al público sin que alguien con permiso lo revise.
        data["estado"] = "revision"

    cambios = []
    for k, v in data.items():
        if getattr(dep, k) != v:
            cambios.append(f"{k}: '{getattr(dep, k)}' -> '{v}'")

    dep = crud.dependencias.actualizar(db, dep, data, payload.alias)
    crud.auditoria.registrar(
        db, usuario.dni, "dependencia", dep.id, "UPDATE", "; ".join(cambios) or "Sin cambios detectados"
    )
    return schemas.DependenciaOut.model_validate(dep)


@router.post("/dependencias/{dep_id}/aprobar", response_model=schemas.DependenciaOut)
def aprobar_dependencia(
    dep_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_aprobar(usuario, dep.area):
        raise HTTPException(403, "Solo un(a) validador(a) de esta área o un(a) administrador(a) puede aprobar")
    if dep.estado != "revision":
        raise HTTPException(400, f"Solo se puede aprobar contenido en revisión (estado actual: {dep.estado})")

    dep = crud.dependencias.aprobar(db, dep)
    crud.auditoria.registrar(db, usuario.dni, "dependencia", dep.id, "APROBAR", f"Publicó '{dep.nombre}'")
    return schemas.DependenciaOut.model_validate(dep)


@router.post("/dependencias/{dep_id}/rechazar", response_model=schemas.DependenciaOut)
def rechazar_dependencia(
    dep_id: int,
    comentario: str = "",
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_aprobar(usuario, dep.area):
        raise HTTPException(403, "Solo un(a) validador(a) de esta área o un(a) administrador(a) puede rechazar")

    dep = crud.dependencias.enviar_a_revision(db, dep)
    detalle = f"Devolvió a revisión '{dep.nombre}'" + (f": {comentario}" if comentario else "")
    crud.auditoria.registrar(db, usuario.dni, "dependencia", dep.id, "RECHAZAR", detalle)
    return schemas.DependenciaOut.model_validate(dep)


@router.delete("/dependencias/{dep_id}")
def desactivar_dependencia(
    dep_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para modificar esta dependencia")

    crud.dependencias.desactivar(db, dep)
    crud.auditoria.registrar(db, usuario.dni, "dependencia", dep.id, "DELETE", f"Desactivó '{dep.nombre}'")
    return {"ok": True}


# ── Servicios anidados ────────────────────────────────────────

@router.get("/dependencias/{dep_id}/servicios", response_model=list[schemas.ServicioOut])
def listar_servicios(
    dep_id: int,
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    return crud.servicios.listar_por_dependencia(db, dep_id, incluir_inactivos=incluir_inactivos)


@router.post("/dependencias/{dep_id}/servicios", response_model=schemas.ServicioOut)
def crear_servicio(
    dep_id: int,
    payload: schemas.ServicioCreate,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    dep = crud.dependencias.obtener(db, dep_id)
    if not dep:
        raise HTTPException(404, "Dependencia no encontrada")
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar los servicios de esta dependencia")

    servicio = crud.servicios.crear(db, dep_id, payload)
    crud.auditoria.registrar(db, usuario.dni, "servicio", servicio.id, "CREATE", f"Creó servicio '{servicio.nombre}' en '{dep.nombre}'")
    return servicio


@router.put("/servicios/{servicio_id}", response_model=schemas.ServicioOut)
def actualizar_servicio(
    servicio_id: int,
    payload: schemas.ServicioUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    servicio = crud.servicios.obtener(db, servicio_id)
    if not servicio:
        raise HTTPException(404, "Servicio no encontrado")
    dep = crud.dependencias.obtener(db, servicio.dependencia_id)
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar este servicio")

    servicio = crud.servicios.actualizar(db, servicio, payload)
    crud.auditoria.registrar(db, usuario.dni, "servicio", servicio.id, "UPDATE", f"Actualizó servicio '{servicio.nombre}'")
    return servicio


@router.delete("/servicios/{servicio_id}")
def desactivar_servicio(
    servicio_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    servicio = crud.servicios.obtener(db, servicio_id)
    if not servicio:
        raise HTTPException(404, "Servicio no encontrado")
    dep = crud.dependencias.obtener(db, servicio.dependencia_id)
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar este servicio")

    crud.servicios.desactivar(db, servicio)
    crud.auditoria.registrar(db, usuario.dni, "servicio", servicio.id, "DELETE", f"Desactivó servicio '{servicio.nombre}'")
    return {"ok": True}


@router.post("/servicios/{servicio_id}/reactivar", response_model=schemas.ServicioOut)
def reactivar_servicio(
    servicio_id: int,
    db: Session = Depends(get_db),
    usuario=Depends(security.get_usuario_actual),
):
    servicio = crud.servicios.obtener(db, servicio_id)
    if not servicio:
        raise HTTPException(404, "Servicio no encontrado")
    dep = crud.dependencias.obtener(db, servicio.dependencia_id)
    if not security.puede_editar_area(usuario, dep.area):
        raise HTTPException(403, "No tienes permiso para editar este servicio")

    servicio = crud.servicios.reactivar(db, servicio)
    crud.auditoria.registrar(db, usuario.dni, "servicio", servicio.id, "REACTIVAR", f"Reactivó servicio '{servicio.nombre}'")
    return servicio
