"""TacticalGrid: punto de entrada de la aplicación por consola.

Purpose:            cargar un escenario JSON con el loader validado del
                    proyecto (todo o nada) y despachar la ejecución según
                    `prueba.modo`: "busqueda", "partida" o "adversarial".
Preconditions:      se ejecuta con `python main.py [ruta.json]`; la ruta por
                    defecto es config/mapa_partida.json.
Postconditions:     imprime el progreso y las métricas en consola; devuelve 0
                    si la ejecución terminó bien y 1 si el escenario es
                    inválido o la configuración de la prueba no se puede
                    ejecutar. Un escenario inválido se rechaza completo: no se
                    simula nada con él.
Complexity:         la del modo elegido (búsqueda: la del algoritmo; partida y
                    adversarial: O(b^d) por turno, con b = factor de
                    ramificación del tablero y d = profundidad de Minimax).
AI usage:           Yes
AI intervention:    la IA escribió el archivo y esta documentación.
Student validation: Validado por el equipo ejecutando los tres modos (busqueda, partida y adversarial) sobre los escenarios de config/ y la suite completa (244 pruebas).

Decisión de diseño (fase adversarial 1 vs 1): el bucle Minimax modela UNA
unidad por bando y avisa en consola si el escenario trae más (se ignoran las
demás). Motivo: el árbol adversarial cuesta O(b^d) con b ≈ 4 por cada unidad
que puede mover el bando del turno; modelar todas las unidades multiplica el
factor de ramificación y obliga a profundidades mayores para que una jugada
tenga efecto, volviendo intratable la búsqueda con d ≥ 3. El formato JSON y el
validador sí admiten varias unidades por bando; es el bucle adversarial el
que usa solo la primera de cada bando (ver también EstadoJuego en
src/models/state.py).
"""

import json
import sys

# Asegurar codificación UTF-8 en la salida de consola (Windows).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.adversarial.agent import MinimaxAgent
from src.game.navegacion import ProblemaNavegacion
from src.game.verificador import verificar_solucion
from src.models.state import EstadoJuego
from src.scenario.loader import EscenarioInvalido, cargar_escenario
from src.search.informed import a_estrella, beam_search
from src.search.uninformed import bfs, dfs, ucs

RUTA_POR_DEFECTO = "config/mapa_partida.json"
MODOS = ("busqueda", "partida", "adversarial")

# Regla determinista de cierre: si nadie gana en MAX_TURNOS, la partida empata.
MAX_TURNOS = 100

_ALGORITMOS_SIMPLES = {"BFS": bfs, "DFS": dfs, "UCS": ucs}
_ALIAS_ALGORITMO = {
    "A*": "A_ESTRELLA",
    "ASTAR": "A_ESTRELLA",
    "A_ESTRELLA": "A_ESTRELLA",
    "BEAM": "BEAM",
    "BEAM_SEARCH": "BEAM",
}


def _unidad_por_bando(escenario, bando):
    """Primera unidad del bando (la fase adversarial modela 1 vs 1; ver nota del módulo)."""
    for unidad in escenario.unidades:
        if unidad.bando == bando:
            return unidad
    return None


def _objetivo_de_prueba(prueba):
    """Extrae (fila, columna) de prueba.objetivo; None si falta o no es numérico."""
    objetivo = prueba.get("objetivo")
    if isinstance(objetivo, dict):
        fila, columna = objetivo.get("fila"), objetivo.get("columna")
    elif isinstance(objetivo, (list, tuple)) and len(objetivo) == 2:
        fila, columna = objetivo
    else:
        return None
    if (isinstance(fila, int) and not isinstance(fila, bool)
            and isinstance(columna, int) and not isinstance(columna, bool)):
        return (fila, columna)
    return None


def _orden_de_prueba(prueba):
    """Lee prueba.orden_direcciones (caso mínimo 9); None si no viene o está mal formado."""
    orden = prueba.get("orden_direcciones")
    if orden is None:
        return None
    try:
        pasos = tuple((int(desplazamiento[0]), int(desplazamiento[1])) for desplazamiento in orden)
    except (TypeError, ValueError, IndexError):
        print("Aviso: 'prueba.orden_direcciones' está mal formado; se usa el orden por defecto.")
        return None
    return pasos or None


