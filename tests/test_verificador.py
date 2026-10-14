"""Pruebas del verificador: soluciones válidas de los cinco algoritmos y un caso negativo por comprobación."""
import copy
import random
import unittest
from dataclasses import replace

from src.game.navegacion import ProblemaNavegacion
from src.game.verificador import verificar_solucion
from src.models.board import Board
from src.scenario.loader import cargar_escenario
from src.search.informed import a_estrella, beam_search
from src.search.uninformed import bfs, dfs, ucs
from tests.base import RUTA_OFICIAL

INICIO, OBJETIVO = (0, 1), (3, 2)


class PruebaVerificador(unittest.TestCase):
    def setUp(self):
        self.tablero = cargar_escenario(RUTA_OFICIAL).tablero
        self.problema = ProblemaNavegacion(self.tablero, INICIO, OBJETIVO)
        self.buena = ucs(self.problema)    # camino válido de costo 7

    def verificar(self, resultado):
        return verificar_solucion(self.tablero, resultado, INICIO, OBJETIVO)

    def assertProblema(self, informe, fragmento):
        self.assertFalse(informe.valido, "se esperaba que NO fuera válida")
        self.assertTrue(any(fragmento in p for p in informe.problemas),
                        f"no hay problema con {fragmento!r} en: {informe.problemas}")


class TestSolucionesValidas(PruebaVerificador):
    def test_los_cinco_algoritmos_producen_soluciones_validas(self):
        resultados = {"bfs": bfs(self.problema), "dfs": dfs(self.problema), "ucs": ucs(self.problema),
                      "a*": a_estrella(self.problema), "a*2": a_estrella(self.problema, "distancia_bfs"),
                      "beam1": beam_search(self.problema, 1), "beam2": beam_search(self.problema, 2),
                      "beam8": beam_search(self.problema, 8)}
        for nombre, r in resultados.items():
            with self.subTest(algoritmo=nombre):
                informe = self.verificar(r)
                self.assertTrue(informe.valido, informe.problemas)

    def test_el_informe_lista_todas_las_comprobaciones(self):
        informe = self.verificar(self.buena)
        descripciones = [d for d, _ in informe.comprobaciones]
        self.assertEqual(len(descripciones), 7)
        self.assertTrue(all(ps == () for _, ps in informe.comprobaciones))
        self.assertIn("El costo reportado es la suma del costo de las celdas destino", descripciones)

    def test_inicio_igual_al_objetivo(self):
        r = ucs(ProblemaNavegacion(self.tablero, INICIO, INICIO))
        self.assertTrue(verificar_solucion(self.tablero, r, INICIO, INICIO).valido)

    def test_costos_decimales(self):
        self.tablero.tipos_terreno["camino"]["costo"] = 0.1
        self.tablero.tipos_terreno["pasto"]["costo"] = 0.2
        r = ucs(self.problema)
        self.assertTrue(self.verificar(r).valido)       # sumas de decimales con tolerancia

    def test_no_modifica_lo_que_recibe(self):
        terreno = copy.deepcopy(self.tablero.terreno)
        antes = replace(self.buena)
        self.verificar(self.buena)
        self.assertEqual(self.tablero.terreno, terreno)
        self.assertEqual(self.buena, antes)


