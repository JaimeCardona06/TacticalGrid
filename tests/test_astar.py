"""Pruebas de A* y de la heurística Manhattan (escalada y sin escalar)."""
import copy
import math
import random
import unittest

from src.game.navegacion import ProblemaNavegacion
from src.models.board import Board
from src.scenario.loader import cargar_escenario
from src.search.heuristics import (HEURISTICAS, crear_distancia_bfs, crear_manhattan,
                                   crear_manhattan_pasos, obtener_fabrica)
from src.search.informed import a_estrella
from src.search.uninformed import ucs
from tests.base import RUTA_OFICIAL

CAMINO_OFICIAL = ((0, 1), (0, 0), (1, 0), (2, 0), (2, 1), (3, 1), (3, 2))

TIPOS_MEDIO = {"r": {"costo": 0.5, "transitable": True}, "n": {"costo": 1, "transitable": True},
               "c": {"costo": 4, "transitable": True}, "m": {"transitable": False}}


def tablero_con(terreno, tipos=None):
    """Tablero nuevo con COPIAS de los datos: una prueba que cambie costos no contamina a las demás."""
    tipos = copy.deepcopy(tipos or TIPOS_MEDIO)
    return Board(len(terreno), len(terreno[0]), tipos, copy.deepcopy(terreno), (0, 0), (0, 0))


def mapa_aleatorio(rng, tipos, nombres):
    f, c = rng.randint(2, 9), rng.randint(2, 9)
    terreno = [[rng.choice(nombres) for _ in range(c)] for _ in range(f)]
    tablero = tablero_con(terreno, tipos)
    libres = [(i, j) for i in range(f) for j in range(c) if tablero.es_transitable((i, j))]
    return tablero, libres


class TestAEstrellaEscenarioOficial(unittest.TestCase):
    """Cifras de referencia para A1 (0,1) -> (3,2) con las convenciones de decisiones.md."""

    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero
        self.problema = ProblemaNavegacion(self.tablero, (0, 1), (3, 2))
        self.r = a_estrella(self.problema, "manhattan")

    def test_camino_y_costo_son_los_de_ucs(self):
        self.assertTrue(self.r.exito)
        self.assertEqual(self.r.camino, CAMINO_OFICIAL)
        self.assertEqual(self.r.costo, 7)
        self.assertEqual(len(self.r.camino) - 1, 6)

    def test_metricas_de_referencia(self):
        self.assertEqual(self.r.estados_generados, 12)
        self.assertEqual(self.r.estados_expandidos, 9)
        self.assertEqual(self.r.maximo_frontera, 5)

    def test_nombre_y_heuristica_en_el_resultado(self):
        self.assertEqual(self.r.algoritmo, "A_ESTRELLA")
        self.assertEqual(self.r.heuristica, "manhattan")
        self.assertEqual(self.r.a_diccionario()["heuristica"], "manhattan")

    def test_mismo_costo_que_ucs_expandiendo_menos(self):
        u = ucs(self.problema)
        self.assertEqual(self.r.costo, u.costo)
        self.assertLess(self.r.estados_expandidos, u.estados_expandidos)  # 9 contra 12

    def test_pantano_en_15_no_cambia_el_resultado(self):
        self.tablero.tipos_terreno["pantano"]["costo"] = 15
        r = a_estrella(self.problema, "manhattan")
        self.assertEqual((r.camino, r.costo), (CAMINO_OFICIAL, 7))

    def test_en_el_mapa_oficial_c_min_es_1_y_las_dos_variantes_coinciden(self):
        self.assertEqual(self.tablero.costo_minimo_transitable(), 1)
        pura = a_estrella(self.problema, "manhattan_pasos")
        self.assertEqual((pura.camino, pura.costo, pura.estados_generados, pura.estados_expandidos),
                         (self.r.camino, self.r.costo, self.r.estados_generados, self.r.estados_expandidos))

    def test_el_camino_es_valido_y_el_costo_cuadra(self):
        total = 0
        for (f1, c1), (f2, c2) in zip(self.r.camino, self.r.camino[1:]):
            self.assertEqual(abs(f1 - f2) + abs(c1 - c2), 1)
            total += self.tablero.costo_entrar((f2, c2))
        self.assertEqual(total, self.r.costo)

    def test_es_reproducible(self):
        otra = a_estrella(self.problema, "manhattan")
        self.assertEqual((otra.camino, otra.estados_generados, otra.estados_expandidos, otra.maximo_frontera),
                         (self.r.camino, self.r.estados_generados, self.r.estados_expandidos,
                          self.r.maximo_frontera))

    def test_con_heuristica_cero_se_comporta_como_ucs(self):
        u = ucs(self.problema)
        r = a_estrella(self.problema, lambda problema: (lambda estado: 0))
        self.assertEqual((r.camino, r.costo, r.estados_generados, r.estados_expandidos, r.maximo_frontera),
                         (u.camino, u.costo, u.estados_generados, u.estados_expandidos, u.maximo_frontera))


