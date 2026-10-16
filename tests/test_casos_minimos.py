"""Casos mínimos del enunciado (pág. 8): cobertura formal y reproducible.

Purpose:            cubrir los 10 casos mínimos exigidos por el enunciado,
                    declarando el estado inicial de cada uno (escenario JSON de
                    config/ o estado construido), ejecutando los algoritmos
                    reales del proyecto y contrastando el resultado ESPERADO
                    contra el OBTENIDO (los mensajes de fallo muestran ambos).
Preconditions:      los escenarios caso_*.json de config/ pasan el validador y
                    los módulos de búsqueda/adversarial están implementados.
Postconditions:     cada caso es una prueba independiente; si un resultado deja
                    de cumplir lo esperado, la prueba falla mostrando el valor
                    esperado y el obtenido. No modifica archivos.
Complexity:         la de los algoritmos que ejercita cada caso (búsqueda:
                    la de cada algoritmo; adversarial: O(b^d) por decisión).
AI usage:           Yes
AI intervention:    la IA asistió en el diseño de los escenarios JSON, la
                    búsqueda de contraejemplos (haz con k=1 y decisión
                    adversarial) y esta documentación.
Student validation: Validado por el equipo ejecutando la suite completa y
                    contrastando los resultados esperados contra los obtenidos.
"""

import os
import unittest

from src.adversarial.agent import MinimaxAgent
from src.adversarial.utility import evaluar_estado
from src.game.navegacion import ProblemaNavegacion
from src.models.state import EstadoJuego
from src.scenario.loader import cargar_escenario
from src.search.informed import a_estrella, beam_search
from src.search.uninformed import bfs, dfs, ucs

from tests.base import RAIZ


def ruta_config(nombre):
    """Ruta absoluta de un escenario de config/."""
    return os.path.join(RAIZ, "config", nombre)


def unidad_por_id(escenario, unidad_id):
    return next(u for u in escenario.unidades if u.id == unidad_id)


def problema_de_prueba(escenario):
    """ProblemaNavegacion desde 'prueba' (unidad_inicio y objetivo) del escenario."""
    unidad = unidad_por_id(escenario, escenario.prueba["unidad_inicio"])
    objetivo = escenario.prueba["objetivo"]
    return ProblemaNavegacion(escenario.tablero, unidad.posicion, (objetivo["fila"], objetivo["columna"]))


def pasos(resultado):
    """Número de movimientos del camino (longitud - 1)."""
    return len(resultado.camino) - 1


