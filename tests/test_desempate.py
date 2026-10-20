"""
Purpose:
    Pruebas del desempate por avance: distancias reales rodeando muros, claves de
    avance en los tres casos (recurso libre, portador propio, portador rival), que
    el agente solo elige ENTRE acciones óptimas empatadas, que no cambia el valor
    ni las métricas de nodos, y que en las partidas las fichas ya no deambulan.

AI usage:           Yes
AI intervention:    la IA diseñó y escribió estas pruebas junto con el módulo.
Student validation: Validado por el equipo ejecutando este archivo
                    (python -m unittest tests.test_desempate -v) y la suite completa.
"""

import functools
import math
import os
import random
import unittest

from src.adversarial.agent import MinimaxAgent
from src.adversarial.desempate import (ESTRATEGIAS_DE_ROBO, INTERCEPCION, PERSECUCION, SIN_RUTA, clave_de_avance,
                                       distancias_reales, holgura_de_intercepcion, ruta_hacia_la_base)
from src.adversarial.minimax import minimax_alphabeta
from src.models.state import EstadoJuego
from src.scenario.loader import cargar_escenario
from src.ui.controlador import iniciar_partida, jugar_turno
import main
from tests.base import RAIZ

RUTA_GRANDE = os.path.join(RAIZ, "config", "mapa_grande.json")
RUTA_GRANDE_SIMETRICO = os.path.join(RAIZ, "config", "mapa_grande_simetrico.json")
RUTA_3V3 = os.path.join(RAIZ, "config", "mapa_3v3.json")
RUTA_INTERCEPCION = os.path.join(RAIZ, "config", "caso_intercepcion.json")


class Tablero:
    """Tablero ficticio a partir de un dibujo: '#' es muro, cualquier otro carácter es libre."""

    def __init__(self, filas):
        self.terreno = [["muro" if c == "#" else "libre" for c in fila] for fila in filas]
        self.tipos_terreno = {"libre": {"costo": 1, "transitable": True}, "muro": {"transitable": False}}

    def es_transitable(self, pos):
        f, c = pos
        return 0 <= f < len(self.terreno) and 0 <= c < len(self.terreno[0]) and self.terreno[f][c] != "muro"


def libre(n=4):
    return Tablero(["." * n] * n)


BASE_A, BASE_B = (0, 0), (3, 3)


class TestDistanciasReales(unittest.TestCase):
    def test_rodea_el_muro_en_lugar_de_ir_en_linea_recta(self):
        t = Tablero([".#.",
                     ".#.",
                     "..."])
        d = distancias_reales(t, (0, 0))
        self.assertEqual(d[(0, 2)], 6)       # Manhattan diría 2: hay que bajar, cruzar y subir
        self.assertEqual(d[(2, 1)], 3)

    def test_celdas_aisladas_o_muros_no_aparecen(self):
        t = Tablero([".#.",
                     ".#.",
                     ".#."])
        d = distancias_reales(t, (0, 0))
        self.assertNotIn((0, 2), d)          # aislada
        self.assertNotIn((1, 1), d)          # muro
        self.assertEqual(sorted(d), [(0, 0), (1, 0), (2, 0)])

    def test_el_origen_vale_cero_y_no_falla_si_esta_en_un_muro(self):
        t = Tablero(["#."])
        self.assertEqual(distancias_reales(t, (0, 0))[(0, 0)], 0)

    def test_no_modifica_el_tablero(self):
        t = Tablero([".#.", "..."])
        antes = [fila[:] for fila in t.terreno]
        distancias_reales(t, (0, 0))
        self.assertEqual(t.terreno, antes)


