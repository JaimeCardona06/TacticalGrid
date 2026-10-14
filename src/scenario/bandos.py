def normalizar_bando(valor):
    """Convierte el valor de un bando del JSON a "A" o "B"; None si no es válido.

    Purpose:            ser la ÚNICA definición de qué se acepta como bando, para
                        que el validador (que pregunta) y el constructor del
                        estado (que convierte) usen exactamente la misma regla.
                        Dentro del modelo solo existen "A" y "B".
    Preconditions:      ninguna; valor puede ser de cualquier tipo.
    Postconditions:     devuelve "A" si valor es el texto "A" o "a"; "B" si es
                        "B" o "b"; None en cualquier otro caso (otro texto,
                        texto con espacios como " A", número, booleano, null).
                        No modifica nada.
    Complexity:         O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: TODO(equipo)
    """
    if not isinstance(valor, str):
        return None
    if valor in ("A", "a"):
        return "A"
    if valor in ("B", "b"):
        return "B"
    return None
