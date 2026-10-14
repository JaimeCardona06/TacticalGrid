"""Pruebas de BFS sobre el problema de navegación."""
import unittest

from src.game.navegacion import ProblemaNavegacion
from src.models.board import Board
from src.scenario.loader import cargar_escenario
from src.search.uninformed import bfs
from tests.base import RUTA_OFICIAL

CAMINO_BFS_OFICIAL = ((0, 1), (0, 2), (1, 2), (2, 2), (3, 2))


def tablero_con(terreno, tipos=None, base_a=(0, 0), base_b=(0, 0)):
    tipos = tipos or {"c": {"costo": 1, "transitable": True}, "m": {"transitable": False}}
    return Board(len(terreno), len(terreno[0]), tipos, terreno, base_a, base_b)


class TestBFSEscenarioOficial(unittest.TestCase):
    """Cifras de referencia para A1 (0,1) -> (3,2) con las convenciones de decisiones.md."""

    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero
        self.r = bfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))

    def test_encuentra_el_camino_de_menos_movimientos(self):
        self.assertTrue(self.r.exito)
        self.assertEqual(self.r.camino, CAMINO_BFS_OFICIAL)
        self.assertEqual(len(self.r.camino) - 1, 4)
        self.assertEqual(self.r.acciones, ("derecha", "abajo", "abajo", "abajo"))

    def test_el_costo_es_la_suma_de_las_celdas_destino(self):
        # pasto 2 + bosque 4 + pantano 7 + camino 1 = 14: BFS ignora los costos
        self.assertEqual(self.r.costo, 14)

    def test_metricas_de_referencia(self):
        self.assertEqual(self.r.estados_generados, 14)
        self.assertEqual(self.r.estados_expandidos, 11)
        self.assertEqual(self.r.maximo_frontera, 4)

    def test_nombre_y_tiempo(self):
        self.assertEqual(self.r.algoritmo, "BFS")
        self.assertIsInstance(self.r.tiempo_segundos, float)
        self.assertGreaterEqual(self.r.tiempo_segundos, 0)

    def test_formato_del_enunciado(self):
        d = self.r.a_diccionario()
        for clave in ("algoritmo", "exito", "camino", "costo", "estados_generados",
                      "estados_expandidos", "maximo_frontera"):
            self.assertIn(clave, d)
        self.assertEqual(d["camino"], [[0, 1], [0, 2], [1, 2], [2, 2], [3, 2]])

    def test_pantano_en_15_cambia_el_costo_pero_no_el_camino(self):
        self.tablero.tipos_terreno["pantano"]["costo"] = 15
        r = bfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertEqual(r.camino, CAMINO_BFS_OFICIAL)
        self.assertEqual(r.costo, 22)

    def test_es_reproducible(self):
        otra = bfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertEqual((otra.camino, otra.costo, otra.estados_generados, otra.estados_expandidos,
                          otra.maximo_frontera),
                         (self.r.camino, self.r.costo, self.r.estados_generados,
                          self.r.estados_expandidos, self.r.maximo_frontera))

    def test_el_camino_es_valido_paso_a_paso(self):
        """El camino empieza y termina donde debe, avanza de a una celda y suma bien."""
        camino = self.r.camino
        self.assertEqual((camino[0], camino[-1]), ((0, 1), (3, 2)))
        total = 0
        for (f1, c1), (f2, c2) in zip(camino, camino[1:]):
            self.assertEqual(abs(f1 - f2) + abs(c1 - c2), 1)
            self.assertTrue(self.tablero.es_transitable((f2, c2)))
            total += self.tablero.costo_entrar((f2, c2))
        self.assertEqual(total, self.r.costo)


class TestBFSCasosLimite(unittest.TestCase):
    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero

    def test_inicio_igual_al_objetivo(self):
        r = bfs(ProblemaNavegacion(self.tablero, (0, 1), (0, 1)))
        self.assertTrue(r.exito)
        self.assertEqual(r.camino, ((0, 1),))
        self.assertEqual((len(r.acciones), r.costo), (0, 0))
        self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (1, 1, 1))

    def test_objetivo_en_un_muro_o_fuera_del_mapa_termina_sin_explorar(self):
        for objetivo in ((1, 1), (9, 9), (-1, 0)):
            with self.subTest(objetivo=objetivo):
                r = bfs(ProblemaNavegacion(self.tablero, (0, 1), objetivo))
                self.assertFalse(r.exito)
                self.assertEqual(r.camino, ())
                self.assertIsNone(r.costo)
                self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (0, 0, 0))

    def test_inicio_en_un_muro(self):
        r = bfs(ProblemaNavegacion(self.tablero, (1, 1), (3, 2)))
        self.assertFalse(r.exito)
        self.assertEqual(r.estados_generados, 0)

    def test_objetivo_en_la_casilla_de_otra_unidad(self):
        # En el ejemplo oficial (3,2) es la casilla de B1: las unidades no bloquean
        self.assertTrue(bfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2))).exito)

    def test_objetivo_encerrado_explora_todo_lo_alcanzable_y_falla(self):
        terreno = [["c", "c", "c", "c"],
                   ["c", "m", "m", "m"],
                   ["c", "m", "c", "m"],   # (2,2) está rodeada de muros
                   ["c", "m", "m", "m"]]
        r = bfs(ProblemaNavegacion(tablero_con(terreno), (0, 0), (2, 2)))
        self.assertFalse(r.exito)
        self.assertEqual(r.camino, ())
        self.assertIsNone(r.costo)
        # Alcanzables desde (0,0): fila 0 (4 celdas) y columna 0 (4 celdas), una compartida = 7
        self.assertEqual(r.estados_generados, 7)
        self.assertEqual(r.estados_expandidos, 7)

    def test_mapa_no_cuadrado(self):
        terreno = [["c"] * 6,
                   ["c", "m", "m", "m", "m", "c"]]
        r = bfs(ProblemaNavegacion(tablero_con(terreno), (1, 0), (1, 5)))
        self.assertTrue(r.exito)
        self.assertEqual(len(r.camino) - 1, 7)  # sube, cruza 5 columnas, baja

    def test_gana_el_menor_numero_de_movimientos_aunque_sea_mas_caro(self):
        """BFS ignora los costos: elige el camino corto y caro sobre el largo y barato."""
        tipos = {"c": {"costo": 1, "transitable": True}, "x": {"costo": 50, "transitable": True},
                 "m": {"transitable": False}}
        terreno = [["c", "x", "c"],      # directo por (0,1): 2 movimientos, costo 51
                   ["c", "c", "c"]]      # rodeo por abajo: 4 movimientos, costo 4
        t = tablero_con(terreno, tipos)
        r = bfs(ProblemaNavegacion(t, (0, 0), (0, 2)))
        self.assertEqual(len(r.camino) - 1, 2)
        self.assertEqual(r.costo, 51)

    def test_no_modifica_el_tablero(self):
        antes = [fila[:] for fila in self.tablero.terreno]
        bfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertEqual(self.tablero.terreno, antes)


if __name__ == "__main__":
    unittest.main()
