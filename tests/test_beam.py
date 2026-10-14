"""Pruebas de Beam Search (búsqueda en haz) sobre el problema de navegación."""
import copy
import random
import unittest

from src.game.navegacion import ProblemaNavegacion
from src.models.board import Board
from src.scenario.loader import cargar_escenario
from src.search.informed import beam_search
from src.search.uninformed import bfs, ucs
from tests.base import RUTA_OFICIAL

CAMINO_K1 = ((0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3), (3, 2))
CAMINO_K2 = ((0, 1), (0, 0), (1, 0), (2, 0), (2, 1), (3, 1), (3, 2))   # el mismo de UCS
CAMINO_BFS = ((0, 1), (0, 2), (1, 2), (2, 2), (3, 2))

TIPOS_UNO = {"n": {"costo": 1, "transitable": True}, "m": {"transitable": False}}
TIPOS_VARIOS = {"a": {"costo": 1, "transitable": True}, "b": {"costo": 3, "transitable": True},
                "c": {"costo": 7, "transitable": True}, "m": {"transitable": False}}


def tablero_con(terreno, tipos=None):
    """Tablero nuevo con copias de los datos (una prueba no contamina a las demás)."""
    tipos = copy.deepcopy(tipos or TIPOS_UNO)
    return Board(len(terreno), len(terreno[0]), tipos, copy.deepcopy(terreno), (0, 0), (0, 0))


def mapa_aleatorio(rng):
    f, c = rng.randint(2, 9), rng.randint(2, 9)
    terreno = [[rng.choice(["a", "a", "b", "c", "m", "m"]) for _ in range(c)] for _ in range(f)]
    tablero = tablero_con(terreno, TIPOS_VARIOS)
    libres = [(i, j) for i in range(f) for j in range(c) if tablero.es_transitable((i, j))]
    return tablero, libres


