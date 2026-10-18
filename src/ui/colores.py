"""Paleta de colores de la GUI: color por costo de terreno, no por nombre.

Mantiene el tablero agnóstico a los nombres de terreno del escenario (p. ej.
"arena"/"lava"/"roca" en config/mapa_agnostico.json): cada celda transitable se
colorea interpolando su costo entre COLOR_VERDE (costo mínimo del catálogo) y
COLOR_MARRON (costo máximo), sin mirar el nombre del terreno.
"""

COLOR_VERDE = "#2ecc71"
COLOR_MARRON = "#8b5a2b"
COLOR_OBSTACULO = "#2b2b2b"
COLOR_BANDO = {"A": "#1f77b4", "B": "#d62728"}
COLOR_RECURSO = "#f1c40f"
COLOR_CAMINO = "#27ae60"
COLOR_RESALTADO = "#9b59b6"

_VERDE_RGB = (46, 204, 113)
_MARRON_RGB = (139, 90, 43)


def color_por_costo(costo, costo_min, costo_max):
    """Color hex entre COLOR_VERDE (costo_min) y COLOR_MARRON (costo_max).

    Purpose:            dar el color de una celda transitable del tablero según
                        su costo de entrada, sin depender del nombre del
                        terreno, para que escenarios con terrenos propios se
                        pinten sin cambiar código.
    Preconditions:      costo, costo_min y costo_max son números; costo_min
                        <= costo_max (o iguales).
    Postconditions:     si costo_min == costo_max, devuelve COLOR_VERDE. Si no,
                        devuelve un color "#rrggbb" en minúsculas, interpolado
                        linealmente según (costo - costo_min) / (costo_max -
                        costo_min), acotado a [0, 1]. No modifica nada.
    Complexity:         O(1) en tiempo y espacio.
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_colores.py.
    """
    if costo_min == costo_max:
        return COLOR_VERDE
    fraccion = (costo - costo_min) / (costo_max - costo_min)
    fraccion = max(0.0, min(1.0, fraccion))
    r = round(_VERDE_RGB[0] + (_MARRON_RGB[0] - _VERDE_RGB[0]) * fraccion)
    g = round(_VERDE_RGB[1] + (_MARRON_RGB[1] - _VERDE_RGB[1]) * fraccion)
    b = round(_VERDE_RGB[2] + (_MARRON_RGB[2] - _VERDE_RGB[2]) * fraccion)
    return f"#{r:02x}{g:02x}{b:02x}"
