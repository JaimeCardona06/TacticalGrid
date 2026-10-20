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
            import tkinter
            from src.ui.gui import CanvasEscenario
            cls.raiz = tkinter.Tk()
            cls.raiz.withdraw()
        except Exception as error:        # sin pantalla, sin tkinter, etc.
            raise unittest.SkipTest(f"no se puede abrir Tkinter: {error}")
        cls.CanvasEscenario = CanvasEscenario
        cls.tablero = cargar_escenario(os.path.join(RAIZ, "config", "mapa_ejemplo.json")).tablero

    @classmethod
    def tearDownClass(cls):
        cls.raiz.destroy()

    def dibujar(self, unidades, portador_id=None):
        canvas = self.CanvasEscenario(self.raiz)
        canvas.dibujar(self.tablero, unidades, "A", (2, 2), portador_id=portador_id)
        ovalos = [i for i in canvas.find_all() if canvas.type(i) == "oval"]
        return canvas, ovalos

    def cajas(self, canvas, ovalos):
        return [canvas.coords(i) for i in ovalos]

    def test_dos_fichas_en_la_misma_celda_se_dibujan_separadas(self):
        canvas, ovalos = self.dibujar([ficha("A1", (0, 0)), ficha("B1", (0, 0))])
        fichas = self.cajas(canvas, ovalos)[1:]          # el primer óvalo es el recurso
        self.assertEqual(len(fichas), 2)
        (a0, _, a1, _), (b0, _, b1, _) = fichas
        self.assertLessEqual(a1, b0 + 1e-6)               # una termina donde empieza la otra: no se tapan

    def test_el_portador_se_dibuja_al_final_y_con_contorno_grueso_aunque_no_sea_el_primero(self):
        canvas, ovalos = self.dibujar([ficha("A1", (0, 0)), ficha("B1", (0, 0)), ficha("B2", (0, 0))], portador_id="A1")
        fichas = ovalos[1:]
        self.assertEqual(float(canvas.itemcget(fichas[-1], "width")), 3.0)    # el último pintado es el portador
        self.assertTrue(all(float(canvas.itemcget(i, "width")) == 1.0 for i in fichas[:-1]))

    def test_una_ficha_sola_se_dibuja_igual_que_antes(self):
        canvas, ovalos = self.dibujar([ficha("A1", (1, 1))])
        x0, y0, x1, y1 = canvas.coords(ovalos[1])
        tam = min(32, 640 // self.tablero.columnas, 640 // self.tablero.filas)
        self.assertAlmostEqual(x1 - x0, 2 * 0.35 * tam)
        self.assertAlmostEqual((x0 + x1) / 2, 1 * tam + tam / 2)

    def test_acepta_un_generador_de_unidades(self):
        canvas, ovalos = self.dibujar(f for f in [ficha("A1", (0, 0)), ficha("B1", (0, 0))])
        self.assertEqual(len(ovalos), 3)


if __name__ == "__main__":
    unittest.main()
