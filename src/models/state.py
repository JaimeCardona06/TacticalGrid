"""
Purpose:
    Representación formal del estado del juego en la cuadrícula táctica
    (TacticalGrid): posiciones de TODAS las unidades de ambos bandos, recurso,
    portador, turno y cálculo de sucesores (incluye recoger, transportar y
    robar el recurso).

AI usage:           Yes
AI intervention:    la IA asistió en la estructuración de la clase, la
                    generalización N vs N del estado, el cálculo de sucesores y
                    la refactorización de la documentación.
Student validation: Validado por el equipo con la suite completa y las
                    simulaciones de partida (modos partida/adversarial), que
                    fuerzan recoger, transportar y robar el recurso con varias
                    unidades por bando.
"""


def _normalizar_posiciones(posiciones):
    """Acepta una celda (fila, columna) o una secuencia de celdas y devuelve
    siempre una tupla de celdas: (fila, columna) -> ((fila, columna),)."""
    if posiciones is None:
        return ()
    if (isinstance(posiciones, (list, tuple)) and len(posiciones) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) for v in posiciones)):
        return (tuple(posiciones),)
    return tuple(tuple(celda) for celda in posiciones)


def _normalizar_portador(portador):
    """Acepta None, 'A'/'B' (una sola unidad por bando) o (bando, indice)."""
    if portador is None:
        return None
    if isinstance(portador, str):
        return (portador, 0)
    return (portador[0], int(portador[1]))


def _es_transitable(tablero, posicion):
    """Valida una celda contra el tablero real (o el fallback de matriz)."""
    if hasattr(tablero, "es_transitable"):
        return tablero.es_transitable(posicion)
    fila, columna = posicion
    filas = len(tablero.matriz)
    cols = len(tablero.matriz[0]) if filas > 0 else 0
    return 0 <= fila < filas and 0 <= columna < cols and tablero.matriz[fila][columna] != 1


