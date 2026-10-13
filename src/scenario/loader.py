import json


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
    Student validation: TODO(equipo)
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
