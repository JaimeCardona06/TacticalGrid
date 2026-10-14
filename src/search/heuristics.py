"""Heurísticas para A* y Beam.

Cada heurística se crea con una FÁBRICA: crear_xxx(problema) -> h, donde h(estado)
devuelve la estimación del costo restante hasta el objetivo. La fábrica hace una
sola vez el trabajo previo (por ejemplo, leer el costo mínimo del tablero), así h
es barata de llamar en cada estado. Los algoritmos reciben la fábrica (o su nombre
en HEURISTICAS), por lo que cambiar de heurística no toca ni el algoritmo ni el
problema. Estas fábricas usan problema.objetivo y problema.tablero.
"""

import math
from collections import deque


def crear_manhattan(problema):
    """Manhattan escalada por el costo mínimo del escenario: h = pasos x c_min.

    Purpose:            estimar el costo restante como (distancia Manhattan al
                        objetivo) x (menor costo de entrada entre los terrenos
                        transitables, leído del JSON). Es la heurística 1.
    Preconditions:      problema.objetivo es una tupla (fila, columna) y
                        problema.tablero ya está validado (con al menos un
                        terreno transitable); movimiento en 4 direcciones, y se
                        cobra la celda destino.
    Postconditions:     devuelve h(estado) -> número >= 0. h(objetivo) = 0. Es
                        ADMISIBLE y CONSISTENTE para cualquier escenario válido
                        (ver análisis abajo). No modifica nada.
    Complexity:         Fábrica: O(t) con t = tipos de terreno. Cada h(estado):
                        O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)

    Análisis (lo que pide el enunciado):
      Qué estima: el costo mínimo imaginable de llegar al objetivo si no hubiera
        obstáculos y todo fuera del terreno más barato.
      Qué información usa: solo las coordenadas del estado y del objetivo, y el
        costo mínimo transitable del escenario. No mira el mapa celda por celda.
      Admisible, porque: con 4 direcciones, todo camino necesita al menos
        Manhattan pasos; cada paso cobra una celda transitable, que cuesta al
        menos c_min; entonces costo real >= Manhattan x c_min = h. Sin escalar,
        h = Manhattan sobreestimaría si algún terreno costara menos de 1 (la
        validación solo exige costo positivo).
      Consistente, porque: al pasar a un vecino, h cambia como máximo en c_min,
        que es <= al costo de ese paso. Por eso un estado cerrado no se reabre.
      Orienta bien cuando: los costos del mapa son parecidos al mínimo y hay pocos
        obstáculos entre el inicio y el objetivo.
      Pierde discriminación cuando: c_min es mucho menor que el costo típico del
        mapa (h queda muy por debajo del costo real y A* se parece a UCS), o hay
        muros que obligan a rodear (Manhattan no los ve).
    """
    objetivo_fila, objetivo_columna = problema.objetivo
    costo_minimo = problema.tablero.costo_minimo_transitable()

    def h(estado):
        return (abs(estado[0] - objetivo_fila) + abs(estado[1] - objetivo_columna)) * costo_minimo

    return h


