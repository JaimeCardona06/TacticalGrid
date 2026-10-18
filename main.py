"""TacticalGrid: punto de entrada de la aplicación por consola.

Purpose:            cargar un escenario JSON con el loader validado del
                    proyecto (todo o nada) y despachar la ejecución según
                    `prueba.modo`: "busqueda", "partida" o "adversarial".
Preconditions:      se ejecuta con `python main.py [ruta.json] [opciones]`; la
                    ruta por defecto es config/mapa_partida.json. Opciones:
                    --algoritmo, --heuristica, --k, --profundidad y
                    --no-preguntar (ver construir_parser). Sin banderas, en
                    consola interactiva se muestra un menú para que el usuario
                    elija el algoritmo y, para A*/Beam, la heurística y el
                    ancho del haz k; el JSON queda como sugerencia.
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

Modelo adversarial N vs N: el bucle Minimax usa TODAS las unidades de cada
bando (ver EstadoJuego en src/models/state.py). En cada turno el bando activo
elige una unidad y una dirección, así que el factor de ramificación es
b = (unidades del bando en turno) × (hasta 4 direcciones): con 3 unidades por
bando queda acotado en 12, demostrable con profundidad limitada y poda
alfa-beta. La profundidad pedida sigue siendo configurable, y los escenarios
1 vs 1 conservan su comportamiento y sus métricas.
"""

import argparse
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
from src.search.heuristics import HEURISTICAS
from src.search.informed import a_estrella, beam_search
from src.search.uninformed import bfs, dfs, ucs

RUTA_POR_DEFECTO = "config/mapa_partida.json"
MODOS = ("busqueda", "partida", "adversarial")

# Regla determinista de cierre: si nadie gana en MAX_TURNOS, la partida empata.
MAX_TURNOS = 100

_ALGORITMOS_SIMPLES = {"BFS": bfs, "DFS": dfs, "UCS": ucs}

# Nombres aceptados por el usuario (banderas, menú o JSON) y su forma canónica.
NOMBRES_BUSQUEDA = ("BFS", "DFS", "UCS", "A*", "BEAM")
NOMBRES_ADVERSARIAL = ("MINIMAX", "ALFA_BETA")
_ALIAS_BUSQUEDA = {
    "BFS": "BFS",
    "DFS": "DFS",
    "UCS": "UCS",
    "A*": "A_ESTRELLA",
    "ASTAR": "A_ESTRELLA",
    "A_ESTRELLA": "A_ESTRELLA",
    "BEAM": "BEAM",
    "BEAM_SEARCH": "BEAM",
}
_ALIAS_ADVERSARIAL = {
    "MINIMAX": False,        # Minimax puro (sin poda)
    "MINIMAX_PURO": False,
    "PURO": False,
    "ALFA_BETA": True,       # Minimax con poda alfa-beta
    "ALFABETA": True,
    "ALFA-BETA": True,
    "PODA": True,
}


def normalizar_algoritmo_busqueda(nombre):
    """Forma canónica ("BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM") de un algoritmo de búsqueda.

    Purpose:            aceptar los nombres que escribe el usuario (banderas,
                        menú o JSON), incluidas variantes como "A*" o "astar",
                        y rechazar lo desconocido con un mensaje útil.
    Preconditions:      nombre es texto o algo convertible a texto.
    Postconditions:     devuelve la forma canónica; lanza ValueError, con la
                        lista de nombres válidos, si no es un algoritmo de
                        búsqueda.
    Complexity:         O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con las pruebas de alias y errores de tests/test_main.py.
    """
    clave = str(nombre).strip().upper().replace(" ", "_")
    if clave not in _ALIAS_BUSQUEDA:
        raise ValueError(
            f"Algoritmo de búsqueda desconocido: {nombre!r}. Usa: {', '.join(NOMBRES_BUSQUEDA)}")
    return _ALIAS_BUSQUEDA[clave]


