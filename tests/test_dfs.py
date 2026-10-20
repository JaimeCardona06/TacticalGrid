"""Pruebas de DFS sobre el problema de navegación."""
import unittest

from src.game.navegacion import ProblemaNavegacion
from src.models.board import Board
from src.scenario.loader import cargar_escenario
from src.search.uninformed import bfs, dfs
from tests.base import RUTA_OFICIAL

CAMINO_DFS_OFICIAL = ((0, 1), (0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2))
CAMINO_BFS_OFICIAL = ((0, 1), (0, 2), (1, 2), (2, 2), (3, 2))


def tablero_con(terreno):
    tipos = {"c": {"costo": 1, "transitable": True}, "m": {"transitable": False}}
    return Board(len(terreno), len(terreno[0]), tipos, terreno, (0, 0), (0, 0))


class TestDFSEscenarioOficial(unittest.TestCase):
    """Cifras de referencia para A1 (0,1) -> (3,2) con las convenciones de decisiones.md."""

    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero
        orden = Board.DIRECCIONES
        self.addCleanup(setattr, Board, "DIRECCIONES", orden)
        self.r = dfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))

    def test_camino_acciones_y_costo(self):
        self.assertTrue(self.r.exito)
        self.assertEqual(self.r.camino, CAMINO_DFS_OFICIAL)
        self.assertEqual(len(self.r.camino) - 1, 6)
        self.assertEqual(self.r.acciones, ("izquierda", "abajo", "abajo", "abajo", "derecha", "derecha"))
        self.assertEqual(self.r.costo, 8)  # camino 1+1+1, pasto 2+2, camino 1

    def test_metricas_de_referencia(self):
        self.assertEqual(self.r.estados_generados, 9)
        self.assertEqual(self.r.estados_expandidos, 7)
        self.assertEqual(self.r.maximo_frontera, 3)
        self.assertEqual(self.r.algoritmo, "DFS")

    def test_caso_1_resuelven_los_dos_pero_recorren_distinto(self):
        """Caso mínimo 1 del enunciado: BFS vs DFS sobre el mismo modelo."""
        problema = ProblemaNavegacion(self.tablero, (0, 1), (3, 2))
        b = bfs(problema)
        self.assertTrue(b.exito and self.r.exito)
        self.assertNotEqual(b.camino, self.r.camino)
        self.assertEqual(b.camino, CAMINO_BFS_OFICIAL)
        self.assertNotEqual((b.estados_generados, b.estados_expandidos),
                            (self.r.estados_generados, self.r.estados_expandidos))

    def test_no_garantiza_el_camino_mas_corto(self):
        self.assertGreater(len(self.r.camino), len(CAMINO_BFS_OFICIAL))

    def test_pantano_en_15_no_cambia_nada_porque_el_camino_no_lo_pisa(self):
        self.tablero.tipos_terreno["pantano"]["costo"] = 15
        r = dfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertEqual((r.camino, r.costo), (CAMINO_DFS_OFICIAL, 8))

    def test_el_orden_de_direcciones_cambia_el_camino(self):
        """Primero explora el ÚLTIMO de DIRECCIONES; invertirlas cambia la rama elegida."""
        Board.DIRECCIONES = ((0, -1), (1, 0), (0, 1), (-1, 0))
        r = dfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertTrue(r.exito)
        self.assertEqual(r.camino, ((0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3), (3, 2)))
        self.assertNotEqual(r.camino, CAMINO_DFS_OFICIAL)

    def test_es_reproducible(self):
        otra = dfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertEqual((otra.camino, otra.costo, otra.estados_generados, otra.estados_expandidos,
                          otra.maximo_frontera),
                         (self.r.camino, self.r.costo, self.r.estados_generados,
                          self.r.estados_expandidos, self.r.maximo_frontera))

    def test_el_camino_es_valido_paso_a_paso(self):
        camino = self.r.camino
        self.assertEqual((camino[0], camino[-1]), ((0, 1), (3, 2)))
        total = 0
        for (f1, c1), (f2, c2) in zip(camino, camino[1:]):
            self.assertEqual(abs(f1 - f2) + abs(c1 - c2), 1)
            self.assertTrue(self.tablero.es_transitable((f2, c2)))
            total += self.tablero.costo_entrar((f2, c2))
        self.assertEqual(total, self.r.costo)
        self.assertEqual(len(set(camino)), len(camino))  # no repite celdas


class TestDFSCasosLimite(unittest.TestCase):
    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero

    def test_inicio_igual_al_objetivo(self):
        r = dfs(ProblemaNavegacion(self.tablero, (0, 1), (0, 1)))
        self.assertTrue(r.exito)
        self.assertEqual((r.camino, r.acciones, r.costo), (((0, 1),), (), 0))
        self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (1, 1, 1))

    def test_objetivo_o_inicio_invalidos_terminan_sin_explorar(self):
        for inicio, objetivo in (((0, 1), (1, 1)), ((0, 1), (9, 9)), ((1, 1), (3, 2)), ((-1, 0), (3, 2))):
            with self.subTest(inicio=inicio, objetivo=objetivo):
                r = dfs(ProblemaNavegacion(self.tablero, inicio, objetivo))
                self.assertFalse(r.exito)
                self.assertEqual(r.camino, ())
                self.assertIsNone(r.costo)
                self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (0, 0, 0))

    def test_objetivo_encerrado_explora_todo_lo_alcanzable_y_falla(self):
        terreno = [["c", "c", "c", "c"],
                   ["c", "m", "m", "m"],
                   ["c", "m", "c", "m"],
                   ["c", "m", "m", "m"]]
        r = dfs(ProblemaNavegacion(tablero_con(terreno), (0, 0), (2, 2)))
        self.assertFalse(r.exito)
        self.assertEqual((r.estados_generados, r.estados_expandidos), (7, 7))

    def test_mismos_resultados_de_exito_que_bfs_en_mapas_pequenos(self):
        """Si hay ruta, ambos la encuentran; si no, ambos fallan."""
        terreno = [["c", "m", "c"],
                   ["c", "m", "c"],
                   ["c", "c", "c"]]
        t = tablero_con(terreno)
        for ini, obj in (((0, 0), (0, 2)), ((0, 0), (2, 2)), ((1, 0), (1, 2))):
            with self.subTest(ini=ini, obj=obj):
                self.assertEqual(bfs(ProblemaNavegacion(t, ini, obj)).exito,
                                 dfs(ProblemaNavegacion(t, ini, obj)).exito)

    def test_mapa_grande_no_depende_del_limite_de_recursion(self):
        n = 120  # 14 400 celdas: una versión recursiva fallaría con RecursionError
        t = tablero_con([["c"] * n for _ in range(n)])
        r = dfs(ProblemaNavegacion(t, (0, 0), (n - 1, n - 1)))
        self.assertTrue(r.exito)
        self.assertEqual(r.camino[0], (0, 0))
        self.assertEqual(r.camino[-1], (n - 1, n - 1))

    def test_no_modifica_el_tablero(self):
        antes = [fila[:] for fila in self.tablero.terreno]
        dfs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertEqual(self.tablero.terreno, antes)


if __name__ == "__main__":
    unittest.main()
