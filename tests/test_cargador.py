"""Pruebas de lectura y carga "todo o nada": leer_json, normalizar_bando, cargar_escenario."""
import json
import os
import tempfile
import unittest

from src.scenario.bandos import normalizar_bando
from src.scenario.loader import (PROFUNDIDAD_POR_DEFECTO, TIPO_UNIDAD_POR_DEFECTO,
                                 ErrorDeCarga, EscenarioInvalido, cargar_escenario,
                                 leer_json)
from tests.base import RUTA_OFICIAL, escenario_oficial


class ConArchivosTemporales(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def ruta(self, nombre):
        return os.path.join(self._dir.name, nombre)

    def escribir_json(self, datos, nombre="escenario.json"):
        with open(self.ruta(nombre), "w", encoding="utf-8") as f:
            json.dump(datos, f)
        return self.ruta(nombre)


class TestLeerJson(ConArchivosTemporales):
    def test_lee_el_escenario_oficial(self):
        datos = leer_json(RUTA_OFICIAL)
        self.assertEqual(datos["mapa"], {"filas": 4, "columnas": 4})

    def test_archivo_inexistente(self):
        with self.assertRaises(ErrorDeCarga) as ctx:
            leer_json(self.ruta("no_existe.json"))
        self.assertIn("No existe el archivo", str(ctx.exception))

    def test_json_mal_formado_indica_linea_y_columna(self):
        with open(self.ruta("roto.json"), "w", encoding="utf-8") as f:
            f.write('{"a": 1,}')
        with self.assertRaises(ErrorDeCarga) as ctx:
            leer_json(self.ruta("roto.json"))
        self.assertIn("línea 1", str(ctx.exception))
        self.assertIn("columna", str(ctx.exception))


class TestNormalizarBando(unittest.TestCase):
    def test_valores_aceptados(self):
        self.assertEqual([normalizar_bando(v) for v in ("A", "a", "B", "b")], ["A", "A", "B", "B"])

    def test_valores_rechazados(self):
        for valor in (" A", "A ", "C", "", "AB", 1, 0, True, False, None, ["A"], {"A": 1}):
            with self.subTest(valor=valor):
                self.assertIsNone(normalizar_bando(valor))


class TestCargarEscenario(ConArchivosTemporales):
    def test_carga_el_escenario_oficial_completo(self):
        e = cargar_escenario(RUTA_OFICIAL)
        t = e.tablero
        self.assertEqual((t.filas, t.columnas), (4, 4))
        self.assertEqual((t.base_a, t.base_b, e.recurso), ((0, 0), (3, 3), (2, 2)))
        self.assertEqual((e.turno, e.portador_recurso, e.profundidad_maxima_minimax), ("A", None, 4))
        self.assertEqual([(u.id, u.bando, u.tipo, u.posicion) for u in e.unidades],
                         [("A1", "A", "estandar", (0, 1)), ("A2", "A", "estandar", (1, 0)),
                          ("B1", "B", "estandar", (3, 2)), ("B2", "B", "estandar", (2, 3))])
        self.assertEqual(e.prueba["modo"], "busqueda")
        self.assertEqual(e.prueba["objetivo"], {"fila": 3, "columna": 2})

    def test_bando_y_turno_en_minuscula_se_normalizan(self):
        d = escenario_oficial()
        d["turno"] = "b"
        d["unidades"][0]["bando"] = "a"
        e = cargar_escenario(self.escribir_json(d))
        self.assertEqual(e.turno, "B")
        self.assertEqual(e.unidades[0].bando, "A")

    def test_valores_por_defecto(self):
        d = escenario_oficial()
        del d["juego"]["profundidad_maxima_minimax"]
        del d["prueba"]
        del d["unidades"][0]["tipo"]
        e = cargar_escenario(self.escribir_json(d))
        self.assertEqual(e.profundidad_maxima_minimax, PROFUNDIDAD_POR_DEFECTO)
        self.assertIsNone(e.prueba)
        self.assertEqual(e.unidades[0].tipo, TIPO_UNIDAD_POR_DEFECTO)

    def test_profundidad_null_usa_el_valor_por_defecto(self):
        d = escenario_oficial()
        d["juego"]["profundidad_maxima_minimax"] = None
        self.assertEqual(cargar_escenario(self.escribir_json(d)).profundidad_maxima_minimax,
                         PROFUNDIDAD_POR_DEFECTO)

    def test_portador_se_conserva(self):
        d = escenario_oficial()
        d["juego"]["portador_recurso"] = "B1"
        self.assertEqual(cargar_escenario(self.escribir_json(d)).portador_recurso, "B1")

    def test_escenario_invalido_lanza_con_todos_los_errores(self):
        d = escenario_oficial()
        d["recurso"]["fila"] = 9
        d["unidades"][1].update(fila=1, columna=1)
        d["turno"] = "X"
        with self.assertRaises(EscenarioInvalido) as ctx:
            cargar_escenario(self.escribir_json(d))
        self.assertEqual(len(ctx.exception.errores), 3)

    def test_archivo_inexistente_o_roto_tambien_es_escenario_invalido(self):
        with self.assertRaises(EscenarioInvalido) as ctx:
            cargar_escenario(self.ruta("nada.json"))
        self.assertEqual(len(ctx.exception.errores), 1)
        with open(self.ruta("roto.json"), "w", encoding="utf-8") as f:
            f.write("{")
        with self.assertRaises(EscenarioInvalido):
            cargar_escenario(self.ruta("roto.json"))

    def test_todo_o_nada_el_escenario_actual_no_se_pierde(self):
        """Patrón de uso: solo se reemplaza el escenario actual si la carga no lanza."""
        actual = cargar_escenario(RUTA_OFICIAL)
        d = escenario_oficial()
        d["terreno"][0][0] = "lava"
        try:
            actual = cargar_escenario(self.escribir_json(d))
        except EscenarioInvalido:
            pass
        self.assertEqual(actual.tablero.terreno[0][0], "camino")

    def test_el_escenario_es_independiente_del_archivo_y_de_otras_cargas(self):
        e1 = cargar_escenario(RUTA_OFICIAL)
        e1.tablero.terreno[0][0] = "muro"
        e1.prueba["modo"] = "otro"
        e2 = cargar_escenario(RUTA_OFICIAL)
        self.assertEqual(e2.tablero.terreno[0][0], "camino")
        self.assertEqual(e2.prueba["modo"], "busqueda")

    def test_las_posiciones_son_tuplas(self):
        e = cargar_escenario(RUTA_OFICIAL)
        self.assertIsInstance(e.recurso, tuple)
        self.assertIsInstance(e.tablero.base_a, tuple)
        self.assertIsInstance(e.unidades[0].posicion, tuple)

    def test_mapa_no_cuadrado_carga_completo(self):
        d = escenario_oficial()
        d["mapa"] = {"filas": 2, "columnas": 3}
        d["terreno"] = [["camino"] * 3, ["pasto"] * 3]
        d["bases"] = {"A": {"fila": 0, "columna": 0}, "B": {"fila": 1, "columna": 2}}
        d["recurso"] = {"fila": 1, "columna": 1}
        d["unidades"] = [{"id": "A1", "bando": "A", "tipo": "estandar", "fila": 0, "columna": 1}]
        d["juego"]["portador_recurso"] = "A1"
        e = cargar_escenario(self.escribir_json(d))
        self.assertEqual((e.tablero.filas, e.tablero.columnas), (2, 3))
        self.assertEqual(e.tablero.vecinos((1, 1)), [(0, 1), (1, 2), (1, 0)])

    def test_cambiar_un_costo_en_el_json_cambia_el_tablero(self):
        d = escenario_oficial()
        d["tipos_terreno"]["pantano"]["costo"] = 15
        e = cargar_escenario(self.escribir_json(d))
        self.assertEqual(e.tablero.costo_entrar((2, 2)), 15)


if __name__ == "__main__":
    unittest.main()
