import time
from collections import deque

from src.search.resultado import ResultadoBusqueda, reconstruir_camino


def bfs(problema):
    """Búsqueda en anchura (BFS): explora por niveles con una cola FIFO.

    Purpose:            encontrar el camino con MENOS MOVIMIENTOS del estado
                        inicial a un estado objetivo, ignorando los costos (esa
                        es la diferencia con UCS) y registrando las métricas.
    Preconditions:      problema ofrece estado_inicial(), sucesores(estado) ->
                        [(accion, nuevo_estado, costo)], es_objetivo(estado) y
                        extremos_transitables(); los estados son hashables.
    Postconditions:     devuelve un ResultadoBusqueda. Si el inicio o el
                        objetivo no son transitables, termina sin éxito sin
                        explorar nada. Si hay ruta, exito=True y el camino tiene
                        el menor número de movimientos posible; el costo es la
                        suma de los costos de ese camino (no necesariamente el
                        mínimo). Convenciones: un estado se marca visitado al
                        GENERARSE; la meta se comprueba al SACAR de la frontera;
                        los sucesores se encolan en el orden en que los da el
                        problema. No modifica el problema.
    Complexity:         Tiempo O(V + E) y espacio O(V) en el peor caso, con V =
                        estados alcanzables (celdas transitables) y E = pasos
                        posibles (a lo sumo 4 por celda); la frontera puede
                        llegar a O(V).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    inicio_reloj = time.perf_counter()

    if not problema.extremos_transitables():
        return ResultadoBusqueda("BFS", False, tiempo_segundos=time.perf_counter() - inicio_reloj)

    inicial = problema.estado_inicial()
    frontera = deque([inicial])
    padre = {inicial: None}  # estado -> (estado_padre, accion, costo_del_paso); también hace de "visitados"
    generados, expandidos, maximo_frontera = 1, 0, 1

    while frontera:
        estado = frontera.popleft()
        expandidos += 1

        if problema.es_objetivo(estado):
            camino, acciones, costo = reconstruir_camino(padre, estado)
            return ResultadoBusqueda(
                "BFS", True, camino, acciones, costo,
                generados, expandidos, maximo_frontera,
                time.perf_counter() - inicio_reloj,
            )

        for accion, nuevo, costo_paso in problema.sucesores(estado):
            if nuevo not in padre:
                padre[nuevo] = (estado, accion, costo_paso)
                frontera.append(nuevo)
                generados += 1

        maximo_frontera = max(maximo_frontera, len(frontera))

    return ResultadoBusqueda(
        "BFS", False, estados_generados=generados, estados_expandidos=expandidos,
        maximo_frontera=maximo_frontera, tiempo_segundos=time.perf_counter() - inicio_reloj,
    )