class TestCasosNegativos(PruebaVerificador):
    """Una solución manipulada para cada comprobación: el verificador debe rechazarla."""

    def test_camino_que_atraviesa_un_muro(self):
        # (0,1) -> (1,1) es el muro -> (2,1) ... baja recto por la columna 1
        malo = replace(self.buena, camino=((0, 1), (1, 1), (2, 1), (3, 1), (3, 2)),
                       acciones=("abajo", "abajo", "abajo", "derecha"), costo=1 + 2 + 2 + 1)
        self.assertProblema(self.verificar(malo), "terreno no transitable ('muro')")

    def test_salto_de_dos_celdas(self):
        malo = replace(self.buena, camino=((0, 1), (0, 0), (2, 0), (2, 1), (3, 1), (3, 2)),
                       acciones=("izquierda", "abajo", "derecha", "abajo", "derecha"))
        self.assertProblema(self.verificar(malo), "que no son celdas vecinas")

    def test_paso_en_diagonal(self):
        malo = replace(self.buena, camino=((0, 1), (0, 0), (1, 0), (2, 0), (3, 1), (3, 2)),
                       acciones=("izquierda", "abajo", "abajo", "derecha", "derecha"))
        self.assertProblema(self.verificar(malo), "que no son celdas vecinas")

    def test_costo_mal_reportado(self):
        for costo in (self.buena.costo + 1, self.buena.costo - 1, 0, None, "7", True):
            with self.subTest(costo=costo):
                self.assertProblema(self.verificar(replace(self.buena, costo=costo)),
                                    "la suma de los pasos es 7")

    def test_empieza_en_otra_celda(self):
        malo = replace(self.buena, camino=((0, 0),) + self.buena.camino[1:])
        self.assertProblema(self.verificar(malo), "empieza en (0, 0) y debía empezar en (0, 1)")

    def test_termina_en_otra_celda(self):
        r = beam_search(ProblemaNavegacion(self.tablero, INICIO, (3, 3)), 2)
        self.assertProblema(self.verificar(r), "termina en (3, 3) y debía terminar en (3, 2)")

    def test_celda_fuera_del_mapa(self):
        for fuera in ((4, 1), (-1, 1), (0, 9)):
            with self.subTest(celda=fuera):
                malo = replace(self.buena, camino=self.buena.camino + (fuera,))
                self.assertProblema(self.verificar(malo), "está fuera del mapa")

    def test_celdas_con_forma_invalida(self):
        for elemento in ("(3,2)", (1,), (1.0, 2), (True, 2), None, (1, 2, 3)):
            with self.subTest(elemento=elemento):
                malo = replace(self.buena, camino=self.buena.camino[:-1] + (elemento,))
                self.assertProblema(self.verificar(malo), "no es una posición (fila, columna) de enteros")

    def test_camino_vacio_con_exito(self):
        self.assertProblema(self.verificar(replace(self.buena, camino=())), "el camino está vacío")

    def test_acciones_que_no_coinciden_o_faltan(self):
        cambiadas = replace(self.buena, acciones=("arriba",) + self.buena.acciones[1:])
        self.assertProblema(self.verificar(cambiadas), "la acción 1 es 'arriba'")
        self.assertProblema(self.verificar(replace(self.buena, acciones=())), "acciones para 6 pasos")

    def test_metricas_incoherentes(self):
        self.assertProblema(self.verificar(replace(self.buena, estados_expandidos=99)),
                            "se expandieron 99 estados pero solo se generaron")
        self.assertProblema(self.verificar(replace(self.buena, estados_generados=-1)),
                            "estados_generados debe ser un entero no negativo")

    def test_sin_exito_pero_con_camino_o_costo(self):
        sin_exito = bfs(ProblemaNavegacion(self.tablero, INICIO, (1, 1)))     # objetivo en un muro: sin ruta
        verificar = lambda r: verificar_solucion(self.tablero, r, INICIO, (1, 1))   # con el MISMO objetivo
        self.assertTrue(verificar(sin_exito).valido)    # coherente: sin camino, acciones ni costo
        self.assertProblema(verificar(replace(sin_exito, camino=((0, 1),))), "trae un camino")
        self.assertProblema(verificar(replace(sin_exito, costo=0)), "trae un costo")
        self.assertProblema(verificar(replace(sin_exito, acciones=("arriba",))), "trae acciones")

    def test_varios_problemas_se_informan_juntos(self):
        malo = replace(self.buena, camino=((0, 1), (1, 1), (3, 2)), acciones=(), costo=3)
        informe = self.verificar(malo)
        self.assertGreaterEqual(len(informe.problemas), 3)    # muro, salto y acciones
        self.assertProblema(informe, "no transitable")
        self.assertProblema(informe, "no son celdas vecinas")


class SoloDatosTablero(Board):
    """Un Board cuyos métodos de consulta fallan: el verificador no debe llamarlos."""

    def _no(self, *a, **k):
        raise AssertionError("el verificador usó un método de Board")

    dentro_del_mapa = es_transitable = costo_entrar = vecinos = costo_minimo_transitable = _no