def resolver_busqueda(problema, prueba):
    """Ejecuta el algoritmo pedido por 'prueba' sobre un problema de navegación.

    Purpose:            traducir el bloque 'prueba' del JSON (algoritmo,
                        heurística y k) a la llamada del algoritmo de búsqueda
                        correspondiente, sin repetir ese despacho en main().
    Preconditions:      problema es un ProblemaNavegacion construido sobre un
                        tablero validado; prueba es el bloque 'prueba' del
                        escenario (puede ser un diccionario vacío).
    Postconditions:     devuelve un ResultadoBusqueda del algoritmo pedido
                        ("BFS", "DFS", "UCS", "A_ESTRELLA" o "BEAM"; "A*" y
                        "BEAM_SEARCH" se aceptan como alias). Lanza ValueError
                        si el algoritmo o la heurística no existen, o si k no
                        es un entero positivo para Beam. No modifica nada.
    Complexity:         la del algoritmo elegido (ver su documentación).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo ejecutando los tres modos (busqueda, partida y adversarial) sobre los escenarios de config/ y la suite completa (244 pruebas).
    """
    algoritmo = str(prueba.get("algoritmo", "A_ESTRELLA")).strip().upper().replace(" ", "_")
    algoritmo = _ALIAS_ALGORITMO.get(algoritmo, algoritmo)
    heuristica = prueba.get("heuristica", "manhattan")

    if algoritmo in _ALGORITMOS_SIMPLES:
        return _ALGORITMOS_SIMPLES[algoritmo](problema)
    if algoritmo == "A_ESTRELLA":
        return a_estrella(problema, heuristica)
    if algoritmo == "BEAM":
        return beam_search(problema, prueba.get("k", 2), heuristica)

    disponibles = sorted({*_ALGORITMOS_SIMPLES, "A_ESTRELLA", "BEAM"})
    raise ValueError(f"Algoritmo desconocido: {algoritmo!r}. Disponibles: {', '.join(disponibles)}")


def ejecutar_busqueda(escenario):
    """Modo 'busqueda': resuelve la navegación pedida en 'prueba' y la verifica.

    Purpose:            correr una prueba de búsqueda uniactiva sobre el
                        escenario (unidad y objetivo indicados en 'prueba'),
                        mostrar el resultado con sus métricas y verificar la
                        solución con el verificador independiente.
    Preconditions:      escenario viene de cargar_escenario (válido y
                        completo); 'prueba.unidad_inicio' identifica una unidad
                        existente y 'prueba.objetivo' trae fila y columna.
    Postconditions:     imprime el resultado del algoritmo y el informe de
                        verificación. Devuelve 0 si la prueba se ejecutó (haya
                        o no ruta) y 1 si la configuración no permite ejecutar
                        (unidad u objetivo inválidos, algoritmo desconocido).
    Complexity:         la del algoritmo elegido más la verificación O(n).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo ejecutando los tres modos (busqueda, partida y adversarial) sobre los escenarios de config/ y la suite completa (244 pruebas).
    """
    prueba = escenario.prueba or {}

    unidad_id = prueba.get("unidad_inicio")
    unidad = next((u for u in escenario.unidades if u.id == unidad_id), None)
    if unidad is None:
        ids = ", ".join(u.id for u in escenario.unidades) or "(ninguna)"
        print(f"Error: 'prueba.unidad_inicio' = {unidad_id!r} no existe. Unidades: {ids}")
        return 1

    objetivo = _objetivo_de_prueba(prueba)
    if objetivo is None:
        print("Error: 'prueba.objetivo' debe traer fila y columna numéricas.")
        return 1

    print(f"\n=== MODO BÚSQUEDA: {unidad.id} {unidad.posicion} -> {objetivo} ===")
    problema = ProblemaNavegacion(escenario.tablero, unidad.posicion, objetivo)
    if not problema.extremos_transitables():
        print("Aviso: el inicio o el objetivo no son transitables; no existe ruta.")

    try:
        resultado = resolver_busqueda(problema, prueba)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    print("\n--- Resultado ---")
    print(json.dumps(resultado.a_diccionario(), ensure_ascii=False, indent=2))

    informe = verificar_solucion(escenario.tablero, resultado, unidad.posicion, objetivo)
    print("\n--- Verificación independiente de la solución ---")
    for descripcion, problemas in informe.comprobaciones:
        print(f"[ERROR] {descripcion}" if problemas else f"[OK]    {descripcion}")
        for texto in problemas:
            print(f"          - {texto}")
    for aviso in informe.avisos:
        print(f"[AVISO] {aviso}")
    print("Resultado de la verificación: " + ("VÁLIDA" if informe.valido else "INVÁLIDA"))
    return 0


