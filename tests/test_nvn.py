"""Modelo adversarial N vs N: varias unidades por bando (3 vs 3).

Purpose:            cubrir la generalización N vs N de la fase adversarial:
                    posiciones múltiples por bando, portador como identidad de
                    unidad (bando, índice), ramificación acotada (unidades ×
                    direcciones), robo con varias unidades, condición de
                    victoria del portador, decisión legal sobre un escenario
                    3 vs 3 real (config/mapa_3v3.json) y regresión numérica de
                    las métricas 1 vs 1 ya reportadas en el documento técnico.
Preconditions:      los escenarios de config/ pasan el validador y los
                    módulos de estado/agente están implementados.
Postconditions:     cada prueba falla mostrando el esperado y el obtenido; no
                    modifica archivos.
Complexity:         la de los algoritmos que ejercita (profundidad <= 3 sobre
                    tableros 4x4 y 5x5).
AI usage:           Yes
AI intervention:    la IA escribió las pruebas y esta documentación.
Student validation: Validado por el equipo ejecutando la suite completa.
"""

import contextlib
import io
import os
import unittest

import main as modulo_main
from src.adversarial.agent import MinimaxAgent
from src.models.state import EstadoJuego
from src.scenario.loader import cargar_escenario

from tests.base import RAIZ


def ruta_config(nombre):
    return os.path.join(RAIZ, "config", nombre)


class Tablero4x4Libre:
    """Tablero ficticio de 4x4 sin obstáculos, con la firma real de Board."""

    def es_transitable(self, pos):
        fila, columna = pos
        return 0 <= fila < 4 and 0 <= columna < 4


class TestEstadoNvsN(unittest.TestCase):
    """Estado con 3 unidades por bando: sucesores, portador y victoria."""

    def setUp(self):
        self.tablero = Tablero4x4Libre()
        self.base_a = (0, 0)
        self.base_b = (3, 3)

    def test_ramificacion_acotada_a_unidades_por_direcciones(self):
        """3 unidades en zona abierta generan 12 = 3 × 4 sucesores."""
        estado = EstadoJuego(
            pos_a=((1, 1), (1, 2), (2, 1)),
            pos_b=((3, 1), (3, 2), (2, 3)),
            portador=None,
            turno="A",
            recurso_pos=(2, 0),
        )
        self.assertEqual(len(estado.sucesores(self.tablero)), 12)

    def test_accion_lleva_indice_y_destino(self):
        estado = EstadoJuego(
            pos_a=((1, 1), (1, 2), (2, 1)),
            pos_b=((3, 1), (3, 2), (2, 3)),
            portador=None,
            turno="A",
            recurso_pos=(2, 0),
        )
        for accion, _ in estado.sucesores(self.tablero):
            indice, destino = accion
            self.assertIn(indice, (0, 1, 2))
            self.assertEqual(len(destino), 2)

    def test_recurso_viaja_solo_con_su_portador(self):
        """Mover al portador mueve el recurso; mover a otra unidad, no."""
        estado = EstadoJuego(
            pos_a=((1, 1), (1, 2)),
            pos_b=((3, 3),),
            portador=("A", 0),
            turno="A",
            recurso_pos=(1, 1),
        )
        movimientos = {accion: nuevo for accion, nuevo in estado.sucesores(self.tablero)}

        mov_portador = movimientos[(0, (0, 1))]
        self.assertEqual(mov_portador.portador, ("A", 0))
        self.assertEqual(mov_portador.recurso_pos, (0, 1))

        mov_otra = movimientos[(1, (1, 3))]
        self.assertEqual(mov_otra.portador, ("A", 0))
        self.assertEqual(mov_otra.recurso_pos, (1, 1))

    def test_robo_al_portador_rival_con_varias_unidades(self):
        """Entrar a la celda del portador rival roba; entrar a otra unidad rival, no."""
        estado = EstadoJuego(
            pos_a=((2, 1), (0, 1)),
            pos_b=((1, 1), (0, 2)),
            portador=("B", 0),
            turno="A",
            recurso_pos=(1, 1),
        )
        movimientos = {accion: nuevo for accion, nuevo in estado.sucesores(self.tablero)}

        roba = movimientos[(0, (1, 1))]
        self.assertEqual(roba.portador, ("A", 0))
        self.assertEqual(roba.recurso_pos, (1, 1))

        no_roba = movimientos[(1, (0, 2))]
        self.assertEqual(no_roba.portador, ("B", 0))
        self.assertEqual(no_roba.recurso_pos, (1, 1))

    def test_gana_solo_el_portador_en_su_base(self):
        sin_portador = EstadoJuego(
            pos_a=((0, 0), (1, 1)), pos_b=((3, 3),),
            portador=None, turno="A", recurso_pos=(2, 2),
        )
        self.assertFalse(sin_portador.es_terminal(self.base_a, self.base_b))

        portador_lejos = EstadoJuego(
            pos_a=((0, 0), (1, 1)), pos_b=((3, 3),),
            portador=("A", 1), turno="A", recurso_pos=(1, 1),
        )
        self.assertFalse(portador_lejos.es_terminal(self.base_a, self.base_b))

        portador_en_base = EstadoJuego(
            pos_a=((0, 0), (1, 1)), pos_b=((3, 3),),
            portador=("A", 0), turno="A", recurso_pos=(0, 0),
        )
        self.assertTrue(portador_en_base.es_terminal(self.base_a, self.base_b))


