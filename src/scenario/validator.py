# Campos obligatorios del formato de escenario (enunciado, pág. 5).
# Cada entrada es la ruta del campo dentro del JSON.
CAMPOS_OBLIGATORIOS = (
    ("version",),
    ("mapa", "filas"),
    ("mapa", "columnas"),
    ("tipos_terreno",),
    ("terreno",),
    ("bases", "A"),
    ("bases", "B"),
    ("recurso",),
    ("unidades",),
    ("turno",),
    ("juego", "portador_recurso"),
)


def validar_escenario(datos):
    """Valida un escenario crudo y devuelve todos los errores encontrados.

    Purpose:            decidir si un escenario cargado desde JSON se puede
                        usar, antes de construir el tablero ("todo o nada").
    Preconditions:      datos es el objeto devuelto por loader.leer_json.
    Postconditions:     devuelve una lista de textos, uno por error, que dicen
                        qué falla y dónde. Lista vacía significa escenario
                        válido. No modifica datos ni ningún otro estado. Si
                        faltan campos obligatorios, solo devuelve esos
                        errores, porque las demás reglas los necesitan.
    Complexity:         O(c) en tiempo, con c = celdas del mapa, cuando estén
                        todas las reglas; por ahora O(1) (solo campos).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    errores = _validar_campos_obligatorios(datos)
    if errores:
        return errores

    errores = _validar_dimensiones(datos)
    if errores:
        # Las reglas siguientes recorren la matriz terreno: con una forma
        # inconsistente fallarían, así que se corta aquí.
        return errores
    return errores


def _validar_campos_obligatorios(datos):
    """Comprueba que existan todos los campos de CAMPOS_OBLIGATORIOS.

    Purpose:            detectar campos que faltan antes de aplicar las demás
                        reglas, que asumen que están.
    Preconditions:      ninguna; datos puede ser de cualquier tipo.
    Postconditions:     devuelve una lista con un error por cada campo que
                        falta (o por la raíz, si datos no es un objeto JSON).
                        No modifica datos. Un campo con valor null cuenta como
                        presente (portador_recurso lo usa).
    Complexity:         O(c), con c = cantidad de campos obligatorios (fija).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    if not isinstance(datos, dict):
        return ["El escenario debe ser un objeto JSON en la raíz"]

    errores = []
    for ruta in CAMPOS_OBLIGATORIOS:
        actual = datos
        for nombre in ruta:
            if not isinstance(actual, dict) or nombre not in actual:
                errores.append(f"Falta el campo obligatorio '{'.'.join(ruta)}'")
                break
            actual = actual[nombre]
    return errores


def _es_entero(valor):
    """True si valor es un entero de verdad (bool también es int en Python)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_dimensiones(datos):
    """Regla 1: filas y columnas positivas y consistentes con la matriz terreno.

    Purpose:            garantizar que el mapa tiene una forma rectangular
                        válida, para que el resto del código pueda indexar
                        terreno[fila][columna] sin salirse. No exige que el
                        mapa sea cuadrado ni de un tamaño mínimo: cualquier
                        filas x columnas positivo es válido.
    Preconditions:      los campos obligatorios existen (ver
                        _validar_campos_obligatorios).
    Postconditions:     devuelve una lista con un error por cada problema:
                        filas o columnas que no son enteros positivos; terreno
                        que no es una lista; cantidad de filas de terreno
                        distinta de mapa.filas; o una fila de terreno con
                        longitud distinta de mapa.columnas (se reporta cada
                        fila incorrecta, con su índice). No modifica datos.
    Complexity:         O(f) en tiempo, con f = filas de la matriz terreno
                        (se mide la longitud de cada fila, sin recorrer celdas).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    errores = []
    filas = datos["mapa"]["filas"]
    columnas = datos["mapa"]["columnas"]

    for nombre, valor in (("mapa.filas", filas), ("mapa.columnas", columnas)):
        if not _es_entero(valor) or valor <= 0:
            errores.append(f"'{nombre}' debe ser un entero positivo (recibido: {valor!r})")
    if errores:
        return errores

    terreno = datos["terreno"]
    if not isinstance(terreno, list):
        return ["'terreno' debe ser una lista de filas"]

    if len(terreno) != filas:
        errores.append(
            f"'terreno' tiene {len(terreno)} filas pero mapa.filas es {filas}"
        )
    for i, fila in enumerate(terreno):
        if not isinstance(fila, list):
            errores.append(f"La fila {i} de 'terreno' debe ser una lista")
        elif len(fila) != columnas:
            errores.append(
                f"La fila {i} de 'terreno' tiene {len(fila)} columnas "
                f"pero mapa.columnas es {columnas}"
            )
    return errores