def _preparar_fase_4(escenario):
    """Estado inicial 1 vs 1 y parámetros efectivos de la fase adversarial.

    Purpose:            traducir el Escenario ya validado a lo que la fase
                        adversarial necesita (estado, profundidad, poda y
                        orden de acciones), sin volver a leer el JSON.
    Preconditions:      escenario viene de cargar_escenario (válido y
                        completo).
    Postconditions:     devuelve (estado, unidad_a, unidad_b, profundidad,
                        usar_poda, orden). estado es None si a algún bando le
                        falta unidad (el escenario sigue siendo válido);
                        profundidad es la de 'prueba.profundidad' si es un
                        entero positivo y, si no, la de
                        'juego.profundidad_maxima_minimax'. No modifica nada.
    Complexity:         O(u) por la búsqueda de la primera unidad de cada bando.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo ejecutando los tres modos (busqueda, partida y adversarial) sobre los escenarios de config/ y la suite completa (244 pruebas).
    """
    prueba = escenario.prueba or {}
    profundidad = prueba.get("profundidad") or escenario.profundidad_maxima_minimax
    if not isinstance(profundidad, int) or isinstance(profundidad, bool) or profundidad < 1:
        print(f"Aviso: profundidad inválida ({profundidad!r}); se usa la del escenario: "
              f"{escenario.profundidad_maxima_minimax}.")
        profundidad = escenario.profundidad_maxima_minimax
    usar_poda = bool(prueba.get("usar_poda", True))
    orden = _orden_de_prueba(prueba)

    unidad_a = _unidad_por_bando(escenario, "A")
    unidad_b = _unidad_por_bando(escenario, "B")
    estado = None
    if unidad_a is not None and unidad_b is not None:
        estado = EstadoJuego(
            pos_a=unidad_a.posicion,
            pos_b=unidad_b.posicion,
            portador=escenario.portador_recurso,
            turno=escenario.turno,
            recurso_pos=escenario.recurso,
        )
    return estado, unidad_a, unidad_b, profundidad, usar_poda, orden


def _avisar_unidades_ignoradas(escenario, unidad_a, unidad_b):
    """Avisa qué unidades del escenario quedan fuera del modelo 1 vs 1."""
    usadas = {unidad_a.id, unidad_b.id}
    ignoradas = [u.id for u in escenario.unidades if u.id not in usadas]
    if ignoradas:
        print(f"Nota: la fase 4 modela 1 vs 1; se ignoran las unidades: {', '.join(ignoradas)}")


def _crear_agentes(profundidad, usar_poda, orden):
    """Un agente Minimax por bando, con los mismos parámetros de búsqueda."""
    return {
        bando: MinimaxAgent(bando, profundidad=profundidad, usar_poda=usar_poda, orden_direcciones=orden)
        for bando in ("A", "B")
    }