def crear_manhattan_pasos(problema):
    """Manhattan SIN escalar: h = número de pasos. Solo es admisible si todo paso cuesta >= 1.

    Purpose:            ofrecer la versión clásica para comparar y para demostrar
                        por qué la escalada es necesaria: con un terreno de costo
                        menor que 1 sobreestima y A* puede devolver un camino más
                        caro que el óptimo.
    Preconditions:      problema.objetivo es una tupla (fila, columna).
    Postconditions:     devuelve h(estado) -> número entero >= 0. NO es admisible
                        en general. No modifica nada.
    Complexity:         Fábrica O(1). Cada h(estado): O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    objetivo_fila, objetivo_columna = problema.objetivo

    def h(estado):
        return abs(estado[0] - objetivo_fila) + abs(estado[1] - objetivo_columna)

    return h


def crear_distancia_bfs(problema):
    """Distancia real en pasos (rodeando muros) por el costo mínimo: h = pasos_reales x c_min.

    Purpose:            estimar el costo restante usando el número REAL de pasos
                        hasta el objetivo, que se calcula una vez con un BFS desde
                        el objetivo sobre el mapa, multiplicado por el menor costo
                        de entrada del escenario. Es la heurística 2.
    Preconditions:      problema.objetivo es una tupla (fila, columna) y
                        problema.tablero ya está validado; movimiento en 4
                        direcciones, y se cobra la celda destino.
    Postconditions:     devuelve h(estado) -> número >= 0, o math.inf si desde ese
                        estado no se puede llegar al objetivo (muro, fuera del
                        mapa, zona aislada, o objetivo no transitable). h(objetivo)
                        = 0. Es ADMISIBLE y CONSISTENTE para cualquier escenario
                        válido, y domina a Manhattan (h2 >= h1). No modifica nada.
    Complexity:         Fábrica: un BFS, O(f*c) en tiempo y en memoria, con f
                        filas y c columnas, una vez por objetivo. Cada
                        h(estado): O(1). Al comparar con Manhattan hay que
                        contar este preprocesamiento en el tiempo total.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)

    Análisis (lo que pide el enunciado):
      Qué estima: el costo de recorrer el camino de MENOS pasos si cada paso
        costara lo mínimo posible. Es un "problema relajado": se relajan los
        costos del terreno, pero se respetan los muros.
      Qué información usa: la forma del mapa (muros y límites), el objetivo y el
        costo mínimo transitable. No usa los costos de cada celda.
      Admisible, porque: ningún camino real tiene menos pasos que la distancia
        BFS, y cada paso cuesta al menos c_min.
      Consistente, porque: entre celdas vecinas la distancia BFS cambia como
        máximo en 1, así que h cambia como máximo en c_min, que es <= al costo
        del paso.
      Domina a Manhattan: rodear un muro nunca acorta, así que sus pasos son >=
        los de Manhattan; con heurísticas consistentes, la que domina expande
        igual o menos estados.
      Orienta bien cuando: hay muros que obligan a rodear (Manhattan no los ve).
      Pierde discriminación cuando: los costos varían mucho entre terrenos (usa
        c_min para todos los pasos), o no hay muros (entonces coincide con
        Manhattan y solo agrega el costo del preprocesamiento).
      Por qué no usar UCS en el preprocesamiento: daría el costo exacto h*, es
        decir, resolver el problema antes de resolverlo; A* no tendría nada que
        hacer. Esta es un punto intermedio: más informada que Manhattan, pero
        sigue siendo una estimación.
    """
    tablero = problema.tablero
    costo_minimo = tablero.costo_minimo_transitable()
    objetivo = problema.objetivo

    pasos = {}
    if tablero.es_transitable(objetivo):   # el BFS solo es válido saliendo de una celda por la que se puede pasar
        pasos[objetivo] = 0
        cola = deque([objetivo])
        while cola:
            celda = cola.popleft()
            for vecino in tablero.vecinos(celda):
                if vecino not in pasos:
                    pasos[vecino] = pasos[celda] + 1
                    cola.append(vecino)

    def h(estado):
        distancia = pasos.get(estado)
        return math.inf if distancia is None else distancia * costo_minimo

    return h


# Heurísticas disponibles por nombre (la interfaz y los JSON de prueba eligen por nombre).
HEURISTICAS = {
    "manhattan": crear_manhattan,
    "manhattan_pasos": crear_manhattan_pasos,
    "distancia_bfs": crear_distancia_bfs,
}


def obtener_fabrica(heuristica):
    """Acepta el nombre de una heurística o directamente su fábrica, y devuelve la fábrica."""
    if callable(heuristica):
        return heuristica
    if heuristica not in HEURISTICAS:
        raise ValueError(f"Heurística desconocida: {heuristica!r}. Disponibles: {sorted(HEURISTICAS)}")
    return HEURISTICAS[heuristica]
