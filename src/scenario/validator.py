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

    # Las reglas siguientes no se cortan entre sí: así se informan todos los
    # errores juntos. Las que consulten tipos_terreno por nombre deben saltarse
    # las celdas con terreno desconocido (ya reportadas por la regla 2).
    errores += _validar_terrenos_existen(datos)
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


def _plural(cantidad, singular, plural):
    """Devuelve singular si cantidad es 1, y plural en otro caso."""
    return singular if cantidad == 1 else plural


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


# Máximo de celdas que se listan por terreno desconocido en el mensaje.
MAX_CELDAS_EN_MENSAJE = 5


def _validar_terrenos_existen(datos):
    """Regla 2: todos los terrenos usados en la matriz existen en tipos_terreno.

    Purpose:            detectar nombres de terreno escritos en la matriz que
                        no están definidos en el catálogo, para que ningún
                        algoritmo consulte un costo o una transitabilidad
                        inexistente.
    Preconditions:      la matriz terreno ya pasó _validar_dimensiones (es una
                        lista de listas del tamaño declarado).
    Postconditions:     devuelve una lista con UN error por cada nombre de
                        terreno desconocido (no uno por celda), que indica las
                        primeras MAX_CELDAS_EN_MENSAJE celdas donde aparece y
                        cuántas hay en total; más un error por 'tipos_terreno'
                        mal formado o por celdas cuyo valor no es texto. No
                        modifica datos.
    Complexity:         O(f*c) en tiempo, con f filas y c columnas (se mira
                        cada celda una vez); O(u) en espacio, con u = celdas
                        con terreno desconocido.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    tipos = datos["tipos_terreno"]
    if not isinstance(tipos, dict):
        return ["'tipos_terreno' debe ser un objeto con un tipo de terreno por nombre"]

    desconocidos = {}  # nombre -> celdas (fila, columna) donde aparece
    no_texto = []      # celdas cuyo valor ni siquiera es un nombre (texto)
    for i, fila in enumerate(datos["terreno"]):
        for j, nombre in enumerate(fila):
            if not isinstance(nombre, str):
                no_texto.append((i, j))
            elif nombre not in tipos:
                desconocidos.setdefault(nombre, []).append((i, j))

    errores = []
    for nombre, celdas in desconocidos.items():
        listadas = ", ".join(str(c) for c in celdas[:MAX_CELDAS_EN_MENSAJE])
        resto = len(celdas) - MAX_CELDAS_EN_MENSAJE
        if resto > 0:
            listadas += f" y {resto} más"
        errores.append(
            f"El terreno '{nombre}' no existe en 'tipos_terreno' "
            f"(aparece en {len(celdas)} {_plural(len(celdas), 'celda', 'celdas')}: {listadas})"
        )
    if no_texto:
        listadas = ", ".join(str(c) for c in no_texto[:MAX_CELDAS_EN_MENSAJE])
        errores.append(
            f"'terreno' tiene {len(no_texto)} {_plural(len(no_texto), 'celda', 'celdas')} "
            f"cuyo valor no es un nombre de terreno (texto): {listadas}"
        )
    return errores