def ejecutar_adversarial(escenario):
    """Modo 'adversarial': evalúa el estado actual y muestra la acción elegida.

    Purpose:            cumplir el modo 'adversarial' del enunciado: evaluar
                        el estado del escenario mediante Minimax/alfa-beta y
                        seleccionar una acción para el bando del turno, sin
                        avanzar la partida.
    Preconditions:      escenario viene de cargar_escenario (válido y
                        completo), con al menos una unidad por bando.
    Postconditions:     imprime el estado evaluado, la acción elegida, su
                        valor, la verificación de legalidad de la acción y las
                        métricas (nodos, podas, tiempo, profundidad efectiva).
                        Devuelve 0 si se pudo decidir y 1 si falta una unidad
                        de algún bando o no hay acciones legales.
    Complexity:         O(b^d) en tiempo, O(d) en espacio (una evaluación de
                        profundidad d; la partida completa está en el modo
                        'partida').
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo ejecutando los tres modos (busqueda, partida y adversarial) sobre los escenarios de config/ y la suite completa (244 pruebas).
    """
    estado, unidad_a, unidad_b, profundidad, usar_poda, orden = _preparar_fase_4(escenario)
    if estado is None:
        print("Error: se necesita al menos una unidad de cada bando para la fase adversarial.")
        return 1
    _avisar_unidades_ignoradas(escenario, unidad_a, unidad_b)

    tablero = escenario.tablero
    print(f"\n=== MODO ADVERSARIAL: evaluación de una acción (lanza {estado.turno}) ===")
    print(f"Profundidad: {profundidad} | Poda alfa-beta: {'sí' if usar_poda else 'no'}")
    print(f"Estado evaluado: {estado}")

    agente = MinimaxAgent(estado.turno, profundidad=profundidad, usar_poda=usar_poda, orden_direcciones=orden)
    accion, metricas = agente.seleccionar_movimiento(estado, tablero, tablero.base_a, tablero.base_b)
    if accion is None:
        print("No hay acciones legales para el bando que debe actuar.")
        return 1

    print(f"Acción elegida: mover el bando {estado.turno} a {accion}")
    print(f"Verificación de legalidad: {'LEGAL' if metricas['accion_legal'] else 'ILEGAL'}"
          f" — {metricas['detalle_legalidad']}")
    print(f"Valor obtenido: {metricas['valor_obtenido']:+.1f} | "
          f"Nodos generados: {metricas['nodos_generados']} | Evaluados: {metricas['nodos_evaluados']} | "
          f"Podas: {metricas['podas_totales']} | Profundidad efectiva: {metricas['profundidad_alcanzada']} | "
          f"Tiempo: {metricas['tiempo_ms']:.2f} ms")
    return 0


def ejecutar_partida(escenario):
    """Modo 'partida': simula la partida por turnos entre dos agentes Minimax.

    Purpose:            continuar el juego por turnos (modo 'partida' del
                        enunciado): en cada turno, el agente del bando activo
                        elige una acción con Minimax/alfa-beta y el estado
                        avanza hasta la victoria o el límite de turnos.
    Preconditions:      escenario viene de cargar_escenario (válido y
                        completo), con al menos una unidad por bando.
    Postconditions:     imprime un renglón por turno (acción, valor, métricas
                        del agente y verificación de legalidad de la acción),
                        el desenlace (victoria de A, de B o empate por límite
                        de turnos) y un resumen acumulado por bando. Devuelve 0
                        si la partida terminó y 1 si faltan unidades de algún
                        bando o una acción elegida no aparece entre los
                        sucesores.
    Complexity:         O(MAX_TURNOS * b^d) en tiempo, O(d) en espacio por
                        turno (más los acumulados O(1)).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo ejecutando los tres modos (busqueda, partida y adversarial) sobre los escenarios de config/ y la suite completa (244 pruebas).
    """
    estado, unidad_a, unidad_b, profundidad, usar_poda, orden = _preparar_fase_4(escenario)
    if estado is None:
        print("Error: se necesita al menos una unidad de cada bando para la fase adversarial.")
        return 1
    _avisar_unidades_ignoradas(escenario, unidad_a, unidad_b)

    tablero = escenario.tablero
    base_a, base_b = tablero.base_a, tablero.base_b
    agentes = _crear_agentes(profundidad, usar_poda, orden)
    totales = {
        bando: {"turnos": 0, "generados": 0, "evaluados": 0, "podas": 0, "tiempo_ms": 0.0}
        for bando in ("A", "B")
    }

    print(f"\n=== MODO PARTIDA: A {unidad_a.posicion} vs B {unidad_b.posicion} ===")
    print(f"Base A: {base_a} | Base B: {base_b} | Recurso: {escenario.recurso}")
    print(f"Profundidad: {profundidad} | Poda alfa-beta: {'sí' if usar_poda else 'no'}")
    print(f"Estado inicial: {estado}\n" + "-" * 100)

    turno_num = 1
    while not estado.es_terminal(base_a, base_b) and turno_num <= MAX_TURNOS:
        bando = estado.turno
        accion, metricas = agentes[bando].seleccionar_movimiento(estado, tablero, base_a, base_b)
        if accion is None:
            print(f"Turno {turno_num:02d}: el bando {bando} no tiene acciones legales; la partida se detiene.")
            break

        acumulado = totales[bando]
        acumulado["turnos"] += 1
        acumulado["generados"] += metricas["nodos_generados"]
        acumulado["evaluados"] += metricas["nodos_evaluados"]
        acumulado["podas"] += metricas["podas_totales"]
        acumulado["tiempo_ms"] += metricas["tiempo_ms"]

        print(f"Turno {turno_num:02d} | {bando} -> {accion} | Valor {metricas['valor_obtenido']:+.1f} | "
              f"Nodos {metricas['nodos_generados']:4d} | Evaluados {metricas['nodos_evaluados']:4d} | "
              f"Podas {metricas['podas_totales']:3d} | Prof. {metricas['profundidad_alcanzada']} | "
              f"Legal {'sí' if metricas['accion_legal'] else 'NO'} | {metricas['tiempo_ms']:.2f} ms")
        if not metricas["accion_legal"]:
            print(f"         ATENCIÓN: la acción no pasó la verificación: {metricas['detalle_legalidad']}")

        estado = next((nuevo for movimiento, nuevo in estado.sucesores(tablero) if movimiento == accion), None)
        if estado is None:
            print(f"Error interno: la acción {accion} no está entre los sucesores del estado.")
            return 1
        turno_num += 1

    print("-" * 100)
    if estado.es_terminal(base_a, base_b):
        print(f"PARTIDA FINALIZADA: gana el bando {estado.portador} en {turno_num - 1} turnos.")
    else:
        print(f"PARTIDA EMPATADA: se alcanzó el límite de {MAX_TURNOS} turnos sin ganador.")

    print("\nResumen por bando:")
    for bando in ("A", "B"):
        datos = totales[bando]
        promedio = datos["tiempo_ms"] / datos["turnos"] if datos["turnos"] else 0.0
        print(f"  {bando}: turnos {datos['turnos']} | nodos generados {datos['generados']} | "
              f"evaluados {datos['evaluados']} | podas {datos['podas']} | "
              f"tiempo total {datos['tiempo_ms']:.2f} ms | promedio {promedio:.2f} ms")
    return 0


