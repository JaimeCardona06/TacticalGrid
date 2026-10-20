"""Pruebas del validador: una o más por cada regla del enunciado (pág. 7)."""
import copy
import random
import unittest

from src.scenario.validator import validar_escenario
from tests.base import PruebaConEscenario, escenario_oficial


class TestEscenarioValido(PruebaConEscenario):
    def test_escenario_oficial_es_valido(self):
        self.assertEqual(validar_escenario(escenario_oficial()), [])

    def test_mapa_no_cuadrado_es_valido(self):
        d = escenario_oficial()
        d["mapa"] = {"filas": 2, "columnas": 3}
        d["terreno"] = [["camino"] * 3, ["pasto"] * 3]
        d["bases"] = {"A": {"fila": 0, "columna": 0}, "B": {"fila": 1, "columna": 2}}
        d["recurso"] = {"fila": 1, "columna": 1}
        d["unidades"] = [{"id": "A1", "bando": "A", "tipo": "estandar", "fila": 0, "columna": 1}]
        self.assertEqual(validar_escenario(d), [])

    def test_no_exige_minimo_de_unidades_ni_de_tamano(self):
        d = escenario_oficial()
        d["unidades"] = []
        self.assertEqual(validar_escenario(d), [])

    def test_campos_extra_se_ignoran(self):
        d = escenario_oficial()
        d["campo_propio"] = {"x": 1}
        d["unidades"][0]["vida"] = 3
        self.assertEqual(validar_escenario(d), [])

    def test_sin_prueba_es_valido(self):
        d = escenario_oficial()
        del d["prueba"]
        self.assertEqual(validar_escenario(d), [])

    def test_portador_null_es_valido(self):
        d = escenario_oficial()
        d["juego"]["portador_recurso"] = None
        self.assertEqual(validar_escenario(d), [])


class TestRegla0CamposObligatorios(PruebaConEscenario):
    def test_falta_cada_campo_obligatorio(self):
        rutas = [("version",), ("mapa", "filas"), ("mapa", "columnas"), ("tipos_terreno",),
                 ("terreno",), ("bases", "A"), ("bases", "B"), ("recurso",), ("unidades",),
                 ("turno",), ("juego", "portador_recurso")]
        for ruta in rutas:
            with self.subTest(campo=".".join(ruta)):
                d = escenario_oficial()
                padre = d
                for k in ruta[:-1]:
                    padre = padre[k]
                del padre[ruta[-1]]
                self.assertUnSoloError(validar_escenario(d), f"'{'.'.join(ruta)}'")

    def test_raiz_que_no_es_objeto(self):
        self.assertUnSoloError(validar_escenario([1, 2]), "objeto JSON")

    def test_seccion_que_no_es_objeto(self):
        d = escenario_oficial()
        d["mapa"] = 5
        errores = validar_escenario(d)
        self.assertHayError(errores, "'mapa.filas'")
        self.assertHayError(errores, "'mapa.columnas'")


class TestRegla1Dimensiones(PruebaConEscenario):
    def test_filas_o_columnas_no_positivas_o_no_enteras(self):
        for campo in ("filas", "columnas"):
            for valor in (0, -2, "4", True, 4.0, None):
                with self.subTest(campo=campo, valor=valor):
                    d = escenario_oficial()
                    d["mapa"][campo] = valor
                    self.assertUnSoloError(validar_escenario(d), f"'mapa.{campo}' debe ser un entero positivo")

    def test_cantidad_de_filas_no_coincide(self):
        d = escenario_oficial()
        d["mapa"]["filas"] = 5
        self.assertUnSoloError(validar_escenario(d), "'terreno' tiene 4 filas pero mapa.filas es 5")

    def test_fila_corta_y_fila_larga(self):
        d = escenario_oficial()
        d["terreno"][2].pop()
        d["terreno"][1].append("pasto")
        errores = validar_escenario(d)
        self.assertEqual(len(errores), 2)
        self.assertHayError(errores, "La fila 2 de 'terreno' tiene 3 columnas")
        self.assertHayError(errores, "La fila 1 de 'terreno' tiene 5 columnas")

    def test_terreno_o_fila_que_no_son_listas(self):
        d = escenario_oficial()
        d["terreno"] = "hola"
        self.assertUnSoloError(validar_escenario(d), "'terreno' debe ser una lista")
        d = escenario_oficial()
        d["terreno"][0] = "camino"
        self.assertUnSoloError(validar_escenario(d), "La fila 0 de 'terreno' debe ser una lista")

    def test_dimensiones_rotas_cortan_las_demas_reglas(self):
        d = escenario_oficial()
        d["mapa"]["filas"] = 0
        d["recurso"]["fila"] = 99
        self.assertUnSoloError(validar_escenario(d), "'mapa.filas'")


