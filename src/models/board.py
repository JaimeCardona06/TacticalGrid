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