class TestHeuristicaManhattan(unittest.TestCase):
    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero
        self.problema = ProblemaNavegacion(self.tablero, (0, 1), (3, 2))

    def test_valores(self):
        h = crear_manhattan(self.problema)
        self.assertEqual(h((3, 2)), 0)
        self.assertEqual(h((0, 1)), 4)   # |0-3| + |1-2| = 4 pasos x c_min 1
        self.assertEqual(h((0, 0)), 5)

    def test_se_escala_por_el_costo_minimo_leido_del_escenario(self):
        self.tablero.tipos_terreno["camino"]["costo"] = 0.5
        self.assertEqual(crear_manhattan(self.problema)((0, 1)), 2.0)  # 4 pasos x 0.5
        self.assertEqual(crear_manhattan_pasos(self.problema)((0, 1)), 4)  # sin escalar

    def test_el_costo_minimo_ignora_terrenos_no_transitables(self):
        self.tablero.tipos_terreno["muro"]["costo"] = 0.01   # no se cobra nunca: no debe contar
        self.assertEqual(self.tablero.costo_minimo_transitable(), 1)

    def test_el_costo_minimo_es_el_del_catalogo_aunque_el_mapa_no_use_ese_terreno(self):
        """Decisión: c_min mira todo el catálogo. Es admisible, pero un terreno barato sin usar debilita h."""
        t = tablero_con([["n", "n", "n"]])  # solo usa "n" (1), pero el catálogo trae "r" (0.5)
        problema = ProblemaNavegacion(t, (0, 0), (0, 2))
        self.assertEqual(t.costo_minimo_transitable(), 0.5)
        self.assertEqual(crear_manhattan(problema)((0, 0)), 1.0)   # 2 pasos x 0.5, aunque el costo real es 2

    def test_nombres_disponibles_y_resolucion(self):
        self.assertEqual(set(HEURISTICAS), {"manhattan", "manhattan_pasos", "distancia_bfs"})
        self.assertIs(obtener_fabrica("manhattan"), crear_manhattan)
        self.assertIs(obtener_fabrica(crear_manhattan_pasos), crear_manhattan_pasos)
        with self.assertRaises(ValueError):
            obtener_fabrica("inventada")
        with self.assertRaises(ValueError):
            a_estrella(self.problema, "inventada")

    def costo_restante(self, tablero, estado, objetivo):
        return ucs(ProblemaNavegacion(tablero, estado, objetivo)).costo

    def test_es_admisible_y_consistente_en_el_mapa_oficial(self):
        objetivo = (3, 2)
        h = crear_manhattan(self.problema)
        for f in range(4):
            for c in range(4):
                if not self.tablero.es_transitable((f, c)):
                    continue
                self.assertLessEqual(h((f, c)), self.costo_restante(self.tablero, (f, c), objetivo), (f, c))
                for _, destino, costo in self.problema.sucesores((f, c)):
                    self.assertLessEqual(h((f, c)), costo + h(destino))   # consistencia

    def test_es_admisible_y_consistente_con_costos_menores_que_1(self):
        rng = random.Random(21)
        revisados = 0
        for _ in range(60):
            tablero, libres = mapa_aleatorio(rng, TIPOS_MEDIO, ["r", "r", "n", "c", "m"])
            if len(libres) < 2:
                continue
            objetivo = rng.choice(libres)
            problema = ProblemaNavegacion(tablero, libres[0], objetivo)
            h = crear_manhattan(problema)
            for estado in libres:
                real = self.costo_restante(tablero, estado, objetivo)
                if real is None:
                    continue
                self.assertLessEqual(h(estado), real + 1e-9)
                for _, destino, costo in problema.sucesores(estado):
                    self.assertLessEqual(h(estado), costo + h(destino) + 1e-9)
                revisados += 1
        self.assertGreater(revisados, 200)


