"""
Purpose:
    Pruebas de la preferencia por ganar antes en Minimax y alfa-beta. Sin ella,
    todas las jugadas que conservan una victoria dentro del horizonte valían lo
    mismo (±10000) y el desempate por orden de generación podía posponer la
    victoria para siempre (en config/mapa_grande.json con profundidad 3 el portador
    de B quedaba a un paso de su base y la partida empataba a 100 turnos).

AI usage:           Yes
AI intervention:    la IA diagnosticó el problema y escribió estas pruebas.
Student validation: Validado por el equipo ejecutando este archivo
                    (python -m unittest tests.test_victoria_rapida -v) y la suite
                    completa; las pruebas fallan con la versión anterior de
                    minimax.py.
"""

import math
import random
import unittest

from src.adversarial.agent import MinimaxAgent
from src.adversarial.minimax import _valor_de_hoja, minimax_alphabeta, minimax_puro
from src.models.state import EstadoJuego
from src.scenario.loader import cargar_escenario
from src.ui.controlador import iniciar_partida, jugar_turno
from tests.base import RAIZ

import os

RUTA_GRANDE = os.path.join(RAIZ, "config", "mapa_grande.json")
BASE_A, BASE_B = (0, 0), (3, 3)


class TableroLibre:
    """Tablero ficticio de 4x4 sin obstáculos, con la firma real de Board."""

    def __init__(self):
        self.tipos_terreno = {"libre": {"costo": 1, "transitable": True}}
        self.terreno = [["libre"] * 4 for _ in range(4)]

    def es_transitable(self, pos):
        fila, col = pos
        return 0 <= fila < 4 and 0 <= col < 4


def decidir(estado, profundidad, usar_poda, bando):
    agente = MinimaxAgent(bando, profundidad=profundidad, usar_poda=usar_poda)
    return agente.seleccionar_movimiento(estado, TableroLibre(), BASE_A, BASE_B)


class TestValorDeHoja(unittest.TestCase):
    def test_victoria_de_a_suma_la_profundidad_restante(self):
        ganador = EstadoJuego([(0, 0)], [(3, 2)], ("A", 0), "B", (0, 0))
        for restante in (0, 1, 4):
            self.assertEqual(_valor_de_hoja(ganador, True, restante, BASE_A, BASE_B, None, 0), 10000.0 + restante)

    def test_victoria_de_b_resta_la_profundidad_restante(self):
        ganador = EstadoJuego([(0, 1)], [(3, 3)], ("B", 0), "A", (3, 3))
        for restante in (0, 1, 4):
            self.assertEqual(_valor_de_hoja(ganador, True, restante, BASE_A, BASE_B, None, 0), -10000.0 - restante)

    def test_un_estado_no_terminal_no_cambia_la_utilidad(self):
        libre = EstadoJuego([(0, 1)], [(3, 2)], None, "A", (1, 1))
        self.assertEqual(_valor_de_hoja(libre, False, 3, BASE_A, BASE_B, None, 0),
                         _valor_de_hoja(libre, False, 0, BASE_A, BASE_B, None, 0))

    def test_cuenta_el_nodo_y_la_profundidad_alcanzada(self):
        stats = {"nodos_evaluados": 0, "profundidad_alcanzada": 0}
        libre = EstadoJuego([(0, 1)], [(3, 2)], None, "A", (1, 1))
        _valor_de_hoja(libre, False, 0, BASE_A, BASE_B, stats, 2)
        _valor_de_hoja(libre, False, 0, BASE_A, BASE_B, stats, 1)
        self.assertEqual(stats, {"nodos_evaluados": 2, "profundidad_alcanzada": 2})


