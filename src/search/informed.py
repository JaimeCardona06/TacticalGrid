import heapq
import time
from itertools import count

from src.search.heuristics import obtener_fabrica
from src.search.resultado import ResultadoBusqueda, reconstruir_camino


def a_estrella(problema, heuristica="manhattan"):
    """Búsqueda A*: expande el estado de menor f = g + h.

    Purpose:            encontrar el camino de menor costo total explorando menos
                        estados que UCS, usando una heurística h que estima el
                        costo restante hasta el objetivo, y registrando las
                        métricas.
    Preconditions:      problema ofrece estado_inicial(), sucesores(estado) ->
                        [(accion, nuevo_estado, costo)], es_objetivo(estado) y
                        extremos_transitables(); los costos son positivos.
                        heuristica es el nombre de una heurística de HEURISTICAS
                        o una fábrica crear(problema) -> h(estado). Para que el
                        resultado sea ÓPTIMO, h debe ser admisible (nunca
                        sobreestimar el costo real).
    Postconditions:     devuelve un ResultadoBusqueda con algoritmo "A_ESTRELLA" y
                        el nombre de la heurística. Si el inicio o el objetivo no
                        son transitables, termina sin éxito sin explorar nada. Con
                        una h admisible, exito=True implica costo mínimo. Mismas
                        convenciones que UCS: heap ordenado por (f, g, orden de
                        llegada); estado cerrado al SACARLO; meta comprobada al
                        sacar; si un estado mejora su g se reinserta (cuenta como
                        generado) y la entrada vieja se descarta al sacarla sin
                        contarla como expandida; el máximo de frontera incluye
                        las entradas viejas. Con h = 0 se comporta como UCS. No
                        modifica el problema.
    Complexity:         Tiempo O(E log E) y espacio O(V) en el peor caso (igual
                        que UCS); con una buena heurística expande muchos menos
                        estados. Cada llamada a h cuesta lo que indique su
                        documentación (O(1) para Manhattan).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    inicio_reloj = time.perf_counter()
    nombre = heuristica if isinstance(heuristica, str) else getattr(heuristica, "__name__", "personalizada")
    fabrica = obtener_fabrica(heuristica)

    if not problema.extremos_transitables():
        return ResultadoBusqueda("A_ESTRELLA", False, tiempo_segundos=time.perf_counter() - inicio_reloj,
                                 heuristica=nombre)

    h = fabrica(problema)
    inicial = problema.estado_inicial()
    orden = count()  # desempate final: a igual (f, g), sale primero el que entró antes
    frontera = [(h(inicial), 0, next(orden), inicial)]
    mejor_g = {inicial: 0}
    padre = {inicial: None}  # estado -> (estado_padre, accion, costo_del_paso)
    generados, expandidos, maximo_frontera = 1, 0, 1

    while frontera:
        _, g, _, estado = heapq.heappop(frontera)
        if g != mejor_g[estado]:
            continue  # entrada vieja: ya se encontró un camino más barato a este estado
        expandidos += 1

        if problema.es_objetivo(estado):
            camino, acciones, costo = reconstruir_camino(padre, estado)
            return ResultadoBusqueda(
                "A_ESTRELLA", True, camino, acciones, costo,
                generados, expandidos, maximo_frontera,
                time.perf_counter() - inicio_reloj, nombre,
            )

        for accion, nuevo, costo_paso in problema.sucesores(estado):
            nuevo_g = g + costo_paso
            if nuevo not in mejor_g or nuevo_g < mejor_g[nuevo]:
                mejor_g[nuevo] = nuevo_g
                padre[nuevo] = (estado, accion, costo_paso)
                heapq.heappush(frontera, (nuevo_g + h(nuevo), nuevo_g, next(orden), nuevo))
                generados += 1

        maximo_frontera = max(maximo_frontera, len(frontera))

    return ResultadoBusqueda(
        "A_ESTRELLA", False, estados_generados=generados, estados_expandidos=expandidos,
        maximo_frontera=maximo_frontera, tiempo_segundos=time.perf_counter() - inicio_reloj,
        heuristica=nombre,
    )