class TestCasosMinimosBusqueda(unittest.TestCase):
    """Casos 1 a 5: búsqueda no informada, costos, informada y memoria limitada."""

    def test_caso_01_bfs_frente_a_dfs(self):
        """Caso 1: BFS y DFS encuentran solución, pero recorren el espacio distinto.

        Estado inicial declarado (config/caso_obstaculo.json): unidad A1 en
        (2, 0) hacia (2, 4) con un muro que obliga a rodear por el borde.
        Esperado: ambos encuentran solución; los caminos y las métricas de
        exploración (expandidos, frontera máxima) difieren.
        """
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        problema = problema_de_prueba(escenario)

        resultado_bfs = bfs(problema)
        resultado_dfs = dfs(problema)

        self.assertTrue(
            resultado_bfs.exito and resultado_dfs.exito,
            f"esperado: ambos encuentran solución; obtenido: BFS={resultado_bfs.exito}, DFS={resultado_dfs.exito}",
        )
        self.assertNotEqual(
            resultado_bfs.camino, resultado_dfs.camino,
            "esperado: caminos distintos (BFS explora por capas, DFS en profundidad); obtenido: el mismo camino",
        )
        self.assertNotEqual(
            (resultado_bfs.estados_expandidos, resultado_bfs.maximo_frontera),
            (resultado_dfs.estados_expandidos, resultado_dfs.maximo_frontera),
            "esperado: exploración distinta; obtenido: mismas métricas "
            f"expandidos={resultado_bfs.estados_expandidos}, frontera={resultado_bfs.maximo_frontera}",
        )

    def test_caso_02_ruta_corta_frente_a_ruta_economica(self):
        """Caso 2: BFS y UCS dan soluciones distintas por los costos del terreno.

        Estado inicial declarado (config/caso_bfs_vs_ucs.json): A1 en (2, 0)
        hacia (2, 4); la fila 2 completa es pantano (costo 7) y el resto camino
        (costo 1).
        Esperado: BFS toma la ruta de menos movimientos (4 pasos, costo 28);
        UCS prefiere la ruta más larga pero económica (6 pasos, costo 12).
        """
        escenario = cargar_escenario(ruta_config("caso_bfs_vs_ucs.json"))
        problema = problema_de_prueba(escenario)

        resultado_bfs = bfs(problema)
        resultado_ucs = ucs(problema)

        self.assertTrue(
            resultado_bfs.exito and resultado_ucs.exito,
            f"esperado: ambos encuentran solución; obtenido: BFS={resultado_bfs.exito}, UCS={resultado_ucs.exito}",
        )
        self.assertEqual(
            pasos(resultado_bfs), 4,
            f"esperado BFS: 4 pasos por el pantano; obtenido: {pasos(resultado_bfs)}",
        )
        self.assertEqual(
            resultado_bfs.costo, 28,
            f"esperado BFS: costo 28 (4 x 7); obtenido: {resultado_bfs.costo}",
        )
        self.assertEqual(
            pasos(resultado_ucs), 6,
            f"esperado UCS: 6 pasos rodeando; obtenido: {pasos(resultado_ucs)}",
        )
        self.assertEqual(
            resultado_ucs.costo, 12,
            f"esperado UCS: costo 12; obtenido: {resultado_ucs.costo}",
        )
        self.assertLess(pasos(resultado_bfs), pasos(resultado_ucs),
                        "esperado: la ruta corta tiene menos movimientos")
        self.assertGreater(resultado_bfs.costo, resultado_ucs.costo,
                           "esperado: la ruta corta es más costosa")

    def test_caso_03_obstaculo_y_heuristica(self):
        """Caso 3: el objetivo parece cercano, pero una barrera obliga a rodearlo.

        Estado inicial declarado (config/caso_obstaculo.json): A1 en (2, 0)
        hacia (2, 4). Manhattan entre ambos es 4, pero el muro de la columna 2
        (filas 1 a 4) obliga a subir hasta la fila 0.
        Esperado: A* encuentra la solución rodeando en 8 pasos (costo 8), más
        del doble de la distancia Manhattan directa.
        """
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        problema = problema_de_prueba(escenario)
        manhattan_directa = abs(problema.inicio[0] - problema.objetivo[0]) + abs(problema.inicio[1] - problema.objetivo[1])

        resultado = a_estrella(problema, "distancia_bfs")

        self.assertTrue(resultado.exito, "esperado: hay solución rodeando el muro; obtenido: sin solución")
        self.assertEqual(manhattan_directa, 4, f"estado inicial inválido: Manhattan esperada 4, obtenida {manhattan_directa}")
        self.assertEqual(
            pasos(resultado), 8,
            f"esperado: 8 pasos rodeando el muro; obtenido: {pasos(resultado)}",
        )
        self.assertGreater(
            pasos(resultado), manhattan_directa,
            f"esperado: la ruta real supera la Manhattan directa ({manhattan_directa}); obtenido: {pasos(resultado)}",
        )
        self.assertEqual(resultado.costo, 8, f"esperado: costo 8; obtenido: {resultado.costo}")

    def test_caso_04_comparacion_de_heuristicas(self):
        """Caso 4: A* con varias heurísticas sobre el mismo escenario.

        Estado inicial declarado (config/caso_obstaculo.json), el mismo del caso 3.
        Esperado: las tres heurísticas devuelven el mismo costo óptimo (8) y la
        distancia BFS (que ve el muro) expande menos estados que Manhattan (que
        no lo ve).
        """
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        problema = problema_de_prueba(escenario)

        manhattan = a_estrella(problema, "manhattan")
        manhattan_pasos = a_estrella(problema, "manhattan_pasos")
        distancia_bfs = a_estrella(problema, "distancia_bfs")

        for nombre, resultado in (("manhattan", manhattan), ("manhattan_pasos", manhattan_pasos), ("distancia_bfs", distancia_bfs)):
            self.assertTrue(resultado.exito, f"esperado: {nombre} encuentra solución; obtenido: sin solución")
            self.assertEqual(
                resultado.costo, 8,
                f"esperado {nombre}: costo óptimo 8; obtenido: {resultado.costo}",
            )
        self.assertLess(
            distancia_bfs.estados_expandidos, manhattan.estados_expandidos,
            f"esperado: distancia_bfs (ve el muro) expande menos que manhattan; obtenido: "
            f"{distancia_bfs.estados_expandidos} vs {manhattan.estados_expandidos}",
        )
        self.assertLessEqual(
            distancia_bfs.estados_generados, manhattan.estados_generados,
            f"esperado: distancia_bfs genera <= que manhattan; obtenido: "
            f"{distancia_bfs.estados_generados} vs {manhattan.estados_generados}",
        )

    def test_caso_05_beam_search(self):
        """Caso 5: cambiar k modifica la exploración y, con memoria limitada, la solución.

        Estado inicial declarado (config/caso_beam.json): A1 en (0, 0) hacia
        (5, 5) en un mapa 6x6 con muros que forman un señuelo.
        Esperado: UCS confirma que existe ruta (costo 10); Beam con k=1 la
        descarta y falla; con k=2, 4 y 8 encuentra la solución óptima y la
        cantidad de nodos generados crece con k.
        """
        escenario = cargar_escenario(ruta_config("caso_beam.json"))
        problema = problema_de_prueba(escenario)

        referencia = ucs(problema)
        k1 = beam_search(problema, 1)
        k2 = beam_search(problema, 2)
        k4 = beam_search(problema, 4)
        k8 = beam_search(problema, 8)

        self.assertTrue(referencia.exito, "esperado: UCS encuentra ruta; obtenido: sin solución (¿escenario roto?)")
        self.assertEqual(referencia.costo, 10, f"esperado UCS: costo 10; obtenido: {referencia.costo}")
        self.assertFalse(
            k1.exito,
            f"esperado k=1: falla aunque existe ruta (descarta el camino bueno); obtenido: exito={k1.exito}, costo={k1.costo}",
        )
        for k, resultado in ((2, k2), (4, k4), (8, k8)):
            self.assertTrue(resultado.exito, f"esperado k={k}: encuentra solución; obtenido: sin solución")
            self.assertEqual(
                resultado.costo, referencia.costo,
                f"esperado k={k}: costo óptimo {referencia.costo}; obtenido: {resultado.costo}",
            )
        self.assertLess(
            k1.estados_generados, k2.estados_generados,
            f"esperado: k=1 explora menos que k=2; obtenido: {k1.estados_generados} vs {k2.estados_generados}",
        )
        self.assertLess(
            k2.estados_generados, k4.estados_generados,
            f"esperado: k=2 explora menos que k=4; obtenido: {k2.estados_generados} vs {k4.estados_generados}",
        )
        self.assertLessEqual(
            k4.estados_generados, k8.estados_generados,
            f"esperado: k=4 genera <= que k=8; obtenido: {k4.estados_generados} vs {k8.estados_generados}",
        )


