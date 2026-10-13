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
