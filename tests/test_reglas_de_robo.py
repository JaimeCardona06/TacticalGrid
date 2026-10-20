"""
Purpose:
    Pruebas que fijan las CONSECUENCIAS de la regla de robo, tal como están documentadas en
    docs/decisiones.md y en la sección 2.4 del documento técnico:
      1. Robar es ENTRAR a la celda del portador rival desde otra celda.
      2. Quien ya comparte celda con el portador no puede robarle sin salir y volver a entrar
         (así el recurso no cambia de manos en cada turno: no hay bucles sin fin).
      3. El portador puede entrar a la celda de un rival sin perder el recurso.
      4. No existe "pasar": toda acción mueve una unidad a una celda vecina.

AI usage:           Yes
AI intervention:    la IA diseñó y escribió estas pruebas a partir de una partida observada
                    (config/caso_robo_visual.json, turnos 2 a 6).
Student validation: Validado por el equipo ejecutando este archivo
                    (python -m unittest tests.test_reglas_de_robo -v) y reproduciendo los
                    turnos 2 a 6 de caso_robo_visual.json en la GUI.
"""
import random
import unittest

from src.models.state import EstadoJuego


class TableroAbierto:
    """Tablero ficticio de 6x6 sin obstáculos, con la firma real de Board."""

    def __init__(self, n=6):
        self.n = n

    def es_transitable(self, pos):
        return 0 <= pos[0] < self.n and 0 <= pos[1] < self.n


T = TableroAbierto()


def hijos(estado):
    return {accion: nuevo for accion, nuevo in estado.sucesores(T)}


class TestRoboEsEntrarALaCeldaDelPortador(unittest.TestCase):
    def test_entrar_a_la_celda_del_portador_rival_le_quita_el_recurso(self):
        # B1 lleva el recurso en (2,3); A1 está al lado, en (2,4), y le toca a A
        e = EstadoJuego([(2, 4)], [(2, 3)], ("B", 0), "A", (2, 3))
        nuevo = hijos(e)[(0, (2, 3))]
        self.assertEqual(nuevo.portador, ("A", 0))
        self.assertEqual(nuevo.recurso_pos, (2, 3))

    def test_pasar_a_una_celda_vecina_sin_portador_no_roba_nada(self):
        e = EstadoJuego([(2, 4)], [(2, 3)], ("B", 0), "A", (2, 3))
        for accion, nuevo in hijos(e).items():
            if accion[1] != (2, 3):
                self.assertEqual(nuevo.portador, ("B", 0), accion)


