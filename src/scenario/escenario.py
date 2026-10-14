from dataclasses import dataclass
from typing import Optional

from src.models.board import Board


@dataclass(frozen=True)
class Unidad:
    """Una unidad tal como viene del escenario, ya normalizada.

    bando es "A" o "B" (mayúscula); posicion es una tupla (fila, columna).
    """
    id: str
    bando: str
    tipo: str
    posicion: tuple


@dataclass(frozen=True)
class Escenario:
    """Resultado de cargar un JSON válido: todo lo que el programa necesita.

    tablero:            parte fija del mapa (Board).
    unidades, turno, recurso, portador_recurso: datos del estado inicial; el
                        constructor del estado (state.py) parte de aquí.
    profundidad_maxima_minimax: profundidad de Minimax (3 si el JSON no la trae).
    prueba:             el bloque 'prueba' tal cual, o None si no vino.
    """
    tablero: Board
    unidades: tuple
    turno: str
    recurso: tuple
    portador_recurso: Optional[str]
    profundidad_maxima_minimax: int
    prueba: Optional[dict]