class TestClaveDeAvance(unittest.TestCase):
    def test_recurso_libre_usa_la_mas_cercana_y_la_suma(self):
        t = libre()
        e = EstadoJuego([(0, 1), (3, 0)], [(3, 3)], None, "B", (0, 3))
        self.assertEqual(clave_de_avance(e, "A", t, BASE_A, BASE_B, {}), (2, 2 + 6))   # A1 a 2, A2 a 6

    def test_portador_propio_usa_distancia_a_la_base_y_escolta(self):
        t = libre()
        e = EstadoJuego([(1, 1), (3, 0), (0, 2)], [(3, 3)], ("A", 0), "B", (1, 1))
        # portador a 2 de la base; las otras dos unidades a 3 y 2 del portador
        self.assertEqual(clave_de_avance(e, "A", t, BASE_A, BASE_B, {}), (2, 3 + 2))

    def test_portador_rival_por_defecto_persigue(self):
        t = libre()
        e = EstadoJuego([(0, 0), (2, 1)], [(2, 3)], ("B", 0), "B", (2, 3))
        self.assertEqual(clave_de_avance(e, "A", t, BASE_A, BASE_B, {}), (2, 2 + 5))     # A2 a 2 del portador, A1 a 5
        self.assertEqual(clave_de_avance(e, "A", t, BASE_A, BASE_B, {}, PERSECUCION), (2, 7))

    def test_portador_rival_con_intercepcion_usa_la_holgura(self):
        t = libre()
        e = EstadoJuego([(0, 0), (2, 1)], [(2, 3)], ("B", 0), "B", (2, 3))
        # ruta del portador: (2,3) -> (3,3) (su base). A2 llega a (3,3) en 3 pasos: holgura 3 - 1 = 2;
        # A1 en 6: holgura 5. Luego: la unidad más cercana al portador (A2, a 2) y la suma de holguras (7).
        self.assertEqual(clave_de_avance(e, "A", t, BASE_A, BASE_B, {}, INTERCEPCION), (2, 2, 7))

    def test_la_estrategia_no_afecta_al_recurso_libre_ni_al_portador_propio(self):
        t = libre()
        libre_ = EstadoJuego([(0, 1), (3, 0)], [(3, 3)], None, "B", (0, 3))
        propio = EstadoJuego([(1, 1), (3, 0), (0, 2)], [(3, 3)], ("A", 0), "B", (1, 1))
        for e in (libre_, propio):
            self.assertEqual(clave_de_avance(e, "A", t, BASE_A, BASE_B, {}, PERSECUCION),
                             clave_de_avance(e, "A", t, BASE_A, BASE_B, {}, INTERCEPCION))

    def test_interceptar_por_delante_pesa_mas_que_estar_cerca_por_detras(self):
        t = libre(10)
        base_b = (9, 9)
        con_delantero = EstadoJuego([(2, 1), (8, 8)], [(2, 2)], ("B", 0), "B", (2, 2))
        solo_detras = EstadoJuego([(2, 1), (0, 0)], [(2, 2)], ("B", 0), "B", (2, 2))
        a = clave_de_avance(con_delantero, "A", t, (0, 0), base_b, {}, INTERCEPCION)
        b = clave_de_avance(solo_detras, "A", t, (0, 0), base_b, {}, INTERCEPCION)
        self.assertLessEqual(a[0], 0)    # la unidad de delante llega a tiempo
        self.assertGreaterEqual(b[0], 1)  # la de atrás nunca alcanza
        self.assertLess(a, b)

    def test_usa_distancia_real_no_manhattan(self):
        t = Tablero([".#.",
                     ".#.",
                     "..."])
        e = EstadoJuego([(0, 0)], [(0, 2)], None, "B", (0, 2))
        self.assertEqual(clave_de_avance(e, "A", t, (0, 0), (0, 0), {}), (6, 6))      # Manhattan sería (2, 2)

    def test_celda_inalcanzable_cuenta_como_sin_ruta(self):
        t = Tablero([".#.",
                     ".#."])
        e = EstadoJuego([(0, 0)], [(0, 2)], None, "B", (0, 2))
        self.assertEqual(clave_de_avance(e, "A", t, (0, 0), (0, 0), {}), (SIN_RUTA, SIN_RUTA))

    def test_reutiliza_la_cache(self):
        t = libre()
        cache = {}
        e = EstadoJuego([(0, 1)], [(3, 3)], None, "B", (0, 3))
        clave_de_avance(e, "A", t, BASE_A, BASE_B, cache)
        self.assertEqual(list(cache), [(0, 3)])


