"""
Purpose:
    Pruebas unitarias de la búsqueda adversarial: equivalencia Minimax puro vs.
    alfa-beta (casos mínimos 7 y 8), orden de acciones y su efecto en la poda
    (caso 9), efecto de la profundidad (caso 10), estado compuesto (caso 6),
    profundidad efectiva y verificación de legalidad de las acciones elegidas.

AI usage:           Yes
AI intervention:    la IA asistió en la estructuración de los casos de prueba y
                    en la refactorización de los tableros simulados de las pruebas.
Student validation: Validado por el equipo ejecutando la suite completa
                    (244 pruebas) con unittest/pytest.
"""

import unittest

from src.adversarial.agent import MinimaxAgent
from src.adversarial.minimax import minimax_alphabeta, minimax_puro
from src.adversarial.utility import evaluar_estado
from src.models.state import EstadoJuego


class TableroSimulado:
    """Tablero ficticio de 4x4 sin obstáculos, con la firma real de Board."""

    def __init__(self):
        self.tipos_terreno = {"libre": {"costo": 1, "transitable": True}}
        self.terreno = [["libre"] * 4 for _ in range(4)]

    def es_transitable(self, pos):
        fila, col = pos
        return 0 <= fila < 4 and 0 <= col < 4


class TableroConMuro:
    """Tablero ficticio de 4x4 con un muro en (0, 1), para probar la legalidad."""

    def __init__(self):
        self.tipos_terreno = {
            "libre": {"costo": 1, "transitable": True},
            "muro": {"transitable": False},
        }
        self.terreno = [
            ["libre", "muro", "libre", "libre"],
            ["libre", "libre", "libre", "libre"],
            ["libre", "libre", "libre", "libre"],
            ["libre", "libre", "libre", "libre"],
        ]

    def es_transitable(self, pos):
        fila, col = pos
        if not (0 <= fila < 4 and 0 <= col < 4):
            return False
        return self.terreno[fila][col] != "muro"


def _stats_vacias():
    return {
        "nodos_visitados": 0,
        "nodos_generados": 0,
        "nodos_evaluados": 0,
        "podas_alfa": 0,
        "podas_beta": 0,
    }