class TestRegla2TerrenosExisten(PruebaConEscenario):
    def test_terreno_desconocido(self):
        d = escenario_oficial()
        d["terreno"][0][0] = "lava"
        self.assertUnSoloError(validar_escenario(d), "El terreno 'lava' no existe")

    def test_un_error_por_nombre_no_por_celda(self):
        d = escenario_oficial()
        for f in range(4):
            for c in range(4):
                d["terreno"][f][c] = "lava"
        d["terreno"][0][0] = "hielo"
        errores = validar_escenario(d)
        self.assertEqual(len(errores), 2)
        self.assertHayError(errores, "'hielo'")
        self.assertHayError(errores, "'lava' no existe en 'tipos_terreno' (aparece en 15 celdas")
        self.assertHayError(errores, "y 10 más")

    def test_singular_cuando_es_una_sola_celda(self):
        d = escenario_oficial()
        d["terreno"][0][0] = "lava"
        self.assertIn("1 celda:", validar_escenario(d)[0])

    def test_nombres_se_comparan_exactamente(self):
        d = escenario_oficial()
        d["terreno"][0][0] = "Camino"
        self.assertUnSoloError(validar_escenario(d), "'Camino'")

    def test_celdas_que_no_son_texto(self):
        d = escenario_oficial()
        d["terreno"][1][1] = 7
        d["terreno"][2][2] = None
        self.assertUnSoloError(validar_escenario(d), "2 celdas cuyo valor no es un nombre de terreno")

    def test_tipos_terreno_que_no_es_objeto(self):
        d = escenario_oficial()
        d["tipos_terreno"] = [1]
        self.assertUnSoloError(validar_escenario(d), "'tipos_terreno' debe ser un objeto")


class TestRegla3CostosPositivos(PruebaConEscenario):
    def test_costo_no_positivo_en_terreno_transitable(self):
        for valor in (0, -1, "1", True, None, float("inf"), float("nan")):
            with self.subTest(costo=valor):
                d = escenario_oficial()
                d["tipos_terreno"]["pantano"]["costo"] = valor
                self.assertUnSoloError(validar_escenario(d), "'pantano' debe tener un costo positivo")

    def test_terreno_transitable_sin_costo(self):
        d = escenario_oficial()
        del d["tipos_terreno"]["pasto"]["costo"]
        self.assertUnSoloError(validar_escenario(d), "'pasto' no tiene 'costo'")

    def test_costo_decimal_positivo_es_valido(self):
        d = escenario_oficial()
        d["tipos_terreno"]["camino"]["costo"] = 0.5
        self.assertEqual(validar_escenario(d), [])

    def test_terreno_no_transitable_ignora_su_costo(self):
        for costo in (None, -5, 0, "abc", 3):
            with self.subTest(costo=costo):
                d = escenario_oficial()
                d["tipos_terreno"]["muro"]["costo"] = costo
                self.assertEqual(validar_escenario(d), [])

    def test_transitable_ausente_o_no_booleano(self):
        d = escenario_oficial()
        del d["tipos_terreno"]["muro"]["transitable"]
        self.assertUnSoloError(validar_escenario(d), "le falta el campo 'transitable'")
        d = escenario_oficial()
        d["tipos_terreno"]["muro"]["transitable"] = "no"
        self.assertUnSoloError(validar_escenario(d), "debe ser true o false")

    def test_tipo_de_terreno_que_no_es_objeto(self):
        d = escenario_oficial()
        d["tipos_terreno"]["lava"] = 3
        self.assertUnSoloError(validar_escenario(d), "El terreno 'lava' debe ser un objeto")


