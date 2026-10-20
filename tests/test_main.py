"""Selección del algoritmo en tiempo de ejecución: banderas, menú y despacho de main.

Purpose:            cubrir la regla "el usuario (no el JSON) elige con qué
                    algoritmo se visualiza y se juega": normalización de
                    nombres (incluidos alias), menú interactivo, despacho con
                    parámetros explícitos y la interfaz de línea de comandos de
                    main.py ejecutada como la usaría el usuario.
Preconditions:      main.py está en la raíz del proyecto y los escenarios de
                    config/ pasan el validador.
Postconditions:     cada prueba falla mostrando el esperado y el obtenido; no
                    modifica archivos.
Complexity:         la de los algoritmos que ejercita (mapas 4x4 y 5x5) más
                    los subprocesos de la CLI.
AI usage:           Yes
AI intervention:    la IA escribió las pruebas y esta documentación.
Student validation: Validado por el equipo ejecutando la suite completa.
"""

import os
import subprocess
import sys
import unittest

import main as modulo_main
from src.game.navegacion import ProblemaNavegacion
from src.scenario.loader import cargar_escenario

from tests.base import RAIZ


def ruta_config(nombre):
    return os.path.join(RAIZ, "config", nombre)


def _respuestas(*valores):
    """Fake de input() para los menús: entrega los valores dados, en orden."""
    pendientes = iter(valores)
    return lambda _indicacion="": next(pendientes)


class TestNormalizacionDeAlgoritmos(unittest.TestCase):

    def test_alias_de_busqueda(self):
        for entrada, esperado in (("BFS", "BFS"), ("bfs", "BFS"), ("A*", "A_ESTRELLA"),
                                  ("astar", "A_ESTRELLA"), ("a estrella", "A_ESTRELLA"),
                                  ("BEAM_SEARCH", "BEAM")):
            with self.subTest(entrada=entrada):
                self.assertEqual(modulo_main.normalizar_algoritmo_busqueda(entrada), esperado,
                                 f"esperado: {esperado}; entrada: {entrada!r}")

    def test_algoritmo_de_busqueda_desconocido(self):
        with self.assertRaises(ValueError):
            modulo_main.normalizar_algoritmo_busqueda("MAGIA")

    def test_alias_adversarial(self):
        self.assertFalse(modulo_main.normalizar_algoritmo_adversarial("MINIMAX"))
        self.assertFalse(modulo_main.normalizar_algoritmo_adversarial("minimax_puro"))
        self.assertTrue(modulo_main.normalizar_algoritmo_adversarial("ALFA_BETA"))
        self.assertTrue(modulo_main.normalizar_algoritmo_adversarial("alfa-beta"))

    def test_algoritmo_adversarial_desconocido(self):
        with self.assertRaises(ValueError):
            modulo_main.normalizar_algoritmo_adversarial("BFS")


class TestResolverBusqueda(unittest.TestCase):

    def setUp(self):
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        prueba = escenario.prueba
        unidad = next(u for u in escenario.unidades if u.id == prueba["unidad_inicio"])
        objetivo = (prueba["objetivo"]["fila"], prueba["objetivo"]["columna"])
        self.problema = ProblemaNavegacion(escenario.tablero, unidad.posicion, objetivo)

    def test_cada_algoritmo_devuelve_su_resultado(self):
        for algoritmo, esperado in (("BFS", "BFS"), ("DFS", "DFS"), ("UCS", "UCS"),
                                    ("A*", "A_ESTRELLA"), ("BEAM", "BEAM")):
            with self.subTest(algoritmo=algoritmo):
                resultado = modulo_main.resolver_busqueda(self.problema, algoritmo, "distancia_bfs", 2)
                self.assertEqual(resultado.algoritmo, esperado,
                                 f"esperado: {esperado}; obtenido: {resultado.algoritmo}")
                self.assertTrue(resultado.exito, f"{algoritmo} debería encontrar solución")

    def test_beam_respeta_k(self):
        resultado = modulo_main.resolver_busqueda(self.problema, "BEAM", "manhattan", 3)
        self.assertEqual(resultado.k, 3, f"esperado k=3; obtenido k={resultado.k}")

    def test_algoritmo_desconocido_lanza_error(self):
        with self.assertRaises(ValueError):
            modulo_main.resolver_busqueda(self.problema, "MAGIA")