class TestIndependenciaDelVerificador(PruebaVerificador):
    def test_no_usa_ningun_metodo_de_board(self):
        t = self.tablero
        sin_metodos = SoloDatosTablero(t.filas, t.columnas, t.tipos_terreno, t.terreno, t.base_a, t.base_b)
        informe = verificar_solucion(sin_metodos, self.buena, INICIO, OBJETIVO)
        self.assertTrue(informe.valido, informe.problemas)

    def test_detecta_un_costo_mal_calculado_por_un_board_con_error(self):
        """Si costo_entrar tuviera un error, el algoritmo lo heredaría pero el verificador lo detecta."""

        class BoardConError(Board):
            def costo_entrar(self, pos):
                return super().costo_entrar(pos) + 1     # error deliberado

        t = self.tablero
        defectuoso = BoardConError(t.filas, t.columnas, t.tipos_terreno, t.terreno, t.base_a, t.base_b)
        r = ucs(ProblemaNavegacion(defectuoso, INICIO, OBJETIVO))
        self.assertGreater(r.costo, 7)                    # el algoritmo reporta un costo inflado...
        informe = verificar_solucion(defectuoso, r, INICIO, OBJETIVO)
        self.assertProblema(informe, "la suma de los pasos es")  # ...y el verificador lo descubre

    def test_detecta_un_board_que_deja_pasar_muros(self):
        class BoardSinMuros(Board):
            def es_transitable(self, pos):
                return self.dentro_del_mapa(pos)

            def costo_entrar(self, pos):
                return 1

        t = self.tablero
        defectuoso = BoardSinMuros(t.filas, t.columnas, t.tipos_terreno, t.terreno, t.base_a, t.base_b)
        destino = (2, 1)    # directamente debajo del muro (1,1): el camino más corto lo cruza
        r = bfs(ProblemaNavegacion(defectuoso, INICIO, destino))
        self.assertTrue(r.exito)
        self.assertIn((1, 1), r.camino)                   # el algoritmo, engañado por el Board, cruza el muro
        self.assertProblema(verificar_solucion(defectuoso, r, INICIO, destino), "no transitable")


class TestTolerancia(PruebaVerificador):
    """Las sumas de decimales no son exactas: 0.1 + 0.2 = 0.30000000000000004."""

    def tablero_decimal(self):
        tipos = {"a": {"costo": 0.1, "transitable": True}, "b": {"costo": 0.2, "transitable": True}}
        return Board(1, 3, tipos, [["a", "a", "b"]], (0, 0), (0, 0))

    def test_una_suma_correcta_con_ruido_de_punto_flotante_no_es_error(self):
        t = self.tablero_decimal()
        suma = 0.1 + 0.2
        self.assertNotEqual(suma, 0.3)                      # el ruido existe: con == fallaría
        r = replace(ucs(ProblemaNavegacion(t, (0, 0), (0, 2))), costo=0.3)   # costo "limpio" reportado
        self.assertTrue(verificar_solucion(t, r, (0, 0), (0, 2)).valido)

    def test_una_diferencia_real_pequena_si_es_error(self):
        t = self.tablero_decimal()
        r = replace(ucs(ProblemaNavegacion(t, (0, 0), (0, 2))), costo=0.3 + 1e-6)
        self.assertProblema(verificar_solucion(t, r, (0, 0), (0, 2)), "la suma de los pasos es")