class TestBeamEscenarioOficial(unittest.TestCase):
    """Cifras de referencia para A1 (0,1) -> (3,2): k = 1, 2, 4, 8 (orden g + h, ver decisiones.md)."""

    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero
        self.problema = ProblemaNavegacion(self.tablero, (0, 1), (3, 2))

    def resumen(self, r):
        return (r.costo, r.estados_generados, r.estados_expandidos, r.maximo_frontera)

    def test_k1_es_avance_codicioso_y_paga_10(self):
        r = beam_search(self.problema, 1)
        self.assertTrue(r.exito)
        self.assertEqual(r.camino, CAMINO_K1)
        self.assertEqual(self.resumen(r), (10, 11, 7, 1))

    def test_k2_conserva_el_buen_camino_y_llega_al_costo_de_ucs(self):
        r = beam_search(self.problema, 2)
        self.assertEqual(r.camino, CAMINO_K2)
        self.assertEqual(self.resumen(r), (7, 19, 12, 2))
        self.assertEqual(r.costo, ucs(self.problema).costo)

    def test_k4_y_k8_se_parecen_a_bfs_y_pagan_14(self):
        for k in (4, 8):
            with self.subTest(k=k):
                r = beam_search(self.problema, k)
                self.assertEqual(r.camino, CAMINO_BFS)
                self.assertEqual(self.resumen(r), (14, 19, 13, 4))

    def test_caso_5_cambiar_k_cambia_la_exploracion_y_la_solucion(self):
        r = {k: beam_search(self.problema, k) for k in (1, 2, 4, 8)}
        self.assertEqual(len({r[k].camino for k in r}), 3)                    # tres caminos distintos
        exploracion = {k: (r[k].estados_generados, r[k].estados_expandidos, r[k].maximo_frontera) for k in r}
        self.assertEqual(exploracion, {1: (11, 7, 1), 2: (19, 12, 2), 4: (19, 13, 4), 8: (19, 13, 4)})
        self.assertEqual(len(set(exploracion.values())), 3)                   # k = 4 y k = 8 ya coinciden
        self.assertEqual([r[k].costo for k in (1, 2, 4, 8)], [10, 7, 14, 14])

    def test_un_haz_mas_ancho_no_siempre_es_mejor(self):
        """k=4 paga más que k=2: por niveles, un haz ancho llega primero por el camino de menos pasos."""
        self.assertGreater(beam_search(self.problema, 4).costo, beam_search(self.problema, 2).costo)

    def test_el_haz_nunca_supera_k(self):
        for k in (1, 2, 4, 8):
            r = beam_search(self.problema, k)
            self.assertLessEqual(r.maximo_frontera, k)
            self.assertLessEqual(r.maximo_candidatos, 4 * k)

    def test_resultado_con_nombre_k_y_heuristica(self):
        r = beam_search(self.problema, 2)
        self.assertEqual((r.algoritmo, r.k, r.heuristica), ("BEAM", 2, "manhattan"))
        d = r.a_diccionario()
        self.assertEqual((d["k"], d["heuristica"]), (2, "manhattan"))
        self.assertIn("maximo_candidatos", d)

    def test_el_camino_es_valido_y_el_costo_cuadra(self):
        for k in (1, 2, 4):
            r = beam_search(self.problema, k)
            total = 0
            for (f1, c1), (f2, c2) in zip(r.camino, r.camino[1:]):
                self.assertEqual(abs(f1 - f2) + abs(c1 - c2), 1)
                total += self.tablero.costo_entrar((f2, c2))
            self.assertEqual(total, r.costo)
            self.assertEqual(len(r.acciones), len(r.camino) - 1)

    def test_es_reproducible(self):
        a, b = beam_search(self.problema, 2), beam_search(self.problema, 2)
        self.assertEqual((a.camino, a.estados_generados, a.estados_expandidos, a.maximo_frontera),
                         (b.camino, b.estados_generados, b.estados_expandidos, b.maximo_frontera))

    def test_acepta_la_segunda_heuristica(self):
        r = beam_search(self.problema, 2, "distancia_bfs")
        self.assertTrue(r.exito)
        self.assertEqual(r.heuristica, "distancia_bfs")

    def test_pantano_en_15_k4_ya_no_pierde_tanto_como_el_costo_de_bfs(self):
        """Por niveles, un haz ancho sigue el camino de menos pasos, aunque ahora cueste 22."""
        self.tablero.tipos_terreno["pantano"]["costo"] = 15
        self.assertEqual(beam_search(self.problema, 4).costo, 22)
        self.assertEqual(beam_search(self.problema, 2).costo, 7)


class TestBeamCuandoFalla(unittest.TestCase):
    """Beam no es completo: puede fallar aunque exista solución."""

    def setUp(self):
        self.tablero = tablero_con([["n", "n", "n"],
                                    ["m", "n", "m"],
                                    ["n", "n", "n"]])
        self.problema = ProblemaNavegacion(self.tablero, (0, 0), (2, 2))

    def test_k1_falla_y_k2_lo_resuelve(self):
        self.assertEqual(ucs(self.problema).costo, 4)       # sí existe solución
        r1, r2 = beam_search(self.problema, 1), beam_search(self.problema, 2)
        self.assertFalse(r1.exito)
        self.assertEqual((r1.camino, r1.acciones), ((), ()))
        self.assertIsNone(r1.costo)
        self.assertGreater(r1.estados_expandidos, 0)        # exploró antes de rendirse
        self.assertTrue(r2.exito)
        self.assertEqual(r2.costo, 4)


