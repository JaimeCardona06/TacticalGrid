"""Verificador de soluciones de búsqueda (opción "Verificar solución" de la aplicación).

Es INDEPENDIENTE de los algoritmos y de los métodos de Board: solo lee los datos
guardados del tablero (la matriz `terreno` y el catálogo `tipos_terreno`, que
vienen del JSON) y recalcula todo por su cuenta. Así, si un algoritmo o un método
de Board tuviera un error, el verificador lo detectaría en vez de heredarlo.
"""
import math
from dataclasses import dataclass

# Dirección de cada paso (propia del verificador: no importa nada de navegacion.py).
_ACCION_DE_PASO = {(-1, 0): "arriba", (0, 1): "derecha", (1, 0): "abajo", (0, -1): "izquierda"}


@dataclass(frozen=True)
class InformeVerificacion:
    """Resultado de verificar una solución.

    comprobaciones: tupla de (descripción, problemas) en el orden en que se hicieron;
                    `problemas` es una tupla de textos (vacía si esa comprobación pasó).
    """
    comprobaciones: tuple

    @property
    def problemas(self):
        return tuple(p for _, ps in self.comprobaciones for p in ps)

    @property
    def valido(self):
        return not self.problemas


def _es_entero(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def _terreno_de(tablero, pos):
    """Tipo de terreno de una celda leyendo la matriz y el catálogo; None si no existe o no se puede saber."""
    if not (isinstance(pos, (tuple, list)) and len(pos) == 2 and all(_es_entero(v) for v in pos)):
        return None
    fila, columna = pos
    if not (0 <= fila < len(tablero.terreno) and 0 <= columna < len(tablero.terreno[fila])):
        return None
    tipo = tablero.tipos_terreno.get(tablero.terreno[fila][columna])
    return tipo if isinstance(tipo, dict) else None


def verificar_solucion(tablero, resultado, inicio, objetivo):
    """Verifica por su cuenta que el resultado de una búsqueda sea una solución válida.

    Purpose:            comprobar la respuesta del propio sistema (el enunciado
                        pide que sea una opción de la aplicación): que cada
                        movimiento sea válido, que no se atraviesen obstáculos,
                        que el costo reportado sea la suma de las transiciones,
                        que el estado final cumpla el objetivo y que las acciones
                        y métricas sean coherentes.
    Preconditions:      tablero tiene los atributos terreno (matriz de nombres) y
                        tipos_terreno (catálogo con costo y transitable);
                        resultado es un ResultadoBusqueda; inicio y objetivo son
                        las posiciones (fila, columna) con que se ejecutó la
                        búsqueda.
    Postconditions:     devuelve un InformeVerificacion con una entrada por cada
                        comprobación y sus problemas (texto que dice qué y dónde).
                        Si exito=True se verifica: forma del camino; inicio y fin;
                        celdas dentro del mapa y transitables; pasos a una celda
                        vecina (4 direcciones); costo = suma del costo de la celda
                        destino de cada paso (convención del equipo); acciones
                        coherentes con los pasos; métricas coherentes. Si
                        exito=False se verifica que no traiga camino, acciones ni
                        costo, y las métricas; NO se puede comprobar que realmente
                        no exista ruta (eso exigiría volver a buscar). No usa
                        ningún método de Board ni de los algoritmos y no modifica
                        nada.
    Complexity:         O(n) en tiempo y espacio, con n = longitud del camino.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    inicio, objetivo = tuple(inicio), tuple(objetivo)
    comprobaciones = []

    def anotar(descripcion, problemas):
        comprobaciones.append((descripcion, tuple(problemas)))

    if not resultado.exito:
        anotar("Una búsqueda sin éxito no trae camino, acciones ni costo",
               [m for m, malo in (("trae un camino", len(resultado.camino) > 0),
                                  ("trae acciones", len(resultado.acciones) > 0),
                                  ("trae un costo", resultado.costo is not None)) if malo])
        anotar("Las métricas son coherentes", _problemas_metricas(resultado))
        return InformeVerificacion(tuple(comprobaciones))

    camino = tuple(resultado.camino)
    forma = []
    if len(camino) == 0:
        forma.append("el camino está vacío")
    for i, p in enumerate(camino):
        if not (isinstance(p, (tuple, list)) and len(p) == 2 and all(_es_entero(v) for v in p)):
            forma.append(f"el elemento {i} del camino no es una posición (fila, columna) de enteros: {p!r}")
    anotar("El camino es una lista de posiciones (fila, columna)", forma)
    if forma:
        return InformeVerificacion(tuple(comprobaciones))   # sin una forma válida no se puede seguir
    camino = tuple(tuple(p) for p in camino)

    extremos = []
    if camino[0] != inicio:
        extremos.append(f"empieza en {camino[0]} y debía empezar en {inicio}")
    if camino[-1] != objetivo:
        extremos.append(f"termina en {camino[-1]} y debía terminar en {objetivo}")
    anotar("El camino empieza en el inicio y termina en el objetivo", extremos)

    celdas = []
    for i, p in enumerate(camino):
        tipo = _terreno_de(tablero, p)
        if tipo is None:
            celdas.append(f"la celda {i} del camino, {p}, está fuera del mapa")
        elif tipo.get("transitable") is not True:
            nombre = tablero.terreno[p[0]][p[1]]
            celdas.append(f"la celda {i} del camino, {p}, es un terreno no transitable ('{nombre}')")
    anotar("Todas las celdas están dentro del mapa y no son obstáculos", celdas)

    pasos = []
    for i, (a, b) in enumerate(zip(camino, camino[1:]), start=1):
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
            pasos.append(f"el paso {i} va de {a} a {b}, que no son celdas vecinas (4 direcciones)")
    anotar("Cada movimiento va a una celda vecina", pasos)

    costo = []
    if celdas:
        costo.append("no se puede recalcular el costo porque hay celdas inválidas")
    else:
        recalculado = 0
        for p in camino[1:]:
            recalculado += _terreno_de(tablero, p).get("costo")
        if not isinstance(resultado.costo, (int, float)) or isinstance(resultado.costo, bool) \
                or not math.isclose(resultado.costo, recalculado, rel_tol=1e-9, abs_tol=1e-9):
            costo.append(f"el costo reportado es {resultado.costo!r} pero la suma de los pasos es {recalculado}")
    anotar("El costo reportado es la suma del costo de las celdas destino", costo)

    acciones = []
    if len(resultado.acciones) != len(camino) - 1:
        acciones.append(f"hay {len(resultado.acciones)} acciones para {len(camino) - 1} pasos")
    else:
        for i, ((a, b), accion) in enumerate(zip(zip(camino, camino[1:]), resultado.acciones), start=1):
            esperada = _ACCION_DE_PASO.get((b[0] - a[0], b[1] - a[1]))
            if esperada is not None and accion != esperada:
                acciones.append(f"la acción {i} es '{accion}' pero el paso de {a} a {b} es '{esperada}'")
    anotar("Las acciones coinciden con los movimientos", acciones)

    anotar("Las métricas son coherentes", _problemas_metricas(resultado))
    return InformeVerificacion(tuple(comprobaciones))


def _problemas_metricas(resultado):
    """Comprobaciones de sentido común sobre las métricas (no dependen del mapa)."""
    problemas = []
    for nombre in ("estados_generados", "estados_expandidos", "maximo_frontera"):
        valor = getattr(resultado, nombre)
        if not _es_entero(valor) or valor < 0:
            problemas.append(f"{nombre} debe ser un entero no negativo (recibido: {valor!r})")
    if not problemas and resultado.estados_expandidos > resultado.estados_generados:
        problemas.append(f"se expandieron {resultado.estados_expandidos} estados pero solo se generaron "
                         f"{resultado.estados_generados}")
    return problemas
