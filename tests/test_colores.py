import unittest

from src.ui.colores import color_por_costo, COLOR_VERDE, COLOR_MARRON


class TestColorPorCosto(unittest.TestCase):
    def test_extremo_minimo_da_verde(self):
        self.assertEqual(color_por_costo(1, 1, 9), COLOR_VERDE)

    def test_extremo_maximo_da_marron(self):
        self.assertEqual(color_por_costo(9, 1, 9), COLOR_MARRON)

    def test_costo_min_igual_max_no_rompe(self):
        self.assertEqual(color_por_costo(5, 3, 3), COLOR_VERDE)

    def test_intermedio_es_un_hex_valido_distinto_de_los_extremos(self):
        color = color_por_costo(5, 1, 9)
        self.assertRegex(color, r"^#[0-9a-f]{6}$")
        self.assertNotIn(color, (COLOR_VERDE, COLOR_MARRON))
