import heapq
import time
from collections import deque
from itertools import count

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


def dfs(problema):
    """Búsqueda en profundidad (DFS): sigue una rama hasta el fondo con una pila LIFO.

    Purpose:            encontrar UN camino del estado inicial a un objetivo,
                        sin garantizar que tenga pocos movimientos ni poco costo,
                        y registrando las métricas. Sirve para contrastar con BFS
                        (caso 1 del enunciado): mismo modelo, otro recorrido.
    Preconditions:      las mismas que bfs: problema ofrece estado_inicial(),
                        sucesores(estado), es_objetivo(estado) y
                        extremos_transitables(); los estados son hashables.
    Postconditions:     devuelve un ResultadoBusqueda. Si el inicio o el objetivo
                        no son transitables, termina sin éxito sin explorar nada.
                        Si hay ruta, exito=True con un camino válido (no
                        necesariamente corto ni barato). Convenciones, iguales a
                        las del notebook del profesor: un estado se marca
                        visitado al GENERARSE; la meta se comprueba al SACAR de
                        la pila; los sucesores se apilan en el orden en que los
                        da el problema, así que se explora PRIMERO el último
                        (con DIRECCIONES por defecto: izquierda). Cambiar el
                        orden de DIRECCIONES puede cambiar el camino. Es
                        iterativo: no depende del límite de recursión de Python.
                        No modifica el problema.
    Complexity:         Tiempo O(V + E) y espacio O(V) en el peor caso, con V =
                        estados alcanzables y E = pasos posibles. La pila
                        (frontera) suele ser menor que la de BFS.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    inicio_reloj = time.perf_counter()

    if not problema.extremos_transitables():
        return ResultadoBusqueda("DFS", False, tiempo_segundos=time.perf_counter() - inicio_reloj)

    inicial = problema.estado_inicial()
    pila = [inicial]
    padre = {inicial: None}  # estado -> (estado_padre, accion, costo_del_paso); también hace de "visitados"
    generados, expandidos, maximo_frontera = 1, 0, 1

    while pila:
        estado = pila.pop()
        expandidos += 1

        if problema.es_objetivo(estado):
            camino, acciones, costo = reconstruir_camino(padre, estado)
            return ResultadoBusqueda(
                "DFS", True, camino, acciones, costo,
                generados, expandidos, maximo_frontera,
                time.perf_counter() - inicio_reloj,
            )

        for accion, nuevo, costo_paso in problema.sucesores(estado):
            if nuevo not in padre:
                padre[nuevo] = (estado, accion, costo_paso)
                pila.append(nuevo)
                generados += 1

        maximo_frontera = max(maximo_frontera, len(pila))

    return ResultadoBusqueda(
        "DFS", False, estados_generados=generados, estados_expandidos=expandidos,
        maximo_frontera=maximo_frontera, tiempo_segundos=time.perf_counter() - inicio_reloj,
    )


def ucs(problema):
    """Búsqueda de costo uniforme (UCS): siempre expande el estado de menor costo acumulado.

    Purpose:            encontrar el camino de MENOR COSTO TOTAL del estado inicial
                        a un objetivo (no el de menos movimientos, que es lo que
                        da BFS), registrando las métricas. Es el caso 2 del
                        enunciado: ruta corta contra ruta económica.
    Preconditions:      problema ofrece estado_inicial(), sucesores(estado) ->
                        [(accion, nuevo_estado, costo)], es_objetivo(estado) y
                        extremos_transitables(); los estados son hashables y
                        todos los costos son POSITIVOS (lo garantiza la regla 3
                        del validador). Con costos negativos UCS no es óptimo.
    Postconditions:     devuelve un ResultadoBusqueda. Si el inicio o el objetivo
                        no son transitables, termina sin éxito sin explorar nada.
                        Si hay ruta, exito=True y el costo es el MÍNIMO posible.
                        Convenciones: la frontera es un heap ordenado por
                        (costo acumulado, orden de llegada); un estado queda
                        cerrado al SACARLO, no al generarlo, y la meta se
                        comprueba al sacar. Si un estado se alcanza con menor
                        costo, se actualiza mejor_g y padre y se vuelve a
                        insertar (cuenta como generado); la entrada vieja se
                        queda en el heap y se descarta al sacarla, sin contarla
                        como expandida (eliminación perezosa, porque heapq no
                        modifica prioridades). El máximo de frontera incluye las
                        entradas viejas: es la memoria realmente usada. El
                        desempate por orden de llegada hace los resultados
                        reproducibles. No modifica el problema.
    Complexity:         Tiempo O(E log E) = O(V log V) y espacio O(V), con V =
                        estados alcanzables y E <= 4V pasos posibles (cada
                        estado se expande una vez, cada paso inserta a lo sumo
                        una entrada).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    inicio_reloj = time.perf_counter()

    if not problema.extremos_transitables():
        return ResultadoBusqueda("UCS", False, tiempo_segundos=time.perf_counter() - inicio_reloj)

    inicial = problema.estado_inicial()
    orden = count()  # desempate: a igual costo, sale primero el que entró antes
    frontera = [(0, next(orden), inicial)]
    mejor_g = {inicial: 0}   # mejor costo conocido hasta cada estado; es quien decide si una entrada está vieja
    padre = {inicial: None}  # estado -> (estado_padre, accion, costo_del_paso); se sobrescribe al mejorar
    generados, expandidos, maximo_frontera = 1, 0, 1

    while frontera:
        g, _, estado = heapq.heappop(frontera)
        if g != mejor_g[estado]:
            continue  # entrada vieja: ya se encontró un camino más barato a este estado
        expandidos += 1

        if problema.es_objetivo(estado):
            camino, acciones, costo = reconstruir_camino(padre, estado)
            return ResultadoBusqueda(
                "UCS", True, camino, acciones, costo,
                generados, expandidos, maximo_frontera,
                time.perf_counter() - inicio_reloj,
            )

        for accion, nuevo, costo_paso in problema.sucesores(estado):
            nuevo_g = g + costo_paso
            if nuevo not in mejor_g or nuevo_g < mejor_g[nuevo]:
                mejor_g[nuevo] = nuevo_g
                padre[nuevo] = (estado, accion, costo_paso)
                heapq.heappush(frontera, (nuevo_g, next(orden), nuevo))
                generados += 1

        maximo_frontera = max(maximo_frontera, len(frontera))

    return ResultadoBusqueda(
        "UCS", False, estados_generados=generados, estados_expandidos=expandidos,
        maximo_frontera=maximo_frontera, tiempo_segundos=time.perf_counter() - inicio_reloj,
    )
