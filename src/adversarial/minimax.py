import math

from src.adversarial.utility import evaluar_estado


def minimax_puro(estado, profundidad, es_max, tablero, base_a, base_b, stats=None, orden_direcciones=None, nivel=0):
    """Minimax tradicional (sin poda): explora el árbol completo hasta la profundidad dada.

    Purpose:            decidir la mejor acción de un bando explorando
                        exhaustivamente el árbol de decisiones adversarial,
                        alternando MAX (bando A) y MIN (bando B), sin poda.
                        Es la línea base para comparar contra alfa-beta.
    Preconditions:      estado es un EstadoJuego; profundidad es un entero >= 0
                        (límite de recursión); es_max indica si le toca a MAX;
                        tablero, base_a y base_b vienen del escenario validado;
                        stats es un diccionario mutable de métricas o None;
                        orden_direcciones es el orden de las acciones (None usa
                        el del tablero); nivel es la profundidad ya recorrida
                        desde la raíz (0 en la llamada inicial).
    Postconditions:     devuelve (mejor_valor, mejor_movimiento): la utilidad
                        desde la perspectiva de MAX y la celda (fila, columna)
                        elegida (None en las hojas). Si stats no es None,
                        acumula nodos_visitados, nodos_generados y
                        nodos_evaluados, y registra profundidad_alcanzada como
                        el mayor nivel en el que se evaluó un estado
                        (profundidad efectiva, que puede ser menor que la
                        pedida si el juego termina antes). No modifica el
                        estado ni el tablero.
    Complexity:         Tiempo O(b^d), con b = factor de ramificación y d = la
                        profundidad pedida; espacio O(d) por la pila de
                        llamadas.
    AI usage:           Yes
    AI intervention:    la IA asistió en la estructuración de la recursión y en
                        la refactorización de las métricas (profundidad efectiva).
    Student validation: Validado por el equipo con la suite completa (290 pruebas),
                        incluidos los casos mínimos 7 y 10 y la comparación de
                        nodos generados y evaluados contra alfa-beta.
    """
    if stats is not None:
        stats["nodos_visitados"] += 1

    if profundidad == 0 or estado.es_terminal(base_a, base_b):
        if stats is not None:
            stats["nodos_evaluados"] += 1
            stats["profundidad_alcanzada"] = max(stats.get("profundidad_alcanzada", 0), nivel)
        return evaluar_estado(estado, base_a, base_b), None

    sucesores = estado.sucesores(tablero, orden_direcciones=orden_direcciones)
    if stats is not None:
        stats["nodos_generados"] += len(sucesores)

    mejor_movimiento = None

    if es_max:  # Turno de MAX (Jugador A)
        max_eval = -math.inf
        for mov, nuevo_estado in sucesores:
            evaluacion, _ = minimax_puro(
                nuevo_estado, profundidad - 1, False, tablero, base_a, base_b,
                stats, orden_direcciones, nivel + 1,
            )
            if evaluacion > max_eval:
                max_eval = evaluacion
                mejor_movimiento = mov
        return max_eval, mejor_movimiento

    else:  # Turno de MIN (Jugador B)
        min_eval = math.inf
        for mov, nuevo_estado in sucesores:
            evaluacion, _ = minimax_puro(
                nuevo_estado, profundidad - 1, True, tablero, base_a, base_b,
                stats, orden_direcciones, nivel + 1,
            )
            if evaluacion < min_eval:
                min_eval = evaluacion
                mejor_movimiento = mov
        return min_eval, mejor_movimiento


def minimax_alphabeta(
    estado, profundidad, alfa, beta, es_max, tablero, base_a, base_b, stats=None,
    orden_direcciones=None, nivel=0,
):
    """Minimax con poda alfa-beta: poda las ramas que no pueden cambiar la decisión.

    Purpose:            decidir la mejor acción de un bando con el mismo
                        resultado que minimax_puro pero descartando ramas
                        irrelevantes mediante los cortes alfa y beta, para
                        reducir nodos generados, evaluados y tiempo.
    Preconditions:      estado es un EstadoJuego; profundidad es un entero >= 0;
                        alfa y beta son la mejor alternativa conocida de MAX y
                        de MIN (-inf e +inf en la raíz); es_max indica si le
                        toca a MAX; tablero, base_a y base_b vienen del
                        escenario validado; stats es un diccionario mutable de
                        métricas o None; orden_direcciones es el orden de las
                        acciones (None usa el del tablero); nivel es la
                        profundidad ya recorrida desde la raíz (0 en la
                        llamada inicial).
    Postconditions:     devuelve (mejor_valor, mejor_movimiento) igual que
                        minimax_puro con la misma profundidad, utilidad y orden
                        de acciones. Si stats no es None, acumula
                        nodos_visitados, nodos_generados, nodos_evaluados,
                        podas_alfa y podas_beta, y registra
                        profundidad_alcanzada como el mayor nivel en el que se
                        evaluó un estado (profundidad efectiva). No modifica el
                        estado ni el tablero.
    Complexity:         Tiempo O(b^d) en el peor caso y O(b^(d/2)) con buen
                        ordenamiento de acciones; espacio O(d) por la pila de
                        llamadas.
    AI usage:           Yes
    AI intervention:    la IA asistió en la estructuración de la recursión, los
                        cortes alfa-beta y la refactorización de las métricas.
    Student validation: Validado por el equipo con la suite completa (290 pruebas),
                        incluidos los casos mínimos 7, 8 y 9 (podas y orden de
                        acciones) y la prueba de profundidad efectiva.
    """
    if stats is not None:
        stats["nodos_visitados"] += 1

    # Condición de parada: límite de profundidad o estado terminal
    if profundidad == 0 or estado.es_terminal(base_a, base_b):
        if stats is not None:
            stats["nodos_evaluados"] += 1
            stats["profundidad_alcanzada"] = max(stats.get("profundidad_alcanzada", 0), nivel)
        return evaluar_estado(estado, base_a, base_b), None

    sucesores = estado.sucesores(tablero, orden_direcciones=orden_direcciones)
    if stats is not None:
        stats["nodos_generados"] += len(sucesores)

    mejor_movimiento = None

    if es_max:  # Turno de MAX (Jugador A)
        max_eval = -math.inf
        for mov, nuevo_estado in sucesores:
            evaluacion, _ = minimax_alphabeta(
                nuevo_estado, profundidad - 1, alfa, beta, False, tablero,
                base_a, base_b, stats, orden_direcciones, nivel + 1,
            )
            if evaluacion > max_eval:
                max_eval = evaluacion
                mejor_movimiento = mov
            alfa = max(alfa, evaluacion)
            if beta <= alfa:
                if stats is not None:
                    stats["podas_beta"] += 1
                break  # Corte beta (MIN ya tiene una opción mejor)
        return max_eval, mejor_movimiento

    else:  # Turno de MIN (Jugador B)
        min_eval = math.inf
        for mov, nuevo_estado in sucesores:
            evaluacion, _ = minimax_alphabeta(
                nuevo_estado, profundidad - 1, alfa, beta, True, tablero,
                base_a, base_b, stats, orden_direcciones, nivel + 1,
            )
            if evaluacion < min_eval:
                min_eval = evaluacion
                mejor_movimiento = mov
            beta = min(beta, evaluacion)
            if beta <= alfa:
                if stats is not None:
                    stats["podas_alfa"] += 1
                break  # Corte alfa (MAX ya tiene una opción mejor)
        return min_eval, mejor_movimiento
