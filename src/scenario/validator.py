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