class TestManhattanSinEscalarNoEsAdmisible(unittest.TestCase):
    """Contraejemplo real: con terrenos de costo 0.5, contar pasos sobreestima."""

    def setUp(self):
        self.tablero = tablero_con([["r", "n", "r", "r"],
                                    ["r", "r", "r", "n"]])
        self.problema = ProblemaNavegacion(self.tablero, (1, 3), (0, 0))

    def test_la_estimacion_supera_el_costo_real(self):
        pura = crear_manhattan_pasos(self.problema)
        real = ucs(self.problema).costo
        self.assertEqual(real, 2.0)
        self.assertGreater(pura((1, 3)), real)           # 4 pasos > 2.0: sobreestima
        self.assertLessEqual(crear_manhattan(self.problema)((1, 3)), real)  # 4 x 0.5 = 2.0: no sobreestima

    def test_a_estrella_sin_escalar_devuelve_un_camino_mas_caro_que_el_optimo(self):
        self.assertEqual(a_estrella(self.problema, "manhattan_pasos").costo, 2.5)

    def test_a_estrella_escalada_encuentra_el_optimo(self):
        self.assertEqual(a_estrella(self.problema, "manhattan").costo, 2.0)


class TestAEstrellaCasosLimite(unittest.TestCase):
    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero

    def test_inicio_igual_al_objetivo(self):
        r = a_estrella(ProblemaNavegacion(self.tablero, (0, 1), (0, 1)))
        self.assertTrue(r.exito)
        self.assertEqual((r.camino, r.acciones, r.costo), (((0, 1),), (), 0))
        self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (1, 1, 1))

    def test_objetivo_o_inicio_invalidos_terminan_sin_explorar(self):
        for inicio, objetivo in (((0, 1), (1, 1)), ((0, 1), (9, 9)), ((1, 1), (3, 2)), ((-1, 0), (3, 2))):
            with self.subTest(inicio=inicio, objetivo=objetivo):
                r = a_estrella(ProblemaNavegacion(self.tablero, inicio, objetivo))
                self.assertFalse(r.exito)
                self.assertEqual(r.camino, ())
                self.assertIsNone(r.costo)
                self.assertEqual((r.estados_generados, r.estados_expandidos, r.maximo_frontera), (0, 0, 0))

    def test_objetivo_encerrado_explora_todo_lo_alcanzable_y_falla(self):
        t = tablero_con([["n", "n", "n", "n"],
                         ["n", "m", "m", "m"],
                         ["n", "m", "n", "m"],
                         ["n", "m", "m", "m"]])
        r = a_estrella(ProblemaNavegacion(t, (0, 0), (2, 2)))
        self.assertFalse(r.exito)
        self.assertEqual((r.estados_generados, r.estados_expandidos), (7, 7))

    def test_objetivo_cercano_tras_un_muro_h_subestima_pero_el_camino_es_optimo(self):
        """Caso 3: Manhattan dice 2 pasos, pero hay que rodear el muro."""
        tipos = {"n": {"costo": 1, "transitable": True}, "m": {"transitable": False}}
        t = tablero_con([["n", "m", "n"],
                         ["n", "m", "n"],
                         ["n", "n", "n"]], tipos)
        problema = ProblemaNavegacion(t, (0, 0), (0, 2))
        r = a_estrella(problema)
        self.assertEqual(crear_manhattan(problema)((0, 0)), 2)  # estima 2
        self.assertEqual(r.costo, 6)                              # costo real 6
        self.assertEqual(r.costo, ucs(problema).costo)

    def test_no_modifica_el_tablero(self):
        antes = [fila[:] for fila in self.tablero.terreno]
        a_estrella(ProblemaNavegacion(self.tablero, (0, 1), (3, 2)))
        self.assertEqual(self.tablero.terreno, antes)