def normalizar_algoritmo_adversarial(nombre):
    """Traduce el algoritmo adversarial pedido a usar_poda (True = alfa-beta, False = puro).

    Purpose:            aceptar MINIMAX/MINIMAX_PURO/PURO y
                        ALFA_BETA/ALFABETA/PODA (cualquier capitalización) y
                        devolver si se juega con poda alfa-beta.
    Preconditions:      nombre es texto o algo convertible a texto.
    Postconditions:     devuelve True (poda) o False (puro); lanza ValueError,
                        con los nombres válidos, si no es un algoritmo
                        adversarial.
    Complexity:         O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con las pruebas de alias y errores de tests/test_main.py.
    """
    clave = str(nombre).strip().upper().replace(" ", "_")
    if clave not in _ALIAS_ADVERSARIAL:
        raise ValueError(
            f"Algoritmo adversarial desconocido: {nombre!r}. Usa: {', '.join(NOMBRES_ADVERSARIAL)}")
    return _ALIAS_ADVERSARIAL[clave]


def _unidades_por_bando(escenario, bando):
    """Todas las unidades del bando, en el orden del escenario (modelo N vs N)."""
    return [unidad for unidad in escenario.unidades if unidad.bando == bando]


def _portador_inicial(escenario, unidades_a, unidades_b):
    """Mapea 'juego.portador_recurso' (id de unidad) a (bando, índice), o None."""
    if escenario.portador_recurso is None:
        return None
    for bando, unidades in (("A", unidades_a), ("B", unidades_b)):
        for indice, unidad in enumerate(unidades):
            if unidad.id == escenario.portador_recurso:
                return (bando, indice)
    return None


def _nombre_unidad(bando, indice, unidades):
    """Identificador para imprimir la unidad que actúa ('A2'), o 'A[índice]' si falta."""
    if 0 <= indice < len(unidades):
        return unidades[indice].id
    return f"{bando}[{indice}]"


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


def resolver_busqueda(problema, algoritmo="A_ESTRELLA", heuristica="manhattan", k=2):
    """Ejecuta el algoritmo de búsqueda pedido sobre un problema de navegación.

    Purpose:            ser el punto ÚNICO de despacho de los algoritmos de
                        búsqueda: recibe el algoritmo como parámetro explícito
                        para que consola y GUI ejecuten exactamente lo que el
                        usuario eligió, sin leer el JSON aquí.
    Preconditions:      problema es un ProblemaNavegacion construido sobre un
                        tablero validado; algoritmo es un nombre de
                        NOMBRES_BUSQUEDA (se aceptan alias como "A*"); k es el
                        ancho del haz para Beam.
    Postconditions:     devuelve un ResultadoBusqueda del algoritmo pedido.
                        Lanza ValueError si el algoritmo o la heurística no
                        existen, o si k no es un entero positivo para Beam. No
                        modifica nada.
    Complexity:         la del algoritmo elegido (ver su documentación).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con las pruebas de despacho de tests/test_main.py y las ejecuciones con banderas.
    """
    canonico = normalizar_algoritmo_busqueda(algoritmo)

    if canonico in _ALGORITMOS_SIMPLES:
        return _ALGORITMOS_SIMPLES[canonico](problema)
    if canonico == "A_ESTRELLA":
        return a_estrella(problema, heuristica)
    return beam_search(problema, k, heuristica)


