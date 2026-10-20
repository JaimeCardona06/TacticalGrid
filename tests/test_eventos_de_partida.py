"""
Purpose:
    Pruebas de los eventos de partida (recoger, robar, ganar), del modo de desempate
    "ninguna" y del escenario config/caso_robo_visual.json, que permite VER en la consola
    y en la GUI qué aporta el desempate y cómo se produce un robo.

AI usage:           Yes
AI intervention:    la IA diseñó el escenario, la función describir_evento y estas pruebas.
Student validation: Validado por el equipo ejecutando este archivo
                    (python -m unittest tests.test_eventos_de_partida -v) y abriendo
                    config/caso_robo_visual.json en la GUI cambiando estrategia_robo.
"""
import contextlib
import io
import os
import unittest

import main
from src.adversarial.desempate import INTERCEPCION, PERSECUCION, SIN_DESEMPATE
from src.models.state import EstadoJuego
from src.scenario.escenario import Unidad
from src.scenario.loader import cargar_escenario
from src.ui.controlador import iniciar_partida, jugar_turno
from tests.base import RAIZ

RUTA_VISUAL = os.path.join(RAIZ, "config", "caso_robo_visual.json")
A = [Unidad("A1", "A", "estandar", (0, 0)), Unidad("A2", "A", "estandar", (0, 1))]
B = [Unidad("B1", "B", "estandar", (3, 3)), Unidad("B2", "B", "estandar", (3, 2))]


def estado(portador, recurso=(1, 1), turno="A"):
    return EstadoJuego([(0, 0), (0, 1)], [(3, 3), (3, 2)], portador, turno, recurso)


class TestDescribirEvento(unittest.TestCase):
    def describir(self, antes, despues, base=False):
        return main.describir_evento(antes, despues, A, B, base)

    def test_recoger_el_recurso_libre(self):
        self.assertEqual(self.describir(estado(None), estado(("A", 1))), "RECOGE el recurso (A2)")
        self.assertEqual(self.describir(estado(None), estado(("B", 0))), "RECOGE el recurso (B1)")

    def test_robo_cuando_el_portador_cambia_de_bando(self):
        self.assertEqual(self.describir(estado(("B", 1)), estado(("A", 0))), "ROBO: A1 le quita el recurso a B2")
        self.assertEqual(self.describir(estado(("A", 0)), estado(("B", 1))), "ROBO: B2 le quita el recurso a A1")

    def test_llegar_a_la_base_gana(self):
        self.assertEqual(self.describir(estado(("A", 0)), estado(("A", 0)), base=True),
                         "GANA: A1 deja el recurso en su base")

    def test_sin_evento_cuando_nada_cambia_de_manos(self):
        self.assertEqual(self.describir(estado(None), estado(None)), "")                 # recurso libre
        self.assertEqual(self.describir(estado(("A", 0)), estado(("A", 0))), "")          # el portador solo avanza

    def test_no_modifica_los_estados(self):
        antes, despues = estado(("B", 1)), estado(("A", 0))
        self.describir(antes, despues)
        self.assertEqual((antes.portador, despues.portador), (("B", 1), ("A", 0)))


