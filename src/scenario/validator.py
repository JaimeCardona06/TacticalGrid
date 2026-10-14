import math

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
    errores += _validar_costos_transitables(datos)
    errores += _validar_posiciones_en_mapa(datos)
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


def _validar_costos_transitables(datos):
    """Regla 3: los terrenos transitables tienen un costo positivo.

    Purpose:            garantizar que todo terreno por el que se puede pasar
                        tiene un costo numérico mayor que 0, porque UCS, A* y
                        el verificador suman esos costos. Los terrenos NO
                        transitables (muro) no se cobran nunca, así que su
                        'costo' (presente, ausente o con cualquier valor) no
                        se comprueba.
    Preconditions:      tipos_terreno existe (puede estar mal formado: se
                        reporta, no se asume).
    Postconditions:     devuelve una lista con un error por cada tipo de
                        terreno del catálogo que: no es un objeto; no tiene
                        'transitable' o no es true/false; o, siendo
                        transitable, no tiene 'costo' numérico finito mayor
                        que 0. No lanza excepciones por claves ausentes. No
                        modifica datos.
    Complexity:         O(t) en tiempo, con t = tipos de terreno del catálogo.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    tipos = datos["tipos_terreno"]
    if not isinstance(tipos, dict):
        return []  # ya lo reporta la regla 2

    errores = []
    for nombre, tipo in tipos.items():
        if not isinstance(tipo, dict):
            errores.append(f"El terreno '{nombre}' debe ser un objeto con 'transitable' y 'costo'")
            continue
        if "transitable" not in tipo:
            errores.append(f"Al terreno '{nombre}' le falta el campo 'transitable'")
            continue
        transitable = tipo["transitable"]
        if not isinstance(transitable, bool):
            errores.append(
                f"'transitable' del terreno '{nombre}' debe ser true o false "
                f"(recibido: {transitable!r})"
            )
            continue
        if not transitable:
            continue  # no se cobra nunca: su costo no importa
        if "costo" not in tipo:
            errores.append(f"El terreno transitable '{nombre}' no tiene 'costo'")
            continue
        costo = tipo["costo"]
        es_numero = isinstance(costo, (int, float)) and not isinstance(costo, bool)
        if not es_numero or not math.isfinite(costo) or costo <= 0:
            errores.append(
                f"El terreno transitable '{nombre}' debe tener un costo "
                f"positivo (recibido: {costo!r})"
            )
    return errores


def _validar_posicion(etiqueta, pos, filas, columnas):
    """Comprueba una posición {"fila": f, "columna": c} contra el tamaño del mapa.

    Purpose:            reutilizar la misma comprobación para bases, recurso y
                        unidades, con un mensaje que nombra el elemento.
    Preconditions:      filas y columnas son enteros positivos (regla 1).
    Postconditions:     devuelve una lista con los errores de esa posición:
                        no es un objeto con 'fila' y 'columna'; alguna no es un
                        entero; o cae fuera de [0, filas) x [0, columnas).
                        Lista vacía si es correcta. No modifica pos.
    Complexity:         O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    if not isinstance(pos, dict) or "fila" not in pos or "columna" not in pos:
        return [f"{etiqueta} debe ser un objeto con 'fila' y 'columna'"]

    errores = []
    for campo in ("fila", "columna"):
        if not _es_entero(pos[campo]):
            errores.append(
                f"{etiqueta} tiene '{campo}' inválida: debe ser un entero "
                f"(recibido: {pos[campo]!r})"
            )
    if errores:
        return errores

    fila, columna = pos["fila"], pos["columna"]
    if not (0 <= fila < filas and 0 <= columna < columnas):
        return [
            f"{etiqueta} está fuera del mapa: ({fila}, {columna}) "
            f"(el mapa tiene {filas} filas y {columnas} columnas)"
        ]
    return []


def _validar_posiciones_en_mapa(datos):
    """Regla 4: bases, recurso y unidades se encuentran dentro del mapa.

    Purpose:            asegurar que toda posición del escenario existe en el
                        tablero, para que ningún algoritmo indexe fuera de la
                        matriz terreno. Este validador hace su propia
                        comprobación de límites porque Board aún no existe
                        (se construye solo con datos ya validados).
    Preconditions:      los campos obligatorios existen y mapa.filas y
                        mapa.columnas son enteros positivos (regla 1 sin
                        errores en esos campos).
    Postconditions:     devuelve una lista con un error por cada posición
                        incorrecta, nombrando el elemento (base A, base B,
                        recurso o unidad por su id, o por su índice si no
                        tiene id). Una posición mal formada se reporta, no
                        hace fallar la función. No modifica datos.
    Complexity:         O(u) en tiempo, con u = cantidad de unidades.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    filas = datos["mapa"]["filas"]
    columnas = datos["mapa"]["columnas"]
    if not (_es_entero(filas) and _es_entero(columnas)) or filas <= 0 or columnas <= 0:
        return []  # dimensiones inválidas: ya reportadas por la regla 1

    errores = []
    bases = datos["bases"]
    for bando in ("A", "B"):
        if isinstance(bases, dict) and bando in bases:
            errores += _validar_posicion(f"La base {bando}", bases[bando], filas, columnas)
    errores += _validar_posicion("El recurso", datos["recurso"], filas, columnas)

    unidades = datos["unidades"]
    if not isinstance(unidades, list):
        return errores + ["'unidades' debe ser una lista"]
    for i, unidad in enumerate(unidades):
        if not isinstance(unidad, dict):
            errores.append(f"La unidad en la posición {i} de 'unidades' debe ser un objeto")
            continue
        id_unidad = unidad.get("id")
        if isinstance(id_unidad, str):
            etiqueta = f"La unidad '{id_unidad}'"
        else:
            etiqueta = f"La unidad en la posición {i} de 'unidades'"
        errores += _validar_posicion(etiqueta, unidad, filas, columnas)
    return errores
