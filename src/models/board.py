class Board:
    """Parte fija del escenario: el mapa, sus terrenos y las bases.
    """

    # Desplazamientos (fila, columna) en el orden de generación de sucesores:
    # arriba, derecha, abajo, izquierda. Cambiar este orden cambia los
    # resultados de DFS y Beam; es el único lugar donde se define.
    DIRECCIONES = ((-1, 0), (0, 1), (1, 0), (0, -1))

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

    def costo_entrar(self, pos):
        """Costo de mover una unidad hacia la celda (fila, columna).

        Purpose:            dar el costo de una transición según la regla del
                            equipo: se cobra el terreno de la celda DESTINO.
        Preconditions:      pos es una tupla (fila, columna) y
                            es_transitable(pos) es True; el tablero ya fue
                            validado (costo positivo en terrenos transitables).
        Postconditions:     devuelve el campo "costo" del terreno de esa celda
                            (un número > 0). Lanza ValueError si la celda no es
                            transitable o está fuera del mapa. No modifica el
                            tablero.
        Complexity:         O(1) en tiempo y espacio.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: TODO(equipo)
        """
        if not self.es_transitable(pos):
            raise ValueError(f"No se puede entrar a la celda {pos}: no es transitable")
        fila, columna = pos
        nombre = self.terreno[fila][columna]
        return self.tipos_terreno[nombre]["costo"]

    def costo_minimo_transitable(self):
        """Menor costo de entrada entre los terrenos transitables del catálogo.

        Purpose:            dar la cota inferior del costo de cualquier paso, que
                            necesitan las heurísticas para seguir siendo admisibles
                            con cualquier escenario (no se asume que sea 1).
        Preconditions:      el tablero ya fue validado (todo terreno transitable
                            tiene costo positivo).
        Postconditions:     devuelve el mínimo de "costo" sobre los tipos de
                            terreno con transitable verdadero, mirando el catálogo
                            completo (no solo los terrenos que aparecen en la
                            matriz); None si no hay ningún terreno transitable.
                            No modifica el tablero.
        Complexity:         O(t) en tiempo y O(1) en espacio, con t = tipos de
                            terreno del catálogo.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: TODO(equipo)
        """
        costos = [t["costo"] for t in self.tipos_terreno.values() if t["transitable"]]
        return min(costos) if costos else None

    def vecinos(self, pos):
        """Celdas adyacentes a las que una unidad puede moverse desde pos.

        Purpose:            generar las posiciones destino de un movimiento de
                            una casilla en 4 direcciones, en el orden fijado
                            por DIRECCIONES.
        Preconditions:      pos es una tupla (fila, columna) de enteros.
        Postconditions:     devuelve una lista de tuplas (fila, columna), en el
                            orden de DIRECCIONES, solo con celdas dentro del
                            mapa y transitables. No ignora ni considera
                            unidades: eso lo decide quien llama. No modifica
                            el tablero.
        Complexity:         O(1) en tiempo y espacio (4 direcciones fijas).
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: TODO(equipo)
        """
        fila, columna = pos
        vecinos = []
        for d_fila, d_columna in self.DIRECCIONES:
            destino = (fila + d_fila, columna + d_columna)
            if self.es_transitable(destino):
                vecinos.append(destino)
        return vecinos