def ejecutar_busqueda(escenario, algoritmo=None, heuristica=None, k=None):
    """Modo 'busqueda': resuelve la navegación pedida en 'prueba' y la verifica.

    Purpose:            correr una prueba de búsqueda uniactiva sobre el
                        escenario (unidad y objetivo indicados en 'prueba'),
                        mostrar el resultado con sus métricas y verificar la
                        solución con el verificador independiente.
    Preconditions:      escenario viene de cargar_escenario (válido y
                        completo); 'prueba.unidad_inicio' identifica una unidad
                        existente y 'prueba.objetivo' trae fila y columna.
                        algoritmo, heuristica y k son la elección explícita del
                        usuario (consola o GUI): None significa "usa la
                        sugerencia del JSON" (y si tampoco está, el valor por
                        defecto).
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

    # El usuario (banderas/menú/GUI) manda; el JSON queda como sugerencia.
    eleccion_algoritmo = algoritmo if algoritmo is not None else prueba.get("algoritmo", "A_ESTRELLA")
    eleccion_heuristica = heuristica if heuristica is not None else prueba.get("heuristica", "manhattan")
    eleccion_k = k if k is not None else prueba.get("k", 2)
    try:
        canonico = normalizar_algoritmo_busqueda(eleccion_algoritmo)
    except ValueError as error:
        print(f"Error: {error}")
        return 1

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

    extras = ""
    if canonico == "A_ESTRELLA":
        extras = f" (heurística: {eleccion_heuristica})"
    elif canonico == "BEAM":
        extras = f" (heurística: {eleccion_heuristica}, k: {eleccion_k})"
    print(f"\n=== MODO BÚSQUEDA: {unidad.id} {unidad.posicion} -> {objetivo} ===")
    print(f"Algoritmo elegido: {canonico}{extras}")
    problema = ProblemaNavegacion(escenario.tablero, unidad.posicion, objetivo)
    if not problema.extremos_transitables():
        print("Aviso: el inicio o el objetivo no son transitables; no existe ruta.")

    try:
        resultado = resolver_busqueda(problema, canonico, eleccion_heuristica, eleccion_k)
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


def _preparar_fase_4(escenario, profundidad=None, usar_poda=None):
    """Estado inicial N vs N y parámetros efectivos de la fase adversarial.

    Purpose:            traducir el Escenario ya validado a lo que la fase
                        adversarial necesita (estado con TODAS las unidades,
                        profundidad, poda y orden de acciones), sin volver a
                        leer el JSON.
    Preconditions:      escenario viene de cargar_escenario (válido y
                        completo); profundidad y usar_poda son la elección
                        explícita del usuario (consola o GUI), o None para
                        usar la sugerencia del JSON.
    Postconditions:     devuelve (estado, unidades_a, unidades_b, profundidad,
                        usar_poda, orden). estado es None si a algún bando le
                        falta unidad (el escenario sigue siendo válido); si
                        'juego.portador_recurso' identifica una unidad, el
                        estado nace con ese portador y el recurso en su celda;
                        profundidad efectiva es la elegida si es un entero
                        positivo y, si no, 'prueba.profundidad' y luego
                        'juego.profundidad_maxima_minimax'; usar_poda efectivo
                        es el elegido y, si no, 'prueba.usar_poda'. No modifica
                        nada.
    Complexity:         O(u) por la búsqueda de unidades y del portador.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo ejecutando los tres modos (busqueda, partida y adversarial) sobre los escenarios de config/ y la suite completa.
    """
    prueba = escenario.prueba or {}
    if profundidad is None:
        profundidad = prueba.get("profundidad") or escenario.profundidad_maxima_minimax
    if not isinstance(profundidad, int) or isinstance(profundidad, bool) or profundidad < 1:
        print(f"Aviso: profundidad inválida ({profundidad!r}); se usa la del escenario: "
              f"{escenario.profundidad_maxima_minimax}.")
        profundidad = escenario.profundidad_maxima_minimax
    if usar_poda is None:
        usar_poda = bool(prueba.get("usar_poda", True))
    orden = _orden_de_prueba(prueba)

    unidades_a = _unidades_por_bando(escenario, "A")
    unidades_b = _unidades_por_bando(escenario, "B")
    estado = None
    if unidades_a and unidades_b:
        portador = _portador_inicial(escenario, unidades_a, unidades_b)
        recurso_pos = escenario.recurso
        if portador is not None:
            bando, indice = portador
            recurso_pos = (unidades_a if bando == "A" else unidades_b)[indice].posicion
        estado = EstadoJuego(
            pos_a=tuple(u.posicion for u in unidades_a),
            pos_b=tuple(u.posicion for u in unidades_b),
            portador=portador,
            turno=escenario.turno,
            recurso_pos=recurso_pos,
        )
    return estado, unidades_a, unidades_b, profundidad, usar_poda, orden


def _crear_agentes(profundidad, usar_poda, orden):
    """Un agente Minimax por bando, con los mismos parámetros de búsqueda."""
    return {
        bando: MinimaxAgent(bando, profundidad=profundidad, usar_poda=usar_poda, orden_direcciones=orden)
        for bando in ("A", "B")
    }


def ejecutar_adversarial(escenario, profundidad=None, usar_poda=None):
    """Modo 'adversarial': evalúa el estado actual y muestra la acción elegida.

    Purpose:            cumplir el modo 'adversarial' del enunciado: evaluar
                        el estado del escenario mediante Minimax/alfa-beta y
                        seleccionar una acción para el bando del turno, sin
                        avanzar la partida.
    Preconditions:      escenario viene de cargar_escenario (válido y
                        completo), con al menos una unidad por bando;
                        profundidad y usar_poda son la elección explícita del
                        usuario (consola o GUI), o None para usar el JSON.
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
    estado, unidades_a, unidades_b, profundidad, usar_poda, orden = _preparar_fase_4(escenario, profundidad, usar_poda)
    if estado is None:
        print("Error: se necesita al menos una unidad de cada bando para la fase adversarial.")
        return 1

    tablero = escenario.tablero
    unidades = unidades_a if estado.turno == "A" else unidades_b
    print(f"\n=== MODO ADVERSARIAL: evaluación de una acción (lanza {estado.turno}) ===")
    print(f"Profundidad: {profundidad} | Poda alfa-beta: {'sí' if usar_poda else 'no'}")
    print(f"Estado evaluado: {estado}")

    agente = MinimaxAgent(estado.turno, profundidad=profundidad, usar_poda=usar_poda, orden_direcciones=orden)
    accion, metricas = agente.seleccionar_movimiento(estado, tablero, tablero.base_a, tablero.base_b)
    if accion is None:
        print("No hay acciones legales para el bando que debe actuar.")
        return 1

    indice, destino = accion
    nombre = _nombre_unidad(estado.turno, indice, unidades)
    print(f"Acción elegida: la unidad {nombre} (bando {estado.turno}) se mueve a {destino}")
    print(f"Verificación de legalidad: {'LEGAL' if metricas['accion_legal'] else 'ILEGAL'}"
          f" — {metricas['detalle_legalidad']}")
    print(f"Valor obtenido: {metricas['valor_obtenido']:+.1f} | "
          f"Nodos generados: {metricas['nodos_generados']} | Evaluados: {metricas['nodos_evaluados']} | "
          f"Podas: {metricas['podas_totales']} | Profundidad efectiva: {metricas['profundidad_alcanzada']} | "
          f"Tiempo: {metricas['tiempo_ms']:.2f} ms")
    return 0