class TestMenuInteractivo(unittest.TestCase):

    def test_menu_busqueda_por_numero(self):
        elegido = modulo_main._elegir_busqueda_interactiva({"algoritmo": "A*"}, entrada=_respuestas("2"))
        self.assertEqual(elegido, "DFS", f"esperado DFS (opción 2); obtenido: {elegido}")

    def test_menu_busqueda_enter_usa_la_sugerencia_del_json(self):
        elegido = modulo_main._elegir_busqueda_interactiva({"algoritmo": "BEAM"}, entrada=_respuestas(""))
        self.assertEqual(elegido, "BEAM", f"esperado la sugerencia del JSON; obtenido: {elegido}")

    def test_menu_busqueda_reintenta_con_opcion_invalida(self):
        elegido = modulo_main._elegir_busqueda_interactiva({}, entrada=_respuestas("9", "1"))
        self.assertEqual(elegido, "BFS", f"esperado BFS tras reintento; obtenido: {elegido}")

    def test_menu_heuristica_por_numero(self):
        elegida = modulo_main._elegir_heuristica_interactiva(
            {"heuristica": "manhattan"}, entrada=_respuestas("3"))
        self.assertEqual(elegida, "distancia_bfs",
                         f"esperado distancia_bfs (opción 3); obtenido: {elegida}")

    def test_menu_heuristica_enter_usa_la_sugerencia_del_json(self):
        elegida = modulo_main._elegir_heuristica_interactiva(
            {"heuristica": "distancia_bfs"}, entrada=_respuestas(""))
        self.assertEqual(elegida, "distancia_bfs",
                         f"esperado la sugerencia del JSON; obtenido: {elegida}")

    def test_menu_heuristica_con_json_invalido_usa_manhattan(self):
        elegida = modulo_main._elegir_heuristica_interactiva(
            {"heuristica": "heuristica_magica"}, entrada=_respuestas(""))
        self.assertEqual(elegida, "manhattan",
                         f"esperado manhattan ante una sugerencia inválida; obtenido: {elegida}")

    def test_menu_heuristica_reintenta_con_opcion_invalida(self):
        elegida = modulo_main._elegir_heuristica_interactiva({}, entrada=_respuestas("9", "2"))
        self.assertEqual(elegida, "manhattan_pasos",
                         f"esperado manhattan_pasos tras reintento; obtenido: {elegida}")

    def test_menu_k_por_numero(self):
        elegido = modulo_main._elegir_k_interactivo({}, entrada=_respuestas("5"))
        self.assertEqual(elegido, 5, f"esperado k=5; obtenido: {elegido}")

    def test_menu_k_enter_usa_la_sugerencia_del_json(self):
        elegido = modulo_main._elegir_k_interactivo({"k": 4}, entrada=_respuestas(""))
        self.assertEqual(elegido, 4, f"esperado la sugerencia del JSON; obtenido: {elegido}")

    def test_menu_k_reintenta_con_entradas_invalidas(self):
        elegido = modulo_main._elegir_k_interactivo({"k": 0}, entrada=_respuestas("0", "x", "3"))
        self.assertEqual(elegido, 3, f"esperado k=3 tras reintentos; obtenido: {elegido}")

    def test_menu_adversarial_algoritmo_y_profundidad(self):
        usar_poda, profundidad = modulo_main._elegir_adversarial_interactiva(
            {"usar_poda": True}, 3, entrada=_respuestas("1", "5"))
        self.assertFalse(usar_poda, "esperado Minimax puro (opción 1)")
        self.assertEqual(profundidad, 5, f"esperado profundidad 5; obtenido: {profundidad}")

    def test_menu_adversarial_enter_usa_sugerencias(self):
        usar_poda, profundidad = modulo_main._elegir_adversarial_interactiva(
            {"usar_poda": False}, 4, entrada=_respuestas("", ""))
        self.assertFalse(usar_poda, "esperado la sugerencia del JSON (sin poda)")
        self.assertEqual(profundidad, 4, f"esperado profundidad sugerida 4; obtenido: {profundidad}")

    def test_menu_adversarial_reintenta_profundidad_invalida(self):
        usar_poda, profundidad = modulo_main._elegir_adversarial_interactiva(
            {"usar_poda": True}, 3, entrada=_respuestas("2", "x", "2"))
        self.assertTrue(usar_poda, "esperado alfa-beta (opción 2)")
        self.assertEqual(profundidad, 2, f"esperado profundidad 2; obtenido: {profundidad}")


class TestCLI(unittest.TestCase):
    """Ejecuta main.py como subproceso, igual que lo haría el usuario."""

    def _ejecutar(self, *argumentos):
        return subprocess.run(
            [sys.executable, "-B", "main.py", *argumentos],
            cwd=RAIZ, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
            input="",
        )

    def test_flag_de_algoritmo_manda_sobre_el_json(self):
        completado = self._ejecutar("config/caso_obstaculo.json", "--algoritmo", "BFS", "--no-preguntar")
        self.assertEqual(completado.returncode, 0, completado.stderr)
        self.assertIn("Algoritmo elegido: BFS", completado.stdout,
                      "esperado que la bandera --algoritmo gane a la sugerencia del JSON")
        self.assertIn("VÁLIDA", completado.stdout)
        self.assertNotIn("Elige el algoritmo", completado.stdout,
                         "con --no-preguntar no debe aparecer el menú")

    def test_alias_y_heuristica_por_flag(self):
        completado = self._ejecutar("config/caso_obstaculo.json", "--algoritmo", "A*",
                                    "--heuristica", "manhattan_pasos", "--no-preguntar")
        self.assertEqual(completado.returncode, 0, completado.stderr)
        self.assertIn("Algoritmo elegido: A_ESTRELLA (heurística: manhattan_pasos)", completado.stdout)

    def test_algoritmo_adversarial_y_profundidad_por_flag(self):
        completado = self._ejecutar("config/caso_adversarial.json", "--algoritmo", "MINIMAX",
                                    "--profundidad", "2", "--no-preguntar")
        self.assertEqual(completado.returncode, 0, completado.stderr)
        self.assertIn("Poda alfa-beta: no", completado.stdout)
        self.assertIn("Profundidad: 2", completado.stdout)

    def test_sin_flags_no_interactivo_usa_la_sugerencia_del_json(self):
        completado = self._ejecutar("config/caso_obstaculo.json")
        self.assertEqual(completado.returncode, 0, completado.stderr)
        self.assertIn("Algoritmo elegido: A_ESTRELLA (heurística: distancia_bfs)", completado.stdout)
        self.assertNotIn("Elige el algoritmo", completado.stdout,
                         "sin terminal interactiva no debe aparecer el menú")

    def test_algoritmo_invalido_muestra_error_claro(self):
        completado = self._ejecutar("config/caso_obstaculo.json", "--algoritmo", "MAGIA", "--no-preguntar")
        self.assertEqual(completado.returncode, 1)
        self.assertIn("desconocido", completado.stdout)
        self.assertIn("BFS", completado.stdout, "el mensaje debe listar los nombres válidos")


if __name__ == "__main__":
    unittest.main()
