"""
Purpose:
    Desempate por avance: cuando varias acciones tienen EXACTAMENTE el mismo valor
    Minimax, elegir la que acerca más al bando a su objetivo en lugar de la
    primera del orden de generación. Sin esto, un bando que ya no puede cambiar el
    valor dentro del horizonte mueve siempre la primera unidad (A1 recorriendo la
    fila 0 de config/mapa_grande.json mientras el rival se lleva el recurso).

    Cuando el rival lleva el recurso hay dos estrategias de robo (ESTRATEGIAS_DE_ROBO):
      - "persecucion" (por defecto): acercarse al portador. Es la que mejor funciona en
        partidas completas (menos empates y más robos), medido en cientos de escenarios
        aleatorios (ver docs/decisiones.md).
      - "intercepcion": dirigirse a un punto de la ruta más corta del portador hacia su
        base al que se llegue a tiempo (ver holgura_de_intercepcion). Roba más que la
        persecución contra un portador que no reacciona y gana donde la persecución no
        puede (config/caso_intercepcion.json), pero contra un portador que también
        decide, la defensora que se coloca por delante lo bloquea y hay más empates.

    Solo decide ENTRE acciones óptimas empatadas: nunca cambia el valor Minimax ni
    elige una acción peor.

AI usage:           Yes
AI intervention:    la IA diagnosticó el comportamiento (todas las acciones de A
                    valían -3200 y se elegía la primera), diseñó la clave de
                    desempate y escribió este módulo y su documentación.
Student validation: Validado por el equipo con tests/test_desempate.py: distancias
                    reales rodeando muros, claves de avance en los tres casos,
                    elección entre acciones empatadas y que nunca cambia el valor.
"""
from collections import deque

# Distancia asignada a una celda a la que no se puede llegar.
SIN_RUTA = 10 ** 6

# Estrategias para quitarle el recurso a un portador rival.
PERSECUCION = "persecucion"
INTERCEPCION = "intercepcion"
ESTRATEGIAS_DE_ROBO = (PERSECUCION, INTERCEPCION)

# "Sin desempate por avance": entre acciones de igual valor se conserva la primera del orden.
# No es una estrategia de robo: sirve para VER, comparando, qué aporta el desempate.
SIN_DESEMPATE = "ninguna"
MODOS_DE_DESEMPATE = ESTRATEGIAS_DE_ROBO + (SIN_DESEMPATE,)

_DIRECCIONES = ((-1, 0), (0, 1), (1, 0), (0, -1))


def distancias_reales(tablero, origen):
    """Pasos mínimos desde `origen` a cada celda alcanzable, rodeando los muros.

    Purpose:            medir cercanía real (no Manhattan): una ficha pegada a un
                        muro puede estar cerca en línea recta y lejos por el camino.
    Preconditions:      tablero ofrece es_transitable(pos) y terreno (matriz de
                        nombres, para conocer las dimensiones); origen es una
                        tupla (fila, columna).
    Postconditions:     devuelve un diccionario celda -> pasos (origen -> 0) con
                        las celdas transitables alcanzables en 4 direcciones. Las
                        celdas ausentes no son alcanzables. No modifica el tablero.
    Complexity:         O(f*c) en tiempo y espacio, f filas y c columnas.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_desempate.py:
                        distancias rodeando un muro, celdas aisladas y origen en
                        un muro.
    """
    filas = len(tablero.terreno)
    columnas = len(tablero.terreno[0]) if filas else 0
    distancias = {origen: 0}
    cola = deque([origen])
    while cola:
        fila, columna = cola.popleft()
        for d_fila, d_columna in _DIRECCIONES:
            vecino = (fila + d_fila, columna + d_columna)
            if (vecino not in distancias and 0 <= vecino[0] < filas and 0 <= vecino[1] < columnas
                    and tablero.es_transitable(vecino)):
                distancias[vecino] = distancias[(fila, columna)] + 1
                cola.append(vecino)
    return distancias


def ruta_hacia_la_base(distancias_a_la_base, origen):
    """Ruta más corta de `origen` a la base, como lista de celdas (incluye el origen).

    Purpose:            predecir por dónde irá un portador rival: el camino de menos
                        pasos hacia su base, eligiendo en cada paso el primer vecino
                        (orden arriba, derecha, abajo, izquierda) que se acerca a la
                        base. Es la misma preferencia que usa el agente al desempatar.
    Preconditions:      distancias_a_la_base es el resultado de distancias_reales
                        desde la base; origen es una tupla (fila, columna).
    Postconditions:     devuelve [origen, c1, c2, ..., base]. Si origen no puede llegar
                        a la base devuelve [origen]. No modifica nada.
    Complexity:         O(L) con L = longitud de la ruta.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_desempate.py: ruta en
                        campo abierto, rodeando un muro y sin camino.
    """
    if origen not in distancias_a_la_base:
        return [origen]
    ruta = [origen]
    actual = origen
    while distancias_a_la_base[actual] > 0:
        for d_fila, d_columna in _DIRECCIONES:
            vecino = (actual[0] + d_fila, actual[1] + d_columna)
            if distancias_a_la_base.get(vecino, SIN_RUTA) < distancias_a_la_base[actual]:
                actual = vecino
                ruta.append(actual)
                break
    return ruta