class TestRutaDelPortador(unittest.TestCase):
    def test_en_campo_abierto_va_derecho_a_la_base(self):
        t = libre()
        ruta = ruta_hacia_la_base(distancias_reales(t, BASE_B), (0, 0))
        self.assertEqual(len(ruta), 7)                         # 6 pasos
        self.assertEqual((ruta[0], ruta[-1]), ((0, 0), BASE_B))
        self.assertEqual(ruta[1], (0, 1))                      # prefiere derecha antes que abajo (orden de direcciones)
        for a, b in zip(ruta, ruta[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_rodea_los_muros(self):
        t = Tablero([".#.",
                     ".#.",
                     "..."])
        ruta = ruta_hacia_la_base(distancias_reales(t, (0, 2)), (0, 0))
        self.assertEqual(len(ruta) - 1, 6)
        self.assertNotIn((0, 1), ruta)
        self.assertNotIn((1, 1), ruta)

    def test_sin_camino_devuelve_solo_el_origen(self):
        t = Tablero([".#.",
                     ".#."])
        self.assertEqual(ruta_hacia_la_base(distancias_reales(t, (0, 2)), (0, 0)), [(0, 0)])

    def test_el_portador_ya_en_la_base(self):
        self.assertEqual(ruta_hacia_la_base(distancias_reales(libre(), BASE_B), BASE_B), [BASE_B])


class TestHolguraDeIntercepcion(unittest.TestCase):
    def setUp(self):
        self.t = libre(10)
        self.ruta = [(0, 5 + m) for m in range(5)]              # el portador avanza por la fila 0 hacia la derecha

    def holgura(self, unidad):
        return holgura_de_intercepcion(self.ruta, distancias_reales(self.t, unidad))

    def test_perseguir_por_detras_nunca_alcanza(self):
        self.assertEqual(self.holgura((0, 4)), 1)               # adyacente detrás: holgura 1 (> 0)
        self.assertEqual(self.holgura((0, 1)), 4)               # más lejos detrás: peor

    def test_una_unidad_por_delante_si_intercepta(self):
        self.assertEqual(self.holgura((1, 8)), -2)              # llega a (0,8) en 1 paso y el portador tarda 3

    def test_a_mayor_cercania_al_punto_menor_holgura(self):
        self.assertLess(self.holgura((1, 8)), self.holgura((3, 8)))

    def test_celdas_inalcanzables(self):
        t = Tablero([".#.", ".#."])
        ruta = [(0, 2), (1, 2)]
        self.assertGreater(holgura_de_intercepcion(ruta, distancias_reales(t, (0, 0))), SIN_RUTA - 5)

    def test_ruta_sin_pasos_no_tiene_holgura(self):
        self.assertEqual(holgura_de_intercepcion([(0, 0)], distancias_reales(libre(), (1, 1))), SIN_RUTA)


_persecucion = functools.partial(clave_de_avance, estrategia_robo=PERSECUCION)
_intercepcion = functools.partial(clave_de_avance, estrategia_robo=INTERCEPCION)


def _simular_robo(tablero, unidades_a, portador, base_b, clave, base_a=(0, 0)):
    """A mueve primero y elige la acción de menor clave; el portador de B sigue su ruta más corta.

    Devuelve la ronda en que A le roba el recurso, o None si el portador llega a su base.
    """
    ruta = ruta_hacia_la_base(distancias_reales(tablero, base_b), portador)
    cache = {}
    pos_a = list(unidades_a)
    for ronda in range(len(ruta) - 1):
        actual = ruta[ronda]
        estado = EstadoJuego(pos_a, [actual], ("B", 0), "A", actual)
        mejor = None
        for _, hijo in estado.sucesores(tablero):
            if hijo.portador[0] == "A":
                return ronda + 1                              # entró a la celda del portador: ROBO
            k = clave(hijo, "A", tablero, base_a, base_b, cache)
            if mejor is None or k < mejor[0]:
                mejor = (k, hijo)
        pos_a = list(mejor[1].pos_a)
    return None


class TestInterceptarEsMejorQuePerseguir(unittest.TestCase):
    def test_caso_concreto_la_unidad_de_delante_roba_y_la_de_atras_no(self):
        """Una ficha detrás del portador y otra a un lado de su ruta, que nunca pasa pegada a ella."""
        t = libre(10)
        pos = [(2, 0), (6, 5)]
        intercepcion = _simular_robo(t, pos, (2, 2), (9, 9), _intercepcion)
        persecucion = _simular_robo(t, pos, (2, 2), (9, 9), _persecucion)
        self.assertEqual(intercepcion, 14)       # la de (6,5) se adelanta y le roba en la ronda 14
        self.assertIsNone(persecucion)           # la que persigue por detrás nunca lo alcanza

    def test_perseguir_solo_por_detras_nunca_roba_en_campo_abierto(self):
        """A igual velocidad la ficha perseguidora no queda adyacente en su turno (fichas no adyacentes al inicio)."""
        t = libre(10)
        for inicio in [(2, 0), (0, 2), (1, 1), (0, 0), (3, 0)]:
            self.assertIsNone(_simular_robo(t, [inicio], (2, 2), (9, 9), _persecucion), inicio)

    def test_la_intercepcion_corta_la_esquina_donde_la_persecucion_no_llega(self):
        """Una ficha que arranca detrás en diagonal se adelanta cortando el giro de la ruta y roba."""
        t = libre(10)
        self.assertEqual(_simular_robo(t, [(3, 0)], (2, 2), (9, 9), _intercepcion), 9)
        self.assertIsNone(_simular_robo(t, [(3, 0)], (2, 2), (9, 9), _persecucion))

    def test_en_configuraciones_aleatorias_intercepta_mas_que_persigue(self):
        rng = random.Random(2026)
        n = 9
        t = libre(n)
        roba_i = roba_p = solo_i = solo_p = total = 0
        for _ in range(40):
            portador = (rng.randrange(0, 3), rng.randrange(0, 3))
            libres = [(f, c) for f in range(n) for c in range(n) if (f, c) != portador]
            unidades = rng.sample(libres, rng.choice([1, 2, 3]))
            i = _simular_robo(t, unidades, portador, (n - 1, n - 1), _intercepcion)
            p = _simular_robo(t, unidades, portador, (n - 1, n - 1), _persecucion)
            total += 1
            roba_i += i is not None
            roba_p += p is not None
            solo_i += i is not None and p is None
            solo_p += p is not None and i is None
        self.assertGreater(roba_i, roba_p)
        self.assertGreater(solo_i, solo_p)
        self.assertGreater(total, 30)


class TestAgenteConDesempate(unittest.TestCase):
    def estado_perdido(self):
        """B lleva el recurso a un paso de su base y A no puede evitarlo: todas las acciones de A valen lo mismo."""
        return EstadoJuego([(0, 1), (2, 1)], [(3, 2)], ("B", 0), "A", (3, 2))

    def decidir(self, desempatar, poda=True, estado=None):
        agente = MinimaxAgent("A", profundidad=3, usar_poda=poda, desempatar_por_avance=desempatar)
        return agente.seleccionar_movimiento(estado or self.estado_perdido(), libre(), BASE_A, BASE_B)

    def test_sin_desempate_mueve_la_primera_unidad(self):
        accion, metricas = self.decidir(False)
        self.assertEqual(accion, (0, (0, 2)))                 # A1, la primera del orden, aunque está lejos
        self.assertIsNone(metricas["acciones_empatadas"])

    def test_con_desempate_mueve_la_unidad_que_persigue(self):
        accion, metricas = self.decidir(True)
        self.assertEqual(accion[0], 1)                         # A2, la más cercana al portador rival
        self.assertIn(accion[1], [(2, 2), (3, 1)])             # y se acerca a él
        self.assertGreater(metricas["acciones_empatadas"], 1)

    def test_no_cambia_el_valor_ni_las_metricas_de_nodos(self):
        _, sin = self.decidir(False)
        _, con = self.decidir(True)
        for clave in ("valor_obtenido", "nodos_visitados", "nodos_generados", "nodos_evaluados",
                      "podas_totales", "profundidad_alcanzada"):
            self.assertEqual(sin[clave], con[clave], clave)

    def test_funciona_igual_con_minimax_puro(self):
        con_poda, _ = self.decidir(True, poda=True)
        sin_poda, _ = self.decidir(True, poda=False)
        self.assertEqual(con_poda, sin_poda)

    def test_la_accion_elegida_es_legal(self):
        _, metricas = self.decidir(True)
        self.assertTrue(metricas["accion_legal"])

    def test_con_el_portador_rival_lejos_la_estrategia_decide_que_unidad_mueve(self):
        """Todas las acciones valen lo mismo (nada se ve a profundidad 1): decide la estrategia de robo."""
        e = EstadoJuego([(2, 0), (8, 8)], [(2, 2)], ("B", 0), "A", (2, 2))
        persigue = MinimaxAgent("A", profundidad=1, desempatar_por_avance=True)          # por defecto: persecución
        accion, metricas = persigue.seleccionar_movimiento(e, libre(10), (0, 0), (9, 9))
        self.assertGreater(metricas["acciones_empatadas"], 1)
        self.assertEqual(accion, (0, (2, 1)))      # la ficha más cercana se acerca al portador
        intercepta = MinimaxAgent("A", profundidad=1, desempatar_por_avance=True, estrategia_robo=INTERCEPCION)
        accion, _ = intercepta.seleccionar_movimiento(e, libre(10), (0, 0), (9, 9))
        self.assertEqual(accion[0], 1)             # mueve la unidad de delante, no la que está detrás del portador
        sin = MinimaxAgent("A", profundidad=1, desempatar_por_avance=False)
        primera, _ = sin.seleccionar_movimiento(e, libre(10), (0, 0), (9, 9))
        self.assertEqual(primera[0], 0)            # sin desempate se movería la primera unidad

    def test_estrategia_de_robo_desconocida_lanza_error(self):
        for valor in ("perseguir", "", None, 1):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    MinimaxAgent("A", estrategia_robo=valor)

    def test_estrategia_por_defecto_es_la_persecucion(self):
        self.assertEqual(MinimaxAgent("A").estrategia_robo, PERSECUCION)
        self.assertEqual(set(ESTRATEGIAS_DE_ROBO), {PERSECUCION, INTERCEPCION})

    def test_si_hay_una_unica_accion_optima_no_cambia_nada(self):
        """B a un paso de su base y le toca a B: la única óptima es entrar (las demás no ganan ya)."""
        e = EstadoJuego([(0, 1), (2, 1)], [(3, 2), (0, 3)], ("B", 0), "B", (3, 2))
        for desempatar in (False, True):
            agente = MinimaxAgent("B", profundidad=3, desempatar_por_avance=desempatar)
            accion, _ = agente.seleccionar_movimiento(e, libre(), BASE_A, BASE_B)
            self.assertEqual(accion, (0, BASE_B))

    def test_solo_elige_entre_acciones_optimas_y_la_de_menor_clave(self):
        """En estados aleatorios: la elegida es óptima y tiene la menor clave entre las óptimas."""
        rng = random.Random(3)
        tablero = libre()
        verificados = 0
        for _ in range(60):
            celdas = [(f, c) for f in range(4) for c in range(4)]
            pos_a, pos_b = rng.sample(celdas, 2), rng.sample(celdas, 2)
            portador = rng.choice([None, ("A", 0), ("B", 0), ("B", 1)])
            recurso = rng.choice(celdas) if portador is None else (pos_a if portador[0] == "A" else pos_b)[portador[1]]
            estado = EstadoJuego(pos_a, pos_b, portador, "A", recurso)
            if estado.es_terminal(BASE_A, BASE_B):
                continue
            agente = MinimaxAgent("A", profundidad=2, desempatar_por_avance=True)
            accion, metricas = agente.seleccionar_movimiento(estado, tablero, BASE_A, BASE_B)

            valores = {mov: minimax_alphabeta(h, 1, -math.inf, math.inf, False, tablero, BASE_A, BASE_B)[0]
                       for mov, h in estado.sucesores(tablero)}
            optimo = max(valores.values())
            self.assertEqual(metricas["valor_obtenido"], optimo)
            self.assertEqual(valores[accion], optimo)          # nunca elige una acción peor
            hijos = dict(estado.sucesores(tablero))
            cache = {}
            claves = {m: clave_de_avance(hijos[m], "A", tablero, BASE_A, BASE_B, cache) for m, v in valores.items() if v == optimo}
            self.assertEqual(claves[accion], min(claves.values()))
            self.assertEqual(metricas["acciones_empatadas"], len(claves))
            verificados += 1
        self.assertGreater(verificados, 40)


class TestPartidaDeInterceptacion(unittest.TestCase):
    """config/caso_intercepcion.json: B ya lleva el recurso; A tiene una ficha detrás y otra por delante."""

    def jugar(self, estrategia=None):
        partida = iniciar_partida(cargar_escenario(RUTA_INTERCEPCION), profundidad=3)
        if estrategia:   # cambia la estrategia declarada en el JSON, para comparar
            partida.agentes = {b: MinimaxAgent(b, profundidad=3, desempatar_por_avance=True, estrategia_robo=estrategia)
                               for b in ("A", "B")}
        robos = []
        anterior = partida.estado.portador
        while not partida.terminada:
            fila = jugar_turno(partida)
            actual = partida.estado.portador
            if anterior and actual and actual[0] != anterior[0]:
                robos.append((fila["turno"], fila["unidad"]))
            anterior = actual
        return partida, robos

    def test_el_json_declara_la_estrategia_de_intercepcion(self):
        self.assertEqual(cargar_escenario(RUTA_INTERCEPCION).prueba["estrategia_robo"], INTERCEPCION)

    def test_con_intercepcion_a_le_roba_el_recurso_a_b_y_gana(self):
        partida, robos = self.jugar()               # usa la estrategia que declara el JSON
        self.assertEqual(partida.ganador, "A")
        self.assertEqual(len(robos), 1)
        self.assertEqual(robos[0][1], "A1")        # la ficha que se adelantó es la que roba

    def test_con_persecucion_nunca_hay_robo_y_gana_b(self):
        partida, robos = self.jugar(PERSECUCION)
        self.assertEqual(partida.ganador, "B")
        self.assertEqual(robos, [])


class TestEstrategiaDeRoboEnLaConfiguracion(unittest.TestCase):
    def test_por_defecto_y_valida(self):
        self.assertEqual(main._estrategia_de_robo({}), PERSECUCION)
        self.assertEqual(main._estrategia_de_robo({"estrategia_robo": "intercepcion"}), INTERCEPCION)
        self.assertEqual(main._estrategia_de_robo({"estrategia_robo": "persecucion"}), PERSECUCION)

    def test_invalida_avisa_y_usa_la_de_por_defecto(self):
        import contextlib
        import io
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            self.assertEqual(main._estrategia_de_robo({"estrategia_robo": "rara"}), PERSECUCION)
        self.assertIn("no es válida", salida.getvalue())

    def test_los_agentes_de_partida_usan_la_estrategia_pedida(self):
        agentes = main._crear_agentes(3, True, None, INTERCEPCION)
        self.assertTrue(all(a.estrategia_robo == INTERCEPCION and a.desempatar_por_avance for a in agentes.values()))
        por_defecto = main._crear_agentes(3, True, None)
        self.assertTrue(all(a.estrategia_robo == PERSECUCION for a in por_defecto.values()))


class TestPartidasConDesempate(unittest.TestCase):
    def jugar(self, ruta):
        partida = iniciar_partida(cargar_escenario(ruta))
        filas = []
        while not partida.terminada:
            filas.append(jugar_turno(partida))
        return partida, filas

    def test_en_mapa_grande_las_fichas_de_a_ya_no_deambulan(self):
        """Antes A1 recorría la fila 0 mientras B se llevaba el recurso; ahora solo persigue la ficha más cercana."""
        partida, filas = self.jugar(RUTA_GRANDE)
        self.assertEqual(partida.ganador, "B")
        unidades_a_tras_el_turno_31 = {f["unidad"] for f in filas if f["bando"] == "A" and f["turno"] > 31}
        self.assertEqual(unidades_a_tras_el_turno_31, {"A3"})

    def test_mapa_3v3_simetrico_termina_en_empate_por_equilibrio(self):
        partida, _ = self.jugar(RUTA_3V3)
        self.assertIsNone(partida.ganador)
        self.assertIsNone(partida.estado.portador)             # nadie se atreve a recoger el recurso

    def test_mapa_grande_simetrico_termina_en_empate_por_equilibrio(self):
        partida, _ = self.jugar(RUTA_GRANDE_SIMETRICO)
        self.assertIsNone(partida.ganador)
        self.assertIsNone(partida.estado.portador)


class TestEscenarioSimetrico(unittest.TestCase):
    """mapa_grande_simetrico.json: cada unidad de A tiene su espejo en B a la misma distancia."""

    def setUp(self):
        from src.game.navegacion import ProblemaNavegacion
        from src.search.uninformed import bfs
        self.e = cargar_escenario(RUTA_GRANDE_SIMETRICO)
        t = self.e.tablero
        self.pasos = {u.id: len(bfs(ProblemaNavegacion(t, u.posicion, self.e.recurso)).camino) - 1
                      for u in self.e.unidades}
        self.al_recurso = lambda origen, destino: len(bfs(ProblemaNavegacion(t, origen, destino)).camino) - 1

    def test_las_unidades_espejo_estan_a_la_misma_distancia_del_recurso(self):
        for i in ("1", "2", "3"):
            self.assertEqual(self.pasos["A" + i], self.pasos["B" + i], i)

    def test_los_portadores_recorren_lo_mismo_hasta_su_base(self):
        t = self.e.tablero
        self.assertEqual(self.al_recurso(self.e.recurso, t.base_a), self.al_recurso(self.e.recurso, t.base_b))

    def test_el_original_da_ventaja_a_b_de_dos_pasos(self):
        original = cargar_escenario(RUTA_GRANDE)
        from src.game.navegacion import ProblemaNavegacion
        from src.search.uninformed import bfs
        d = {u.id: len(bfs(ProblemaNavegacion(original.tablero, u.posicion, original.recurso)).camino) - 1
             for u in original.unidades}
        self.assertEqual(d["A3"] - d["B3"], 2)


if __name__ == "__main__":
    unittest.main()