class TestCompartirCeldaNoPermiteRobar(unittest.TestCase):
    """Caso observado en caso_robo_visual.json (turnos 5 y 6): tras el robo, el despojado comparte celda."""

    def setUp(self):
        # A1 acaba de robarle el recurso a B1: los dos están en (2,5) y le toca a B
        self.e = EstadoJuego([(2, 5)], [(2, 5)], ("A", 0), "B", (2, 5))

    def test_ninguna_accion_del_despojado_le_devuelve_el_recurso(self):
        acciones = hijos(self.e)
        self.assertEqual(len(acciones), 3)                          # (2,5) está en el borde del tablero: 3 vecinas
        for accion, nuevo in acciones.items():
            self.assertEqual(nuevo.portador, ("A", 0), accion)       # el recurso sigue siendo de A

    def test_no_existe_una_accion_de_quedarse_en_la_misma_celda(self):
        for (indice, destino), _ in hijos(self.e).items():
            self.assertNotEqual(destino, (2, 5))

    def test_para_recuperarlo_hay_que_salir_y_volver_a_entrar_y_solo_si_el_portador_sigue_ahi(self):
        # B1 sale a (1,5); si A1 NO se mueve de (2,5) (mueve otra ficha), B1 puede volver a entrar y robar...
        e = EstadoJuego([(2, 5), (5, 5)], [(2, 5)], ("A", 0), "B", (2, 5))
        despues_de_salir = hijos(e)[(0, (1, 5))]
        despues_de_otra_ficha_de_a = hijos(despues_de_salir)[(1, (5, 4))]
        recupera = hijos(despues_de_otra_ficha_de_a)[(0, (2, 5))]
        self.assertEqual(recupera.portador, ("B", 0))
        # ...pero un portador que se mueve se aleja: B1 entra a la celda vieja y ya no hay nadie
        despues_de_mover_el_portador = hijos(despues_de_salir)[(0, (2, 4))]
        entra_tarde = hijos(despues_de_mover_el_portador)[(0, (2, 5))]
        self.assertEqual(entra_tarde.portador, ("A", 0))

    def test_propiedad_una_ficha_que_empieza_en_la_celda_del_portador_nunca_roba(self):
        """En 400 estados aleatorios: ninguna acción de una ficha que ya está en la celda del portador rival cambia de dueño."""
        rng = random.Random(9)
        celdas = [(f, c) for f in range(6) for c in range(6)]
        revisadas = 0
        for _ in range(400):
            portador_bando = rng.choice("AB")
            propias = rng.sample(celdas, 3)
            rivales = rng.sample(celdas, 3)
            if portador_bando == "A":
                pos_a, pos_b, portador = propias, rivales, ("A", 0)
                en_celda_del_portador = pos_a[0]
            else:
                pos_a, pos_b, portador = rivales, propias, ("B", 0)
                en_celda_del_portador = pos_b[0]
            # una ficha del bando contrario comparte celda con el portador y le toca mover
            contrario = "B" if portador_bando == "A" else "A"
            lista = pos_b if contrario == "B" else pos_a
            lista[1] = en_celda_del_portador
            e = EstadoJuego(pos_a, pos_b, portador, contrario, en_celda_del_portador)
            for (indice, destino), nuevo in e.sucesores(T):
                if indice == 1:                                       # la ficha que comparte celda con el portador
                    self.assertEqual(nuevo.portador, portador, (indice, destino))
                    revisadas += 1
        self.assertGreater(revisadas, 800)


class TestElPortadorPuedeEntrarALaCeldaDeUnRival(unittest.TestCase):
    def test_no_pierde_el_recurso_por_entrar_a_la_celda_de_un_rival(self):
        # B1 lleva el recurso en (2,3) y A1 está en (2,4): le toca a B
        e = EstadoJuego([(2, 4)], [(2, 3)], ("B", 0), "B", (2, 3))
        nuevo = hijos(e)[(0, (2, 4))]
        self.assertEqual(nuevo.portador, ("B", 0))                    # sigue siendo suyo
        self.assertEqual(nuevo.recurso_pos, (2, 4))                   # viaja con él
        self.assertEqual(nuevo.pos_a, ((2, 4),))                      # y comparte celda con A1

    def test_en_esa_celda_la_ficha_rival_no_puede_robarle(self):
        # tras "abrazar" a A1, le toca a A: A1 comparte celda con el portador y no puede robarlo
        e = EstadoJuego([(2, 4)], [(2, 4)], ("B", 0), "A", (2, 4))
        for accion, nuevo in hijos(e).items():
            self.assertEqual(nuevo.portador, ("B", 0), accion)


class TestNoExistePasar(unittest.TestCase):
    def test_toda_accion_mueve_una_unidad_a_una_celda_vecina(self):
        e = EstadoJuego([(2, 2), (4, 4)], [(0, 5)], None, "A", (3, 3))
        origenes = {0: (2, 2), 1: (4, 4)}
        acciones = list(e.sucesores(T))
        self.assertTrue(acciones)
        for (indice, destino), nuevo in acciones:
            origen = origenes[indice]
            self.assertEqual(abs(origen[0] - destino[0]) + abs(origen[1] - destino[1]), 1)
            self.assertNotEqual(nuevo.pos_a, e.pos_a)                # el estado siempre cambia

    def test_un_bando_con_una_sola_ficha_esta_obligado_a_moverla(self):
        e = EstadoJuego([(2, 5)], [(2, 5)], ("A", 0), "B", (2, 5))
        self.assertTrue(all(nuevo.pos_b != e.pos_b for _, nuevo in e.sucesores(T)))


if __name__ == "__main__":
    unittest.main()
