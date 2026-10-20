"""
Purpose:
    Pruebas de la disposición de fichas que comparten celda: la función pura
    controlador.disposicion_de_fichas (sin tkinter) y el dibujo real en un canvas de
    Tkinter (se omite si la máquina no tiene pantalla). Antes, las fichas de una misma
    celda se pintaban en el mismo punto y la última tapaba a las demás, incluido el
    portador del recurso.

AI usage:           Yes
AI intervention:    la IA escribió la función, estas pruebas y diagnosticó el problema.
Student validation: Validado por el equipo ejecutando este archivo
                    (python -m unittest tests.test_disposicion_fichas -v) y abriendo la
                    GUI con config/caso_intercepcion.json.
"""
import math
import os
import random
import unittest

from src.scenario.escenario import Unidad
from src.scenario.loader import cargar_escenario
from src.ui.controlador import OCUPACION_DE_RANURA, RADIO_FICHA_SOLA, disposicion_de_fichas
from tests.base import RAIZ
from tests.tk_soporte import raiz_compartida


def ficha(identificador, posicion):
    return Unidad(identificador, identificador[0], "estandar", posicion)


def circulos_se_solapan(a, b):
    (ax, ay, ar), (bx, by, br) = a, b
    return math.hypot(ax - bx, ay - by) < ar + br - 1e-9


class TestDisposicionDeFichas(unittest.TestCase):
    def test_una_ficha_sola_queda_centrada_como_antes(self):
        self.assertEqual(disposicion_de_fichas([ficha("A1", (3, 4))]), {"A1": (0.5, 0.5, RADIO_FICHA_SOLA)})

    def test_fichas_en_celdas_distintas_son_independientes(self):
        d = disposicion_de_fichas([ficha("A1", (0, 0)), ficha("B1", (0, 1)), ficha("A2", (5, 5))])
        self.assertTrue(all(v == (0.5, 0.5, RADIO_FICHA_SOLA) for v in d.values()))

    def test_dos_fichas_en_la_misma_celda_van_una_al_lado_de_la_otra(self):
        d = disposicion_de_fichas([ficha("A1", (2, 2)), ficha("B1", (2, 2))])
        (x1, y1, r1), (x2, y2, r2) = d["A1"], d["B1"]
        self.assertLess(x1, x2)                       # la primera a la izquierda, la segunda a la derecha
        self.assertEqual(y1, y2)
        self.assertEqual(r1, r2)
        self.assertAlmostEqual(r1, OCUPACION_DE_RANURA * 0.5)
        self.assertFalse(circulos_se_solapan(d["A1"], d["B1"]))

    def test_de_2_a_12_fichas_nunca_se_solapan_ni_se_salen_de_la_celda(self):
        for k in range(2, 13):
            with self.subTest(fichas=k):
                d = disposicion_de_fichas([ficha(f"A{i}", (1, 1)) for i in range(1, k + 1)])
                self.assertEqual(len(d), k)
                circulos = list(d.values())
                for cx, cy, r in circulos:
                    self.assertGreater(r, 0)
                    self.assertGreaterEqual(cx - r, 0)
                    self.assertLessEqual(cx + r, 1)
                    self.assertGreaterEqual(cy - r, 0)
                    self.assertLessEqual(cy + r, 1)
                for i in range(k):
                    for j in range(i + 1, k):
                        self.assertFalse(circulos_se_solapan(circulos[i], circulos[j]), (i, j))

    def test_el_orden_recibido_decide_la_ranura(self):
        a = disposicion_de_fichas([ficha("A1", (0, 0)), ficha("A2", (0, 0))])
        b = disposicion_de_fichas([ficha("A2", (0, 0)), ficha("A1", (0, 0))])
        self.assertEqual(a["A1"], b["A2"])
        self.assertEqual(a["A2"], b["A1"])

    def test_configuraciones_aleatorias(self):
        rng = random.Random(4)
        for _ in range(200):
            fichas = [ficha(f"{rng.choice('AB')}{i}", (rng.randrange(3), rng.randrange(3))) for i in range(rng.randint(1, 9))]
            d = disposicion_de_fichas(fichas)
            self.assertEqual(set(d), {f.id for f in fichas})
            por_celda = {}
            for f in fichas:
                por_celda.setdefault(f.posicion, []).append(d[f.id])
            for grupo in por_celda.values():
                for i in range(len(grupo)):
                    for j in range(i + 1, len(grupo)):
                        self.assertFalse(circulos_se_solapan(grupo[i], grupo[j]))

    def test_no_modifica_las_unidades_y_acepta_un_generador(self):
        fichas = [ficha("A1", (0, 0)), ficha("B1", (0, 0))]
        copia = list(fichas)
        disposicion_de_fichas(f for f in fichas)
        self.assertEqual(fichas, copia)