class EstadoJuego:
    """
    Estado del juego en un momento dado de la partida.

    Modelo N vs N: el estado guarda las posiciones de todas las unidades de
    cada bando (pos_a, pos_b como tuplas de celdas, en el orden de las unidades
    del escenario) y el portador del recurso como identidad de unidad
    (bando, índice). El factor de ramificación por turno es (unidades del bando
    en turno) × (hasta 4 direcciones): con 3 unidades por bando queda acotado en
    12, lo que mantiene demostrables las profundidades limitadas de Minimax y
    alfa-beta. Las unidades pueden compartir celda (no hay bloqueo).
    """

    def __init__(self, pos_a, pos_b, portador, turno, recurso_pos):
        """
        Purpose:
            Inicializa una instancia inmutable del estado del juego.

        Preconditions:
            - pos_a / pos_b: secuencia de celdas (fila, columna) de cada bando;
              también se acepta una celda suelta (se normaliza a una tupla de
              una unidad) por compatibilidad con las pruebas 1 vs 1.
            - portador: (bando, índice), o 'A'/'B' (equivale al índice 0), o
              None si el recurso está libre.
            - turno: 'A' o 'B' indicando a quién le corresponde mover.
            - recurso_pos: celda (fila, columna) con la posición actual del
              recurso (la del portador cuando alguien lo transporta).

        Postconditions:
            - Instancia un nuevo EstadoJuego con sus propiedades congeladas.

        Complexity:
            - O(u) tiempo y espacio por la normalización de las posiciones.

        AI usage:           Yes
        AI intervention:    la IA escribió el constructor y esta documentación.
        Student validation: Validado por el equipo en la suite completa y las
                            simulaciones de partida (modos partida/adversarial).
        """
        self.pos_a = _normalizar_posiciones(pos_a)
        self.pos_b = _normalizar_posiciones(pos_b)
        self.portador = _normalizar_portador(portador)
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
            - Retorna True si la unidad que transporta el recurso está sobre la
              base de su propio bando; False de lo contrario (incluido el
              recurso sin portador).

        Complexity:
            - O(1) tiempo y espacio.

        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo al finalizar las partidas de
                            simulación cuando un portador llega a su base.
        """
        if self.portador is None:
            return False
        bando, indice = self.portador
        posiciones = self.pos_a if bando == "A" else self.pos_b
        if not (0 <= indice < len(posiciones)):
            return False
        return posiciones[indice] == (base_a if bando == "A" else base_b)

    def sucesores(self, tablero, orden_direcciones=None):
        """
        Purpose:
            Genera todos los estados válidos alcanzables desde el estado actual
            para el jugador del turno: una acción por unidad del bando (mover a
            una celda vecina transitable, en el orden de direcciones dado).

        Preconditions:
            - tablero: Objeto mapa que valide si una celda es transitable.
            - orden_direcciones: Lista/tupla opcional con el orden de
              desplazamientos, e.g. [(-1, 0), (1, 0), (0, -1), (0, 1)]
              (Arriba, Abajo, Izquierda, Derecha).

        Postconditions:
            - Retorna una lista de tuplas `(accion, nuevo_estado)`, con
              accion = (índice de la unidad en su bando, celda destino). El
              orden es por unidad (orden del escenario) y, dentro de cada
              unidad, el orden de las direcciones; solo se incluyen celdas
              transitables. Una unidad sin recurso que entra a la celda del
              recurso libre lo recoge; si el portador se mueve, el recurso viaja
              con él; si una unidad entra a la celda del portador rival, le roba
              el recurso. No modifica el estado.

        Complexity:
            - O(u · d) tiempo (u unidades del bando en turno, d ≤ 4
              direcciones) y O(u) espacio auxiliar.

        AI usage:           Yes
        AI intervention:    la IA asistió en la generalización N vs N del
                            cálculo de sucesores y en esta documentación.
        Student validation: Validado por el equipo con la generación de vecinos
                            en la suite completa y el caso mínimo 9 (orden y
                            podas).
        """
        sucesores_lista = []
        bando = self.turno
        posiciones = list(self.pos_a if bando == "A" else self.pos_b)

        # Usar direcciones del tablero o fallback estandarizado (Arriba, Derecha, Abajo, Izquierda)
        direcciones = orden_direcciones or getattr(
            tablero, "DIRECCIONES", [(-1, 0), (0, 1), (1, 0), (0, -1)]
        )

        for indice, (fila, columna) in enumerate(posiciones):
            for df, dc in direcciones:
                nueva_pos = (fila + df, columna + dc)

                # Validar transitabilidad con la firma real de Board (tupla pos)
                if not _es_transitable(tablero, nueva_pos):
                    continue

                # 1. Calcular el nuevo portador y posición del recurso
                nuevo_portador = self.portador
                nuevo_recurso_pos = self.recurso_pos

                # El recurso libre se recoge al entrar a su celda.
                if self.portador is None and nueva_pos == self.recurso_pos:
                    nuevo_portador = (bando, indice)
                    nuevo_recurso_pos = nueva_pos
                # Si quien se mueve es el portador actual, el recurso viaja con él.
                elif self.portador == (bando, indice):
                    nuevo_recurso_pos = nueva_pos
                # Si el portador es rival, entrar a su celda lo roba.
                elif (self.portador is not None and self.portador[0] != bando
                        and nueva_pos == self.recurso_pos):
                    nuevo_portador = (bando, indice)
                    nuevo_recurso_pos = nueva_pos

                # 2. Construir el nuevo estado
                posiciones_nuevas = list(posiciones)
                posiciones_nuevas[indice] = nueva_pos
                siguiente_turno = "B" if bando == "A" else "A"

                nuevo_estado = EstadoJuego(
                    pos_a=posiciones_nuevas if bando == "A" else self.pos_a,
                    pos_b=posiciones_nuevas if bando == "B" else self.pos_b,
                    portador=nuevo_portador,
                    turno=siguiente_turno,
                    recurso_pos=nuevo_recurso_pos,
                )
                sucesores_lista.append(((indice, nueva_pos), nuevo_estado))

        return sucesores_lista

    def __repr__(self):
        return (
            f"<Estado | A:{self.pos_a} B:{self.pos_b} "
            f"Portador:{self.portador} Turno:{self.turno}>"
        )