class TestSinExito(PruebaVerificador):
    """Un 'sin éxito' se comprueba con una búsqueda de alcanzabilidad independiente."""

    def test_sin_ruta_confirma_el_sin_exito(self):
        for algoritmo in (bfs, dfs, ucs, a_estrella):
            with self.subTest(algoritmo=algoritmo.__name__):
                r = algoritmo(ProblemaNavegacion(self.tablero, INICIO, (1, 1)))     # objetivo en un muro
                informe = self.verificar_con(r, (1, 1))
                self.assertTrue(informe.valido)
                self.assertEqual(informe.avisos, ())

    def verificar_con(self, resultado, objetivo, tablero=None):
        return verificar_solucion(tablero or self.tablero, resultado, INICIO, objetivo)

    def test_objetivo_encerrado_de_verdad_es_un_sin_exito_valido(self):
        t = Board(4, 4, {"n": {"costo": 1, "transitable": True}, "m": {"transitable": False}},
                  [["n", "n", "n", "n"], ["n", "m", "m", "m"], ["n", "m", "n", "m"], ["n", "m", "m", "m"]],
                  (0, 0), (0, 0))
        for algoritmo in (bfs, dfs, ucs, a_estrella):
            r = algoritmo(ProblemaNavegacion(t, (0, 0), (2, 2)))
            self.assertFalse(r.exito)
            informe = verificar_solucion(t, r, (0, 0), (2, 2))
            self.assertTrue(informe.valido, informe.problemas)

    def test_un_algoritmo_completo_que_falla_aunque_hay_ruta_es_un_error(self):
        for algoritmo in (bfs, dfs, ucs, a_estrella):
            with self.subTest(algoritmo=algoritmo.__name__):
                bueno = algoritmo(self.problema)
                falso_fallo = replace(bueno, exito=False, camino=(), acciones=(), costo=None)
                self.assertProblema(self.verificar(falso_fallo), "pero sí existe una ruta")

    def test_beam_que_falla_aunque_hay_ruta_es_un_aviso_no_un_error(self):
        t = Board(3, 3, {"n": {"costo": 1, "transitable": True}, "m": {"transitable": False}},
                  [["n", "n", "n"], ["m", "n", "m"], ["n", "n", "n"]], (0, 0), (0, 0))
        r = beam_search(ProblemaNavegacion(t, (0, 0), (2, 2)), 1)
        self.assertFalse(r.exito)
        informe = verificar_solucion(t, r, (0, 0), (2, 2))
        self.assertTrue(informe.valido)
        self.assertEqual(len(informe.avisos), 1)
        self.assertIn("Beam Search con k = 1", informe.avisos[0])
        self.assertIn("sí existe una ruta", informe.avisos[0])
        # con k = 2 sí lo encuentra: no hay aviso
        r2 = beam_search(ProblemaNavegacion(t, (0, 0), (2, 2)), 2)
        self.assertEqual(verificar_solucion(t, r2, (0, 0), (2, 2)).avisos, ())

    def test_la_alcanzabilidad_tampoco_usa_metodos_de_board(self):
        t = self.tablero
        sin_metodos = SoloDatosTablero(t.filas, t.columnas, t.tipos_terreno, t.terreno, t.base_a, t.base_b)
        r = bfs(ProblemaNavegacion(t, INICIO, (1, 1)))
        self.assertTrue(verificar_solucion(sin_metodos, r, INICIO, (1, 1)).valido)
        falso_fallo = replace(self.buena, exito=False, camino=(), acciones=(), costo=None)
        self.assertProblema(verificar_solucion(sin_metodos, falso_fallo, INICIO, OBJETIVO), "pero sí existe una ruta")


class TestVerificadorEnMapasAleatorios(unittest.TestCase):
    def test_todas_las_soluciones_exitosas_de_todos_los_algoritmos_son_validas(self):
        tipos = {"a": {"costo": 1, "transitable": True}, "b": {"costo": 0.5, "transitable": True},
                 "c": {"costo": 7, "transitable": True}, "m": {"transitable": False}}
        rng = random.Random(31)
        verificadas = 0
        for _ in range(150):
            f, c = rng.randint(2, 9), rng.randint(2, 9)
            terreno = [[rng.choice(["a", "a", "b", "c", "m", "m"]) for _ in range(c)] for _ in range(f)]
            tablero = Board(f, c, copy.deepcopy(tipos), terreno, (0, 0), (0, 0))
            libres = [(i, j) for i in range(f) for j in range(c) if tablero.es_transitable((i, j))]
            if len(libres) < 2:
                continue
            ini, obj = rng.choice(libres), rng.choice(libres)
            problema = ProblemaNavegacion(tablero, ini, obj)
            for r in (bfs(problema), dfs(problema), ucs(problema), a_estrella(problema, "manhattan"),
                      a_estrella(problema, "distancia_bfs"), beam_search(problema, 1),
                      beam_search(problema, 3), beam_search(problema, 8)):
                informe = verificar_solucion(tablero, r, ini, obj)
                self.assertTrue(informe.valido, (r.algoritmo, informe.problemas))
                verificadas += r.exito
        self.assertGreater(verificadas, 600)


if __name__ == "__main__":
    unittest.main()