class TestRegla4PosicionesEnElMapa(PruebaConEscenario):
    def test_recurso_fuera_del_mapa(self):
        for fila, columna in ((9, 2), (-1, 2), (2, 4), (2, -1)):
            with self.subTest(pos=(fila, columna)):
                d = escenario_oficial()
                d["recurso"] = {"fila": fila, "columna": columna}
                self.assertUnSoloError(validar_escenario(d), "El recurso está fuera del mapa")

    def test_bases_fuera_del_mapa(self):
        d = escenario_oficial()
        d["bases"]["A"]["columna"] = 4
        d["bases"]["B"]["fila"] = -1
        errores = validar_escenario(d)
        self.assertEqual(len(errores), 2)
        self.assertHayError(errores, "La base A está fuera del mapa")
        self.assertHayError(errores, "La base B está fuera del mapa")

    def test_unidad_fuera_del_mapa_con_y_sin_id(self):
        d = escenario_oficial()
        d["unidades"][2].update(fila=4, columna=0)
        self.assertUnSoloError(validar_escenario(d), "La unidad 'B1' está fuera del mapa")
        d = escenario_oficial()
        del d["unidades"][0]["id"]
        d["unidades"][0]["fila"] = 7
        errores = validar_escenario(d)
        self.assertHayError(errores, "La unidad en la posición 0 de 'unidades' está fuera del mapa")

    def test_posicion_con_tipos_invalidos(self):
        for valor in ("2", 1.5, True, None):
            with self.subTest(valor=valor):
                d = escenario_oficial()
                d["recurso"]["fila"] = valor
                self.assertUnSoloError(validar_escenario(d), "debe ser un entero")

    def test_posicion_mal_formada(self):
        d = escenario_oficial()
        del d["bases"]["B"]["columna"]
        self.assertUnSoloError(validar_escenario(d), "La base B debe ser un objeto con 'fila' y 'columna'")
        d = escenario_oficial()
        d["bases"]["B"] = [3, 3]
        self.assertUnSoloError(validar_escenario(d), "La base B debe ser un objeto")

    def test_unidad_que_no_es_objeto_y_unidades_que_no_es_lista(self):
        d = escenario_oficial()
        d["unidades"][1] = "A2"
        self.assertHayError(validar_escenario(d), "debe ser un objeto")
        d = escenario_oficial()
        d["unidades"] = "hola"
        self.assertUnSoloError(validar_escenario(d), "'unidades' debe ser una lista")

    def test_mapa_no_cuadrado_usa_sus_dos_dimensiones(self):
        d = escenario_oficial()
        d["mapa"] = {"filas": 2, "columnas": 3}
        d["terreno"] = [["camino"] * 3, ["camino"] * 3]
        d["bases"] = {"A": {"fila": 0, "columna": 0}, "B": {"fila": 2, "columna": 0}}
        d["recurso"] = {"fila": 0, "columna": 3}
        d["unidades"] = []
        errores = validar_escenario(d)
        self.assertEqual(len(errores), 2)
        self.assertIn("2 filas y 3 columnas", errores[0])


class TestRegla5UnidadEnCeldaTransitable(PruebaConEscenario):
    def test_unidad_sobre_muro(self):
        d = escenario_oficial()
        d["unidades"][1].update(fila=1, columna=1)
        self.assertUnSoloError(validar_escenario(d), "La unidad 'A2' está sobre un terreno no transitable: 'muro' en (1, 1)")

    def test_unidad_sin_id_sobre_muro(self):
        d = escenario_oficial()
        del d["unidades"][0]["id"]
        d["unidades"][0].update(fila=1, columna=1)
        self.assertHayError(validar_escenario(d), "La unidad en la posición 0 de 'unidades' está sobre un terreno no transitable")

    def test_unidad_fuera_del_mapa_solo_da_el_error_de_la_regla_4(self):
        for fila, columna in ((9, 9), (-1, 0), (0, -1)):
            with self.subTest(pos=(fila, columna)):
                d = escenario_oficial()
                d["unidades"][1].update(fila=fila, columna=columna)
                self.assertUnSoloError(validar_escenario(d), "fuera del mapa")

    def test_posicion_con_tipos_invalidos_solo_da_el_error_de_la_regla_4(self):
        for valor in (True, "1", 1.5):
            with self.subTest(valor=valor):
                d = escenario_oficial()
                d["unidades"][1].update(fila=valor, columna=1)
                self.assertUnSoloError(validar_escenario(d), "debe ser un entero")

    def test_terreno_desconocido_solo_da_el_error_de_la_regla_2(self):
        d = escenario_oficial()
        d["terreno"][0][1] = "lava"
        self.assertUnSoloError(validar_escenario(d), "'lava' no existe")

    def test_catalogo_mal_formado_solo_da_el_error_de_su_regla(self):
        d = escenario_oficial()
        d["tipos_terreno"]["muro"] = 3
        d["unidades"][1].update(fila=1, columna=1)
        self.assertUnSoloError(validar_escenario(d), "El terreno 'muro' debe ser un objeto")

    def test_unidad_en_terreno_transitable_es_valida(self):
        d = escenario_oficial()
        d["unidades"][1].update(fila=2, columna=2)  # pantano
        self.assertEqual(validar_escenario(d), [])


