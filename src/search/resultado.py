from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResultadoBusqueda:
    """Resultado de una búsqueda, con las métricas que pide el enunciado.

    Definiciones (iguales para todos los algoritmos; ver docs/decisiones.md):
      estados_generados:  estados que entraron a la frontera (incluido el inicial).
      estados_expandidos: estados que se sacaron de la frontera para analizarlos
                          (incluye el objetivo cuando se encuentra).
      maximo_frontera:    mayor tamaño de la frontera, medido justo después de
                          agregar los sucesores de cada expansión (y al inicio).
    """
    algoritmo: str
    exito: bool
    camino: tuple = ()          # estados (fila, columna) desde el inicio hasta el objetivo
    acciones: tuple = ()        # una por paso: len(acciones) == len(camino) - 1
    costo: float = None         # suma de los costos de los pasos; None si no hubo ruta
    estados_generados: int = 0
    estados_expandidos: int = 0
    maximo_frontera: int = 0
    tiempo_segundos: float = 0.0
    heuristica: str = None      # nombre de la heurística, solo en los algoritmos informados

    def a_diccionario(self):
        """Formato equivalente al del enunciado (pág. 7), más acciones y tiempo."""
        datos = {
            "algoritmo": self.algoritmo,
            "exito": self.exito,
            "camino": [list(p) for p in self.camino],
            "acciones": list(self.acciones),
            "costo": self.costo,
            "estados_generados": self.estados_generados,
            "estados_expandidos": self.estados_expandidos,
            "maximo_frontera": self.maximo_frontera,
            "tiempo_segundos": self.tiempo_segundos,
        }
        if self.heuristica is not None:
            datos["heuristica"] = self.heuristica
        return datos


def reconstruir_camino(padre, meta):
    """Recorre los enlaces `padre` desde la meta hasta el inicio.

    Purpose:            obtener el camino, las acciones y el costo total una sola
                        vez, al final de la búsqueda, en lugar de copiar listas
                        en cada nodo.
    Preconditions:      padre es un diccionario estado -> (estado_padre, accion,
                        costo_del_paso); el inicio tiene valor None; meta está
                        en padre.
    Postconditions:     devuelve (camino, acciones, costo) con el camino del
                        inicio a la meta, las acciones de cada paso y la suma de
                        los costos de los pasos. No modifica padre.
    Complexity:         O(d) en tiempo y espacio, con d = longitud del camino.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    camino, acciones, costo = [meta], [], 0
    estado = meta
    while padre[estado] is not None:
        anterior, accion, costo_paso = padre[estado]
        camino.append(anterior)
        acciones.append(accion)
        costo += costo_paso
        estado = anterior
    camino.reverse()
    acciones.reverse()
    return tuple(camino), tuple(acciones), costo
