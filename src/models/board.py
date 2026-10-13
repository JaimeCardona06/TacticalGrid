class Board:
    """Parte fija del escenario: el mapa, sus terrenos y las bases.
    """

    def __init__(self, filas, columnas, tipos_terreno, terreno, base_a, base_b):
        """Recibe datos que YA pasaron la validación (ver scenario/validator.py).

        Las posiciones se guardan como tuplas (fila, columna).
        """
        self.filas = filas
        self.columnas = columnas
        self.tipos_terreno = tipos_terreno
        self.terreno = terreno
        self.base_a = base_a
        self.base_b = base_b

    def dentro_del_mapa(self, pos):
        """Indica si la posición (fila, columna) cae dentro de los límites del mapa.

        Purpose:            responder si una celda existe, para que el resto del
                            código no se salga de la matriz del terreno.
        Preconditions:      pos es una tupla (fila, columna) de enteros.
        Postconditions:     devuelve True si 0 <= fila < filas y
                            0 <= columna < columnas; False en otro caso.
                            No modifica el tablero.
        Complexity:         O(1) en tiempo y espacio.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: TODO(equipo)
        """
        fila, columna = pos
        return 0 <= fila < self.filas and 0 <= columna < self.columnas

    def es_transitable(self, pos):
        """Indica si una unidad puede pisar la celda (fila, columna).

        Purpose:            decidir si una celda es un destino posible al
                            generar sucesores (un muro no lo es).
        Preconditions:      pos es una tupla (fila, columna) de enteros; el
                            tablero ya fue validado (todo nombre de terreno
                            usado existe en tipos_terreno).
        Postconditions:     devuelve False si pos está fuera del mapa; si no,
                            devuelve el campo "transitable" del tipo de terreno
                            de esa celda. No modifica el tablero.
        Complexity:         O(1) en tiempo y espacio.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: TODO(equipo)
        """
        if not self.dentro_del_mapa(pos):
            return False
        fila, columna = pos
        nombre = self.terreno[fila][columna]
        return self.tipos_terreno[nombre]["transitable"]
