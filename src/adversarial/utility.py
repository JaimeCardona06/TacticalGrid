"""
Purpose:
    Función de utilidad del juego adversarial: valora un estado desde la
    perspectiva de MAX (bando A) con una jerarquía de victorias, el avance del
    portador del recurso hacia su base y la carrera por capturarlo cuando está
    libre en el tablero, considerando TODAS las unidades de cada bando
    (modelo N vs N).

AI usage:           Yes
AI intervention:    la IA asistió en la estructuración de la jerarquía de
                    recompensas, la generalización N vs N y la refactorización
                    de la documentación.
Student validation: Validado por el equipo en la suite completa, incluido el
                    caso mínimo 6 (estado compuesto) y las simulaciones de
                    partida con varias unidades por bando.
"""


def _distancia(pos, otra):
    """Distancia Manhattan entre dos celdas (fila, columna)."""
    return abs(pos[0] - otra[0]) + abs(pos[1] - otra[1])


def evaluar_estado(estado, base_a, base_b):
    """
    Purpose:
        Calcula la función de utilidad/evaluación de un estado del juego desde la
        perspectiva del jugador MAX ('A').

    Preconditions:
        - estado: instancia válida de EstadoJuego (posiciones de todas las
          unidades de cada bando y portador como (bando, índice)).
        - base_a: Tupla (fila, columna) con la posición de la base de A.
        - base_b: Tupla (fila, columna) con la posición de la base de B.

    Postconditions:
        - Retorna un flotante/entero con la jerarquía: +10000 si gana A y
          -10000 si gana B; con portador, ±(5000 - 100·distancia del portador
          a la base propia); con el recurso libre, 50 por la unidad más cercana
          de B menos 50 por la más cercana de A.
        - Esta función es pura: no sabe a qué profundidad está el estado. La
          preferencia por ganar antes (±(10000 + profundidad restante)) la agrega
          minimax._valor_de_hoja al evaluar las hojas del árbol.

    Complexity:
        - O(u) tiempo (u = unidades de ambos bandos) y O(1) espacio.

    AI usage:           Yes
    AI intervention:    la IA escribió la jerarquía de recompensas y esta documentación.
    Student validation: Validado por el equipo en la suite completa y en las
                        simulaciones de partida, comprobando coherencia de las
                        puntuaciones (victoria, portador y carrera).
    """
    # 1. Estados Terminales de Victoria Absoluta
    if estado.es_terminal(base_a, base_b):
        return 10000.0 if estado.portador[0] == "A" else -10000.0

    # 2. Evaluación según la posición del recurso y el portador
    if estado.portador is not None:
        bando, indice = estado.portador
        if bando == "A":
            # A tiene el recurso: prioridad máxima es llegar a su base A.
            dist_a_base = _distancia(estado.pos_a[indice], base_a)
            return 5000.0 - (dist_a_base * 100.0)
        # B tiene el recurso: penalización para A si B se acerca a su base B.
        dist_b_base = _distancia(estado.pos_b[indice], base_b)
        return -(5000.0 - (dist_b_base * 100.0))

    # 3. El recurso está libre: carrera por recogerlo (unidad más cercana).
    if not estado.pos_a or not estado.pos_b:
        return 0.0
    dist_a_rec = min(_distancia(pos, estado.recurso_pos) for pos in estado.pos_a)
    dist_b_rec = min(_distancia(pos, estado.recurso_pos) for pos in estado.pos_b)
    return (dist_b_rec * 50.0) - (dist_a_rec * 50.0)
