import os
import unittest
from dataclasses import replace
from unittest.mock import patch

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
        self.unidades_a = (
            Unidad(id="A1", bando="A", tipo="estandar", posicion=(0, 0)),
            Unidad(id="A2", bando="A", tipo="estandar", posicion=(0, 1)),
        )
        self.unidades_b = (
            Unidad(id="B1", bando="B", tipo="estandar", posicion=(1, 0)),
        )

    def test_reemplaza_las_posiciones_de_todas_las_unidades_por_indice(self):
        resultado = unidades_con_posiciones(
            self.unidades_a, ((3, 3), (3, 4)), self.unidades_b, ((4, 4),))
        por_id = {u.id: u.posicion for u in resultado}
        self.assertEqual(por_id, {"A1": (3, 3), "A2": (3, 4), "B1": (4, 4)})


class TestPortadorUnidadId(unittest.TestCase):
    def test_resuelve_por_bando_e_indice(self):
        unidades_a = (
            Unidad(id="A1", bando="A", tipo="estandar", posicion=(0, 0)),
            Unidad(id="A2", bando="A", tipo="estandar", posicion=(0, 1)),
        )
        unidades_b = (Unidad(id="B1", bando="B", tipo="estandar", posicion=(1, 1)),)
        self.assertEqual(portador_unidad_id(FakeEstado(("A", 1)), unidades_a, unidades_b), "A2")
        self.assertEqual(portador_unidad_id(FakeEstado(("B", 0)), unidades_a, unidades_b), "B1")
        self.assertIsNone(portador_unidad_id(FakeEstado(None), unidades_a, unidades_b))


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
        self.assertEqual(resultado["accion"], (0, (2, 2)),
                          f"esperado: (0, (2, 2)); obtenido: {resultado['accion']}")
        self.assertEqual(resultado["destino"], (2, 2))
        self.assertEqual(resultado["nombre_unidad"], "A1")

    def test_caso_minimo_7_profundidad_3_se_repliega(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        resultado = evaluar_adversarial(escenario, profundidad=3)
        self.assertEqual(resultado["accion"], (0, (1, 1)),
                          f"esperado: (0, (1, 1)); obtenido: {resultado['accion']}")
        self.assertEqual(resultado["metricas"]["valor_obtenido"], -4800.0,
                          f"esperado: -4800.0; obtenido: {resultado['metricas']['valor_obtenido']}")

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

    def test_3vs3_usa_todas_las_unidades_del_escenario(self):
        escenario = cargar_escenario(ruta_config("mapa_3v3.json"))
        resultado = evaluar_adversarial(escenario, profundidad=2)
        self.assertEqual(len(resultado["unidades_a"]), 3)
        self.assertEqual(len(resultado["unidades_b"]), 3)
        indice, destino = resultado["accion"]
        self.assertIn(indice, (0, 1, 2), f"esperado un indice de unidad A; obtenido: {indice}")
        self.assertTrue(resultado["metricas"]["accion_legal"],
                         resultado["metricas"]["detalle_legalidad"])
        self.assertTrue(resultado["nombre_unidad"].startswith("A"))


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

    def test_empate_por_limite_de_turnos_termina_en_empate_al_alcanzar_el_limite(self):
        import main as modulo_main
        escenario = cargar_escenario(ruta_config("mapa_partida.json"))
        with patch.object(modulo_main, "MAX_TURNOS", 5):
            partida = iniciar_partida(escenario)
            for _ in range(5):
                jugar_turno(partida)
            self.assertTrue(partida.terminada)
            self.assertIsNone(partida.ganador,
                               f"esperado empate (None); obtenido: {partida.ganador}")
            self.assertEqual(partida.turno_num - 1, 5,
                              f"esperado: 5 turnos; obtenido: {partida.turno_num - 1}")
            with self.assertRaises(ErrorControlador):
                jugar_turno(partida)

    def test_partida_3vs3_usa_todas_las_unidades_y_termina(self):
        escenario = cargar_escenario(ruta_config("mapa_3v3.json"))
        partida = iniciar_partida(escenario, profundidad=2)
        self.assertEqual(len(partida.unidades_a), 3)
        self.assertEqual(len(partida.unidades_b), 3)
        ids_validos = {u.id for u in partida.unidades_a + partida.unidades_b}

        turnos = 0
        while not partida.terminada and turnos < 100:
            fila = jugar_turno(partida)
            if "mensaje" not in fila:
                self.assertIn(fila["unidad"], ids_validos,
                               f"unidad desconocida en la fila: {fila['unidad']!r}")
            turnos += 1

        self.assertTrue(partida.terminada)
        self.assertIn(partida.ganador, ("A", "B", None),
                       f"ganador debe ser 'A', 'B' o None; obtenido: {partida.ganador!r}")
