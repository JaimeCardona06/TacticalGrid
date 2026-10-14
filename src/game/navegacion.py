# Nombre de cada desplazamiento (fila, columna) para describir la acción de un paso.
NOMBRES_DIRECCION = {
    (-1, 0): "arriba",
    (0, 1): "derecha",
    (1, 0): "abajo",
    (0, -1): "izquierda",
}


class ProblemaNavegacion:
    """Problema de búsqueda de una sola unidad: ir de un inicio a un objetivo.

    Es lo único que los algoritmos de búsqueda conocen: reciben este objeto y
    le hacen tres preguntas (estado inicial, sucesores, ¿es objetivo?). No
    importan nada de la interfaz ni del JSON.

    Modelo (ver docs/decisiones.md):
      - Estado:   la posición (fila, columna) como tupla. Las demás unidades se
                  ignoran (en estas etapas se ignora al adversario).
      - Acción:   la dirección del paso ("arriba", "derecha", "abajo", "izquierda").
      - Costo:    el costo de la celda destino, leído del tablero.
    La heurística NO va aquí: es una función aparte que A* y Beam reciben, y
    que puede consultar `objetivo`.
    """

    def __init__(self, tablero, inicio, objetivo):
        """Recibe un Board ya validado y dos posiciones (fila, columna).

        No lanza error si inicio u objetivo no son transitables: eso se consulta
        con extremos_transitables() y la búsqueda lo informa como "sin ruta".
        """
        self.tablero = tablero
        self.inicio = tuple(inicio)
        self.objetivo = tuple(objetivo)

    def estado_inicial(self):
        return self.inicio

    def es_objetivo(self, estado):
        return estado == self.objetivo

    def extremos_transitables(self):
        """True si el inicio y el objetivo son celdas del mapa por las que se puede pasar.

        Si es False no existe ruta: la búsqueda debe terminar sin éxito, de
        forma determinista, sin explorar nada.
        """
        return self.tablero.es_transitable(self.inicio) and self.tablero.es_transitable(self.objetivo)

    def sucesores(self, estado):
        """Pasos posibles desde una posición, como lista de (accion, nuevo_estado, costo).

        Purpose:            generar los sucesores de un estado de navegación: cada
                            vecino transitable, con la dirección del paso y lo que
                            cuesta entrar a él.
        Preconditions:      estado es una tupla (fila, columna) dentro del mapa.
        Postconditions:     devuelve una lista nueva, en el orden de
                            Board.DIRECCIONES, con una tupla por vecino transitable:
                            (acción como texto, nuevo estado como tupla, costo > 0).
                            No incluye muros ni celdas fuera del mapa, ni considera
                            otras unidades. No modifica nada.
        Complexity:         O(1) en tiempo y espacio (a lo sumo 4 sucesores).
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: TODO(equipo)
        """
        fila, columna = estado
        resultado = []
        for destino in self.tablero.vecinos(estado):
            desplazamiento = (destino[0] - fila, destino[1] - columna)
            accion = NOMBRES_DIRECCION.get(desplazamiento, str(desplazamiento))
            resultado.append((accion, destino, self.tablero.costo_entrar(destino)))
        return resultado