class TestRegla6IdsUnicos(PruebaConEscenario):
    def test_id_repetido(self):
        d = escenario_oficial()
        d["unidades"][1]["id"] = "A1"
        self.assertUnSoloError(validar_escenario(d), "El id 'A1' está repetido en 2 unidades (posiciones 0, 1")

    def test_dos_ids_repetidos_dan_dos_errores(self):
        d = escenario_oficial()
        d["unidades"][1]["id"] = "A1"
        d["unidades"][3]["id"] = "B1"
        self.assertEqual(len(validar_escenario(d)), 2)

    def test_muchas_repeticiones_se_resumen(self):
        d = escenario_oficial()
        d["unidades"] = [dict(d["unidades"][0]) for _ in range(7)]
        errores = validar_escenario(d)
        self.assertUnSoloError(errores, "repetido en 7 unidades")
        self.assertIn("y 2 más", errores[0])

    def test_ids_se_comparan_exactamente(self):
        d = escenario_oficial()
        d["unidades"][1]["id"] = "a1"
        self.assertEqual(validar_escenario(d), [])

    def test_id_ausente_o_invalido(self):
        for valor in ("__ausente__", None, 7, "", ["A1"], True):
            with self.subTest(id=valor):
                d = escenario_oficial()
                if valor == "__ausente__":
                    del d["unidades"][1]["id"]
                else:
                    d["unidades"][1]["id"] = valor
                self.assertUnSoloError(validar_escenario(d), "no tiene un 'id' válido")


class TestReglas7y8Bandos(PruebaConEscenario):
    def test_bando_invalido(self):
        for valor in ("C", " A", "", 1, True, None, ["A"]):
            with self.subTest(bando=valor):
                d = escenario_oficial()
                d["unidades"][1]["bando"] = valor
                self.assertUnSoloError(validar_escenario(d), "La unidad 'A2' tiene bando")

    def test_bando_ausente(self):
        d = escenario_oficial()
        del d["unidades"][1]["bando"]
        self.assertUnSoloError(validar_escenario(d), "tiene bando None")

    def test_minusculas_se_aceptan(self):
        d = escenario_oficial()
        d["unidades"][0]["bando"] = "a"
        d["turno"] = "b"
        self.assertEqual(validar_escenario(d), [])

    def test_turno_invalido(self):
        for valor in ("C", " A", "", 0, None, ["A"], False):
            with self.subTest(turno=valor):
                d = escenario_oficial()
                d["turno"] = valor
                self.assertUnSoloError(validar_escenario(d), "El turno es")

    def test_clave_de_bases_en_minuscula_no_se_acepta(self):
        d = escenario_oficial()
        d["bases"]["a"] = d["bases"].pop("A")
        self.assertUnSoloError(validar_escenario(d), "'bases.A'")


