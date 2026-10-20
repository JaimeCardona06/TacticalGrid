"""Compatibilidad con escenarios externos: nombres de terreno propios (arena/lava/roca).

Purpose:            demostrar que el sistema NO depende de los nombres del
                    ejemplo del enunciado ("camino", "pasto", ...): carga,
                    valida y resuelve un escenario cuyos terrenos se llaman
                    "arena" (costo 2), "lava" (costo 9) y "roca" (no
                    transitable), leyendo costos y transitabilidad del JSON.
Preconditions:      config/mapa_agnostico.json existe y pasa el validador.
Postconditions:     cada prueba falla mostrando el esperado y el obtenido;
                    no modifica archivos.
Complexity:         la de los algoritmos que ejercita (BFS/UCS/A* sobre 5x5).
AI usage:           Yes
AI intervention:    la IA escribió el escenario, las pruebas y esta documentación.
Student validation: Validado por el equipo ejecutando la suite completa.
"""

import copy
import os
import unittest

from src.game.navegacion import ProblemaNavegacion
from src.game.verificador import verificar_solucion
from src.scenario.loader import cargar_escenario, leer_json
from src.scenario.validator import validar_escenario
from src.search.informed import a_estrella
from src.search.uninformed import bfs, ucs

from tests.base import RAIZ

RUTA_AGNOSTICO = os.path.join(RAIZ, "config", "mapa_agnostico.json")


class TestMapaAgnostico(unittest.TestCase):
    """El sistema funciona con nombres y costos de terreno definidos por el JSON."""

    def setUp(self):
        self.escenario = cargar_escenario(RUTA_AGNOSTICO)
        self.tablero = self.escenario.tablero
        unidad = next(u for u in self.escenario.unidades if u.id == "A1")
        self.inicio = unidad.posicion
        self.objetivo = (2, 4)

    def test_carga_con_nombres_y_costos_del_json(self):
        """El catálogo usa nombres propios y Board lee costo/transitabilidad del JSON."""
        self.assertEqual(set(self.tablero.tipos_terreno), {"arena", "lava", "roca"},
                         "esperado: catálogo con los nombres propios; obtenido: otro conjunto")
        self.assertEqual(self.tablero.costo_entrar((0, 0)), 2,
                         "esperado: costo de 'arena' = 2 (leído del JSON)")
        self.assertEqual(self.tablero.costo_entrar((2, 2)), 9,
                         "esperado: costo de 'lava' = 9 (leído del JSON)")
        self.assertFalse(self.tablero.es_transitable((1, 1)),
                         "esperado: 'roca' no transitable")

    def test_busqueda_usa_los_costos_del_json(self):
        """BFS cruza la lava (corto y caro); UCS/A* rodean por arena (largo y barato)."""
        problema = ProblemaNavegacion(self.tablero, self.inicio, self.objetivo)

        resultado_bfs = bfs(problema)
        resultado_ucs = ucs(problema)
        resultado_a = a_estrella(problema, "distancia_bfs")

        self.assertTrue(resultado_bfs.exito and resultado_ucs.exito and resultado_a.exito,
                        "esperado: los tres encuentran solución")
        self.assertEqual(len(resultado_bfs.camino) - 1, 4,
                         f"esperado BFS: 4 pasos por la lava; obtenido: {len(resultado_bfs.camino) - 1}")
        self.assertEqual(resultado_bfs.costo, 36,
                         f"esperado BFS: costo 36 (4 x 9); obtenido: {resultado_bfs.costo}")
        self.assertEqual(len(resultado_ucs.camino) - 1, 8,
                         f"esperado UCS: 8 pasos rodeando; obtenido: {len(resultado_ucs.camino) - 1}")
        self.assertEqual(resultado_ucs.costo, 23,
                         f"esperado UCS: costo 23 (7 x 2 + 9); obtenido: {resultado_ucs.costo}")
        self.assertEqual(resultado_a.costo, resultado_ucs.costo,
                         f"esperado A*: mismo costo óptimo que UCS; obtenido: {resultado_a.costo}")

        informe = verificar_solucion(self.tablero, resultado_a, self.inicio, self.objetivo)
        self.assertTrue(informe.valido,
                        f"esperado: verificación VÁLIDA; obtenido: {informe.problemas}")

    def test_validador_exige_que_los_nombres_esten_en_el_catalogo(self):
        """Un terreno usado que no existe en tipos_terreno se rechaza (los nombres no son libres)."""
        datos = copy.deepcopy(leer_json(RUTA_AGNOSTICO))
        datos["terreno"][0][0] = "agua"

        errores = validar_escenario(datos)

        self.assertTrue(any("agua" in error for error in errores),
                        f"esperado: error que mencione 'agua'; obtenido: {errores}")


if __name__ == "__main__":
    unittest.main()
