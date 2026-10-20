"""Utilidades comunes de las pruebas: el escenario oficial como punto de partida."""
import copy
import os
import unittest

from src.scenario.loader import leer_json

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_OFICIAL = os.path.join(RAIZ, "config", "mapa_ejemplo.json")


def escenario_oficial():
    """Copia nueva del escenario de la pág. 6 del enunciado (diccionario crudo)."""
    return copy.deepcopy(leer_json(RUTA_OFICIAL))


class PruebaConEscenario(unittest.TestCase):
    def assertUnSoloError(self, errores, fragmento):
        """La validación dio exactamente un error y contiene el fragmento."""
        self.assertEqual(len(errores), 1, f"se esperaba 1 error, hubo: {errores}")
        self.assertIn(fragmento, errores[0])

    def assertHayError(self, errores, fragmento):
        """Alguno de los errores contiene el fragmento."""
        self.assertTrue(
            any(fragmento in e for e in errores),
            f"no hay error con {fragmento!r} en: {errores}",
        )
