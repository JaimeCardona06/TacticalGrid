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


def beam_search(problema, k, heuristica="manhattan"):
    """Búsqueda en haz (Beam Search): por niveles, conservando solo los k mejores candidatos.

    Purpose:            buscar con memoria limitada: en cada nivel solo se
                        expanden k estados, los de menor f = g + h; el resto se
                        descarta para siempre. Muestra el costo de la memoria
                        limitada: puede devolver un camino peor que el óptimo o
                        fallar aunque exista solución.
    Preconditions:      problema ofrece estado_inicial(), sucesores(estado) ->
                        [(accion, nuevo_estado, costo)], es_objetivo(estado) y
                        extremos_transitables(); k es un entero positivo;
                        heuristica es el nombre de una de HEURISTICAS o una
                        fábrica crear(problema) -> h(estado).
    Postconditions:     devuelve un ResultadoBusqueda con algoritmo "BEAM", k y el
                        nombre de la heurística. Si el inicio o el objetivo no son
                        transitables, termina sin éxito sin explorar nada. NO es
                        completo ni óptimo: exito=False no prueba que no haya
                        ruta, y el costo puede ser mayor que el mínimo. Políticas
                        (decisión del equipo, distinta del notebook; ver
                        decisiones.md): se ordena por g + h (no solo por h); un
                        estado ya expandido no se vuelve a considerar; si dos
                        candidatos de un nivel son el mismo estado se conserva el
                        de menor g; un estado descartado por la poda PUEDE volver
                        a generarse en otro nivel; la meta se comprueba al
                        EXPANDIR (al recorrer el haz). Desempate: orden de
                        generación. Métricas: generados = candidatos creados
                        (incluidos los que luego se descartan) más el inicial;
                        expandidos = estados del haz que se procesaron (incluye la
                        meta); maximo_frontera = mayor tamaño del haz (<= k);
                        maximo_candidatos = mayor cantidad de candidatos creados
                        en un nivel antes de podar (la memoria transitoria real).
                        Siempre termina: cada nivel expande al menos un estado
                        nuevo y no se repiten estados expandidos. Lanza
                        ValueError si k no es un entero positivo. No modifica el
                        problema.
    Complexity:         Tiempo O(V * b log b) en el peor caso, con V = estados
                        alcanzables y b = k * 4 candidatos por nivel (cada estado
                        se expande a lo sumo una vez y se ordenan los
                        candidatos de cada nivel). Memoria de la búsqueda:
                        O(k) por nivel más el conjunto de cerrados y los enlaces
                        de camino O(V); la frontera propiamente dicha es O(k).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    inicio_reloj = time.perf_counter()
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError(f"k debe ser un entero positivo (recibido: {k!r})")
    nombre = heuristica if isinstance(heuristica, str) else getattr(heuristica, "__name__", "personalizada")
    fabrica = obtener_fabrica(heuristica)

    if not problema.extremos_transitables():
        return ResultadoBusqueda("BEAM", False, tiempo_segundos=time.perf_counter() - inicio_reloj,
                                 heuristica=nombre, k=k, maximo_candidatos=0)

    h = fabrica(problema)
    inicial = problema.estado_inicial()
    haz = [(inicial, 0)]       # (estado, g): los estados que se expandirán en este nivel
    padre = {inicial: None}    # estado -> (estado_padre, accion, costo_del_paso); solo para sobrevivientes
    cerrados = set()
    generados, expandidos, maximo_haz, maximo_candidatos = 1, 0, 1, 0

    while haz:
        candidatos = []        # (f, g, estado, estado_padre, accion, costo_del_paso)
        en_haz = {estado for estado, _ in haz}
        for estado, g in haz:
            expandidos += 1
            if problema.es_objetivo(estado):
                camino, acciones, costo = reconstruir_camino(padre, estado)
                return ResultadoBusqueda(
                    "BEAM", True, camino, acciones, costo,
                    generados, expandidos, maximo_haz,
                    time.perf_counter() - inicio_reloj, nombre, k, maximo_candidatos,
                )
            cerrados.add(estado)
            for accion, nuevo, costo_paso in problema.sucesores(estado):
                if nuevo in cerrados or nuevo in en_haz:
                    continue
                nuevo_g = g + costo_paso
                candidatos.append((nuevo_g + h(nuevo), nuevo_g, nuevo, estado, accion, costo_paso))
                generados += 1
        maximo_candidatos = max(maximo_candidatos, len(candidatos))

        # Un candidato por estado en este nivel: el de menor g (el primero en llegar si empatan).
        mejor = {}
        for c in candidatos:
            if c[2] not in mejor or c[1] < mejor[c[2]][1]:
                mejor[c[2]] = c
        unicos = [c for c in candidatos if mejor[c[2]] is c]

        unicos.sort(key=lambda c: c[0])  # estable: a igual f, gana el que se generó primero
        sobrevivientes = unicos[:k]
        for f, g, estado, padre_estado, accion, costo_paso in sobrevivientes:
            padre[estado] = (padre_estado, accion, costo_paso)
        haz = [(c[2], c[1]) for c in sobrevivientes]
        maximo_haz = max(maximo_haz, len(haz))

    return ResultadoBusqueda(
        "BEAM", False, estados_generados=generados, estados_expandidos=expandidos,
        maximo_frontera=maximo_haz, tiempo_segundos=time.perf_counter() - inicio_reloj,
        heuristica=nombre, k=k, maximo_candidatos=maximo_candidatos,
    )
