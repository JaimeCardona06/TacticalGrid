"""Orquestación de la GUI: une main.py y los módulos del motor sin importar tkinter.

No reimplementa lógica de búsqueda, adversarial ni de escenarios: solo llama a
lo ya existente y traduce errores a ErrorControlador (mensaje listo para
mostrar en la interfaz). Por no depender de tkinter, este módulo es testeable
con unittest igual que el resto del proyecto.
"""
from dataclasses import replace


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
