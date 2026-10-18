"""Orquestación de la GUI: une main.py y los módulos del motor sin importar tkinter.

No reimplementa lógica de búsqueda, adversarial ni de escenarios: solo llama a
lo ya existente y traduce errores a ErrorControlador (mensaje listo para
mostrar en la interfaz). Por no depender de tkinter, este módulo es testeable
con unittest igual que el resto del proyecto.
"""
from dataclasses import dataclass, replace

import main
from src.adversarial.agent import MinimaxAgent
from src.game.navegacion import ProblemaNavegacion
from src.game.verificador import verificar_solucion


class ErrorControlador(Exception):
    """Error de orquestación con un mensaje ya listo para mostrar al usuario."""


def unidades_con_posiciones(unidades_a, pos_a, unidades_b, pos_b):
    """Unidades de ambos bandos con sus posiciones actuales (modelo N vs N).

    Purpose:            dar la lista completa de unidades a dibujar en el
                        canvas durante una partida en curso, con la posición
                        de cada una tomada de pos_a/pos_b por índice (el mismo
                        orden que usan EstadoJuego y main._unidades_por_bando).
    Preconditions:      unidades_a/unidades_b son las listas de Unidad de cada
                        bando (main._preparar_fase_4); pos_a/pos_b son
                        secuencias de celdas (fila, columna) del mismo largo,
                        en el mismo orden (estado.pos_a/estado.pos_b).
    Postconditions:     devuelve una tupla con una Unidad por cada elemento de
                        unidades_a seguido de cada elemento de unidades_b, con
                        su campo posicion reemplazado por la celda de
                        pos_a/pos_b en su mismo índice. No modifica
                        unidades_a ni unidades_b.
    Complexity:         O(u) en tiempo y espacio, u = len(unidades_a) + len(unidades_b).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    resultado = [replace(unidad, posicion=tuple(pos))
                 for unidad, pos in zip(unidades_a, pos_a)]
    resultado.extend(replace(unidad, posicion=tuple(pos))
                      for unidad, pos in zip(unidades_b, pos_b))
    return tuple(resultado)


def portador_unidad_id(estado, unidades_a, unidades_b):
    """Id de la unidad que transporta el recurso según estado.portador ((bando, índice) o None).

    Purpose:            traducir el portador de un EstadoJuego N vs N
                        ((bando, índice) o None) al id de la unidad concreta
                        que lo transporta, para que el canvas sepa a cuál
                        unidad resaltar.
    Preconditions:      estado.portador es (bando, índice) o None; unidades_a
                        y unidades_b son las listas de Unidad de cada bando,
                        en el mismo orden que estado.pos_a/estado.pos_b.
    Postconditions:     devuelve el id de unidades_a[índice] o
                        unidades_b[índice] según el bando de estado.portador;
                        None si estado.portador es None o el índice no existe
                        en esa lista. No modifica nada.
    Complexity:         O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    if estado.portador is None:
        return None
    bando, indice = estado.portador
    unidades = unidades_a if bando == "A" else unidades_b
    if 0 <= indice < len(unidades):
        return unidades[indice].id
    return None


