"""Ruta más corta dentro de un edificio, sobre un grafo de nodos
reconocibles físicamente (wayfinding auto-declarado -- ver
app/models/nodo_ubicacion.py). Deliberadamente simple: Dijkstra clásico
sin dependencias externas, igual de auditable que el resto del proyecto
("IA responsable": nunca inventar, siempre poder explicar el porqué)."""
import heapq
from collections import defaultdict
from typing import Optional

Grafo = dict[int, list[tuple[int, int, Optional[str]]]]  # nodo_id -> [(vecino_id, distancia, instruccion)]


def construir_grafo(conexiones) -> Grafo:
    """conexiones: lista de ConexionNodo. Cada fila se agrega en ambos
    sentidos, con la instrucción propia de cada dirección."""
    grafo: Grafo = defaultdict(list)
    for c in conexiones:
        peso = c.distancia or 1
        grafo[c.nodo_a_id].append((c.nodo_b_id, peso, c.instruccion_a_b))
        grafo[c.nodo_b_id].append((c.nodo_a_id, peso, c.instruccion_b_a))
    return grafo


def ruta_mas_corta(grafo: Grafo, origen_id: int, destino_id: int) -> Optional[list[int]]:
    """Dijkstra. Devuelve la secuencia de nodo_id del origen al destino
    (ambos incluidos), o None si no existe una ruta conectada."""
    if origen_id == destino_id:
        return [origen_id]

    distancias = {origen_id: 0}
    previos: dict[int, int] = {}
    visitados = set()
    cola = [(0, origen_id)]

    while cola:
        dist, nodo = heapq.heappop(cola)
        if nodo in visitados:
            continue
        visitados.add(nodo)
        if nodo == destino_id:
            break
        for vecino, peso, _instruccion in grafo.get(nodo, []):
            nueva_dist = dist + peso
            if vecino not in distancias or nueva_dist < distancias[vecino]:
                distancias[vecino] = nueva_dist
                previos[vecino] = nodo
                heapq.heappush(cola, (nueva_dist, vecino))

    if destino_id not in distancias:
        return None

    camino = [destino_id]
    while camino[-1] != origen_id:
        camino.append(previos[camino[-1]])
    camino.reverse()
    return camino


def instrucciones_de_ruta(grafo: Grafo, camino: list[int]) -> list[dict]:
    """Convierte la secuencia de nodo_id en pasos, cada uno con la
    instrucción de texto del tramo (según el sentido en que se recorre)."""
    pasos = []
    for actual, siguiente in zip(camino, camino[1:]):
        instruccion = None
        for vecino, _peso, texto in grafo.get(actual, []):
            if vecino == siguiente:
                instruccion = texto
                break
        pasos.append({"desde_id": actual, "hasta_id": siguiente, "instruccion": instruccion})
    return pasos
