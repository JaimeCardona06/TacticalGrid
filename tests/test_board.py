"""Pruebas del tablero (Board): límites, transitabilidad, costos y vecinos."""
import unittest

from src.models.board import Board
from src.scenario.loader import cargar_escenario
from tests.base import RUTA_OFICIAL


class TestBoardOficial(unittest.TestCase):
    def setUp(self):
        self.b = cargar_escenario(RUTA_OFICIAL).tablero
        orden = Board.DIRECCIONES
        self.addCleanup(setattr, Board, "DIRECCIONES", orden)

    def test_dentro_del_mapa(self):
        for pos in ((0, 0), (3, 3), (0, 3), (3, 0)):
            self.assertTrue(self.b.dentro_del_mapa(pos), pos)
        for pos in ((-1, 0), (0, -1), (4, 0), (0, 4), (9, 9)):
            self.assertFalse(self.b.dentro_del_mapa(pos), pos)

    def test_es_transitable(self):
        self.assertTrue(self.b.es_transitable((0, 0)))
        self.assertTrue(self.b.es_transitable((2, 2)))   # pantano
        self.assertFalse(self.b.es_transitable((1, 1)))  # muro
        self.assertFalse(self.b.es_transitable((4, 0)))  # fuera
        self.assertFalse(self.b.es_transitable((-1, 0)))  # fuera (negativo)

    def test_costo_de_entrar_sale_del_catalogo(self):
        esperado = {(0, 0): 1, (0, 2): 2, (1, 2): 4, (2, 2): 7}  # camino, pasto, bosque, pantano
        for pos, costo in esperado.items():
            self.assertEqual(self.b.costo_entrar(pos), costo, pos)

    def test_costo_de_celda_no_transitable_o_fuera_lanza_error(self):
        for pos in ((1, 1), (4, 0), (-1, -1)):
            with self.assertRaises(ValueError, msg=pos):
                self.b.costo_entrar(pos)

    def test_el_costo_cambia_si_cambia_el_catalogo(self):
        self.b.tipos_terreno["pantano"]["costo"] = 15
        self.assertEqual(self.b.costo_entrar((2, 2)), 15)

    def test_vecinos_en_orden_arriba_derecha_abajo_izquierda(self):
        self.assertEqual(self.b.vecinos((0, 1)), [(0, 2), (0, 0)])               # arriba no existe; abajo es muro
        self.assertEqual(self.b.vecinos((2, 1)), [(2, 2), (3, 1), (2, 0)])       # arriba es muro
        self.assertEqual(self.b.vecinos((3, 3)), [(2, 3), (3, 2)])               # esquina
        self.assertEqual(self.b.vecinos((2, 0)), [(1, 0), (2, 1), (3, 0)])       # borde izquierdo

    def test_vecinos_nunca_incluye_muros_ni_celdas_fuera(self):
        for f in range(4):
            for c in range(4):
                for v in self.b.vecinos((f, c)):
                    self.assertTrue(self.b.es_transitable(v))

    def test_cambiar_direcciones_cambia_el_orden_de_los_vecinos(self):
        antes = self.b.vecinos((3, 3))
        Board.DIRECCIONES = ((0, 1), (1, 0), (0, -1), (-1, 0))
        despues = self.b.vecinos((3, 3))
        self.assertEqual(antes, [(2, 3), (3, 2)])
        self.assertEqual(despues, [(3, 2), (2, 3)])
        self.assertCountEqual(antes, despues)  # mismos vecinos, otro orden


class TestBoardNoCuadrado(unittest.TestCase):
    def setUp(self):
        tipos = {"camino": {"costo": 1, "transitable": True},
                 "muro": {"transitable": False}}
        terreno = [["camino", "camino", "camino", "muro", "camino"],
                   ["camino", "muro", "camino", "camino", "camino"]]
        self.b = Board(2, 5, tipos, terreno, (0, 0), (1, 4))

    def test_usa_filas_y_columnas_por_separado(self):
        self.assertTrue(self.b.dentro_del_mapa((1, 4)))
        self.assertFalse(self.b.dentro_del_mapa((2, 0)))
        self.assertFalse(self.b.dentro_del_mapa((0, 5)))

    def test_vecinos(self):
        self.assertEqual(self.b.vecinos((1, 2)), [(0, 2), (1, 3)])


if __name__ == "__main__":
    unittest.main()
