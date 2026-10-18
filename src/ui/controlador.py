"""Orquestación de la GUI: une main.py y los módulos del motor sin importar tkinter.

No reimplementa lógica de búsqueda, adversarial ni de escenarios: solo llama a
lo ya existente y traduce errores a ErrorControlador (mensaje listo para
mostrar en la interfaz). Por no depender de tkinter, este módulo es testeable
con unittest igual que el resto del proyecto.
"""
from dataclasses import replace

import main
from src.adversarial.agent import MinimaxAgent
from src.game.navegacion import ProblemaNavegacion
from src.game.verificador import verificar_solucion


class ErrorControlador(Exception):
    """Error de orquestación con un mensaje ya listo para mostrar al usuario."""


def unidades_con_posiciones(unidades, unidad_a_id, pos_a, unidad_b_id, pos_b):
    """Copia de 'unidades' con las posiciones de unidad_a_id/unidad_b_id reemplazadas.

    Purpose:            dar la lista de unidades a dibujar en el canvas durante
                        una partida en curso, reflejando dónde están ahora las
                        dos unidades que mueve el modelo 1 vs 1, sin tocar las
                        demás (que no se mueven).
    Preconditions:      unidades es una tupla de Unidad; unidad_a_id y
                        unidad_b_id son ids presentes en unidades (o no, si no
                        hay coincidencia no se reemplaza nada); pos_a y pos_b
                        son tuplas (fila, columna).
    Postconditions:     devuelve una tupla nueva, mismo orden, con la posición
                        de la unidad cuyo id es unidad_a_id cambiada a pos_a y
                        la de unidad_b_id a pos_b; las demás quedan iguales. No
                        modifica unidades.
    Complexity:         O(n) en tiempo y espacio, n = len(unidades).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    resultado = []
    for unidad in unidades:
        if unidad.id == unidad_a_id:
            resultado.append(replace(unidad, posicion=tuple(pos_a)))
        elif unidad.id == unidad_b_id:
            resultado.append(replace(unidad, posicion=tuple(pos_b)))
        else:
            resultado.append(unidad)
    return tuple(resultado)


def portador_unidad_id(estado, unidad_a, unidad_b):
    """Id de la unidad que transporta el recurso según estado.portador ("A"/"B"/None).

    Purpose:            traducir el bando portador de un EstadoJuego al id de
                        la unidad concreta que lo transporta, para que el
                        canvas sepa a cuál unidad resaltar.
    Preconditions:      estado tiene un atributo portador ("A", "B" o None);
                        unidad_a y unidad_b son las Unidad de cada bando.
    Postconditions:     devuelve unidad_a.id si estado.portador == "A",
                        unidad_b.id si es "B", None en otro caso. No modifica
                        nada.
    Complexity:         O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    if estado.portador == "A":
        return unidad_a.id
    if estado.portador == "B":
        return unidad_b.id
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
    """Estado inicial 1 vs 1 y parámetros efectivos para adversarial/partida.

    Purpose:            envolver main._preparar_fase_4 para la GUI, fallando
                        con un mensaje claro en vez de devolver un estado None
                        cuando el escenario no tiene unidad de algún bando.
    Preconditions:      escenario viene de cargar_escenario (válido);
                        profundidad y usar_poda son la elección del usuario en
                        la GUI, o None para usar la sugerencia del escenario.
    Postconditions:     devuelve (estado, unidad_a, unidad_b, profundidad,
                        usar_poda, orden), igual que main._preparar_fase_4.
                        Lanza ErrorControlador si falta una unidad de algún
                        bando. No modifica nada.
    Complexity:         O(u) en tiempo, u = número de unidades; O(1) en espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    estado, unidad_a, unidad_b, profundidad, usar_poda, orden = main._preparar_fase_4(
        escenario, profundidad, usar_poda)
    if estado is None:
        raise ErrorControlador(
            "Se necesita al menos una unidad de cada bando (A y B) para los modos "
            "adversarial y partida.")
    return estado, unidad_a, unidad_b, profundidad, usar_poda, orden


def evaluar_adversarial(escenario, profundidad=None, usar_poda=None):
    """Evalúa el estado inicial del escenario y elige una jugada (sin avanzarla).

    Purpose:            cumplir el modo 'adversarial' de la GUI: decidir con
                        Minimax/alfa-beta la acción del bando del turno sobre
                        el estado inicial del escenario, sin mover ninguna
                        unidad.
    Preconditions:      escenario viene de cargar_escenario (válido);
                        profundidad y usar_poda son la elección del usuario en
                        la GUI, o None para usar la sugerencia del escenario.
    Postconditions:     devuelve un dict con claves "estado", "accion",
                        "metricas", "unidad_a", "unidad_b" e "ignoradas" (ids
                        de unidades fuera del modelo 1 vs 1). Lanza
                        ErrorControlador si falta una unidad de algún bando o
                        si no hay acciones legales para el bando del turno. No
                        modifica nada.
    Complexity:         O(b^d) con Minimax puro, O(b^(d/2)) con alfa-beta
                        (buen orden); b = factor de ramificación (<=4).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_controlador.py.
    """
    estado, unidad_a, unidad_b, profundidad, usar_poda, orden = preparar_estado_inicial(
        escenario, profundidad, usar_poda)
    ignoradas = tuple(
        u.id for u in escenario.unidades if u.id not in (unidad_a.id, unidad_b.id))

    agente = MinimaxAgent(estado.turno, profundidad=profundidad, usar_poda=usar_poda,
                           orden_direcciones=orden)
    accion, metricas = agente.seleccionar_movimiento(
        estado, escenario.tablero, escenario.tablero.base_a, escenario.tablero.base_b)
    if accion is None:
        raise ErrorControlador("No hay acciones legales para el bando que debe actuar.")

    return {
        "estado": estado,
        "accion": accion,
        "metricas": metricas,
        "unidad_a": unidad_a,
        "unidad_b": unidad_b,
        "ignoradas": ignoradas,
    }
