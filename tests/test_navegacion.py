"""Pruebas del problema de navegación: estado inicial, sucesores, objetivo y costos."""
import unittest

from src.game.navegacion import ProblemaNavegacion
from src.models.board import Board
from src.scenario.loader import cargar_escenario
from tests.base import RUTA_OFICIAL


class TestProblemaNavegacion(unittest.TestCase):
    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero
        orden = Board.DIRECCIONES
        self.addCleanup(setattr, Board, "DIRECCIONES", orden)
        self.p = ProblemaNavegacion(self.tablero, (0, 1), (3, 2))  # el caso de la prueba oficial

    def test_estado_inicial_y_objetivo_son_tuplas(self):
        self.assertEqual(self.p.estado_inicial(), (0, 1))
        self.assertEqual(self.p.objetivo, (3, 2))
        self.assertIsInstance(self.p.estado_inicial(), tuple)

    def test_acepta_listas_y_las_convierte_en_tuplas(self):
        p = ProblemaNavegacion(self.tablero, [0, 1], [3, 2])
        self.assertEqual((p.inicio, p.objetivo), ((0, 1), (3, 2)))

    def test_es_objetivo(self):
        self.assertTrue(self.p.es_objetivo((3, 2)))
        self.assertFalse(self.p.es_objetivo((3, 3)))

    def test_inicio_igual_al_objetivo(self):
        p = ProblemaNavegacion(self.tablero, (0, 1), (0, 1))
        self.assertTrue(p.es_objetivo(p.estado_inicial()))

    def test_sucesores_traen_accion_estado_y_costo(self):
        # Desde (0,1): arriba no existe, derecha es pasto (2), abajo es muro, izquierda es camino (1)
        self.assertEqual(self.p.sucesores((0, 1)),
                         [("derecha", (0, 2), 2), ("izquierda", (0, 0), 1)])

    def test_sucesores_en_el_orden_arriba_derecha_abajo_izquierda(self):
        self.assertEqual([a for a, _, _ in self.p.sucesores((2, 1))],
                         ["derecha", "abajo", "izquierda"])  # arriba es el muro (1,1)
        self.assertEqual([a for a, _, _ in self.p.sucesores((2, 0))],
                         ["arriba", "derecha", "abajo"])

    def test_el_costo_es_el_de_la_celda_destino(self):
        # Desde (1,2) (bosque) hacia abajo está (2,2) (pantano): se cobra 7, no 4
        costos = {a: c for a, _, c in self.p.sucesores((1, 2))}
        self.assertEqual(costos["abajo"], 7)

    def test_sin_muros_ni_fuera_del_mapa(self):
        for f in range(4):
            for c in range(4):
                if self.tablero.es_transitable((f, c)):
                    for _, destino, costo in self.p.sucesores((f, c)):
                        self.assertTrue(self.tablero.es_transitable(destino))
                        self.assertGreater(costo, 0)

    def test_los_sucesores_son_una_lista_nueva(self):
        self.p.sucesores((0, 1)).clear()
        self.assertEqual(len(self.p.sucesores((0, 1))), 2)

    def test_cambiar_direcciones_cambia_el_orden_de_los_sucesores(self):
        Board.DIRECCIONES = ((0, -1), (1, 0), (0, 1), (-1, 0))
        self.assertEqual([a for a, _, _ in self.p.sucesores((0, 1))], ["izquierda", "derecha"])

    def test_cambiar_un_costo_del_catalogo_cambia_el_costo_del_paso(self):
        self.tablero.tipos_terreno["pantano"]["costo"] = 15
        costos = {a: c for a, _, c in self.p.sucesores((1, 2))}
        self.assertEqual(costos["abajo"], 15)

    def test_extremos_transitables(self):
        self.assertTrue(self.p.extremos_transitables())
        self.assertFalse(ProblemaNavegacion(self.tablero, (0, 1), (1, 1)).extremos_transitables())  # objetivo en muro
        self.assertFalse(ProblemaNavegacion(self.tablero, (1, 1), (3, 2)).extremos_transitables())  # inicio en muro
        self.assertFalse(ProblemaNavegacion(self.tablero, (0, 1), (9, 9)).extremos_transitables())  # objetivo fuera
        self.assertFalse(ProblemaNavegacion(self.tablero, (-1, 0), (3, 2)).extremos_transitables())  # inicio fuera

    def test_objetivo_en_la_casilla_de_otra_unidad_es_alcanzable(self):
        # En el ejemplo oficial el objetivo (3,2) es la casilla de B1: las unidades no bloquean
        self.assertTrue(self.p.extremos_transitables())


if __name__ == "__main__":
    unittest.main()