class TestAEstrellaEsOptimo(unittest.TestCase):
    def comparar_con_ucs(self, tipos, nombres, semilla, mapas):
        rng = random.Random(semilla)
        verificados = 0
        for _ in range(mapas):
            tablero, libres = mapa_aleatorio(rng, tipos, nombres)
            if len(libres) < 2:
                continue
            problema = ProblemaNavegacion(tablero, rng.choice(libres), rng.choice(libres))
            u, a = ucs(problema), a_estrella(problema, "manhattan")
            self.assertEqual(a.exito, u.exito)
            if u.exito:
                self.assertAlmostEqual(a.costo, u.costo)
                self.assertAlmostEqual(sum(tablero.costo_entrar(p) for p in a.camino[1:]), a.costo)
                verificados += 1
        self.assertGreater(verificados, mapas // 3)

    def test_costo_igual_al_de_ucs_con_costos_enteros(self):
        tipos = {k: {"costo": v, "transitable": True} for k, v in (("a", 1), ("b", 2), ("c", 4), ("d", 7))}
        tipos["m"] = {"transitable": False}
        self.comparar_con_ucs(tipos, ["a", "a", "b", "c", "d", "m"], semilla=3, mapas=300)

    def test_costo_igual_al_de_ucs_con_costos_menores_que_1(self):
        self.comparar_con_ucs(TIPOS_MEDIO, ["r", "r", "n", "c", "m"], semilla=4, mapas=300)

    def test_costo_igual_al_de_ucs_con_un_costo_minimo_mayor_que_1(self):
        tipos = {"b": {"costo": 3, "transitable": True}, "c": {"costo": 10, "transitable": True},
                 "m": {"transitable": False}}
        self.comparar_con_ucs(tipos, ["b", "b", "c", "m"], semilla=5, mapas=300)


MURO_QUE_OBLIGA_A_RODEAR = [["n", "n", "m", "n", "n"],
                            ["n", "n", "m", "n", "n"],
                            ["n", "n", "m", "n", "n"],
                            ["n", "n", "m", "n", "n"],
                            ["n", "n", "n", "n", "n"]]
TIPOS_UNO = {"n": {"costo": 1, "transitable": True}, "m": {"transitable": False}}


class TestHeuristicaDistanciaBFS(unittest.TestCase):
    """Heurística 2: pasos reales (rodeando muros) por el costo mínimo."""

    def setUp(self):
        self.tablero = tablero_con(MURO_QUE_OBLIGA_A_RODEAR, TIPOS_UNO)
        self.problema = ProblemaNavegacion(self.tablero, (2, 0), (2, 4))

    def test_valores_rodeando_el_muro(self):
        h = crear_distancia_bfs(self.problema)
        self.assertEqual(h((2, 4)), 0)
        self.assertEqual(h((2, 0)), 8)   # baja 2, cruza 4, sube 2: Manhattan diría 4
        self.assertEqual(crear_manhattan(self.problema)((2, 0)), 4)

    def test_se_escala_por_el_costo_minimo_del_escenario(self):
        self.tablero.tipos_terreno["n"]["costo"] = 3
        self.assertEqual(crear_distancia_bfs(self.problema)((2, 0)), 24)  # 8 pasos x 3

    def test_celdas_inalcanzables_valen_infinito(self):
        h = crear_distancia_bfs(self.problema)
        self.assertEqual(h((0, 2)), math.inf)    # un muro
        self.assertEqual(h((9, 9)), math.inf)    # fuera del mapa
        aislado = tablero_con([["n", "m", "n"]], TIPOS_UNO)
        self.assertEqual(crear_distancia_bfs(ProblemaNavegacion(aislado, (0, 0), (0, 2)))((0, 0)), math.inf)

    def test_objetivo_no_transitable_no_falla_y_todo_es_infinito(self):
        h = crear_distancia_bfs(ProblemaNavegacion(self.tablero, (2, 0), (0, 2)))  # (0,2) es muro
        self.assertEqual(h((2, 0)), math.inf)
        self.assertEqual(h((0, 2)), math.inf)

    def test_domina_a_manhattan_en_todas_las_celdas(self):
        rng = random.Random(8)
        comparadas = 0
        for _ in range(80):
            tablero, libres = mapa_aleatorio(rng, TIPOS_MEDIO, ["r", "n", "n", "c", "m", "m"])
            if len(libres) < 2:
                continue
            problema = ProblemaNavegacion(tablero, libres[0], rng.choice(libres))
            h1, h2 = crear_manhattan(problema), crear_distancia_bfs(problema)
            for estado in libres:
                self.assertGreaterEqual(h2(estado) + 1e-9, h1(estado))
                comparadas += 1
        self.assertGreater(comparadas, 300)

    def test_es_admisible_y_consistente_con_costos_menores_que_1(self):
        rng = random.Random(9)
        revisados = 0
        for _ in range(60):
            tablero, libres = mapa_aleatorio(rng, TIPOS_MEDIO, ["r", "r", "n", "c", "m", "m"])
            if len(libres) < 2:
                continue
            objetivo = rng.choice(libres)
            problema = ProblemaNavegacion(tablero, libres[0], objetivo)
            h = crear_distancia_bfs(problema)
            for estado in libres:
                real = ucs(ProblemaNavegacion(tablero, estado, objetivo)).costo
                if real is None:
                    self.assertEqual(h(estado), math.inf)   # sin ruta: infinito, nunca un número finito
                    continue
                self.assertLessEqual(h(estado), real + 1e-9)
                for _, destino, costo in problema.sucesores(estado):
                    self.assertLessEqual(h(estado), costo + h(destino) + 1e-9)
                revisados += 1
        self.assertGreater(revisados, 150)

    def test_caso_3_expande_menos_que_manhattan_con_el_mismo_costo(self):
        """Caso 3: el objetivo parece cercano pero un muro obliga a rodear."""
        m = a_estrella(self.problema, "manhattan")
        b = a_estrella(self.problema, "distancia_bfs")
        u = ucs(self.problema)
        self.assertEqual((m.costo, b.costo, u.costo), (8, 8, 8))
        self.assertEqual((m.estados_generados, m.estados_expandidos), (18, 17))
        self.assertEqual((b.estados_generados, b.estados_expandidos), (16, 13))
        self.assertLess(b.estados_expandidos, m.estados_expandidos)
        self.assertLess(m.estados_expandidos, u.estados_expandidos + 1)   # Manhattan casi no mejora a UCS (17 contra 18)

    def test_en_el_mapa_oficial_coincide_con_manhattan(self):
        tablero = cargar_escenario(RUTA_OFICIAL).tablero
        problema = ProblemaNavegacion(tablero, (0, 1), (3, 2))
        r = a_estrella(problema, "distancia_bfs")
        self.assertEqual((r.costo, r.estados_generados, r.estados_expandidos, r.maximo_frontera), (7, 12, 9, 5))
        self.assertEqual(r.heuristica, "distancia_bfs")

    def test_a_estrella_con_ella_siempre_da_el_costo_de_ucs(self):
        rng = random.Random(10)
        verificados = 0
        for _ in range(300):
            tablero, libres = mapa_aleatorio(rng, TIPOS_MEDIO, ["r", "n", "n", "c", "m", "m"])
            if len(libres) < 2:
                continue
            problema = ProblemaNavegacion(tablero, rng.choice(libres), rng.choice(libres))
            u, a = ucs(problema), a_estrella(problema, "distancia_bfs")
            self.assertEqual(a.exito, u.exito)
            if u.exito:
                self.assertAlmostEqual(a.costo, u.costo)
                verificados += 1
        self.assertGreater(verificados, 100)

    def test_sin_ruta_termina_sin_exito(self):
        aislado = tablero_con([["n", "m", "n"]], TIPOS_UNO)
        r = a_estrella(ProblemaNavegacion(aislado, (0, 0), (0, 2)), "distancia_bfs")
        self.assertFalse(r.exito)
        self.assertEqual(r.camino, ())


if __name__ == "__main__":
    unittest.main()