def recurso_pos_inicial(escenario):
    """Posición donde dibujar el recurso antes de iniciar ningún modo de juego.

    Purpose:            resolver dónde está el recurso en la vista estática del
                        escenario recién cargado: en su posición propia, o en
                        la de la unidad que lo transporta según
                        escenario.portador_recurso (un id de unidad, no un
                        bando, tal como lo define el contrato JSON).
    Preconditions:      escenario viene de cargar_escenario (válido); si
                        escenario.portador_recurso no es None, identifica una
                        unidad existente (lo garantiza el validador).
    Postconditions:     devuelve la posición de esa unidad si
                        escenario.portador_recurso no es None; si no, devuelve
                        escenario.recurso. No modifica nada.
    Complexity:         O(u) en tiempo, u = número de unidades; O(1) en espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    if escenario.portador_recurso is not None:
        for unidad in escenario.unidades:
            if unidad.id == escenario.portador_recurso:
                return unidad.posicion
    return escenario.recurso


def resolver_busqueda_gui(escenario, unidad_id, objetivo, algoritmo, heuristica="manhattan", k=2):
    """Resuelve y verifica una búsqueda para la pestaña Búsqueda de la GUI.

    Purpose:            envolver ProblemaNavegacion + main.resolver_busqueda +
                        verificar_solucion para que la GUI reciba datos listos
                        para mostrar, sin tener que conocer esas tres piezas ni
                        manejar sus excepciones por separado.
    Preconditions:      escenario viene de cargar_escenario (válido); unidad_id
                        es el id elegido en el combobox de la GUI; objetivo es
                        (fila, columna); algoritmo/heuristica/k son la
                        elección del usuario en los controles de la GUI.
    Postconditions:     devuelve (resultado, informe): resultado es el
                        ResultadoBusqueda del algoritmo pedido e informe es el
                        InformeVerificacion de esa solución. Lanza
                        ErrorControlador, con un mensaje listo para mostrar, si
                        unidad_id no existe en escenario.unidades o si
                        algoritmo/heuristica/k no son válidos (ValueError de
                        main.resolver_busqueda). No modifica nada.
    Complexity:         la del algoritmo elegido más la verificación O(n).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    unidad = next((u for u in escenario.unidades if u.id == unidad_id), None)
    if unidad is None:
        raise ErrorControlador(f"La unidad {unidad_id!r} no existe en el escenario.")

    problema = ProblemaNavegacion(escenario.tablero, unidad.posicion, tuple(objetivo))
    try:
        resultado = main.resolver_busqueda(problema, algoritmo, heuristica, k)
    except ValueError as error:
        raise ErrorControlador(str(error))

    informe = verificar_solucion(escenario.tablero, resultado, unidad.posicion, tuple(objetivo))
    return resultado, informe


def preparar_estado_inicial(escenario, profundidad=None, usar_poda=None):
    """Estado inicial N vs N y parámetros efectivos para adversarial/partida.

    Purpose:            envolver main._preparar_fase_4 para la GUI, fallando
                        con un mensaje claro en vez de devolver un estado None
                        cuando el escenario no tiene unidad de algún bando.
    Preconditions:      escenario viene de cargar_escenario (válido);
                        profundidad y usar_poda son la elección del usuario en
                        la GUI, o None para usar la sugerencia del escenario.
    Postconditions:     devuelve (estado, unidades_a, unidades_b, profundidad,
                        usar_poda, orden), igual que main._preparar_fase_4:
                        unidades_a/unidades_b son TODAS las unidades de cada
                        bando (listas), en el mismo orden que estado.pos_a/
                        estado.pos_b. Lanza ErrorControlador si falta una
                        unidad de algún bando. No modifica nada.
    Complexity:         O(u) en tiempo, u = número de unidades; O(1) en espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    estado, unidades_a, unidades_b, profundidad, usar_poda, orden = main._preparar_fase_4(
        escenario, profundidad, usar_poda)
    if estado is None:
        raise ErrorControlador(
            "Se necesita al menos una unidad de cada bando (A y B) para los modos "
            "adversarial y partida.")
    return estado, unidades_a, unidades_b, profundidad, usar_poda, orden


def evaluar_adversarial(escenario, profundidad=None, usar_poda=None):
    """Evalúa el estado inicial del escenario y elige una jugada (sin avanzarla).

    Purpose:            cumplir el modo 'adversarial' de la GUI: decidir con
                        Minimax/alfa-beta la acción del bando del turno sobre
                        el estado inicial del escenario (TODAS sus unidades,
                        modelo N vs N), sin mover ninguna.
    Preconditions:      escenario viene de cargar_escenario (válido);
                        profundidad y usar_poda son la elección del usuario en
                        la GUI, o None para usar la sugerencia del escenario.
    Postconditions:     devuelve un dict con claves "estado", "accion" (tupla
                        (índice, destino) de main._preparar_fase_4/
                        MinimaxAgent), "indice", "destino", "nombre_unidad"
                        (id de la unidad que se mueve, vía main._nombre_unidad),
                        "metricas", "unidades_a" y "unidades_b". Lanza
                        ErrorControlador si falta una unidad de algún bando o
                        si no hay acciones legales para el bando del turno. No
                        modifica nada.
    Complexity:         O(b^d) con Minimax puro, O(b^(d/2)) con alfa-beta
                        (buen orden); b = factor de ramificación (unidades del
                        bando en turno × hasta 4 direcciones).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    estado, unidades_a, unidades_b, profundidad, usar_poda, orden = preparar_estado_inicial(
        escenario, profundidad, usar_poda)

    agente = MinimaxAgent(estado.turno, profundidad=profundidad, usar_poda=usar_poda,
                           orden_direcciones=orden)
    accion, metricas = agente.seleccionar_movimiento(
        estado, escenario.tablero, escenario.tablero.base_a, escenario.tablero.base_b)
    if accion is None:
        raise ErrorControlador("No hay acciones legales para el bando que debe actuar.")

    indice, destino = accion
    unidades_turno = unidades_a if estado.turno == "A" else unidades_b
    nombre_unidad = main._nombre_unidad(estado.turno, indice, unidades_turno)

    return {
        "estado": estado,
        "accion": accion,
        "indice": indice,
        "destino": destino,
        "nombre_unidad": nombre_unidad,
        "metricas": metricas,
        "unidades_a": unidades_a,
        "unidades_b": unidades_b,
    }


