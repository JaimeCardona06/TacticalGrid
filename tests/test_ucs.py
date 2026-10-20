"""Pruebas de UCS (costo uniforme) sobre el problema de navegación y sobre un grafo de juguete."""
import math
import random
import unittest

from src.game.navegacion import ProblemaNavegacion
from src.models.board import Board
from src.scenario.loader import cargar_escenario
from src.search.uninformed import bfs, ucs
from tests.base import RUTA_OFICIAL

CAMINO_UCS_OFICIAL = ((0, 1), (0, 0), (1, 0), (2, 0), (2, 1), (3, 1), (3, 2))
CAMINO_BFS_OFICIAL = ((0, 1), (0, 2), (1, 2), (2, 2), (3, 2))


class ProblemaGrafo:
    """Problema de juguete con costos explícitos por arista, para casos que el mapa no produce."""

    def __init__(self, aristas, inicio, objetivo):
        self.aristas, self.inicio, self.objetivo = aristas, inicio, objetivo

    def estado_inicial(self):
        return self.inicio

    def es_objetivo(self, estado):
        return estado == self.objetivo

    def extremos_transitables(self):
        return True

    def sucesores(self, estado):
        return list(self.aristas.get(estado, []))


class TestUCSEscenarioOficial(unittest.TestCase):
    """Cifras de referencia para A1 (0,1) -> (3,2) con las convenciones de decisiones.md."""

    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero
        self.problema = ProblemaNavegacion(self.tablero, (0, 1), (3, 2))
        self.r = ucs(self.problema)

    def test_camino_acciones_y_costo(self):
        self.assertTrue(self.r.exito)
        self.assertEqual(self.r.camino, CAMINO_UCS_OFICIAL)
        self.assertEqual(len(self.r.camino) - 1, 6)
        self.assertEqual(self.r.acciones, ("izquierda", "abajo", "abajo", "derecha", "abajo", "derecha"))
        self.assertEqual(self.r.costo, 7)  # celdas destino: 1 + 1 + 1 + 1 + 2 (pasto) + 1

    def test_metricas_de_referencia(self):
        self.assertEqual(self.r.estados_generados, 14)
        self.assertEqual(self.r.estados_expandidos, 12)
        self.assertEqual(self.r.maximo_frontera, 5)
        self.assertEqual(self.r.algoritmo, "UCS")

    def test_caso_2_ruta_corta_contra_ruta_economica(self):
        """Caso mínimo 2 del enunciado: BFS y UCS dan caminos distintos por los costos."""
        b = bfs(self.problema)
        self.assertEqual(b.camino, CAMINO_BFS_OFICIAL)
        self.assertNotEqual(b.camino, self.r.camino)
        self.assertLess(len(b.camino), len(self.r.camino))   # BFS: menos movimientos...
        self.assertGreater(b.costo, self.r.costo)             # ...pero más caro: 14 contra 7

    def test_prediccion_del_profesor_pantano_en_15(self):
        """UCS ya evitaba el pantano: no cambia nada; BFS sube de 14 a 22."""
        self.tablero.tipos_terreno["pantano"]["costo"] = 15
        u = ucs(self.problema)
        b = bfs(self.problema)
        self.assertEqual((u.camino, u.costo), (CAMINO_UCS_OFICIAL, 7))
        self.assertEqual((b.camino, b.costo), (CAMINO_BFS_OFICIAL, 22))

    def test_si_el_pantano_baja_a_1_ucs_lo_aprovecha(self):
        self.tablero.tipos_terreno["pantano"]["costo"] = 1
        self.tablero.tipos_terreno["bosque"]["costo"] = 1
        self.tablero.tipos_terreno["pasto"]["costo"] = 1
        r = ucs(self.problema)
        self.assertEqual(r.costo, 4)  # el camino directo de 4 movimientos ahora vale 4
        self.assertEqual(len(r.camino) - 1, 4)

    def test_el_camino_es_valido_y_el_costo_cuadra(self):
        camino = self.r.camino
        total = 0
        for (f1, c1), (f2, c2) in zip(camino, camino[1:]):
            self.assertEqual(abs(f1 - f2) + abs(c1 - c2), 1)
            self.assertTrue(self.tablero.es_transitable((f2, c2)))
            total += self.tablero.costo_entrar((f2, c2))
        self.assertEqual(total, self.r.costo)

    def test_es_reproducible(self):
        otra = ucs(self.problema)
        self.assertEqual((otra.camino, otra.costo, otra.estados_generados, otra.estados_expandidos,
                          otra.maximo_frontera),
                         (self.r.camino, self.r.costo, self.r.estados_generados,
                          self.r.estados_expandidos, self.r.maximo_frontera))