class TestCasoMinimoEstadoCompuesto(unittest.TestCase):
    """Caso 6: la misma posición física representa estados diferentes."""

    def test_caso_06_estado_compuesto(self):
        """Caso 6: la misma posición física son estados distintos por el portador.

        Estado inicial declarado (config/caso_adversarial.json): A1 en (2, 1),
        B1 en (3, 2) y recurso en (2, 2). Se comparan DOS estados con las mismas
        posiciones: uno sin portador y otro con A transportando el recurso.
        Esperado: no son el mismo estado: la utilidad difiere y, al mover a A a
        (2, 0), en uno el recurso queda en (2, 2) y en el otro viaja con A.
        """
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        tablero = escenario.tablero
        pos_a = unidad_por_id(escenario, "A1").posicion
        pos_b = unidad_por_id(escenario, "B1").posicion

        sin_portador = EstadoJuego(pos_a=pos_a, pos_b=pos_b, portador=None, turno="A", recurso_pos=escenario.recurso)
        con_portador = EstadoJuego(pos_a=pos_a, pos_b=pos_b, portador="A", turno="A", recurso_pos=pos_a)

        self.assertEqual(
            (sin_portador.pos_a, sin_portador.pos_b), (con_portador.pos_a, con_portador.pos_b),
            "declaración del caso: las posiciones físicas deben ser idénticas",
        )

        valor_sin = evaluar_estado(sin_portador, tablero.base_a, tablero.base_b)
        valor_con = evaluar_estado(con_portador, tablero.base_a, tablero.base_b)
        self.assertNotEqual(
            valor_sin, valor_con,
            f"esperado: utilidades distintas por el portador; obtenido: {valor_sin} y {valor_con}",
        )

        destino = (pos_a[0], pos_a[1] - 1)
        hijo_sin = next(estado for mov, estado in sin_portador.sucesores(tablero) if mov == destino)
        hijo_con = next(estado for mov, estado in con_portador.sucesores(tablero) if mov == destino)

        self.assertIsNone(hijo_sin.portador, "sin portador, mover no cambia quién lleva el recurso")
        self.assertEqual(
            hijo_sin.recurso_pos, escenario.recurso,
            f"esperado: el recurso libre queda en {escenario.recurso}; obtenido: {hijo_sin.recurso_pos}",
        )
        self.assertEqual(hijo_con.portador, "A", "con portador, el recurso sigue siendo de A")
        self.assertEqual(
            hijo_con.recurso_pos, destino,
            f"esperado: el recurso viaja con A a {destino}; obtenido: {hijo_con.recurso_pos}",
        )


