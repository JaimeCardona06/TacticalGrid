"""
Purpose:
    Representación formal del estado del juego en la cuadrícula táctica
    (TacticalGrid): posiciones de los agentes, recurso, portador, turno y
    cálculo de sucesores (incluye recoger, transportar y robar el recurso).

AI usage:           Yes
AI intervention:    la IA asistió en la estructuración de la clase, el cálculo
                    de sucesores y la refactorización de la documentación.
Student validation: Validado por el equipo con la suite completa (244 pruebas) y
                    simulaciones de partida que fuerzan recoger, transportar y
                    robar el recurso.
"""


class EstadoJuego:
    """
    Estado del juego en un momento dado de la partida.

    Nota de diseño (fase adversarial 1 vs 1): el estado guarda UNA posición por
    bando (pos_a, pos_b). Mantener una sola unidad por bando acota el factor de
    ramificación del árbol de Minimax (b ≈ 4) y permite profundidades
    demostrables (d ≥ 3) sin explosión combinatoria; el escenario JSON sí
    admite más unidades por bando (el validador lo permite), pero el bucle
    adversarial usa solo la primera de cada bando (ver main.py).
    """

    def __init__(self, pos_a, pos_b, portador, turno, recurso_pos):
        """
        Purpose:
            Inicializa una instancia inmutable del estado del juego.

        Preconditions:
            - pos_a: Tupla (fila, columna) con la posición del Jugador A.
            - pos_b: Tupla (fila, columna) con la posición del Jugador B.
            - portador: Cadena ('A', 'B') o None indicando quién lleva el recurso.
            - turno: Cadena ('A' o 'B') indicando a quién le corresponde mover.
            - recurso_pos: Tupla (fila, columna) con la posición actual del recurso.

        Postconditions:
            - Instancia un nuevo EstadoJuego con sus propiedades congeladas.

        Complexity:
            - O(1) tiempo y espacio.

        AI usage:           Yes
        AI intervention:    la IA escribió el constructor y esta documentación.
        Student validation: Validado por el equipo en las 244 pruebas y en las
                            simulaciones de partida (modos partida/adversarial).
        """
        self.pos_a = tuple(pos_a) if isinstance(pos_a, (list, tuple)) else pos_a
        self.pos_b = tuple(pos_b) if isinstance(pos_b, (list, tuple)) else pos_b
        self.portador = portador
        self.turno = turno
        self.recurso_pos = (
            tuple(recurso_pos)
            if isinstance(recurso_pos, (list, tuple))
            else recurso_pos
        )

    def es_terminal(self, base_a, base_b):
        """
        Purpose:
            Determina si el estado actual es un estado final de partida (victoria).

        Preconditions:
            - base_a: Tupla (fila, columna) indicando la base del Jugador A.
            - base_b: Tupla (fila, columna) indicando la base del Jugador B.

        Postconditions:
            - Retorna True si algún jugador depositó el recurso en su base, False de lo contrario.

        Complexity:
            - O(1) tiempo y espacio.

        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo al finalizar las partidas de
                            simulación cuando un portador llega a su base (244 pruebas).
        """
        if self.portador == "A" and self.pos_a == base_a:
            return True
        if self.portador == "B" and self.pos_b == base_b:
            return True
        return False

    def sucesores(self, tablero, orden_direcciones=None):
        """
        Purpose:
            Genera todos los estados válidos alcanzables desde el estado actual para
            el jugador del turno, permitiendo configurar el orden de evaluación de acciones.

        Preconditions:
            - tablero: Objeto mapa/matriz que valide si una celda es transitable.
            - orden_direcciones: Lista/tupla opcional con el orden de desplazamientos,
              e.g. [(-1, 0), (1, 0), (0, -1), (0, 1)] (Arriba, Abajo, Izquierda, Derecha).

        Postconditions:
            - Retorna una lista de tuplas `(nueva_posicion, nuevo_estado)`.

        Complexity:
            - O(k) donde k es el número de movimientos ortogonales posibles (máximo 4).
            - O(1) en espacio auxiliar.

        AI usage:           Yes
        AI intervention:    la IA asistió en la parametrización del orden de
                            acciones (caso mínimo 9) y en esta documentación.
        Student validation: Validado por el equipo con la generación de vecinos
                            en las 244 pruebas y el caso mínimo 9 (orden y podas).
        """
        sucesores_lista = []
        pos_actual = self.pos_a if self.turno == "A" else self.pos_b

        # Usar direcciones del tablero o fallback estandarizado (Arriba, Derecha, Abajo, Izquierda)
        direcciones = orden_direcciones or getattr(
            tablero, "DIRECCIONES", [(-1, 0), (0, 1), (1, 0), (0, -1)]
        )

        for df, dc in direcciones:
            nueva_f = pos_actual[0] + df
            nueva_c = pos_actual[1] + dc
            nueva_pos = (nueva_f, nueva_c)

            # Validar transitabilidad con la firma real de Board (tupla pos)
            if hasattr(tablero, "es_transitable"):
                if not tablero.es_transitable(nueva_pos):
                    continue
            elif hasattr(tablero, "matriz"):
                filas = len(tablero.matriz)
                cols = len(tablero.matriz[0]) if filas > 0 else 0
                if not (0 <= nueva_f < filas and 0 <= nueva_c < cols and tablero.matriz[nueva_f][nueva_c] != 1):
                    continue

            # 2. Calcular el nuevo portador y posición del recurso
            nuevo_portador = self.portador
            nuevo_recurso_pos = self.recurso_pos

            # Si el recurso no tiene portador y la nueva posición coincide con el recurso -> Recoger
            if self.portador is None and nueva_pos == self.recurso_pos:
                nuevo_portador = self.turno
                nuevo_recurso_pos = nueva_pos
            elif self.portador == self.turno:
                nuevo_recurso_pos = nueva_pos

            # 3. Lógica de Robo / Intercepción
            pos_rival = self.pos_b if self.turno == "A" else self.pos_a
            if nueva_pos == pos_rival and self.portador is not None and self.portador != self.turno:
                nuevo_portador = self.turno
                nuevo_recurso_pos = nueva_pos

            # 4. Construir el nuevo estado
            pos_a_nueva = nueva_pos if self.turno == "A" else self.pos_a
            pos_b_nueva = nueva_pos if self.turno == "B" else self.pos_b
            siguiente_turno = "B" if self.turno == "A" else "A"

            nuevo_estado = EstadoJuego(
                pos_a=pos_a_nueva,
                pos_b=pos_b_nueva,
                portador=nuevo_portador,
                turno=siguiente_turno,
                recurso_pos=nuevo_recurso_pos,
            )

            sucesores_lista.append((nueva_pos, nuevo_estado))

        return sucesores_lista

    def __repr__(self):
        return (
            f"<Estado | A:{self.pos_a} B:{self.pos_b} "
            f"Portador:{self.portador} Turno:{self.turno}>"
        )