class TestUCSCasosLimite(unittest.TestCase):
    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero

    def test_inicio_igual_al_objetivo(self):
        r = ucs(ProblemaNavegacion(self.tablero, (0, 1), (0, 1)))
        self.assertTrue(r.exito)
        self.assertEqual((r.camino, r.acciones, r.costo), (((0, 1),), (), 0))
        self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (1, 1, 1))

    def test_objetivo_o_inicio_invalidos_terminan_sin_explorar(self):
        for inicio, objetivo in (((0, 1), (1, 1)), ((0, 1), (9, 9)), ((1, 1), (3, 2)), ((-1, 0), (3, 2))):
            with self.subTest(inicio=inicio, objetivo=objetivo):
                r = ucs(ProblemaNavegacion(self.tablero, inicio, objetivo))
                self.assertFalse(r.exito)
                self.assertEqual(r.camino, ())
                self.assertIsNone(r.costo)
                self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (0, 0, 0))

    def test_objetivo_encerrado_explora_todo_lo_alcanzable_y_falla(self):
        tipos = {"c": {"costo": 1, "transitable": True}, "m": {"transitable": False}}
        terreno = [["c", "c", "c", "c"],
                   ["c", "m", "m", "m"],
                   ["c", "m", "c", "m"],
                   ["c", "m", "m", "m"]]
        t = Board(4, 4, tipos, terreno, (0, 0), (0, 0))
        r = ucs(ProblemaNavegacion(t, (0, 0), (2, 2)))
        self.assertFalse(r.exito)
        self.assertEqual((r.estados_generados, r.estados_expandidos), (7, 7))

    def test_con_costos_iguales_coincide_con_bfs_en_costo(self):
        """Si todas las celdas cuestan lo mismo, el camino más barato es el de menos movimientos."""
        tipos = {"c": {"costo": 3, "transitable": True}, "m": {"transitable": False}}
        terreno = [["c", "c", "c", "c"], ["c", "m", "m", "c"], ["c", "c", "c", "c"]]
        t = Board(3, 4, tipos, terreno, (0, 0), (0, 0))
        problema = ProblemaNavegacion(t, (0, 0), (2, 3))
        u, b = ucs(problema), bfs(problema)
        self.assertEqual(len(u.camino), len(b.camino))
        self.assertEqual(u.costo, b.costo)

    def test_no_modifica_el_tablero(self):
        antes = [fila[:] for fila in self.tablero.terreno]
        ucs(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertEqual(self.tablero.terreno, antes)


class TestUCSEliminacionPerezosa(unittest.TestCase):
    """Un estado generado caro y luego mejorado: la entrada vieja se descarta sin contarla."""

    def setUp(self):
        aristas = {
            "A": [("a-X", "X", 9), ("a-B", "B", 1), ("a-G", "G", 20)],
            "B": [("b-X", "X", 3)],
            "X": [("x-G", "G", 10)],
        }
        self.r = ucs(ProblemaGrafo(aristas, "A", "G"))

    def test_encuentra_el_camino_mas_barato_actualizando_el_padre(self):
        self.assertTrue(self.r.exito)
        self.assertEqual(self.r.camino, ("A", "B", "X", "G"))  # X se alcanzó primero por A (9) y luego por B (4)
        self.assertEqual(self.r.acciones, ("a-B", "b-X", "x-G"))
        self.assertEqual(self.r.costo, 14)

    def test_metricas_con_entradas_viejas(self):
        # Generados: A, X(9), B, G(20), X(4) reinsertado, G(14) reinsertado = 6
        self.assertEqual(self.r.estados_generados, 6)
        # Expandidos: A, B, X, G = 4. La entrada vieja X(9) se descarta y NO cuenta
        self.assertEqual(self.r.estados_expandidos, 4)
        # La frontera incluye la entrada vieja X(9): nunca baja de 3 entradas
        self.assertEqual(self.r.maximo_frontera, 3)

    def test_gana_el_camino_barato_aunque_el_directo_tenga_menos_movimientos(self):
        aristas = {"A": [("directo", "G", 10), ("paso1", "B", 1)], "B": [("paso2", "C", 1)], "C": [("paso3", "G", 1)]}
        r = ucs(ProblemaGrafo(aristas, "A", "G"))
        self.assertEqual((r.camino, r.costo), (("A", "B", "C", "G"), 3))

    def test_desempate_por_orden_de_llegada(self):
        """Dos caminos con el mismo costo: gana el que se generó primero."""
        aristas = {"A": [("por-B", "B", 1), ("por-C", "C", 1)], "B": [("b-G", "G", 1)], "C": [("c-G", "G", 1)]}
        r = ucs(ProblemaGrafo(aristas, "A", "G"))
        self.assertEqual(r.camino, ("A", "B", "G"))


class TestUCSEsOptimo(unittest.TestCase):
    """UCS contra un cálculo independiente del costo mínimo (relajación de aristas)."""

    @staticmethod
    def costo_minimo(tablero, inicio, objetivo):
        mejor = {inicio: 0}
        cambio = True
        while cambio:
            cambio = False
            for estado, g in list(mejor.items()):
                for destino in tablero.vecinos(estado):
                    ng = g + tablero.costo_entrar(destino)
                    if ng < mejor.get(destino, math.inf):
                        mejor[destino] = ng
                        cambio = True
        return mejor.get(objetivo)

    def test_costo_igual_al_minimo_en_mapas_aleatorios(self):
        rng = random.Random(11)
        costos = [1, 2, 4, 7, 15]
        verificados = 0
        for _ in range(300):
            f, c = rng.randint(2, 10), rng.randint(2, 10)
            tipos = {f"t{k}": {"costo": k, "transitable": True} for k in costos}
            tipos["m"] = {"transitable": False}
            terreno = [[("m" if rng.random() < 0.2 else f"t{rng.choice(costos)}") for _ in range(c)] for _ in range(f)]
            tablero = Board(f, c, tipos, terreno, (0, 0), (0, 0))
            libres = [(i, j) for i in range(f) for j in range(c) if tablero.es_transitable((i, j))]
            if len(libres) < 2:
                continue
            inicio, objetivo = rng.choice(libres), rng.choice(libres)
            esperado = self.costo_minimo(tablero, inicio, objetivo)
            r = ucs(ProblemaNavegacion(tablero, inicio, objetivo))
            if esperado is None:
                self.assertFalse(r.exito)
            else:
                self.assertTrue(r.exito)
                self.assertEqual(r.costo, esperado)
                # Y el costo informado coincide con la suma de los pasos del camino devuelto
                self.assertEqual(sum(tablero.costo_entrar(p) for p in r.camino[1:]), r.costo)
                verificados += 1
        self.assertGreater(verificados, 100)

    def test_nunca_cuesta_mas_que_bfs(self):
        rng = random.Random(5)
        for _ in range(200):
            f, c = rng.randint(2, 10), rng.randint(2, 10)
            tipos = {"a": {"costo": 1, "transitable": True}, "b": {"costo": 9, "transitable": True},
                     "m": {"transitable": False}}
            terreno = [[rng.choice(["a", "a", "b", "m"]) for _ in range(c)] for _ in range(f)]
            tablero = Board(f, c, tipos, terreno, (0, 0), (0, 0))
            libres = [(i, j) for i in range(f) for j in range(c) if tablero.es_transitable((i, j))]
            if len(libres) < 2:
                continue
            problema = ProblemaNavegacion(tablero, rng.choice(libres), rng.choice(libres))
            u, b = ucs(problema), bfs(problema)
            self.assertEqual(u.exito, b.exito)
            if u.exito:
                self.assertLessEqual(u.costo, b.costo)
                self.assertGreaterEqual(len(u.camino), len(b.camino))  # BFS: nunca más movimientos que UCS


if __name__ == "__main__":
    unittest.main()
