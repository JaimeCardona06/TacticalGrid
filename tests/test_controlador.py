import os
import unittest
from dataclasses import replace

from src.scenario.escenario import Unidad
from src.scenario.loader import cargar_escenario
from src.ui.controlador import (
    unidades_con_posiciones, portador_unidad_id, recurso_pos_inicial,
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