class TestDecision3vs3(unittest.TestCase):
    """Decisión real sobre config/mapa_3v3.json (3 unidades por bando)."""

    def setUp(self):
        self.escenario = cargar_escenario(ruta_config("mapa_3v3.json"))
        self.tablero = self.escenario.tablero
        self.unidades_a = [u for u in self.escenario.unidades if u.bando == "A"]
        self.unidades_b = [u for u in self.escenario.unidades if u.bando == "B"]
        self.estado = EstadoJuego(
            pos_a=tuple(u.posicion for u in self.unidades_a),
            pos_b=tuple(u.posicion for u in self.unidades_b),
            portador=None,
            turno="A",
            recurso_pos=self.escenario.recurso,
        )

    def test_decision_3vs3_es_legal(self):
        agente = MinimaxAgent("A", profundidad=2, usar_poda=True)
        accion, metricas = agente.seleccionar_movimiento(
            self.estado, self.tablero, self.tablero.base_a, self.tablero.base_b,
        )
        self.assertIsNotNone(accion, "esperado: hay acciones legales para A")
        indice, _ = accion
        self.assertIn(indice, (0, 1, 2), f"esperado índice de unidad A; obtenido: {indice}")
        self.assertTrue(metricas["accion_legal"], metricas["detalle_legalidad"])

    def test_partida_3vs3_usa_todas_las_unidades(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = modulo_main.ejecutar_partida(self.escenario, profundidad=2, usar_poda=True)
        texto = salida.getvalue()
        self.assertEqual(codigo, 0, texto)
        self.assertIn("3 unidad(es) de A vs 3 de B", texto)
        self.assertIn("A1, A2, A3", texto)
        self.assertIn("B1, B2, B3", texto)
        self.assertNotIn("se ignoran", texto, "el modelo N vs N no debe ignorar unidades")
        self.assertTrue("PARTIDA FINALIZADA" in texto or "PARTIDA EMPATADA" in texto)


class TestRegresionMetricas1vs1(unittest.TestCase):
    """Las métricas 1 vs 1 reportadas en el documento técnico no cambian."""

    def test_caso_adversarial_d3_identico_al_documento(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        tablero = escenario.tablero
        pos_a = next(u.posicion for u in escenario.unidades if u.bando == "A")
        pos_b = next(u.posicion for u in escenario.unidades if u.bando == "B")
        estado = EstadoJuego(
            pos_a=pos_a, pos_b=pos_b, portador=None, turno="A", recurso_pos=escenario.recurso,
        )
        agente = MinimaxAgent("A", profundidad=3, usar_poda=True)
        accion, metricas = agente.seleccionar_movimiento(
            estado, tablero, tablero.base_a, tablero.base_b,
        )
        self.assertEqual(accion, (0, (1, 1)))
        self.assertEqual(metricas["valor_obtenido"], -4800.0)
        self.assertEqual(metricas["nodos_generados"], 38)
        self.assertEqual(metricas["nodos_evaluados"], 16)
        self.assertEqual(metricas["nodos_visitados"], 27)
        self.assertEqual(metricas["podas_totales"], 5)
        self.assertTrue(metricas["accion_legal"])


if __name__ == "__main__":
    unittest.main()