class TestBeamCasosLimite(unittest.TestCase):
    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero

    def test_k_invalido_lanza_error(self):
        problema = ProblemaNavegacion(self.tablero, (0, 1), (3, 2))
        for k in (0, -1, 2.5, "2", None, True):
            with self.subTest(k=k):
                with self.assertRaises(ValueError):
                    beam_search(problema, k)

    def test_inicio_igual_al_objetivo(self):
        r = beam_search(ProblemaNavegacion(self.tablero, (0, 1), (0, 1)), 1)
        self.assertTrue(r.exito)
        self.assertEqual((r.camino, r.acciones, r.costo), (((0, 1),), (), 0))
        self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (1, 1, 1))

    def test_objetivo_o_inicio_invalidos_terminan_sin_explorar(self):
        for inicio, objetivo in (((0, 1), (1, 1)), ((0, 1), (9, 9)), ((1, 1), (3, 2)), ((-1, 0), (3, 2))):
            with self.subTest(inicio=inicio, objetivo=objetivo):
                r = beam_search(ProblemaNavegacion(self.tablero, inicio, objetivo), 2)
                self.assertFalse(r.exito)
                self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (0, 0, 0))
                self.assertEqual(r.k, 2)

    def test_objetivo_encerrado_termina_sin_exito(self):
        t = tablero_con([["n", "n", "n", "n"],
                         ["n", "m", "m", "m"],
                         ["n", "m", "n", "m"],
                         ["n", "m", "m", "m"]])
        for k in (1, 2, 8):
            with self.subTest(k=k):
                r = beam_search(ProblemaNavegacion(t, (0, 0), (2, 2)), k)
                self.assertFalse(r.exito)

    def test_no_modifica_el_tablero(self):
        antes = [fila[:] for fila in self.tablero.terreno]
        beam_search(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)), 2)
        self.assertEqual(self.tablero.terreno, antes)


class TestBeamPropiedades(unittest.TestCase):
    """Propiedades sobre mapas aleatorios con costos distintos."""

    def casos(self, semilla, mapas):
        rng = random.Random(semilla)
        for _ in range(mapas):
            tablero, libres = mapa_aleatorio(rng)
            if len(libres) >= 2:
                yield tablero, ProblemaNavegacion(tablero, rng.choice(libres), rng.choice(libres))

    def test_siempre_termina_y_si_hay_exito_el_camino_es_valido_y_no_baja_del_optimo(self):
        verificados = 0
        for tablero, problema in self.casos(12, 250):
            optimo = ucs(problema)
            for k in (1, 2, 4):
                r = beam_search(problema, k)       # si hubiera un ciclo infinito, esta línea no regresaría
                if r.exito:
                    self.assertTrue(optimo.exito)
                    self.assertGreaterEqual(r.costo, optimo.costo)    # nunca mejor que el óptimo
                    self.assertEqual(sum(tablero.costo_entrar(p) for p in r.camino[1:]), r.costo)
                    self.assertEqual((r.camino[0], r.camino[-1]), (problema.inicio, problema.objetivo))
                    self.assertEqual(len(set(r.camino)), len(r.camino))   # no repite celdas
                    verificados += 1
                else:
                    self.assertEqual(r.camino, ())
        self.assertGreater(verificados, 200)

    def test_el_haz_y_los_candidatos_respetan_sus_cotas(self):
        for _, problema in self.casos(13, 150):
            for k in (1, 2, 4, 8):
                r = beam_search(problema, k)
                self.assertLessEqual(r.maximo_frontera, k)
                self.assertLessEqual(r.maximo_candidatos, 4 * k)

    def test_con_un_haz_enorme_encuentra_solucion_siempre_que_exista(self):
        for _, problema in self.casos(14, 200):
            self.assertEqual(beam_search(problema, 10_000).exito, ucs(problema).exito)

    def test_con_un_haz_enorme_encuentra_el_camino_de_menos_pasos_como_bfs(self):
        """Por niveles, un haz sin límite se comporta como BFS (menos movimientos, no menor costo)."""
        for _, problema in self.casos(15, 200):
            b, r = bfs(problema), beam_search(problema, 10_000)
            self.assertEqual(r.exito, b.exito)
            if b.exito:
                self.assertEqual(len(r.camino), len(b.camino))


if __name__ == "__main__":
    unittest.main()