class TestCasosMinimosAdversarial(unittest.TestCase):
    """Casos 7 a 10: decisión adversarial, poda, orden de acciones y profundidad."""

    def setUp(self):
        self.escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        self.tablero = self.escenario.tablero
        self.base_a, self.base_b = self.tablero.base_a, self.tablero.base_b
        self.pos_a = unidad_por_id(self.escenario, "A1").posicion
        self.pos_b = unidad_por_id(self.escenario, "B1").posicion
        self.recurso = self.escenario.recurso
        self.estado = EstadoJuego(
            pos_a=self.pos_a, pos_b=self.pos_b, portador=None, turno="A", recurso_pos=self.recurso,
        )

    def _agente(self, profundidad, usar_poda=True, orden=None):
        return MinimaxAgent("A", profundidad=profundidad, usar_poda=usar_poda, orden_direcciones=orden)

    def _seleccionar(self, agente):
        return agente.seleccionar_movimiento(self.estado, self.tablero, self.base_a, self.base_b)

    @staticmethod
    def _distancia(pos, otra):
        return abs(pos[0] - otra[0]) + abs(pos[1] - otra[1])

    def test_caso_07_decision_adversarial(self):
        """Caso 7: la mejor decisión con adversario no es avanzar directamente al recurso.

        Estado inicial declarado (config/caso_adversarial.json): A1 en (2, 1) a
        un paso del recurso (2, 2); B1 en (3, 2) pegado al recurso, listo para
        robarlo. Turno de A.
        Esperado: con profundidad 1 (miope) A agarra el recurso (2, 2) con una
        valoración positiva; con profundidad 3, Minimax anticipa el robo de B y
        elige otra celda más lejos del recurso (y legal), con valoración negativa.
        """
        accion_miope, met_miope = self._seleccionar(self._agente(1))
        accion_profunda, met_profunda = self._seleccionar(self._agente(3))

        self.assertEqual(
            accion_miope, self.recurso,
            f"esperado miope (profundidad 1): agarrar el recurso {self.recurso}; obtenido: {accion_miope}",
        )
        self.assertNotEqual(
            accion_profunda, accion_miope,
            "esperado: la decisión cambia al considerar las respuestas del adversario; obtenido: la misma acción",
        )
        self.assertGreaterEqual(
            self._distancia(accion_profunda, self.recurso), self._distancia(self.pos_a, self.recurso),
            f"esperado: no avanza directamente al recurso; obtenido: {accion_profunda} (más cerca que {self.pos_a})",
        )
        legal, detalle = self._agente(3).verificar_accion(self.estado, self.tablero, accion_profunda)
        self.assertTrue(legal, f"esperado: acción legal; obtenido: {detalle}")
        self.assertGreater(
            met_miope["valor_obtenido"], 0,
            f"esperado miope: valor positivo (agarra); obtenido: {met_miope['valor_obtenido']}",
        )
        self.assertLess(
            met_profunda["valor_obtenido"], 0,
            f"esperado profundo: valor negativo al ver el robo; obtenido: {met_profunda['valor_obtenido']}",
        )

    def test_caso_08_minimax_frente_a_alfa_beta(self):
        """Caso 8: misma decisión, pero alfa-beta evita evaluar parte del árbol.

        Mismo estado inicial del caso 7, profundidad 3.
        Esperado: Minimax puro y alfa-beta eligen la misma acción con el mismo
        valor; alfa-beta visita menos nodos y registra podas.
        """
        accion_puro, met_puro = self._seleccionar(self._agente(3, usar_poda=False))
        accion_ab, met_ab = self._seleccionar(self._agente(3, usar_poda=True))

        self.assertEqual(
            accion_puro, accion_ab,
            f"esperado: misma acción; obtenido: puro={accion_puro}, alfa-beta={accion_ab}",
        )
        self.assertEqual(
            met_puro["valor_obtenido"], met_ab["valor_obtenido"],
            f"esperado: mismo valor; obtenido: puro={met_puro['valor_obtenido']}, alfa-beta={met_ab['valor_obtenido']}",
        )
        self.assertLess(
            met_ab["nodos_visitados"], met_puro["nodos_visitados"],
            f"esperado: alfa-beta visita menos nodos; obtenido: puro={met_puro['nodos_visitados']}, "
            f"alfa-beta={met_ab['nodos_visitados']}",
        )
        self.assertGreater(
            met_ab["podas_totales"], 0,
            "esperado: alfa-beta poda al menos una rama; obtenido: 0 podas",
        )

    def test_caso_09_orden_de_acciones_y_poda(self):
        """Caso 9: cambiar el orden de los sucesores cambia la cantidad de poda.

        Mismo estado inicial del caso 7, profundidad 3, con dos órdenes de
        direcciones distintos.
        Esperado: el mismo valor óptimo con ambos órdenes, pero la exploración
        (nodos visitados y podas) es distinta según el orden.
        """
        orden_arriba = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        orden_abajo = [(1, 0), (0, -1), (-1, 0), (0, 1)]

        _, met_arriba = self._seleccionar(self._agente(3, orden=orden_arriba))
        _, met_abajo = self._seleccionar(self._agente(3, orden=orden_abajo))

        self.assertEqual(
            met_arriba["valor_obtenido"], met_abajo["valor_obtenido"],
            f"esperado: mismo valor con ambos órdenes; obtenido: "
            f"{met_arriba['valor_obtenido']} y {met_abajo['valor_obtenido']}",
        )
        self.assertNotEqual(
            (met_arriba["nodos_visitados"], met_arriba["podas_totales"]),
            (met_abajo["nodos_visitados"], met_abajo["podas_totales"]),
            "esperado: exploración distinta según el orden; obtenido: "
            f"visitados={met_arriba['nodos_visitados']} y podas={met_arriba['podas_totales']} en ambos",
        )

    def test_caso_10_efecto_de_la_profundidad(self):
        """Caso 10: el mismo estado con distintas profundidades.

        Mismo estado inicial del caso 7, profundidades 1 a 4.
        Esperado: los nodos generados crecen estrictamente al profundizar,
        todas las acciones elegidas son legales y el valor cambia al ver más
        jugadas (el miope es positivo; el de profundidad 3, negativo por el robo).
        """
        metricas = {}
        for profundidad in (1, 2, 3, 4):
            agente = self._agente(profundidad)
            accion, met = self._seleccionar(agente)
            legal, detalle = agente.verificar_accion(self.estado, self.tablero, accion)
            self.assertTrue(legal, f"profundidad {profundidad}: esperado acción legal; obtenido: {detalle}")
            metricas[profundidad] = met

        for profundidad in (1, 2, 3):
            self.assertLess(
                metricas[profundidad]["nodos_generados"], metricas[profundidad + 1]["nodos_generados"],
                f"esperado: más nodos al profundizar ({profundidad} -> {profundidad + 1}); obtenido: "
                f"{metricas[profundidad]['nodos_generados']} y {metricas[profundidad + 1]['nodos_generados']}",
            )
        self.assertGreater(
            metricas[1]["valor_obtenido"], 0,
            f"esperado profundidad 1: valor positivo; obtenido: {metricas[1]['valor_obtenido']}",
        )
        self.assertLess(
            metricas[3]["valor_obtenido"], 0,
            f"esperado profundidad 3: valor negativo (anticipa el robo); obtenido: {metricas[3]['valor_obtenido']}",
        )


if __name__ == "__main__":
    unittest.main()