class TestMinimaxAdversarial(unittest.TestCase):

    def setUp(self):
        """Configuración del estado de prueba inicial."""
        self.tablero = TableroSimulado()
        self.base_a = (0, 0)
        self.base_b = (3, 3)
        self.recurso = (1, 1)
        self.estado_inicial = EstadoJuego(
            pos_a=(0, 0),
            pos_b=(3, 3),
            portador=None,
            turno="A",
            recurso_pos=self.recurso,
        )

    def test_equivalencia_minimax_y_alphabeta(self):
        """
        Casos Mínimos 7 y 8:
        Demuestra que Minimax Puro y Alpha-Beta eligen la misma acción y el mismo valor,
        pero Alpha-Beta explora/evalúa un número igual o menor de nodos.
        """
        profundidad = 3

        stats_puro = _stats_vacias()
        val_puro, mov_puro = minimax_puro(
            self.estado_inicial, profundidad, True, self.tablero,
            self.base_a, self.base_b, stats_puro,
        )

        stats_ab = _stats_vacias()
        val_ab, mov_ab = minimax_alphabeta(
            self.estado_inicial, profundidad, float("-inf"), float("inf"), True,
            self.tablero, self.base_a, self.base_b, stats_ab,
        )

        # 1. Mismo valor heurístico y misma acción óptima
        self.assertEqual(mov_puro, mov_ab, f"Las acciones difieren: Puro={mov_puro}, AB={mov_ab}")
        self.assertEqual(val_puro, val_ab, f"Los valores difieren: Puro={val_puro}, AB={val_ab}")

        # 2. Alpha-Beta debe visitar igual o menos nodos
        self.assertLessEqual(
            stats_ab["nodos_visitados"],
            stats_puro["nodos_visitados"],
            "Alpha-Beta no debería visitar más nodos que Minimax puro",
        )

    def test_legalidad_de_movimientos(self):
        """
        Verificación de legalidad (enunciado: "las acciones consideradas por
        minimax son legales dentro de las reglas del juego"):
        la acción del agente está entre los sucesores legales, el verificador
        del agente la aprueba y la métrica 'accion_legal' queda en True.
        """
        agente = MinimaxAgent("A", profundidad=3, usar_poda=True)
        movimiento, metricas = agente.seleccionar_movimiento(
            self.estado_inicial, self.tablero, self.base_a, self.base_b,
        )

        sucesores_legales = [mov for mov, _ in self.estado_inicial.sucesores(self.tablero)]
        self.assertIn(
            movimiento, sucesores_legales,
            f"El movimiento {movimiento} no se encuentra dentro de las opciones legales.",
        )

        legal, _ = agente.verificar_accion(self.estado_inicial, self.tablero, movimiento)
        self.assertTrue(legal, "El verificador del agente rechazó una acción que sí es legal")
        self.assertTrue(metricas["accion_legal"], "La métrica 'accion_legal' debería ser True")

    def test_verificar_accion_detecta_ilegales(self):
        """El verificador del agente rechaza muros, celdas no vecinas, índices inexistentes y celdas fuera del mapa."""
        tablero = TableroConMuro()
        agente = MinimaxAgent("A", profundidad=1)
        estado = EstadoJuego(
            pos_a=(0, 0), pos_b=(3, 3), portador=None, turno="A", recurso_pos=(1, 1),
        )

        legal, _ = agente.verificar_accion(estado, tablero, (0, (1, 0)))
        self.assertTrue(legal, "Mover la unidad 0 a (1, 0) desde (0, 0) debería ser legal")

        legal, detalle = agente.verificar_accion(estado, tablero, (0, (0, 1)))
        self.assertFalse(legal, "Mover a un muro debería ser ilegal")
        self.assertIn("transitable", detalle)

        legal, detalle = agente.verificar_accion(estado, tablero, (0, (2, 2)))
        self.assertFalse(legal, "Mover a una celda no vecina debería ser ilegal")
        self.assertIn("vecina", detalle)

        legal, detalle = agente.verificar_accion(estado, tablero, (0, (-1, 0)))
        self.assertFalse(legal, "Mover fuera del mapa debería ser ilegal")
        self.assertIn("fuera del mapa", detalle)

        legal, detalle = agente.verificar_accion(estado, tablero, (5, (1, 0)))
        self.assertFalse(legal, "Un índice de unidad inexistente debería ser ilegal")
        self.assertIn("no existe", detalle)

        legal, _ = agente.verificar_accion(estado, tablero, None)
        self.assertFalse(legal, "Una acción None debería ser ilegal")

    def test_caso_minimo_6_estado_compuesto(self):
        """
        Caso Mínimo 6:
        Misma posición física de unidades pero con distinto portador o turno
        debe comportarse distinto (evaluación y estado terminal).
        """
        st1 = EstadoJuego(pos_a=(0, 0), pos_b=(3, 3), portador=None, turno="A", recurso_pos=(2, 2))
        st2 = EstadoJuego(pos_a=(0, 0), pos_b=(3, 3), portador="A", turno="A", recurso_pos=(0, 0))

        # En st2, A tiene el recurso sobre su base (0,0) -> Estado Terminal de victoria
        self.assertFalse(st1.es_terminal(self.base_a, self.base_b))
        self.assertTrue(st2.es_terminal(self.base_a, self.base_b))

        # Las evaluaciones heurísticas deben diferir sustancialmente
        val1 = evaluar_estado(st1, self.base_a, self.base_b)
        val2 = evaluar_estado(st2, self.base_a, self.base_b)
        self.assertNotEqual(val1, val2)

    def test_caso_minimo_9_orden_direcciones_afecta_podas(self):
        """
        Caso Mínimo 9:
        Demuestra que cambiar el orden de exploración en sucesores() altera
        la cantidad de podas Alpha-Beta conservando el valor óptimo.
        """

        class TableroAsimetrico:
            def es_transitable(self, pos):
                fila, col = pos
                # Bloquear casillas para obligar a ramas de decisión asimétricas
                if (fila, col) in [(0, 1), (1, 0)]:
                    return False
                return 0 <= fila < 4 and 0 <= col < 4

        tablero_asim = TableroAsimetrico()

        # Las unidades NO deben empezar en sus bases (base_a=(0,0), base_b=(3,3))
        # para evitar terminar en el nodo raíz.
        estado_asim = EstadoJuego(
            pos_a=(1, 1),
            pos_b=(2, 2),
            portador=None,
            turno="A",
            recurso_pos=(0, 2),
        )

        profundidad = 3
        orden_a = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # Arriba, Der, Abajo, Izq
        orden_b = [(1, 0), (0, -1), (-1, 0), (0, 1)]  # Abajo, Izq, Arriba, Der

        stats_a = _stats_vacias()
        val_a, mov_a = minimax_alphabeta(
            estado_asim, profundidad, float("-inf"), float("inf"), True,
            tablero_asim, self.base_a, self.base_b, stats_a, orden_direcciones=orden_a,
        )

        stats_b = _stats_vacias()
        val_b, mov_b = minimax_alphabeta(
            estado_asim, profundidad, float("-inf"), float("inf"), True,
            tablero_asim, self.base_a, self.base_b, stats_b, orden_direcciones=orden_b,
        )

        # 1. El valor de la decisión debe ser idéntico
        self.assertEqual(val_a, val_b)

        # 2. Las podas o nodos visitados deben variar según el orden de ramas
        podas_totales_a = stats_a["podas_alfa"] + stats_a["podas_beta"]
        podas_totales_b = stats_b["podas_alfa"] + stats_b["podas_beta"]

        self.assertTrue(
            podas_totales_a != podas_totales_b or stats_a["nodos_visitados"] != stats_b["nodos_visitados"],
            f"El orden debió impactar la exploración. Stats A: {stats_a}, Stats B: {stats_b}",
        )

    def test_caso_minimo_10_impacto_profundidad(self):
        """
        Caso Mínimo 10:
        Evalúa cómo influye incrementar la profundidad en la cantidad de nodos visitados.
        """
        stats_p3 = _stats_vacias()
        minimax_alphabeta(
            self.estado_inicial, 3, float("-inf"), float("inf"), True,
            self.tablero, self.base_a, self.base_b, stats_p3,
        )

        stats_p4 = _stats_vacias()
        minimax_alphabeta(
            self.estado_inicial, 4, float("-inf"), float("inf"), True,
            self.tablero, self.base_a, self.base_b, stats_p4,
        )

        # A mayor profundidad, mayor o igual cantidad de nodos generados y visitados
        self.assertGreater(stats_p4["nodos_generados"], stats_p3["nodos_generados"])

    def test_profundidad_alcanzada_es_la_efectiva(self):
        """
        La métrica 'profundidad_alcanzada' reporta el mayor nivel evaluado
        (profundidad efectiva), no la profundidad pedida: con un estado
        terminal en la raíz, la búsqueda no baja de nivel.
        """
        pedida = 3

        stats_normal = _stats_vacias()
        minimax_alphabeta(
            self.estado_inicial, pedida, float("-inf"), float("inf"), True,
            self.tablero, self.base_a, self.base_b, stats_normal,
        )
        self.assertEqual(stats_normal["profundidad_alcanzada"], pedida)

        terminal = EstadoJuego(
            pos_a=self.base_a, pos_b=(2, 2), portador="A", turno="A", recurso_pos=None,
        )
        stats_terminal = _stats_vacias()
        minimax_alphabeta(
            terminal, pedida, float("-inf"), float("inf"), True,
            self.tablero, self.base_a, self.base_b, stats_terminal,
        )
        self.assertEqual(stats_terminal["profundidad_alcanzada"], 0)
        self.assertEqual(stats_terminal["nodos_evaluados"], 1)

    def test_agente_reporta_profundidad_efectiva(self):
        """La métrica del agente usa la profundidad efectiva registrada por la búsqueda."""
        agente = MinimaxAgent("A", profundidad=3, usar_poda=True)
        _, metricas = agente.seleccionar_movimiento(
            self.estado_inicial, self.tablero, self.base_a, self.base_b,
        )
        self.assertEqual(metricas["profundidad_alcanzada"], 3)


if __name__ == "__main__":
    unittest.main()
