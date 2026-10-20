import time

from src.adversarial.desempate import ESTRATEGIAS_DE_ROBO, PERSECUCION, clave_de_avance
from src.adversarial.minimax import minimax_alphabeta, minimax_puro


class MinimaxAgent:
    """Agente adversarial: decide con Minimax y verifica la legalidad de su acción.

    Purpose:            envolver la búsqueda adversarial (Minimax puro o
                        alfa-beta) para un bando, devolviendo la acción elegida
                        junto con las métricas del enunciado (nodos generados,
                        evaluados, podas, profundidad efectiva, tiempo, acción
                        y valor) y un verificador propio de legalidad que
                        comprueba la acción contra los datos crudos del
                        tablero, sin confiar en los sucesores generados.
    Preconditions:      nombre es "A" (MAX) o "B" (MIN); profundidad es un
                        entero >= 1; usar_poda elige alfa-beta (True) o Minimax
                        puro (False); orden_direcciones es el orden de las
                        acciones (None usa el del tablero).
    Postconditions:     seleccionar_movimiento devuelve (acción, métricas) y
                        verificar_accion valida acciones individuales. El
                        agente no modifica el estado ni el tablero.
    Complexity:         O(1) por instancia; cada decisión cuesta lo que la
                        búsqueda elegida (O(b^d) puro; O(b^(d/2)) alfa-beta con
                        buen orden de acciones).
    AI usage:           Yes
    AI intervention:    la IA asistió en la estructuración del agente, la
                        refactorización de las métricas y el verificador de
                        legalidad.
    Student validation: Validado por el equipo con la suite completa (375 pruebas),
                        incluida la legalidad de la acción elegida, y con las
                        simulaciones de partida de los modos partida/adversarial.
    """

    def __init__(self, nombre, profundidad=3, usar_poda=True, orden_direcciones=None,
                 desempatar_por_avance=False, estrategia_robo=PERSECUCION):
        """Crea el agente de un bando con la configuración de búsqueda dada.

        Purpose:            fijar los parámetros del agente (bando, profundidad,
                            algoritmo con o sin poda, orden de acciones y si
                            desempata por avance entre acciones de igual valor).
        Preconditions:      nombre es "A" o "B"; profundidad es un entero >= 1;
                            usar_poda es booleano; orden_direcciones es None o
                            una secuencia de desplazamientos (df, dc);
                            desempatar_por_avance es booleano (False por defecto:
                            se conserva la primera acción óptima del orden);
                            estrategia_robo es "persecucion" (por defecto) o
                            "intercepcion" (cómo desempata cuando el rival lleva el
                            recurso; solo importa si desempatar_por_avance es True).
        Postconditions:     instancia lista para decidir y verificar; no toca
                            el estado del juego.
        Complexity:         O(1) tiempo y espacio.
        AI usage:           Yes
        AI intervention:    la IA escribió el constructor y esta documentación.
        Student validation: Validado por el equipo instanciando agentes en las
                            375 pruebas y en las simulaciones de partida.
        """
        self.nombre = nombre
        self.profundidad = profundidad
        self.usar_poda = usar_poda
        self.orden_direcciones = orden_direcciones
        self.desempatar_por_avance = desempatar_por_avance
        if estrategia_robo not in ESTRATEGIAS_DE_ROBO:
            raise ValueError(f"estrategia_robo desconocida: {estrategia_robo!r}. Opciones: {list(ESTRATEGIAS_DE_ROBO)}")
        self.estrategia_robo = estrategia_robo

    def seleccionar_movimiento(self, estado, tablero, base_a, base_b):
        """Elige la mejor acción del bando y devuelve las métricas del turno.

        Purpose:            llamar a la búsqueda adversarial con la configuración
                            del agente, medir el tiempo y reportar las métricas
                            del enunciado, incluida la profundidad efectiva y
                            la verificación de legalidad de la acción elegida.
        Preconditions:      estado es el EstadoJuego en el turno de
                            self.nombre; tablero, base_a y base_b vienen del
                            escenario validado.
        Postconditions:     devuelve (accion, metricas): accion es
                            (índice de unidad, celda destino) elegida o None si
                            no hay acciones legales; metricas trae accion, accion_legal,
                            detalle_legalidad, valor_obtenido, tiempo_ms,
                            nodos_visitados, nodos_generados, nodos_evaluados,
                            podas_totales, podas_alfa, podas_beta y
                            profundidad_alcanzada (efectiva). No modifica el
                            estado.
        Complexity:         O(b^d) con Minimax puro y O(b^(d/2)) con alfa-beta
                            (buen orden); espacio O(d) por la recursión.
        AI usage:           Yes
        AI intervention:    la IA asistió en la integración de las métricas, la
                            latencia y la refactorización de la salida.
        Student validation: Validado por el equipo comparando las métricas de
                            partida/adversarial con los 375 tests y verificando
                            que la acción elegida siempre es legal.
        """
        es_max = self.nombre == "A"

        stats = {
            "nodos_visitados": 0,
            "nodos_generados": 0,
            "nodos_evaluados": 0,
            "podas_alfa": 0,
            "podas_beta": 0,
            "profundidad_alcanzada": 0,
        }

        t_inicio = time.perf_counter()

        if self.usar_poda:
            valor, mejor_movimiento = minimax_alphabeta(
                estado, self.profundidad, float("-inf"), float("inf"), es_max,
                tablero, base_a, base_b, stats, self.orden_direcciones,
            )
        else:
            valor, mejor_movimiento = minimax_puro(
                estado, self.profundidad, es_max, tablero, base_a, base_b,
                stats, self.orden_direcciones,
            )

        empatadas = None
        if self.desempatar_por_avance and mejor_movimiento is not None:
            mejor_movimiento, empatadas = self._desempatar(
                estado, tablero, base_a, base_b, valor, mejor_movimiento, es_max)

        t_fin = time.perf_counter()
        legal, detalle = self.verificar_accion(estado, tablero, mejor_movimiento)

        metricas = {
            "acciones_empatadas": empatadas,
            "accion": mejor_movimiento,
            "accion_legal": legal,
            "detalle_legalidad": detalle,
            "valor_obtenido": valor,
            "tiempo_ms": (t_fin - t_inicio) * 1000.0,
            "nodos_visitados": stats["nodos_visitados"],
            "nodos_generados": stats["nodos_generados"],
            "nodos_evaluados": stats["nodos_evaluados"],
            "podas_totales": stats["podas_alfa"] + stats["podas_beta"],
            "podas_alfa": stats["podas_alfa"],
            "podas_beta": stats["podas_beta"],
            "profundidad_alcanzada": stats.get("profundidad_alcanzada", 0),
        }
        return mejor_movimiento, metricas

    def _desempatar(self, estado, tablero, base_a, base_b, valor, mejor_movimiento, es_max):
        """Entre las acciones con el MISMO valor Minimax, elige la que más avanza.

        Purpose:            evitar que un bando que no puede cambiar el valor dentro
                            del horizonte mueva siempre la primera unidad del orden
                            (fichas que "deambulan"): entre las acciones óptimas
                            empatadas elige la de menor clave de avance (ver
                            desempate.clave_de_avance).
        Preconditions:      valor y mejor_movimiento son lo que devolvió la búsqueda
                            sobre `estado` para este agente; es_max indica si el
                            agente es MAX.
        Postconditions:     devuelve (accion, cantidad_de_empatadas). Solo se
                            consideran acciones cuyo valor exacto es igual a
                            `valor`: nunca elige una acción peor ni cambia el valor.
                            Cada acción se comprueba con alfa-beta en la ventana
                            estrecha (valor - 0.5, valor + 0.5), que devuelve el
                            valor exacto si coincide y una cota fuera de la ventana
                            si no. Si hay un empate de clave, gana la primera del
                            orden de generación. No cuenta en las métricas de
                            nodos del agente y no modifica el estado.
        Complexity:         hasta u*4 búsquedas de profundidad d-1 con ventana
                            estrecha, más un BFS por origen nuevo (O(f*c)).
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo con tests/test_desempate.py:
                            elige la acción que avanza entre las empatadas, nunca
                            cambia el valor y es independiente del orden de las
                            acciones.
        """
        base_propia, base_rival = (base_a, base_b) if self.nombre == "A" else (base_b, base_a)
        cache = {}
        candidatas = []
        for movimiento, hijo in estado.sucesores(tablero, orden_direcciones=self.orden_direcciones):
            if movimiento == mejor_movimiento:
                candidatas.append((movimiento, hijo))
                continue
            valor_hijo, _ = minimax_alphabeta(
                hijo, self.profundidad - 1, valor - 0.5, valor + 0.5, not es_max,
                tablero, base_a, base_b, None, self.orden_direcciones,
            )
            if abs(valor_hijo - valor) < 0.5:
                candidatas.append((movimiento, hijo))
        elegida = min(candidatas, key=lambda c: clave_de_avance(c[1], self.nombre, tablero, base_propia, base_rival, cache,
                                                      self.estrategia_robo))
        return elegida[0], len(candidatas)

    def verificar_accion(self, estado, tablero, accion):
        """Verifica, con datos crudos del tablero, que una acción sea legal.

        Purpose:            comprobar, sin confiar en los sucesores que la
                            propia búsqueda generó, que la acción elegida es
                            legal dentro de las reglas del juego: mover la
                            unidad indicada a una celda a distancia Manhattan 1,
                            dentro del mapa y transitable según el catálogo de
                            terrenos del escenario.
        Preconditions:      estado es un EstadoJuego en el turno de self.nombre;
                            tablero tiene terreno (matriz de nombres) y
                            tipos_terreno (catálogo con "transitable");
                            accion es (índice de unidad, celda destino) o None.
        Postconditions:     devuelve (legal, descripcion): legal es True solo
                            si el índice existe en el bando y la celda destino
                            es una vecina ortogonal transitable de esa unidad;
                            descripcion explica el motivo cuando es ilegal. No
                            usa los métodos de Board ni modifica nada.
        Complexity:         O(1) en tiempo y espacio.
        AI usage:           Yes
        AI intervention:    la IA escribió el verificador y esta documentación.
        Student validation: Validado por el equipo con pruebas dedicadas de
                            muros, celdas no vecinas, índices inexistentes y
                            celdas fuera del mapa, dentro de la suite completa.
        """
        if accion is None:
            return False, "el agente no devolvió ninguna acción"

        if not (isinstance(accion, (tuple, list)) and len(accion) == 2):
            return False, f"la acción {accion!r} no es (índice de unidad, celda)"
        indice, destino = accion

        if not (isinstance(indice, int) and not isinstance(indice, bool)):
            return False, f"el índice de unidad {indice!r} no es un entero"

        if not (isinstance(destino, (tuple, list)) and len(destino) == 2
                and all(isinstance(v, int) and not isinstance(v, bool) for v in destino)):
            return False, f"la celda destino {destino!r} no es (fila, columna) de enteros"
        fila, columna = destino

        posiciones = estado.pos_a if self.nombre == "A" else estado.pos_b
        if not (0 <= indice < len(posiciones)):
            return False, f"la unidad {indice} no existe en el bando {self.nombre}"
        origen = posiciones[indice]

        if abs(fila - origen[0]) + abs(columna - origen[1]) != 1:
            return False, f"la celda {destino} no es vecina ortogonal de {origen}"

        terreno = tablero.terreno
        if not (0 <= fila < len(terreno) and 0 <= columna < len(terreno[fila])):
            return False, f"la celda {destino} está fuera del mapa"

        tipo = tablero.tipos_terreno.get(terreno[fila][columna])
        if not isinstance(tipo, dict) or not tipo.get("transitable"):
            return False, f"la celda {destino} ({terreno[fila][columna]}) no es transitable"

        return True, f"la celda {destino} es vecina de {origen} y su terreno es transitable"
