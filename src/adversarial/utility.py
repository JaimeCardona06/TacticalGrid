"""
Purpose:
    Función de utilidad del juego adversarial: valora un estado desde la
    perspectiva de MAX (bando A) con una jerarquía de victorias, el avance del
    portador del recurso hacia su base y la carrera por capturarlo cuando está
    libre en el tablero.

AI usage:           Yes
AI intervention:    la IA asistió en la estructuración de la jerarquía de
                    recompensas y la refactorización de la documentación.
Student validation: Validado por el equipo en la suite completa (244 pruebas),
                    incluido el caso mínimo 6 (estado compuesto) y las
                    simulaciones de partida.
"""


def evaluar_estado(estado, base_a, base_b):
    """
    Purpose:
        Calcula la función de utilidad/evaluación de un estado del juego desde la
        perspectiva del jugador MAX ('A').

    Preconditions:
        - estado: Instancia válida de EstadoJuego.
        - base_a: Tupla (fila, columna) con la posición de la base de A.
        - base_b: Tupla (fila, columna) con la posición de la base de B.

    Postconditions:
        - Retorna un flotante/entero representando el valor heurístico del estado.

    Complexity:
        - O(1) tiempo y espacio (cálculos de distancia Manhattan).

    AI usage:           Yes
    AI intervention:    la IA escribió la jerarquía de recompensas y esta documentación.
    Student validation: Validado por el equipo en la suite completa (244 pruebas)
                        y en las simulaciones de partida, comprobando coherencia
                        de las puntuaciones (victoria, portador y carrera).
    """
    # 1. Estados Terminales de Victoria Absoluta
    if estado.portador == "A" and estado.pos_a == base_a:
        return 10000.0
    if estado.portador == "B" and estado.pos_b == base_b:
        return -10000.0

    score = 0.0

    # 2. Evaluación según la posición del recurso y el portador
    if estado.portador == "A":
        # A tiene el recurso: Prioridad máxima es llegar a su base A
        dist_a_base = abs(estado.pos_a[0] - base_a[0]) + abs(estado.pos_a[1] - base_a[1])
        score += 5000.0 - (dist_a_base * 100.0)

    elif estado.portador == "B":
        # B tiene el recurso: Penalización para A si B se acerca a su base B
        dist_b_base = abs(estado.pos_b[0] - base_b[0]) + abs(estado.pos_b[1] - base_b[1])
        score -= (5000.0 - (dist_b_base * 100.0))

    else:
        # El recurso está libre en el tablero: Carrera por recogerlo
        dist_a_rec = abs(estado.pos_a[0] - estado.recurso_pos[0]) + abs(estado.pos_a[1] - estado.recurso_pos[1])
        dist_b_rec = abs(estado.pos_b[0] - estado.recurso_pos[0]) + abs(estado.pos_b[1] - estado.recurso_pos[1])

        score += (dist_b_rec * 50.0) - (dist_a_rec * 50.0)

    return score