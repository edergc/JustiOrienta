"""Limitador de tasa simple, en memoria -- sin Redis ni servicios de pago,
acorde al resto del proyecto (costo cero). Vive en el proceso: se reinicia
si el servidor se reinicia o el plan gratuito de Render lo pone a dormir.
Es una pérdida aceptable para este uso (frenar abuso obvio, no una defensa
perfecta) -- el token de un solo uso y su vencimiento de 30 minutos ya
limitan el daño real de cualquier intento que sí pase el límite.
"""
import time
from collections import defaultdict

_intentos: dict[str, list[float]] = defaultdict(list)


def permitido(clave: str, maximo: int, ventana_segundos: int) -> bool:
    """True si esta clave (ej. "olvide:12345678" o "olvide-ip:1.2.3.4")
    todavía no llegó al máximo de intentos dentro de la ventana -- y, si no
    llegó, registra este intento. Cada clave se limita por separado, así que
    llamar con dos claves distintas para un mismo pedido (ej. por DNI y por
    IP) exige que AMBAS lo permitan."""
    ahora = time.time()
    intentos = _intentos[clave]
    intentos[:] = [t for t in intentos if ahora - t < ventana_segundos]
    if len(intentos) >= maximo:
        return False
    intentos.append(ahora)
    return True