def ejecutar_partida(escenario, profundidad=None, usar_poda=None):
    """Modo 'partida': simula la partida por turnos entre dos agentes Minimax.

    Purpose:            continuar el juego por turnos (modo 'partida' del
                        enunciado): en cada turno, el agente del bando activo
                        elige una acción con Minimax/alfa-beta y el estado
                        avanza hasta la victoria o el límite de turnos.
    Preconditions:      escenario viene de cargar_escenario (válido y
                        completo), con al menos una unidad por bando;
                        profundidad y usar_poda son la elección explícita del
                        usuario (consola o GUI), o None para usar el JSON.
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
    estado, unidades_a, unidades_b, profundidad, usar_poda, orden = _preparar_fase_4(escenario, profundidad, usar_poda)
    if estado is None:
        print("Error: se necesita al menos una unidad de cada bando para la fase adversarial.")
        return 1

    tablero = escenario.tablero
    base_a, base_b = tablero.base_a, tablero.base_b
    agentes = _crear_agentes(profundidad, usar_poda, orden)
    totales = {
        bando: {"turnos": 0, "generados": 0, "evaluados": 0, "podas": 0, "tiempo_ms": 0.0}
        for bando in ("A", "B")
    }

    print(f"\n=== MODO PARTIDA: {len(unidades_a)} unidad(es) de A vs {len(unidades_b)} de B ===")
    print(f"Unidades A: {', '.join(u.id for u in unidades_a)} | Unidades B: {', '.join(u.id for u in unidades_b)}")
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

        indice, destino = accion
        nombre = _nombre_unidad(bando, indice, unidades_a if bando == "A" else unidades_b)
        print(f"Turno {turno_num:02d} | {bando} -> {nombre} {destino} | Valor {metricas['valor_obtenido']:+.1f} | "
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
        print(f"PARTIDA FINALIZADA: gana el bando {estado.portador[0]} en {turno_num - 1} turnos.")
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


def _profundidad_sugerida(escenario):
    """Profundidad que el JSON sugiere para jugar (prueba.profundidad > juego)."""
    prueba = escenario.prueba or {}
    valor = prueba.get("profundidad") or escenario.profundidad_maxima_minimax
    if isinstance(valor, int) and not isinstance(valor, bool) and valor >= 1:
        return valor
    return escenario.profundidad_maxima_minimax


def _elegir_busqueda_interactiva(prueba, entrada=input):
    """Menú numerado para elegir el algoritmo de búsqueda a visualizar.

    Purpose:            cumplir la regla de que el usuario (no el JSON) elige
                        con qué algoritmo se visualiza/ejecuta la búsqueda.
    Preconditions:      prueba es el bloque 'prueba' del escenario (sugerencia);
                        entrada es input() o una función equivalente (pruebas).
    Postconditions:     imprime el menú y devuelve la forma canónica del
                        algoritmo elegido ("BFS", "DFS", "UCS", "A_ESTRELLA" o
                        "BEAM"). Enter acepta la sugerencia del JSON (o
                        A_ESTRELLA si el JSON no trae un nombre válido).
    Complexity:         O(1) en tiempo y espacio (espera interacción).
    AI usage:           Yes
    AI intervention:    la IA escribió el menú y esta documentación.
    Student validation: Validado por el equipo con las pruebas del menú (opción, Enter y reintento).
    """
    try:
        sugerido = normalizar_algoritmo_busqueda(prueba.get("algoritmo", "A_ESTRELLA"))
    except ValueError:
        sugerido = "A_ESTRELLA"
    opciones = ("BFS", "DFS", "UCS", "A_ESTRELLA", "BEAM")
    etiquetas = {
        "BFS": "BFS (anchura)",
        "DFS": "DFS (profundidad)",
        "UCS": "UCS (costo uniforme)",
        "A_ESTRELLA": "A* (heurística)",
        "BEAM": "Beam Search (haz)",
    }
    print("\nAlgoritmos disponibles para la búsqueda:")
    for indice, opcion in enumerate(opciones, start=1):
        marca = "   <- sugerido por el JSON" if opcion == sugerido else ""
        print(f"  {indice}) {etiquetas[opcion]}{marca}")
    while True:
        try:
            respuesta = entrada(f"Elige el algoritmo [1-{len(opciones)}, Enter = {sugerido}]: ").strip()
        except EOFError:
            print("\nAviso: no hay entrada interactiva; se usa la sugerencia del JSON.")
            return sugerido
        if not respuesta:
            return sugerido
        if respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
            return opciones[int(respuesta) - 1]
        print(f"  Opción inválida: escribe un número del 1 al {len(opciones)} o Enter para {sugerido}.")


def _elegir_heuristica_interactiva(prueba, entrada=input):
    """Menú numerado para elegir la heurística de A* o Beam Search.

    Purpose:            cumplir la regla de que el usuario (no el JSON) elige
                        con qué heurística se busca cuando eligió un algoritmo
                        informado y no pasó --heuristica.
    Preconditions:      prueba es el bloque 'prueba' del escenario (sugerencia);
                        entrada es input() o una función equivalente (pruebas).
    Postconditions:     imprime el menú y devuelve el nombre canónico de la
                        heurística ("manhattan", "manhattan_pasos" o
                        "distancia_bfs"). Enter acepta la sugerencia del JSON
                        (o "manhattan" si el JSON no trae un nombre válido).
    Complexity:         O(1) en tiempo y espacio (espera interacción).
    AI usage:           Yes
    AI intervention:    la IA escribió el menú y esta documentación.
    Student validation: Validado por el equipo con las pruebas del menú (opción, Enter y reintento).
    """
    sugerida = prueba.get("heuristica", "manhattan")
    if sugerida not in HEURISTICAS:
        sugerida = "manhattan"
    opciones = ("manhattan", "manhattan_pasos", "distancia_bfs")
    etiquetas = {
        "manhattan": "manhattan (pasos x costo mínimo)",
        "manhattan_pasos": "manhattan_pasos (solo pasos)",
        "distancia_bfs": "distancia_bfs (rodeando muros)",
    }
    print("\nHeurísticas disponibles para A*/Beam:")
    for indice, opcion in enumerate(opciones, start=1):
        marca = "   <- sugerida por el JSON" if opcion == sugerida else ""
        print(f"  {indice}) {etiquetas[opcion]}{marca}")
    while True:
        try:
            respuesta = entrada(f"Elige la heurística [1-{len(opciones)}, Enter = {sugerida}]: ").strip()
        except EOFError:
            print("\nAviso: no hay entrada interactiva; se usa la sugerencia del JSON.")
            return sugerida
        if not respuesta:
            return sugerida
        if respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
            return opciones[int(respuesta) - 1]
        print(f"  Opción inválida: escribe un número del 1 al {len(opciones)} o Enter para {sugerida}.")


def _elegir_k_interactivo(prueba, entrada=input):
    """Pregunta el ancho del haz k para Beam Search.

    Purpose:            cumplir la regla de que el usuario (no el JSON) elige
                        con qué k se ejecuta Beam cuando no pasó --k.
    Preconditions:      prueba es el bloque 'prueba' del escenario (sugerencia);
                        entrada es input() o una función equivalente (pruebas).
    Postconditions:     devuelve un entero >= 1. Enter acepta la sugerencia del
                        JSON (o 2 si no trae un k válido). Reintenta con
                        entradas inválidas; EOFError devuelve la sugerencia.
    Complexity:         O(1) en tiempo y espacio (espera interacción).
    AI usage:           Yes
    AI intervention:    la IA escribió la pregunta y esta documentación.
    Student validation: Validado por el equipo con las pruebas del menú (valor, Enter y reintento).
    """
    sugerido = prueba.get("k", 2)
    if isinstance(sugerido, bool) or not isinstance(sugerido, int) or sugerido < 1:
        sugerido = 2
    while True:
        try:
            respuesta = entrada(f"Ancho del haz k [Enter = {sugerido}]: ").strip()
        except EOFError:
            print("\nAviso: no hay entrada interactiva; se usa la sugerencia del JSON.")
            return sugerido
        if not respuesta:
            return sugerido
        if respuesta.isdigit() and int(respuesta) >= 1:
            return int(respuesta)
        print(f"  k inválido: escribe un entero >= 1 o Enter para {sugerido}.")


def _elegir_adversarial_interactiva(prueba, profundidad_sugerida, entrada=input):
    """Menú numerado para elegir el algoritmo adversarial y la profundidad.

    Purpose:            cumplir la regla de que el usuario (no el JSON) elige
                        con qué algoritmo se juega: Minimax puro o alfa-beta, y
                        a qué profundidad.
    Preconditions:      prueba es el bloque 'prueba' del escenario (sugerencia);
                        profundidad_sugerida es un entero >= 1; entrada es
                        input() o una función equivalente (pruebas).
    Postconditions:     imprime el menú y devuelve (usar_poda, profundidad):
                        usar_poda=True para alfa-beta y False para Minimax
                        puro. Enter acepta la sugerencia en cada pregunta.
    Complexity:         O(1) en tiempo y espacio (espera interacción).
    AI usage:           Yes
    AI intervention:    la IA escribió el menú y esta documentación.
    Student validation: Validado por el equipo con las pruebas del menú (opción, Enter y reintento).
    """
    poda_sugerida = bool(prueba.get("usar_poda", True))
    print("\nAlgoritmos disponibles para jugar:")
    print("  1) Minimax puro (sin poda)" + ("   <- sugerido por el JSON" if not poda_sugerida else ""))
    print("  2) Alfa-beta (con poda)" + ("   <- sugerido por el JSON" if poda_sugerida else ""))
    while True:
        try:
            respuesta = entrada(f"Elige el algoritmo [1-2, Enter = {2 if poda_sugerida else 1}]: ").strip()
        except EOFError:
            print("\nAviso: no hay entrada interactiva; se usan las sugerencias del JSON.")
            return poda_sugerida, profundidad_sugerida
        if not respuesta:
            usar_poda = poda_sugerida
            break
        if respuesta in ("1", "2"):
            usar_poda = respuesta == "2"
            break
        print("  Opción inválida: escribe 1, 2 o Enter.")
    while True:
        try:
            respuesta = entrada(f"Profundidad [Enter = {profundidad_sugerida}]: ").strip()
        except EOFError:
            print("\nAviso: no hay entrada interactiva; se usa la profundidad sugerida.")
            return usar_poda, profundidad_sugerida
        if not respuesta:
            return usar_poda, profundidad_sugerida
        if respuesta.isdigit() and int(respuesta) >= 1:
            return usar_poda, int(respuesta)
        print("  Profundidad inválida: escribe un entero >= 1 o Enter.")


def construir_parser():
    """Parser de argumentos: ruta del escenario y elección del usuario.

    Purpose:            definir la interfaz de consola: ruta opcional y
                        banderas para elegir el algoritmo (búsqueda o
                        adversarial), la heurística, el ancho del haz y la
                        profundidad.
    Preconditions:      ninguna.
    Postconditions:     devuelve un argparse.ArgumentParser sin usarlo; no
                        imprime ni valida combinaciones (eso lo hace main()).
    Complexity:         O(1).
    AI usage:           Yes
    AI intervention:    la IA escribió el parser y esta documentación.
    Student validation: Validado por el equipo ejecutando main.py con banderas y sin ellas.
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="TacticalGrid: carga un escenario JSON y ejecuta el modo de su 'prueba'.")
    parser.add_argument("ruta", nargs="?", default=None,
                        help=f"escenario JSON (por defecto: {RUTA_POR_DEFECTO})")
    parser.add_argument("--algoritmo", default=None,
                        help="búsqueda: BFS, DFS, UCS, A* o BEAM | jugar: MINIMAX (puro) o ALFA_BETA")
    parser.add_argument("--heuristica", default=None,
                        help="heurística de A*/Beam: manhattan, manhattan_pasos o distancia_bfs")
    parser.add_argument("--k", type=int, default=None, help="ancho del haz para Beam Search")
    parser.add_argument("--profundidad", type=int, default=None,
                        help="profundidad de Minimax para jugar (partida/adversarial)")
    parser.add_argument("--no-preguntar", action="store_true",
                        help="no mostrar el menú interactivo; usa la sugerencia del JSON")
    return parser