@dataclass
class PartidaEnCurso:
    """Estado mutable de una partida jugándose turno a turno en la GUI (modelo N vs N)."""
    escenario: object
    tablero: object
    base_a: tuple
    base_b: tuple
    unidades_a: object
    unidades_b: object
    agentes: dict
    estado: object
    turno_num: int
    totales: dict
    terminada: bool = False
    ganador: str = None


def iniciar_partida(escenario, profundidad=None, usar_poda=None):
    """Construye una PartidaEnCurso lista para jugar_turno, en el turno 1.

    Purpose:            preparar el estado inicial (con TODAS las unidades de
                        cada bando), los agentes de ambos bandos y los
                        acumulados por bando que la pestaña Partida de la GUI
                        necesita antes del primer "Siguiente turno".
    Preconditions:      escenario viene de cargar_escenario (válido);
                        profundidad y usar_poda son la elección del usuario en
                        la GUI, o None para usar la sugerencia del escenario.
    Postconditions:     devuelve una PartidaEnCurso con turno_num=1,
                        terminada=False, ganador=None y totales en cero por
                        bando. Lanza ErrorControlador si falta una unidad de
                        algún bando (vía preparar_estado_inicial). No modifica
                        escenario.
    Complexity:         O(u) en tiempo, u = número de unidades; O(1) en espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    estado, unidades_a, unidades_b, profundidad, usar_poda, orden = preparar_estado_inicial(
        escenario, profundidad, usar_poda)
    agentes = main._crear_agentes(profundidad, usar_poda, orden)
    totales = {
        bando: {"turnos": 0, "generados": 0, "evaluados": 0, "podas": 0, "tiempo_ms": 0.0}
        for bando in ("A", "B")
    }
    return PartidaEnCurso(
        escenario=escenario, tablero=escenario.tablero, base_a=escenario.tablero.base_a,
        base_b=escenario.tablero.base_b, unidades_a=unidades_a, unidades_b=unidades_b,
        agentes=agentes, estado=estado, turno_num=1, totales=totales)


def jugar_turno(partida):
    """Juega un turno de partida (muta `partida` in place) y devuelve su fila de log.

    Purpose:            reproducir, para un único turno, el mismo cuerpo del
                        bucle de main.ejecutar_partida, pero devolviendo los
                        datos del turno a la GUI en vez de imprimirlos, para
                        que "Siguiente turno" avance la partida un turno por
                        clic.
    Preconditions:      partida viene de iniciar_partida (o de una llamada
                        previa a jugar_turno que no terminó la partida).
    Postconditions:     si partida.terminada ya era True, lanza
                        ErrorControlador sin modificar partida. Si no, pide la
                        acción (índice de unidad, destino) al agente del bando
                        activo: si no hay acción legal, marca
                        partida.terminada=True, partida.ganador=None y
                        devuelve una fila con accion=None y "mensaje"; si hay
                        acción, acumula en partida.totales[bando], aplica la
                        acción (partida.estado pasa al sucesor
                        correspondiente), marca partida.terminada/
                        partida.ganador (el BANDO ganador, no la tupla
                        portador) si el estado es terminal o se alcanzó
                        main.MAX_TURNOS, incrementa partida.turno_num y
                        devuelve la fila de métricas de ese turno (incluye
                        "unidad": el id de la unidad que se movió). Lanza
                        ErrorControlador si la acción elegida no aparece entre
                        los sucesores del estado (no debería ocurrir con un
                        agente válido).
    Complexity:         O(b^d) con Minimax puro, O(b^(d/2)) con alfa-beta
                        (buen orden) para decidir la acción del turno.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    if partida.terminada:
        raise ErrorControlador(
            "La partida ya terminó; usa 'Reiniciar partida' para jugar de nuevo.")

    bando = partida.estado.turno
    accion, metricas = partida.agentes[bando].seleccionar_movimiento(
        partida.estado, partida.tablero, partida.base_a, partida.base_b)

    if accion is None:
        partida.terminada = True
        partida.ganador = None
        return {
            "turno": partida.turno_num, "bando": bando, "accion": None,
            "mensaje": f"El bando {bando} no tiene acciones legales; la partida se detiene.",
        }

    acumulado = partida.totales[bando]
    acumulado["turnos"] += 1
    acumulado["generados"] += metricas["nodos_generados"]
    acumulado["evaluados"] += metricas["nodos_evaluados"]
    acumulado["podas"] += metricas["podas_totales"]
    acumulado["tiempo_ms"] += metricas["tiempo_ms"]

    nuevo_estado = next(
        (nuevo for movimiento, nuevo in partida.estado.sucesores(partida.tablero)
         if movimiento == accion), None)
    if nuevo_estado is None:
        raise ErrorControlador(f"Error interno: la acción {accion} no está entre los "
                                f"sucesores del estado.")

    indice, destino = accion
    unidades_bando = partida.unidades_a if bando == "A" else partida.unidades_b
    nombre_unidad = main._nombre_unidad(bando, indice, unidades_bando)

    fila = {
        "turno": partida.turno_num,
        "bando": bando,
        "unidad": nombre_unidad,
        "accion": destino,
        "valor": metricas["valor_obtenido"],
        "nodos_generados": metricas["nodos_generados"],
        "nodos_evaluados": metricas["nodos_evaluados"],
        "podas": metricas["podas_totales"],
        "profundidad": metricas["profundidad_alcanzada"],
        "legal": metricas["accion_legal"],
        "detalle_legalidad": metricas["detalle_legalidad"],
        "tiempo_ms": metricas["tiempo_ms"],
    }

    if partida.turno_num >= main.MAX_TURNOS:
        partida.terminada = True
        partida.ganador = None
    partida.estado = nuevo_estado
    if partida.estado.es_terminal(partida.base_a, partida.base_b):
        partida.terminada = True
        partida.ganador = partida.estado.portador[0]

    partida.turno_num += 1
    return fila