class TestModoNinguna(unittest.TestCase):
    def test_se_acepta_en_el_json_y_apaga_el_desempate(self):
        self.assertEqual(main._estrategia_de_robo({"estrategia_robo": SIN_DESEMPATE}), SIN_DESEMPATE)
        agentes = main._crear_agentes(3, True, None, SIN_DESEMPATE)
        self.assertTrue(all(not a.desempatar_por_avance for a in agentes.values()))

    def test_las_otras_estrategias_siguen_activando_el_desempate(self):
        for estrategia in (PERSECUCION, INTERCEPCION):
            agentes = main._crear_agentes(3, True, None, estrategia)
            self.assertTrue(all(a.desempatar_por_avance and a.estrategia_robo == estrategia for a in agentes.values()))

    def test_un_valor_invalido_avisa_e_incluye_las_tres_opciones(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            self.assertEqual(main._estrategia_de_robo({"estrategia_robo": "rara"}), PERSECUCION)
        for opcion in (PERSECUCION, INTERCEPCION, SIN_DESEMPATE):
            self.assertIn(opcion, salida.getvalue())


class TestCasoRoboVisual(unittest.TestCase):
    """Un solo JSON, tres comportamientos distintos según prueba.estrategia_robo."""

    def jugar(self, estrategia):
        escenario = cargar_escenario(RUTA_VISUAL)
        escenario.prueba["estrategia_robo"] = estrategia
        partida = iniciar_partida(escenario, profundidad=3)
        filas = []
        while not partida.terminada:
            filas.append(jugar_turno(partida))
        eventos = [(f["turno"], f["evento"]) for f in filas if f["evento"]]
        return partida, filas, eventos

    def test_el_json_trae_la_persecucion_declarada(self):
        self.assertEqual(cargar_escenario(RUTA_VISUAL).prueba["estrategia_robo"], PERSECUCION)

    def test_sin_desempate_a_deambula_y_gana_b_sin_robo(self):
        partida, filas, eventos = self.jugar(SIN_DESEMPATE)
        self.assertEqual((partida.ganador, partida.turno_num - 1), ("B", 14))
        self.assertEqual(eventos, [(14, "GANA: B1 deja el recurso en su base")])
        self.assertTrue(all(f["acciones_empatadas"] is None for f in filas))      # el desempate está apagado
        unidades_a = [f["unidad"] for f in filas if f["bando"] == "A"]
        self.assertEqual(set(unidades_a), {"A1"})                                  # siempre la primera unidad del orden

    def test_con_persecucion_a1_roba_en_el_turno_5_y_gana_a(self):
        partida, filas, eventos = self.jugar(PERSECUCION)
        self.assertEqual((partida.ganador, partida.turno_num - 1), ("A", 19))
        self.assertEqual(eventos, [(5, "ROBO: A1 le quita el recurso a B1"), (19, "GANA: A1 deja el recurso en su base")])
        self.assertTrue(any(f["acciones_empatadas"] and f["acciones_empatadas"] > 1 for f in filas))

    def test_con_intercepcion_a1_roba_mas_tarde_y_tambien_gana_a(self):
        partida, _, eventos = self.jugar(INTERCEPCION)
        self.assertEqual((partida.ganador, partida.turno_num - 1), ("A", 27))
        self.assertEqual(eventos, [(9, "ROBO: A1 le quita el recurso a B1"), (27, "GANA: A1 deja el recurso en su base")])

    def test_la_consola_marca_el_robo_y_el_numero_de_acciones_empatadas(self):
        escenario = cargar_escenario(RUTA_VISUAL)
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            main.ejecutar_partida(escenario)
        texto = salida.getvalue()
        self.assertIn(">>> ROBO: A1 le quita el recurso a B1", texto)
        self.assertIn(">>> GANA: A1 deja el recurso en su base", texto)
        self.assertIn(" | Emp. ", texto)

        escenario.prueba["estrategia_robo"] = SIN_DESEMPATE
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            main.ejecutar_partida(escenario)
        self.assertNotIn(" | Emp. ", salida.getvalue())
        self.assertNotIn("ROBO", salida.getvalue())


class TestTablaDeLaGUI(unittest.TestCase):
    """La tabla de la GUI real muestra el evento y resalta la fila del robo."""

    @classmethod
    def setUpClass(cls):
        try:
            from src.ui.gui import AppTacticalGrid
            cls.app = AppTacticalGrid()
            cls.app.withdraw()
        except Exception as error:
            raise unittest.SkipTest(f"no se puede abrir Tkinter: {error}")

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def test_el_robo_aparece_en_la_tabla_con_su_color(self):
        app = self.app
        app._cargar_escenario(RUTA_VISUAL)
        app._reiniciar_partida()
        while app._partida is not None and not app._partida.terminada:
            app._siguiente_turno()
        tabla = app.tabla_partida
        self.assertIn("evento", tabla["columns"])
        self.assertIn("empatadas", tabla["columns"])
        filas = tabla.get_children()
        etiquetas = {tabla.item(i, "tags")[0]: tabla.item(i, "values")[tabla["columns"].index("evento")]
                     for i in filas if tabla.item(i, "tags")}
        self.assertEqual(etiquetas["robo"], "ROBO: A1 le quita el recurso a B1")
        self.assertEqual(etiquetas["gana"], "GANA: A1 deja el recurso en su base")
        self.assertEqual(len(filas), 19)


if __name__ == "__main__":
    unittest.main()