def holgura_de_intercepcion(ruta, distancias_de_la_unidad):
    """Holgura con la que una unidad puede interceptar a un portador que sigue `ruta`.

    Purpose:            medir si una unidad llega a tiempo a un punto de la ruta del
                        portador: tras mi movimiento el portador mueve primero, así
                        que en mi movimiento m-ésimo está en ruta[m]; puedo robarle
                        ahí si necesito d(ruta[m]) <= m movimientos (m-1 para quedar
                        adyacente y 1 para entrar a su celda).
    Preconditions:      ruta = [c0, c1, ...] es la ruta prevista del portador desde su
                        posición actual (c0); distancias_de_la_unidad son las
                        distancias reales desde la unidad (distancias_reales).
    Postconditions:     devuelve min sobre m >= 1 de (d(ruta[m]) - m). Un valor <= 0
                        significa que la unidad PUEDE interceptar al portador si este
                        sigue la ruta; cuanto menor, más holgura; un valor positivo
                        es cuánto le faltaría. SIN_RUTA si no hay puntos que evaluar.
                        Perseguir por detrás da siempre >= 1 (nunca alcanza). No
                        modifica nada.
    Complexity:         O(L) con L = longitud de la ruta.
    AI usage:           Yes
    AI intervention:    la IA dedujo la condición de intercepción y escribió la
                        función y esta documentación.
    Student validation: Validado por el equipo con tests/test_desempate.py: unidad por
                        delante (holgura <= 0), unidad por detrás (holgura 1), muros y
                        celdas inalcanzables.
    """
    return min((distancias_de_la_unidad.get(celda, SIN_RUTA) - m
                for m, celda in enumerate(ruta) if m >= 1), default=SIN_RUTA)


def clave_de_avance(estado, bando, tablero, base_propia, base_rival, cache, estrategia_robo=PERSECUCION):
    """Clave de desempate de un estado desde el punto de vista de `bando` (menor = mejor).

    Purpose:            medir cuánto ha avanzado un bando hacia su objetivo para
                        decidir entre acciones de igual valor Minimax.
    Preconditions:      estado es el EstadoJuego RESULTANTE de una acción de
                        `bando`; base_propia y base_rival son las bases de ese bando
                        y de su rival; estrategia_robo es una de ESTRATEGIAS_DE_ROBO
                        (solo importa cuando lo lleva el rival); cache es un
                        diccionario (puede estar vacío) que guarda las distancias
                        ya calculadas por origen y se puede reutilizar entre
                        estados del mismo tablero.
    Postconditions:     devuelve una tupla comparable, siempre con distancias
                        reales (rodeando muros), según quién lleva el recurso:
                        - libre: (distancia de la unidad más cercana al recurso,
                          suma de las distancias de todas las unidades);
                        - lo lleva el bando: (distancia del portador a la base
                          propia, suma de las distancias de las demás unidades al
                          portador);
                        - lo lleva el rival y la estrategia es "persecucion": (distancia
                          de la unidad más cercana al portador, suma de las distancias
                          de todas);
                        - lo lleva el rival y la estrategia es "intercepcion": (menor
                          holgura de intercepción entre las unidades, distancia de la
                          unidad más cercana al portador, suma de las holguras), con la
                          ruta más corta del portador hacia SU base: primero se mira si
                          se llega a tiempo a algún punto de esa ruta; si hay igualdad,
                          la unidad más cercana al portador; luego la suma.
                        Una celda inalcanzable cuenta como SIN_RUTA. No modifica
                        el estado ni el tablero.
    Complexity:         O(f*c) por origen nuevo (BFS) y O(u) por clave, u unidades
                        del bando; las distancias se reutilizan vía `cache`.
    AI usage:           Yes
    AI intervention:    la IA diseñó la clave y escribió la función y esta
                        documentación.
    Student validation: Validado por el equipo con tests/test_desempate.py: las
                        tres claves (recurso libre, portador propio y portador
                        rival), muros que obligan a rodear y celdas aisladas.
    """
    propias = estado.pos_a if bando == "A" else estado.pos_b

    def distancias(origen):
        if origen not in cache:
            cache[origen] = distancias_reales(tablero, origen)
        return cache[origen]

    if estado.portador is not None and estado.portador[0] == bando:
        indice = estado.portador[1]
        portador = propias[indice]
        a_la_base = distancias(base_propia).get(portador, SIN_RUTA)
        al_portador = distancias(portador)
        otras = [al_portador.get(p, SIN_RUTA) for i, p in enumerate(propias) if i != indice]
        return (a_la_base, sum(otras))

    hasta_recurso = distancias(estado.recurso_pos)   # libre: el recurso; si no, la celda del portador rival
    lejanias = [hasta_recurso.get(p, SIN_RUTA) for p in propias]

    if estado.portador is not None and estrategia_robo == INTERCEPCION:
        ruta = ruta_hacia_la_base(distancias(base_rival), estado.recurso_pos)
        holguras = [holgura_de_intercepcion(ruta, distancias(p)) for p in propias]
        return (min(holguras), min(lejanias), sum(holguras))

    return (min(lejanias), sum(lejanias))
