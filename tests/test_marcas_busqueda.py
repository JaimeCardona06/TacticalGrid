"""
Purpose:
    Pruebas de las marcas de inicio/objetivo de la pestaña Búsqueda y del botón
    "Limpiar": el canvas debe marcar con "I" cian la unidad elegida y con "O"
    naranja el objetivo, mostrar solo esas marcas en la pestaña Búsqueda, y el
    botón Limpiar debe borrar el camino y el panel sin tocar las marcas.

AI usage:           Yes
AI intervention:    la IA escribió las marcas, el botón, estas pruebas y su documentación.
Student validation: Validado por el equipo abriendo la GUI con los escenarios de
                    config/ y ejecutando esta prueba
                    (python -m unittest tests.test_marcas_busqueda -v).
"""
import os
import unittest

from src.scenario.loader import cargar_escenario
from src.ui import colores
from tests.base import RAIZ
from tests.tk_soporte import raiz_compartida


class TestMarcasEnElCanvas(unittest.TestCase):
    """Dibuja de verdad en un CanvasEscenario y revisa las marcas y sus etiquetas."""

    @classmethod
    def setUpClass(cls):
        try:
            from src.ui import colores
            from src.ui.gui import CanvasEscenario
            cls.raiz = raiz_compartida()
        except unittest.SkipTest:
            raise
        except Exception as error:        # sin pantalla, sin tkinter, etc.
            raise unittest.SkipTest(f"no se puede abrir Tkinter: {error}")
        cls.CanvasEscenario = CanvasEscenario
        cls.colores = colores
        cls.escenario = cargar_escenario(os.path.join(RAIZ, "config", "caso_bfs_vs_ucs.json"))

    def dibujar(self, inicio=None, objetivo=None):
        canvas = self.CanvasEscenario(self.raiz)
        canvas.dibujar(
            self.escenario.tablero, self.escenario.unidades, self.escenario.turno,
            self.escenario.recurso, inicio=inicio, objetivo=objetivo)
        return canvas

    def textos(self, canvas, tag):
        return [canvas.itemcget(item, "text")
                for item in canvas.find_withtag(tag) if canvas.type(item) == "text"]

    def contornos(self, canvas, tag):
        return [canvas.itemcget(item, "outline")
                for item in canvas.find_withtag(tag) if canvas.type(item) == "rectangle"]

    def test_marca_inicio_y_objetivo_con_sus_colores_y_letras(self):
        canvas = self.dibujar(inicio=(0, 1), objetivo=(2, 4))
        self.assertIn("I", self.textos(canvas, "marca_inicio"))
        self.assertIn("O", self.textos(canvas, "marca_objetivo"))
        self.assertIn(self.colores.COLOR_INICIO, self.contornos(canvas, "marca_inicio"))
        self.assertIn(self.colores.COLOR_OBJETIVO, self.contornos(canvas, "marca_objetivo"))

    def test_sin_inicio_ni_objetivo_no_dibuja_marcas(self):
        canvas = self.dibujar()
        self.assertEqual(canvas.find_withtag("marca_inicio"), ())
        self.assertEqual(canvas.find_withtag("marca_objetivo"), ())

    def test_celdas_fuera_del_tablero_no_se_marcan(self):
        canvas = self.dibujar(inicio=(99, 99), objetivo=(-1, 0))
        self.assertEqual(canvas.find_withtag("marca_inicio"), ())
        self.assertEqual(canvas.find_withtag("marca_objetivo"), ())


class TestMarcasEnLaApp(unittest.TestCase):
    """Carga escenarios en la ventana real y prueba las marcas y el botón Limpiar."""

    @classmethod
    def setUpClass(cls):
        try:
            from src.ui.gui import AppTacticalGrid
            cls.app = AppTacticalGrid(raiz_compartida())
            cls.app.withdraw()
        except unittest.SkipTest:
            raise
        except Exception as error:        # sin pantalla, sin tkinter, etc.
            raise unittest.SkipTest(f"no se puede abrir Tkinter: {error}")

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.app.notebook.select(self.app.pestana_busqueda)
        self.app._cargar_escenario(os.path.join(RAIZ, "config", "caso_bfs_vs_ucs.json"))
        self.app._limpiar_busqueda()

    def test_al_cargar_usa_unidad_inicio_y_objetivo_del_json(self):
        self.assertEqual(self.app.combo_unidad.get(), "A1")
        self.assertEqual((self.app.spin_fila.get(), self.app.spin_columna.get()), ("2", "4"))
        self.assertTrue(self.app.canvas.find_withtag("marca_inicio"))
        self.assertTrue(self.app.canvas.find_withtag("marca_objetivo"))

    def test_limpiar_borra_camino_y_panel_pero_no_las_marcas(self):
        self.app._resolver_busqueda()
        self.assertIsNotNone(self.app._camino_resuelto)
        self.assertTrue(self.app.canvas.find_withtag("camino"))
        self.assertTrue(self.app.texto_busqueda.get("1.0", "end").strip())

        self.app._limpiar_busqueda()
        self.assertIsNone(self.app._camino_resuelto)
        self.assertEqual(self.app.canvas.find_withtag("camino"), ())
        self.assertEqual(self.app.texto_busqueda.get("1.0", "end").strip(), "")
        self.assertTrue(self.app.canvas.find_withtag("marca_inicio"))
        self.assertTrue(self.app.canvas.find_withtag("marca_objetivo"))

    def test_las_marcas_solo_se_ven_en_la_pestana_busqueda(self):
        self.app._resolver_busqueda()
        self.app.update()
        self.assertTrue(self.app.canvas.find_withtag("marca_inicio"))
        self.assertTrue(self.app.canvas.find_withtag("marca_objetivo"))
        self.assertTrue(self.app.canvas.find_withtag("camino"))

        self.app.notebook.select(self.app.pestana_adversarial)
        self.app.update()
        self.assertEqual(self.app.canvas.find_withtag("marca_inicio"), ())
        self.assertEqual(self.app.canvas.find_withtag("marca_objetivo"), ())
        self.assertEqual(self.app.canvas.find_withtag("camino"), ())

        self.app.notebook.select(self.app.pestana_partida)
        self.app.update()
        self.assertEqual(self.app.canvas.find_withtag("marca_inicio"), ())
        self.assertEqual(self.app.canvas.find_withtag("marca_objetivo"), ())
        self.assertEqual(self.app.canvas.find_withtag("camino"), ())
        self.assertEqual(self.app.canvas.find_withtag("celda_resaltada"), ())
        contornos = [self.app.canvas.itemcget(item, "outline")
                     for item in self.app.canvas.find_all()
                     if self.app.canvas.type(item) == "rectangle"]
        self.assertIn(colores.COLOR_BANDO["A"], contornos)
        self.assertIn(colores.COLOR_BANDO["B"], contornos)

        self.app.notebook.select(self.app.pestana_busqueda)
        self.app.update()
        self.assertTrue(self.app.canvas.find_withtag("marca_inicio"))
        self.assertTrue(self.app.canvas.find_withtag("marca_objetivo"))
        self.assertTrue(self.app.canvas.find_withtag("camino"))

        self.app.notebook.select(self.app.pestana_partida)
        self.app.update()
        self.app._reiniciar_partida()
        self.app.update()
        self.assertEqual(self.app.canvas.find_withtag("marca_inicio"), ())
        self.assertEqual(self.app.canvas.find_withtag("marca_objetivo"), ())
        self.assertEqual(self.app.canvas.find_withtag("camino"), ())
        self.assertEqual(self.app.canvas.find_withtag("celda_resaltada"), ())


if __name__ == "__main__":
    unittest.main()