def main(argv=None):
    """Punto de entrada: carga el escenario (todo o nada) y despacha por 'prueba.modo'.

    Purpose:            ser el único punto de arranque: valida y carga el
                        escenario con cargar_escenario, resuelve el algoritmo
                        elegido (banderas > menú interactivo > JSON) y
                        despacha al modo "busqueda", "partida" o "adversarial".
    Preconditions:      argv son los argumentos de consola (None = sys.argv).
    Postconditions:     devuelve 0 si el modo terminó bien y 1 si el escenario
                        fue rechazado (se listan los errores), el modo no
                        existe o la elección del usuario no es válida. Sin
                        ninguna bandera, en consola interactiva muestra el
                        menú; con --no-preguntar o sin terminal usa las
                        sugerencias del JSON. No modifica archivos.
    Complexity:         O(n) por la carga (n = tamaño del JSON) más la
                        complejidad del modo elegido.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo ejecutando los tres modos con y sin banderas, más la suite completa.
    """
    args = construir_parser().parse_args(argv)
    ruta = args.ruta or RUTA_POR_DEFECTO
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

    # El usuario elige el algoritmo: banderas de consola > menú interactivo > JSON.
    hay_banderas = any(valor is not None for valor in
                       (args.algoritmo, args.heuristica, args.k, args.profundidad))
    preguntar = not hay_banderas and not args.no_preguntar and sys.stdin.isatty()

    if modo == "busqueda":
        if args.profundidad is not None:
            print("Aviso: --profundidad solo aplica a partida/adversarial; se ignora en búsqueda.")
        algoritmo = args.algoritmo
        if preguntar:
            algoritmo = _elegir_busqueda_interactiva(escenario.prueba or {})
        heuristica, k = args.heuristica, args.k
        canonico = None
        if algoritmo is not None:
            try:
                canonico = normalizar_algoritmo_busqueda(algoritmo)
            except ValueError:
                canonico = None  # el nombre inválido lo reporta ejecutar_busqueda
        puede_preguntar = not args.no_preguntar and sys.stdin.isatty()
        if canonico in ("A_ESTRELLA", "BEAM") and heuristica is None and puede_preguntar:
            heuristica = _elegir_heuristica_interactiva(escenario.prueba or {})
        if canonico == "BEAM" and k is None and puede_preguntar:
            k = _elegir_k_interactivo(escenario.prueba or {})
        return ejecutar_busqueda(escenario, algoritmo=algoritmo, heuristica=heuristica, k=k)

    if args.k is not None or args.heuristica is not None:
        print("Aviso: --heuristica y --k solo aplican a búsqueda; se ignoran al jugar.")

    profundidad, usar_poda = args.profundidad, None
    try:
        if args.algoritmo is not None:
            usar_poda = normalizar_algoritmo_adversarial(args.algoritmo)
        elif preguntar:
            usar_poda, profundidad = _elegir_adversarial_interactiva(
                escenario.prueba or {}, profundidad or _profundidad_sugerida(escenario))
    except ValueError as error:
        print(f"Error: {error}")
        return 1

    if modo == "adversarial":
        return ejecutar_adversarial(escenario, profundidad=profundidad, usar_poda=usar_poda)
    return ejecutar_partida(escenario, profundidad=profundidad, usar_poda=usar_poda)


if __name__ == "__main__":
    sys.exit(main())
