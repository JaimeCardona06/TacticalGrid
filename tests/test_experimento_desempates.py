"""
Purpose:
    Prueba de humo del experimento experimentos/comparar_desempates.py: que el script se
    pueda ejecutar, que todos los modos jueguen los mismos escenarios, que sea reproducible
    con la misma semilla y que no haya acciones ilegales ni excepciones.

AI usage:           Yes
AI intervention:    la IA escribió estas pruebas.
Student validation: Validado por el equipo ejecutando este archivo y el script del experimento.
"""
import contextlib
import io
import unittest

import random

from experimentos.comparar_desempates import MODOS, comparar, escenario_aleatorio, main


class TestExperimentoDesempates(unittest.TestCase):
    def test_los_escenarios_aleatorios_son_validos_para_el_cargador(self):
        import json
        import os
        import tempfile
        from src.scenario.loader import cargar_escenario
        rng = random.Random(1)
        ruta = os.path.join(tempfile.mkdtemp(), "e.json")
        generados = 0
        for _ in range(60):
            datos = escenario_aleatorio(rng)
            if datos is None:
                continue
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo)
            cargar_escenario(ruta)          # no debe lanzar EscenarioInvalido
            generados += 1
        self.assertGreater(generados, 40)

    def test_todos_los_modos_juegan_los_mismos_escenarios_sin_fallos(self):
        resultados = comparar(profundidad=2, escenarios=6, semilla=5)
        self.assertEqual(set(resultados), set(MODOS))
        for modo, e in resultados.items():
            self.assertEqual(e["partidas"], 6, modo)
            self.assertEqual(e["empates"] + e["decisivas"] + e["excepciones"], 6, modo)
            self.assertEqual(e["ilegales"], 0, modo)
            self.assertEqual(e["excepciones"], 0, modo)

    def test_es_reproducible_con_la_misma_semilla(self):
        a = comparar(profundidad=2, escenarios=4, semilla=11)
        b = comparar(profundidad=2, escenarios=4, semilla=11)
        self.assertEqual(a, b)

    def test_main_imprime_una_fila_por_modo(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            main(["--profundidad", "2", "--escenarios", "2", "--semilla", "3"])
        texto = salida.getvalue()
        for modo in MODOS:
            self.assertIn(modo, texto)


if __name__ == "__main__":
    unittest.main()