def main():
    """Punto de entrada: carga el escenario (todo o nada) y despacha por 'prueba.modo'.

    Purpose:            ser el único punto de arranque: valida y carga el
                        escenario con cargar_escenario y despacha al modo
                        "busqueda", "partida" o "adversarial".
    Preconditions:      sys.argv[1] es, si viene, la ruta de un escenario JSON.
    Postconditions:     devuelve 0 si el modo terminó bien y 1 si el escenario
                        fue rechazado (se listan los errores), el modo no
                        existe o el modo no se pudo ejecutar. No modifica
                        archivos.
    Complexity:         O(n) por la carga (n = tamaño del JSON) más la
                        complejidad del modo elegido.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo ejecutando los tres modos (busqueda, partida y adversarial) sobre los escenarios de config/ y la suite completa (244 pruebas).
    """
    ruta = sys.argv[1] if len(sys.argv) > 1 else RUTA_POR_DEFECTO
    print(f"TacticalGrid: cargando escenario {ruta}")

    try:
        escenario = cargar_escenario(ruta)
    except EscenarioInvalido as error:
        print("El escenario se rechaza completo; no se cargó nada:")
        for problema in error.errores:
            print(f"  - {problema}")
        return 1

    tablero = escenario.tablero
    print(f"Escenario válido: {tablero.filas}x{tablero.columnas} | "
          f"{len(escenario.unidades)} unidad(es) | turno {escenario.turno} | "
          f"profundidad Minimax {escenario.profundidad_maxima_minimax}")

    modo = (escenario.prueba or {}).get("modo", "partida")
    if modo not in MODOS:
        print(f"Error: modo desconocido {modo!r}. Modos soportados: {', '.join(MODOS)}")
        return 1
    if modo == "busqueda":
        return ejecutar_busqueda(escenario)
    if modo == "adversarial":
        return ejecutar_adversarial(escenario)
    return ejecutar_partida(escenario)


if __name__ == "__main__":
    sys.exit(main())