class TestElPortadorEntraALaBase(unittest.TestCase):
    """El portador a un paso de su base debe entrar: antes se elegía la primera acción empatada."""

    def estado_b(self):
        # B1 y B2 lejos; B3 (índice 2) lleva el recurso desde (3, 2), a un paso de la base B (3, 3)
        return EstadoJuego([(0, 1), (1, 0)], [(0, 3), (1, 3), (3, 2)], ("B", 2), "B", (3, 2))

    def estado_a(self):
        # Simétrico: A3 (índice 2) lleva el recurso desde (0, 1), a un paso de la base A (0, 0)
        return EstadoJuego([(3, 0), (2, 0), (0, 1)], [(3, 2), (2, 3)], ("A", 2), "A", (0, 1))

    def test_b_entra_a_su_base_con_y_sin_poda(self):
        for usar_poda in (True, False):
            for profundidad in (1, 2, 3):
                with self.subTest(poda=usar_poda, profundidad=profundidad):
                    accion, metricas = decidir(self.estado_b(), profundidad, usar_poda, "B")
                    self.assertEqual(accion, (2, BASE_B))
                    self.assertEqual(metricas["valor_obtenido"], -(10000.0 + profundidad - 1))
                    self.assertTrue(metricas["accion_legal"])

    def test_a_entra_a_su_base_con_y_sin_poda(self):
        for usar_poda in (True, False):
            for profundidad in (1, 2, 3):
                with self.subTest(poda=usar_poda, profundidad=profundidad):
                    accion, metricas = decidir(self.estado_a(), profundidad, usar_poda, "A")
                    self.assertEqual(accion, (2, BASE_A))
                    self.assertEqual(metricas["valor_obtenido"], 10000.0 + profundidad - 1)

    def test_minimax_y_alfa_beta_devuelven_lo_mismo_en_estas_posiciones(self):
        tablero = TableroLibre()
        for estado, es_max in ((self.estado_b(), False), (self.estado_a(), True)):
            for profundidad in (1, 2, 3):
                puro = minimax_puro(estado, profundidad, es_max, tablero, BASE_A, BASE_B)
                poda = minimax_alphabeta(estado, profundidad, -math.inf, math.inf, es_max, tablero, BASE_A, BASE_B)
                self.assertEqual(puro, poda)


class TestGanarAntesVale(unittest.TestCase):
    def test_prefiere_ganar_en_3_jugadas_que_en_5(self):
        """El portador de A está a 2 pasos: mover primero otra unidad también gana, pero 2 jugadas después."""
        estado = EstadoJuego([(3, 0), (2, 0), (0, 2)], [(3, 3), (3, 2), (2, 3)], ("A", 2), "A", (0, 2))
        accion, metricas = decidir(estado, 5, True, "A")
        self.assertEqual(accion, (2, (0, 1)))                 # mueve el portador, no la primera unidad
        self.assertEqual(metricas["valor_obtenido"], 10002.0)  # gana en el nivel 3 de 5 → restante 2

    def test_misma_decision_sin_poda(self):
        estado = EstadoJuego([(3, 0), (2, 0), (0, 2)], [(3, 3), (3, 2), (2, 3)], ("A", 2), "A", (0, 2))
        con_poda, _ = decidir(estado, 3, True, "A")
        sin_poda, _ = decidir(estado, 3, False, "A")
        self.assertEqual(con_poda, sin_poda)

    def test_minimax_y_alfa_beta_coinciden_en_estados_aleatorios(self):
        rng = random.Random(7)
        tablero = TableroLibre()
        casos = 0
        for _ in range(150):
            celdas = [(f, c) for f in range(4) for c in range(4)]
            pos_a = rng.sample(celdas, 2)
            pos_b = rng.sample(celdas, 2)
            portador = rng.choice([None, ("A", 0), ("A", 1), ("B", 0), ("B", 1)])
            turno = rng.choice(["A", "B"])
            recurso = rng.choice(celdas) if portador is None else (pos_a if portador[0] == "A" else pos_b)[portador[1]]
            estado = EstadoJuego(pos_a, pos_b, portador, turno, recurso)
            if estado.es_terminal(BASE_A, BASE_B):
                continue
            es_max = turno == "A"
            for profundidad in (1, 2, 3):
                puro = minimax_puro(estado, profundidad, es_max, tablero, BASE_A, BASE_B)
                poda = minimax_alphabeta(estado, profundidad, -math.inf, math.inf, es_max, tablero, BASE_A, BASE_B)
                self.assertEqual(puro, poda, (estado, profundidad))
                casos += 1
        self.assertGreater(casos, 300)


class TestPartidaGrandeTermina(unittest.TestCase):
    """Regresión: mapa_grande.json con la profundidad 3 sugerida por el JSON empataba a 100 turnos."""

    def jugar(self, profundidad):
        partida = iniciar_partida(cargar_escenario(RUTA_GRANDE), profundidad=profundidad)
        while not partida.terminada:
            jugar_turno(partida)
        return partida

    def test_con_profundidad_3_hay_ganador_antes_del_limite(self):
        partida = self.jugar(3)
        self.assertIsNotNone(partida.ganador, "la partida volvió a empatar por el límite de turnos")
        self.assertLess(partida.turno_num - 1, 100)

    def test_con_profundidad_2_tambien_termina(self):
        partida = self.jugar(2)
        self.assertIsNotNone(partida.ganador)

    def test_el_ganador_entra_con_el_recurso_a_su_base(self):
        partida = self.jugar(3)
        self.assertTrue(partida.estado.es_terminal(partida.base_a, partida.base_b))
        self.assertEqual(partida.estado.portador[0], partida.ganador)


if __name__ == "__main__":
    unittest.main()