class TestDibujoEnElCanvas(unittest.TestCase):
    """Dibuja de verdad en un canvas de Tkinter y mira los círculos resultantes."""

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
        cls.color_recurso = colores.COLOR_RECURSO
        cls.tablero = cargar_escenario(os.path.join(RAIZ, "config", "mapa_ejemplo.json")).tablero

    def dibujar(self, unidades, portador_id=None, recurso_pos=(2, 2)):
        """Devuelve (canvas, óvalos de fichas en orden de dibujo, óvalos del recurso en orden de dibujo)."""
        canvas = self.CanvasEscenario(self.raiz)
        canvas.dibujar(self.tablero, unidades, "A", recurso_pos, portador_id=portador_id)
        ovalos = [i for i in canvas.find_all() if canvas.type(i) == "oval"]
        fichas = [i for i in ovalos if canvas.itemcget(i, "fill") != self.color_recurso]
        recursos = [i for i in ovalos if canvas.itemcget(i, "fill") == self.color_recurso]
        return canvas, fichas, recursos

    def centro(self, canvas, item):
        x0, y0, x1, y1 = canvas.coords(item)
        return (x0 + x1) / 2, (y0 + y1) / 2

    def test_dos_fichas_en_la_misma_celda_se_dibujan_separadas(self):
        canvas, fichas, _ = self.dibujar([ficha("A1", (0, 0)), ficha("B1", (0, 0))])
        self.assertEqual(len(fichas), 2)
        (a0, _, a1, _), (b0, _, b1, _) = [canvas.coords(i) for i in fichas]
        self.assertLessEqual(a1, b0 + 1e-6)               # una termina donde empieza la otra: no se tapan

    def test_el_portador_se_dibuja_al_final_y_con_contorno_grueso_aunque_no_sea_el_primero(self):
        canvas, fichas, _ = self.dibujar([ficha("A1", (0, 0)), ficha("B1", (0, 0)), ficha("B2", (0, 0))],
                                         portador_id="A1")
        self.assertEqual(float(canvas.itemcget(fichas[-1], "width")), 3.0)    # la última pintada es el portador
        self.assertTrue(all(float(canvas.itemcget(i, "width")) == 1.0 for i in fichas[:-1]))

    def test_una_ficha_sola_se_dibuja_igual_que_antes(self):
        canvas, fichas, _ = self.dibujar([ficha("A1", (1, 1))])
        x0, y0, x1, y1 = canvas.coords(fichas[0])
        tam = min(32, 640 // self.tablero.columnas, 640 // self.tablero.filas)
        self.assertAlmostEqual(x1 - x0, 2 * 0.35 * tam)
        self.assertAlmostEqual((x0 + x1) / 2, 1 * tam + tam / 2)

    def test_acepta_un_generador_de_unidades(self):
        canvas, fichas, recursos = self.dibujar(f for f in [ficha("A1", (0, 0)), ficha("B1", (0, 0))])
        self.assertEqual((len(fichas), len(recursos)), (2, 1))

    def test_recurso_libre_es_un_punto_en_el_centro_de_su_celda(self):
        canvas, fichas, recursos = self.dibujar([ficha("A1", (0, 0))], recurso_pos=(2, 2))
        self.assertEqual(len(recursos), 1)
        tam = min(32, 640 // self.tablero.columnas, 640 // self.tablero.filas)
        cx, cy = self.centro(canvas, recursos[0])
        self.assertAlmostEqual(cx, 2 * tam + tam / 2)
        self.assertAlmostEqual(cy, 2 * tam + tam / 2)

    def test_recurso_transportado_se_ve_pegado_al_portador_y_por_encima(self):
        """Antes se pintaba DEBAJO de la ficha que lo lleva y no se veía dónde estaba."""
        canvas, fichas, recursos = self.dibujar([ficha("A1", (1, 1)), ficha("B1", (3, 3))],
                                                portador_id="A1", recurso_pos=(1, 1))
        self.assertEqual(len(recursos), 1)
        todos = [i for i in canvas.find_all() if canvas.type(i) == "oval"]
        self.assertEqual(todos[-1], recursos[0])                          # es lo último que se pinta
        tam = min(32, 640 // self.tablero.columnas, 640 // self.tablero.filas)
        portador = next(i for i in fichas if float(canvas.itemcget(i, "width")) == 3.0)
        px, py = self.centro(canvas, portador)
        mx, my = self.centro(canvas, recursos[0])
        self.assertLess(math.hypot(mx - px, my - py), 0.35 * tam * 1.4)   # pegado a la ficha del portador
        self.assertTrue(1 * tam <= mx <= 2 * tam and 1 * tam <= my <= 2 * tam)   # y dentro de su celda

    def test_recurso_transportado_con_fichas_apiladas_queda_en_la_ficha_del_portador(self):
        canvas, fichas, recursos = self.dibujar([ficha("A1", (1, 1)), ficha("B1", (1, 1))],
                                                portador_id="B1", recurso_pos=(1, 1))
        portador = next(i for i in fichas if float(canvas.itemcget(i, "width")) == 3.0)
        otra = next(i for i in fichas if i != portador)
        mx, my = self.centro(canvas, recursos[0])
        self.assertLess(math.hypot(mx - self.centro(canvas, portador)[0], my - self.centro(canvas, portador)[1]),
                        math.hypot(mx - self.centro(canvas, otra)[0], my - self.centro(canvas, otra)[1]))

    def test_el_recurso_siempre_esta_en_el_canvas_durante_la_partida_visual(self):
        """En caso_robo_visual el recurso se ve en cada turno y, tras el robo, junto a A1."""
        from src.ui.gui import AppTacticalGrid
        app = AppTacticalGrid(raiz_compartida())
        app.withdraw()
        try:
            app._cargar_escenario(os.path.join(RAIZ, "config", "caso_robo_visual.json"))
            app._reiniciar_partida()
            turno_robo = None
            while not app._partida.terminada:
                app._siguiente_turno()
                canvas = app.canvas
                ovalos = [i for i in canvas.find_all() if canvas.type(i) == "oval"]
                recursos = [i for i in ovalos if canvas.itemcget(i, "fill") == self.color_recurso]
                self.assertEqual(len(recursos), 1, f"turno {app._partida.turno_num - 1}")
                estado = app._partida.estado
                if estado.portador == ("A", 0) and turno_robo is None:
                    turno_robo = app._partida.turno_num - 1
                    tam = min(32, 640 // self.tablero.columnas, 640 // self.tablero.filas)
                    fila, columna = estado.recurso_pos
                    mx, my = self.centro(canvas, recursos[0])
                    self.assertTrue(columna * tam <= mx <= (columna + 1) * tam and fila * tam <= my <= (fila + 1) * tam)
            self.assertEqual(turno_robo, 5)
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
