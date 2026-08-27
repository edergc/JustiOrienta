from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NodoBase(BaseModel):
    sede_id: int
    piso: Optional[str] = None
    nombre: str
    es_punto_partida: bool = True
    dependencia_id: Optional[int] = None
    # 0-100: porcentaje del ancho/alto del mapa visual (ver renderMapaSVG en
    # public.js) -- un valor fuera de rango dibujaría el punto fuera del
    # plano visible sin ningún aviso, así que se rechaza aquí antes de que
    # llegue a la base de datos.
    pos_x: Optional[float] = Field(default=None, ge=0, le=100)
    pos_y: Optional[float] = Field(default=None, ge=0, le=100)


class NodoCreate(NodoBase):
    pass


class NodoUpdate(NodoBase):
    pass


class NodoOut(NodoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ConexionBase(BaseModel):
    nodo_a_id: int
    nodo_b_id: int
    distancia: int = 1
    instruccion_a_b: Optional[str] = None
    instruccion_b_a: Optional[str] = None


class ConexionCreate(ConexionBase):
    pass


class ConexionUpdate(ConexionBase):
    pass


class ConexionOut(ConexionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PasoRuta(BaseModel):
    nodo_id: int
    nombre: str
    instruccion: Optional[str] = None
    # Piso y posición del nodo -- el frontend los usa para decidir si puede
    # dibujar el mapa visual de esta ruta (solo cuando TODOS los pasos caen
    # en un piso con plano dibujado y coordenadas cargadas) sin tener que
    # pedir estos datos aparte.
    piso: Optional[str] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None


class RutaOut(BaseModel):
    origen_id: int
    destino_id: int
    dependencia_nombre: str
    pasos: list[PasoRuta]
    # True cuando la dependencia no tiene un nodo propio vinculado a mano y
    # la ruta llega solo hasta un punto de referencia de su piso (ej. el hall
    # de ascensores) -- el paso final no es la puerta exacta de la oficina.
    aproximada: bool = False
