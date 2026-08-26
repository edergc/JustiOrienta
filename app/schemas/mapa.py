from typing import Optional

from pydantic import BaseModel, ConfigDict


class NodoBase(BaseModel):
    sede_id: int
    piso: Optional[str] = None
    nombre: str
    es_punto_partida: bool = True
    dependencia_id: Optional[int] = None


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


class RutaOut(BaseModel):
    origen_id: int
    destino_id: int
    dependencia_nombre: str
    pasos: list[PasoRuta]
