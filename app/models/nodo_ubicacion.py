from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class NodoUbicacion(Base, TimestampMixin):
    """Un punto reconocible físicamente dentro de una sede -- el "Usted está
    aquí" de un directorio de mall, no una coordenada GPS. Wayfinding
    auto-declarado (Fase 4, "mapa interno"): el ciudadano elige en cuál de
    estos puntos está parado, no lo detecta el sistema -- un navegador no
    puede leer señal WiFi/Bluetooth para triangular posición, y esta es la
    alternativa de costo cero que sí es viable."""

    __tablename__ = "nodos_ubicacion"

    id = Column(Integer, primary_key=True, index=True)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False, index=True)
    piso = Column(String(30), nullable=True)
    nombre = Column(String(200), nullable=False)  # "Ingreso principal", "Ascensor A", "Pasillo ala este"

    # Si aparece en la lista "¿Dónde estás?" que ve el ciudadano. En falso
    # para nodos intermedios sin nada reconocible (un cruce de pasillo que
    # solo sirve para que el grafo tenga forma, pero nadie diría "estoy en
    # el cruce de pasillo 3").
    es_punto_partida = Column(Boolean, default=True)

    # Si este nodo ES (o es el más cercano a) una dependencia del catálogo
    # -- así una búsqueda normal puede ofrecer "¿cómo llego desde aquí?"
    # sin que el área tenga que mantener un segundo catálogo de ubicaciones.
    dependencia_id = Column(Integer, ForeignKey("dependencias.id"), nullable=True, index=True)

    # Posición aproximada (0-100, porcentaje del ancho/alto del plano) para
    # dibujar este punto sobre el mapa visual del piso -- solo tiene sentido
    # donde ya existe un plano dibujado (hoy, el Nivel 1 de la Sede Javier
    # Alzamora Valdez). Nulo en el resto: sin plano, no hay dónde ubicarlo,
    # y el sistema simplemente no dibuja el mapa para esos casos.
    pos_x = Column(Float, nullable=True)
    pos_y = Column(Float, nullable=True)

    sede = relationship("Sede")
    dependencia = relationship("Dependencia")

    def __repr__(self):
        return f"<NodoUbicacion {self.nombre} (sede {self.sede_id}, piso {self.piso})>"


class ConexionNodo(Base, TimestampMixin):
    """Una arista del grafo: que dos nodos son alcanzables directamente a
    pie, sin pasar por un tercero. Se guarda una sola fila por conexión y
    se usa en ambos sentidos -- pero con una instrucción de texto distinta
    para cada sentido, porque "sube la escalera" y "baja la escalera" no es
    la misma frase leída al revés."""

    __tablename__ = "conexiones_nodo"

    id = Column(Integer, primary_key=True, index=True)
    nodo_a_id = Column(Integer, ForeignKey("nodos_ubicacion.id"), nullable=False, index=True)
    nodo_b_id = Column(Integer, ForeignKey("nodos_ubicacion.id"), nullable=False, index=True)

    # Peso para la ruta más corta -- pasos aproximados, o simplemente 1 si
    # nadie lo mide: con peso uniforme, Dijkstra igual encuentra la ruta
    # con menos tramos, que ya es una respuesta útil.
    distancia = Column(Integer, default=1)

    instruccion_a_b = Column(Text, nullable=True)  # instrucción caminando de A hacia B
    instruccion_b_a = Column(Text, nullable=True)  # instrucción caminando de B hacia A

    nodo_a = relationship("NodoUbicacion", foreign_keys=[nodo_a_id])
    nodo_b = relationship("NodoUbicacion", foreign_keys=[nodo_b_id])

    def __repr__(self):
        return f"<ConexionNodo {self.nodo_a_id} <-> {self.nodo_b_id}>"