class TestRegla9Portador(PruebaConEscenario):
    def test_portador_que_existe(self):
        for id_unidad in ("A1", "A2", "B1", "B2"):
            with self.subTest(portador=id_unidad):
                d = escenario_oficial()
                d["juego"]["portador_recurso"] = id_unidad
                self.assertEqual(validar_escenario(d), [])

    def test_portador_inexistente_o_con_otra_capitalizacion(self):
        for valor in ("Z9", "a1"):
            with self.subTest(portador=valor):
                d = escenario_oficial()
                d["juego"]["portador_recurso"] = valor
                self.assertUnSoloError(validar_escenario(d), "ninguna unidad tiene ese id")

    def test_portador_que_no_es_texto_o_esta_vacio(self):
        for valor in (5, True, "", ["A1"], {"id": "A1"}):
            with self.subTest(portador=valor):
                d = escenario_oficial()
                d["juego"]["portador_recurso"] = valor
                self.assertUnSoloError(validar_escenario(d), "debe ser el id de una unidad o null")

    def test_portador_con_id_repetido_solo_da_el_error_de_la_regla_6(self):
        d = escenario_oficial()
        d["juego"]["portador_recurso"] = "A1"
        d["unidades"][1]["id"] = "A1"
        self.assertUnSoloError(validar_escenario(d), "está repetido")

    def test_id_de_unidad_no_hashable_no_rompe_la_regla_9(self):
        """Regresión: un id que es una lista hacía fallar al armar el conjunto de ids."""
        d = escenario_oficial()
        d["unidades"][1]["id"] = ["A2"]
        d["juego"]["portador_recurso"] = "A1"
        self.assertUnSoloError(validar_escenario(d), "no tiene un 'id' válido")

    def test_portador_ausente_solo_lo_reporta_la_regla_0(self):
        d = escenario_oficial()
        del d["juego"]["portador_recurso"]
        self.assertUnSoloError(validar_escenario(d), "Falta el campo obligatorio 'juego.portador_recurso'")


class TestProfundidadMinimax(PruebaConEscenario):
    def test_ausente_o_null_es_valida(self):
        d = escenario_oficial()
        del d["juego"]["profundidad_maxima_minimax"]
        self.assertEqual(validar_escenario(d), [])
        d["juego"]["profundidad_maxima_minimax"] = None
        self.assertEqual(validar_escenario(d), [])

    def test_valores_invalidos(self):
        for valor in (0, -3, "4", 2.5, True):
            with self.subTest(profundidad=valor):
                d = escenario_oficial()
                d["juego"]["profundidad_maxima_minimax"] = valor
                self.assertUnSoloError(validar_escenario(d), "profundidad_maxima_minimax")


class TestComportamientoGeneral(PruebaConEscenario):
    def test_los_errores_se_acumulan(self):
        d = escenario_oficial()
        d["terreno"][0][0] = "lava"                          # regla 2
        d["tipos_terreno"]["pantano"]["costo"] = 0            # regla 3
        d["recurso"]["fila"] = 9                              # regla 4
        d["unidades"][1].update(fila=1, columna=1)            # regla 5
        d["unidades"][2]["id"] = "A1"                         # regla 6
        d["unidades"][3]["bando"] = "Z"                       # regla 7
        d["turno"] = "X"                                      # regla 8
        d["juego"]["portador_recurso"] = "Q"                  # regla 9
        self.assertEqual(len(validar_escenario(d)), 8)

    def test_no_modifica_el_escenario_recibido(self):
        d = escenario_oficial()
        d["recurso"]["fila"] = 9
        d["turno"] = "b"
        antes = copy.deepcopy(d)
        validar_escenario(d)
        self.assertEqual(d, antes)

    def test_nunca_lanza_excepciones_con_json_danado(self):
        """Mutaciones aleatorias reproducibles (semilla fija) del escenario oficial."""
        basura = [None, 0, -1, 1.5, "x", "", [], {}, True, False, 10 ** 6, "A", "a", " A",
                  [1], {"fila": 1}, float("inf")]

        def caminos(o, ruta=()):
            yield ruta
            if isinstance(o, dict):
                for k, v in o.items():
                    yield from caminos(v, ruta + (k,))
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    yield from caminos(v, ruta + (i,))

        rng = random.Random(2026)
        for _ in range(3000):
            d = escenario_oficial()
            for _ in range(rng.choice([1, 2, 3])):
                ruta = rng.choice(list(caminos(d)))
                if not ruta:
                    continue
                padre = d
                for k in ruta[:-1]:
                    padre = padre[k]
                if rng.random() < 0.3:
                    padre.pop(ruta[-1]) if isinstance(padre, list) else padre.pop(ruta[-1], None)
                else:
                    padre[ruta[-1]] = rng.choice(basura)
            try:
                errores = validar_escenario(d)
            except Exception as ex:  # pragma: no cover - si pasa, la prueba falla
                self.fail(f"validar_escenario lanzó {type(ex).__name__}: {ex}\nentrada: {d}")
            self.assertIsInstance(errores, list)
            self.assertTrue(all(isinstance(e, str) and e for e in errores))


if __name__ == "__main__":
    unittest.main()
