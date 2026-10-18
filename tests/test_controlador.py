import os
import unittest
from dataclasses import replace

from dataclasses import replace as _replace

from src.models.board import Board
from src.scenario.escenario import Escenario, Unidad
from src.scenario.loader import cargar_escenario
from src.ui.controlador import (
    ErrorControlador, unidades_con_posiciones, portador_unidad_id, recurso_pos_inicial,
    resolver_busqueda_gui, preparar_estado_inicial, evaluar_adversarial,
    PartidaEnCurso, iniciar_partida, jugar_turno,
)
from tests.base import RAIZ


def ruta_config(nombre):
    return os.path.join(RAIZ, "config", nombre)


class FakeEstado:
    def __init__(self, portador):
        self.portador = portador


class TestUnidadesConPosiciones(unittest.TestCase):
    def setUp(self):
        self.unidades = (
            Unidad(id="A1", bando="A", tipo="estandar", posicion=(0, 0)),
            Unidad(id="A2", bando="A", tipo="estandar", posicion=(0, 1)),
            Unidad(id="B1", bando="B", tipo="estandar", posicion=(1, 0)),
        )

    def test_reemplaza_solo_las_indicadas(self):
        resultado = unidades_con_posiciones(self.unidades, "A1", (3, 3), "B1", (4, 4))
        por_id = {u.id: u.posicion for u in resultado}
        self.assertEqual(por_id, {"A1": (3, 3), "A2": (0, 1), "B1": (4, 4)})


class TestPortadorUnidadId(unittest.TestCase):
    def test_bando_a(self):
        unidad_a = Unidad(id="A1", bando="A", tipo="estandar", posicion=(0, 0))
        unidad_b = Unidad(id="B1", bando="B", tipo="estandar", posicion=(1, 1))
        self.assertEqual(portador_unidad_id(FakeEstado("A"), unidad_a, unidad_b), "A1")
        self.assertEqual(portador_unidad_id(FakeEstado("B"), unidad_a, unidad_b), "B1")
        self.assertIsNone(portador_unidad_id(FakeEstado(None), unidad_a, unidad_b))


class TestRecursoPosInicial(unittest.TestCase):
    def test_sin_portador_devuelve_la_posicion_del_recurso(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        self.assertEqual(recurso_pos_inicial(escenario), escenario.recurso)

    def test_con_portador_devuelve_la_posicion_de_esa_unidad(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        portador_id = escenario.unidades[0].id
        escenario_con_portador = replace(escenario, portador_recurso=portador_id)
        self.assertEqual(
            recurso_pos_inicial(escenario_con_portador), escenario.unidades[0].posicion)


class TestResolverBusquedaGui(unittest.TestCase):
    def test_bfs_resuelve_el_caso_del_obstaculo(self):
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        resultado, informe = resolver_busqueda_gui(
            escenario, "A1", (2, 4), "BFS")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.costo, 8, f"esperado: 8; obtenido: {resultado.costo}")
        self.assertTrue(informe.valido, informe.problemas)

    def test_unidad_inexistente_lanza_error_controlador(self):
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        with self.assertRaises(ErrorControlador):
            resolver_busqueda_gui(escenario, "ZZZ", (2, 4), "BFS")

    def test_algoritmo_desconocido_lanza_error_controlador(self):
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        with self.assertRaises(ErrorControlador):
            resolver_busqueda_gui(escenario, "A1", (2, 4), "MAGIA")


class TestPrepararEstadoInicial(unittest.TestCase):
    def test_falta_unidad_de_un_bando_lanza_error_controlador(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        solo_a = _replace(escenario, unidades=tuple(
            u for u in escenario.unidades if u.bando == "A"))
        with self.assertRaises(ErrorControlador):
            preparar_estado_inicial(solo_a)


class TestEvaluarAdversarial(unittest.TestCase):
    def test_caso_minimo_7_profundidad_1_agarra_el_recurso(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        resultado = evaluar_adversarial(escenario, profundidad=1)
        self.assertEqual(resultado["accion"], (2, 2),
                          f"esperado: (2, 2); obtenido: {resultado['accion']}")

    def test_caso_minimo_7_profundidad_3_se_repliega(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        resultado = evaluar_adversarial(escenario, profundidad=3)
        self.assertEqual(resultado["accion"], (1, 1),
                          f"esperado: (1, 1); obtenido: {resultado['accion']}")

    def test_sin_acciones_legales_lanza_error_controlador(self):
        tablero = Board(
            filas=1, columnas=1,
            tipos_terreno={"camino": {"costo": 1, "transitable": True}},
            terreno=[["camino"]], base_a=(0, 0), base_b=(0, 0))
        escenario = Escenario(
            tablero=tablero,
            unidades=(Unidad("A1", "A", "estandar", (0, 0)),
                      Unidad("B1", "B", "estandar", (0, 0))),
            turno="A", recurso=(0, 0), portador_recurso=None,
            profundidad_maxima_minimax=2, prueba=None)
        with self.assertRaises(ErrorControlador):
            evaluar_adversarial(escenario, profundidad=2)


class TestPartida(unittest.TestCase):
    def test_mapa_partida_lo_gana_b_en_22_turnos(self):
        escenario = cargar_escenario(ruta_config("mapa_partida.json"))
        partida = iniciar_partida(escenario)
        self.assertIsInstance(partida, PartidaEnCurso)
        filas = []
        while not partida.terminada:
            filas.append(jugar_turno(partida))
        self.assertEqual(partida.ganador, "B",
                          f"esperado: B; obtenido: {partida.ganador}")
        self.assertEqual(partida.turno_num - 1, 22,
                          f"esperado: 22 turnos; obtenido: {partida.turno_num - 1}")
        self.assertEqual(len(filas), 22)

    def test_jugar_turno_despues_de_terminada_lanza_error_controlador(self):
        escenario = cargar_escenario(ruta_config("mapa_partida.json"))
        partida = iniciar_partida(escenario)
        while not partida.terminada:
            jugar_turno(partida)
        with self.assertRaises(ErrorControlador):
            jugar_turno(partida)

    def test_empate_por_limite_de_turnos_no_excede_max_turnos(self):
        import main as modulo_main
        tablero = Board(
            filas=1, columnas=3,
            tipos_terreno={"camino": {"costo": 1, "transitable": True}},
            terreno=[["camino", "camino", "camino"]], base_a=(0, 0), base_b=(0, 2))
        escenario = Escenario(
            tablero=tablero,
            unidades=(Unidad("A1", "A", "estandar", (0, 0)),
                      Unidad("B1", "B", "estandar", (0, 2))),
            turno="A", recurso=(0, 1), portador_recurso=None,
            profundidad_maxima_minimax=1, prueba=None)
        partida = iniciar_partida(escenario, profundidad=1)
        turnos_jugados = 0
        while not partida.terminada and turnos_jugados <= modulo_main.MAX_TURNOS + 1:
            jugar_turno(partida)
            turnos_jugados += 1
        self.assertTrue(partida.terminada)
        self.assertLessEqual(turnos_jugados, modulo_main.MAX_TURNOS)
