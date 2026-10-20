"""Prueba del escenario 20x20 de busqueda con obstaculos."""

import os
import unittest

from src.game.navegacion import ProblemaNavegacion
from src.game.verificador import verificar_solucion
from src.scenario.loader import cargar_escenario
from src.search.informed import a_estrella, beam_search
from src.search.uninformed import bfs, dfs, ucs

from tests.base import RAIZ


class TestMapaGrandeBusqueda(unittest.TestCase):
    """Ejecuta todos los algoritmos de busqueda sobre el mapa grande."""

    def setUp(self):
        self.escenario = cargar_escenario(
            os.path.join(RAIZ, "config", "mapa_grande_busqueda.json"))
        self.prueba = self.escenario.prueba
        self.unidad = next(
            unidad for unidad in self.escenario.unidades
            if unidad.id == self.prueba["unidad_inicio"])
        self.objetivo = (
            self.prueba["objetivo"]["fila"], self.prueba["objetivo"]["columna"])
        self.problema = ProblemaNavegacion(
            self.escenario.tablero, self.unidad.posicion, self.objetivo)

    def test_escenario_20x20_y_todos_los_algoritmos(self):
        self.assertEqual(
            (self.escenario.tablero.filas, self.escenario.tablero.columnas), (20, 20))
        self.assertEqual(self.prueba["modo"], "busqueda")
        muros = sum(
            celda == "muro"
            for fila in self.escenario.tablero.terreno for celda in fila)
        self.assertGreater(muros, 0, "el escenario debe tener obstaculos")

        resultados = {
            "BFS": bfs(self.problema),
            "DFS": dfs(self.problema),
            "UCS": ucs(self.problema),
            "A* manhattan": a_estrella(self.problema, "manhattan"),
            "A* manhattan_pasos": a_estrella(self.problema, "manhattan_pasos"),
            "A* distancia_bfs": a_estrella(self.problema, "distancia_bfs"),
            "Beam k=1": beam_search(self.problema, 1, "distancia_bfs"),
            "Beam k=2": beam_search(self.problema, 2, "distancia_bfs"),
            "Beam k=4": beam_search(self.problema, 4, "distancia_bfs"),
            "Beam k=8": beam_search(self.problema, 8, "distancia_bfs"),
        }

        for nombre, resultado in resultados.items():
            self.assertTrue(
                resultado.exito,
                f"{nombre} no encontro ruta en el mapa 20x20")
            informe = verificar_solucion(
                self.escenario.tablero, resultado, self.problema.inicio, self.objetivo)
            self.assertTrue(
                informe.valido,
                f"{nombre} produjo una solucion invalida: {informe.problemas}")

        self.assertEqual(len(resultados["BFS"].camino) - 1, 37)
        self.assertEqual(resultados["UCS"].costo, 39)
        self.assertEqual(resultados["A* distancia_bfs"].costo, 39)
        self.assertLess(
            resultados["A* distancia_bfs"].estados_expandidos,
            resultados["UCS"].estados_expandidos)


if __name__ == "__main__":
    unittest.main()
