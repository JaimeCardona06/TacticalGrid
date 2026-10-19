import copy
import json

from src.models.board import Board
from src.scenario.bandos import normalizar_bando
from src.scenario.escenario import Escenario, Unidad
from src.scenario.validator import validar_escenario


class ErrorDeCarga(Exception):
    """El archivo no se pudo leer o no es un JSON bien formado."""


def leer_json(ruta):
    """Lee un archivo de escenario y devuelve su contenido como diccionario crudo.

    Purpose:            separar la lectura del archivo de su validación: aquí
                        solo se comprueba que el archivo existe y es JSON; si
                        el escenario es coherente lo decide validator.py.
    Preconditions:      ruta es la ruta de un archivo de texto en UTF-8.
    Postconditions:     devuelve el objeto JSON tal como viene (sin validar ni
                        modificar). Lanza ErrorDeCarga, con un mensaje que dice
                        qué pasó y dónde, si el archivo no existe, no se puede
                        leer o no es JSON válido. No modifica ningún estado.
    Complexity:         O(n) en tiempo y espacio, con n el tamaño del archivo.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_cargador.py: lectura del
                        escenario oficial, archivo inexistente y JSON mal formado con línea y
                        columna.
    """
    try:
        with open(ruta, encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        raise ErrorDeCarga(f"No existe el archivo: {ruta}")
    except OSError as error:
        raise ErrorDeCarga(f"No se pudo leer {ruta}: {error}")
    except json.JSONDecodeError as error:
        raise ErrorDeCarga(
            f"{ruta} no es un JSON válido (línea {error.lineno}, "
            f"columna {error.colno}): {error.msg}"
        )


# Profundidad de Minimax cuando el JSON no trae 'profundidad_maxima_minimax'.
PROFUNDIDAD_POR_DEFECTO = 3

# Tipo de unidad cuando el JSON no trae 'tipo'.
TIPO_UNIDAD_POR_DEFECTO = "estandar"


class EscenarioInvalido(Exception):
    """El escenario no se pudo cargar. 'errores' lista cada problema (qué y dónde)."""

    def __init__(self, errores):
        self.errores = list(errores)
        super().__init__("\n".join(self.errores))


def cargar_escenario(ruta):
    """Lee, valida y construye un escenario completo, todo o nada.

    Purpose:            ser el único punto de entrada para cargar un escenario:
                        o devuelve un Escenario completo y válido, o lanza
                        EscenarioInvalido con todos los errores, sin devolver
                        nada a medias.
    Preconditions:      ruta es la ruta de un archivo de texto en UTF-8.
    Postconditions:     si el archivo se lee y validar_escenario no da errores,
                        devuelve un Escenario independiente del JSON leído
                        (copias propias; bandos en mayúscula; posiciones como
                        tuplas). Si no, lanza EscenarioInvalido con la lista de
                        errores (un problema de lectura cuenta como un error).
                        No modifica ningún estado: quien llama reemplaza su
                        escenario actual solo si esta función no lanzó.
    Complexity:         O(n) en tiempo y espacio, con n = tamaño del escenario
                        (celdas del mapa más unidades).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_cargador.py: carga completa,
                        errores acumulados en un solo EscenarioInvalido, archivo roto o
                        inexistente, y que el escenario anterior no se pierde si la carga
                        falla.
    """
    try:
        datos = leer_json(ruta)
    except ErrorDeCarga as error:
        raise EscenarioInvalido([str(error)])

    errores = validar_escenario(datos)
    if errores:
        raise EscenarioInvalido(errores)
    return _construir_escenario(datos)


def _posicion(objeto):
    """Convierte {"fila": f, "columna": c} (ya validado) en la tupla (f, c)."""
    return (objeto["fila"], objeto["columna"])


def _construir_escenario(datos):
    """Construye el Escenario a partir de un diccionario YA validado.

    Purpose:            traducir el JSON al modelo interno: Board, unidades con
                        bando normalizado, posiciones como tuplas y valores por
                        defecto para los campos opcionales.
    Preconditions:      validar_escenario(datos) devolvió una lista vacía.
    Postconditions:     devuelve un Escenario que no comparte objetos mutables
                        con datos (se copian tipos_terreno, terreno y prueba).
                        No modifica datos.
    Complexity:         O(f*c + u): copia de la matriz y recorrido de unidades.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_cargador.py: normalización de
                        bandos y turno, valores por defecto, posiciones como tuplas, copias
                        independientes del JSON leído y mapa no cuadrado.
    """
    tablero = Board(
        filas=datos["mapa"]["filas"],
        columnas=datos["mapa"]["columnas"],
        tipos_terreno=copy.deepcopy(datos["tipos_terreno"]),
        terreno=copy.deepcopy(datos["terreno"]),
        base_a=_posicion(datos["bases"]["A"]),
        base_b=_posicion(datos["bases"]["B"]),
    )
    unidades = tuple(
        Unidad(
            id=u["id"],
            bando=normalizar_bando(u["bando"]),
            tipo=u.get("tipo", TIPO_UNIDAD_POR_DEFECTO),
            posicion=_posicion(u),
        )
        for u in datos["unidades"]
    )
    juego = datos["juego"]
    profundidad = juego.get("profundidad_maxima_minimax")
    return Escenario(
        tablero=tablero,
        unidades=unidades,
        turno=normalizar_bando(datos["turno"]),
        recurso=_posicion(datos["recurso"]),
        portador_recurso=juego["portador_recurso"],
        profundidad_maxima_minimax=PROFUNDIDAD_POR_DEFECTO if profundidad is None else profundidad,
        prueba=copy.deepcopy(datos.get("prueba")),
    )
