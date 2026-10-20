# GUI Tkinter — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar `src/ui/gui.py` (hoy vacío) como una interfaz gráfica Tkinter que carga un
escenario JSON y permite ejecutar sobre él los tres modos del enunciado (búsqueda, adversarial,
partida), mostrando la cuadrícula y las métricas de cada ejecución.

**Architecture:** Una capa de orquestación pura sin Tkinter (`src/ui/controlador.py`, testeable con
`unittest`) que reutiliza `main.py` y los módulos de `src/scenario`, `src/game`, `src/search`,
`src/adversarial` sin modificarlos; y una capa de vista Tkinter (`src/ui/gui.py`: `CanvasEscenario`
para dibujar el tablero y `AppTacticalGrid` para la ventana y las tres pestañas) que solo llama a
`controlador` y pinta lo que devuelve.

**Tech Stack:** Python 3.10+, `tkinter`/`ttk` (biblioteca estándar, sin dependencias nuevas),
`unittest` para `controlador.py`.

**Spec:** `docs/superpowers/specs/2026-10-18-gui-tkinter-design.md`

## Global Constraints

- Sin dependencias externas: solo biblioteca estándar de Python (incluye `tkinter`).
- No se modifica ningún archivo de `src/search/`, `src/game/`, `src/adversarial/`, `src/scenario/`,
  `src/models/` ni `main.py`. La GUI es un consumidor más de esa API.
- No se exponen estados explorados ni frontera: solo el camino final y las métricas agregadas de
  `ResultadoBusqueda`.
- El modo partida avanza con un botón "Siguiente turno" (un turno por clic); no hay reproducción
  automática ni animación.
- Carga de escenario todo o nada: un `EscenarioInvalido` no reemplaza el escenario ya cargado en
  la GUI.
- Python >= 3.10 (igual que el resto del proyecto).
- No hay suite automatizada para `src/ui/gui.py` (Tkinter); sí la hay, con `unittest`, para
  `src/ui/colores.py` y `src/ui/controlador.py`, que no importan `tkinter`.

## Review Focus

- Escenario válido pero sin unidad de algún bando (A o B): los modos adversarial y partida deben
  fallar con un mensaje claro, no con una excepción cruda. → cubierto en Tarea 4
  (`preparar_estado_inicial`) y Tarea 5 (`iniciar_partida`).
- Escenario con terreno de nombre propio o con un solo costo transitable en el catálogo (p. ej.
  `mapa_agnostico.json`, o un catálogo con un único terreno transitable): el color por costo no
  debe dividir por cero ni romperse cuando `costo_min == costo_max`. → cubierto en Tarea 1.
- Pedir "Siguiente turno" cuando la partida ya terminó (victoria o empate por `MAX_TURNOS`): no debe
  jugar un turno de más ni duplicar el resultado; debe fallar con un mensaje claro. → cubierto en
  Tarea 5.
- Un bando sin acciones legales (unidad encerrada): el modo adversarial debe reportarlo como error
  claro en vez de devolver una acción `None` sin explicar por qué. → cubierto en Tarea 4.
- Algoritmo, heurística o `k` inválidos llegando al controlador (selección desincronizada en la
  GUI, o `k` ≤ 0): `resolver_busqueda_gui` debe traducir el `ValueError` interno en un
  `ErrorControlador` con mensaje legible, no dejarlo propagarse crudo. → cubierto en Tarea 3.

---

## Task 1: Colores por costo (`src/ui/colores.py`)

**Files:**
- Create: `src/ui/colores.py`
- Test: `tests/test_colores.py`

**Interfaces:**
- Produces: `color_por_costo(costo: float, costo_min: float, costo_max: float) -> str` (hex
  `"#rrggbb"`); constantes `COLOR_VERDE = "#2ecc71"`, `COLOR_MARRON = "#8b5a2b"`,
  `COLOR_OBSTACULO = "#2b2b2b"`, `COLOR_BANDO = {"A": "#1f77b4", "B": "#d62728"}`,
  `COLOR_RECURSO = "#f1c40f"`, `COLOR_CAMINO = "#27ae60"`, `COLOR_RESALTADO = "#9b59b6"`.
  Usadas por `CanvasEscenario` (Tarea 6).

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# tests/test_colores.py
import unittest
from src.ui.colores import color_por_costo, COLOR_VERDE, COLOR_MARRON

class TestColorPorCosto(unittest.TestCase):
    def test_extremo_minimo_da_verde(self):
        self.assertEqual(color_por_costo(1, 1, 9), COLOR_VERDE)

    def test_extremo_maximo_da_marron(self):
        self.assertEqual(color_por_costo(9, 1, 9), COLOR_MARRON)

    def test_costo_min_igual_max_no_rompe(self):
        self.assertEqual(color_por_costo(5, 3, 3), COLOR_VERDE)

    def test_intermedio_es_un_hex_valido_distinto_de_los_extremos(self):
        color = color_por_costo(5, 1, 9)
        self.assertRegex(color, r"^#[0-9a-f]{6}$")
        self.assertNotIn(color, (COLOR_VERDE, COLOR_MARRON))
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run: `python -m unittest tests.test_colores -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.ui.colores'`)

- [ ] **Step 3: Implementar `src/ui/colores.py`**

Definir las constantes de arriba y `color_por_costo`: si `costo_min == costo_max` devuelve
`COLOR_VERDE`; si no, calcula `fraccion = (costo - costo_min) / (costo_max - costo_min)` acotada a
`[0, 1]` e interpola linealmente el RGB entre `COLOR_VERDE` y `COLOR_MARRON`, devolviendo
`"#rrggbb"` en minúsculas.

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run: `python -m unittest tests.test_colores -v`
Expected: OK (4 pruebas)

- [ ] **Step 5: Commit**

```bash
git add src/ui/colores.py tests/test_colores.py
git commit -m "feat(ui): agregar paleta de colores por costo para la GUI"
```

---

## Task 2: Helpers de renderizado (`src/ui/controlador.py`, creación)

**Files:**
- Create: `src/ui/controlador.py`
- Test: `tests/test_controlador.py`

**Interfaces:**
- Consumes: `src.scenario.escenario.Unidad` (campos `id`, `bando`, `tipo`, `posicion`);
  `src.scenario.loader.cargar_escenario`.
- Produces: `class ErrorControlador(Exception)`;
  `unidades_con_posiciones(unidades: tuple, unidad_a_id: str, pos_a: tuple, unidad_b_id: str, pos_b: tuple) -> tuple`;
  `portador_unidad_id(estado, unidad_a, unidad_b) -> str | None`;
  `recurso_pos_inicial(escenario) -> tuple`. Usadas por `CanvasEscenario`/`AppTacticalGrid`
  (Tarea 6) y por las Tareas 4-5 (partida/adversarial).

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# tests/test_controlador.py
import os
import unittest
from dataclasses import replace

from src.scenario.escenario import Unidad
from src.scenario.loader import cargar_escenario
from src.ui.controlador import (
    unidades_con_posiciones, portador_unidad_id, recurso_pos_inicial,
)
from tests.base import RAIZ


def ruta_config(nombre):
    return os.path.join(RAIZ, "config", nombre)


class FakeEstado:
    def __init__(self, portador):
        self.portador = portador


class TestUnidadesConPosiciones(unittest.TestCase):
    def setUp(self):
        self.unidades = (
            Unidad(id="A1", bando="A", tipo="estandar", posicion=(0, 0)),
            Unidad(id="A2", bando="A", tipo="estandar", posicion=(0, 1)),
            Unidad(id="B1", bando="B", tipo="estandar", posicion=(1, 0)),
        )

    def test_reemplaza_solo_las_indicadas(self):
        resultado = unidades_con_posiciones(self.unidades, "A1", (3, 3), "B1", (4, 4))
        por_id = {u.id: u.posicion for u in resultado}
        self.assertEqual(por_id, {"A1": (3, 3), "A2": (0, 1), "B1": (4, 4)})


class TestPortadorUnidadId(unittest.TestCase):
    def test_bando_a(self):
        unidad_a = Unidad(id="A1", bando="A", tipo="estandar", posicion=(0, 0))
        unidad_b = Unidad(id="B1", bando="B", tipo="estandar", posicion=(1, 1))
        self.assertEqual(portador_unidad_id(FakeEstado("A"), unidad_a, unidad_b), "A1")
        self.assertEqual(portador_unidad_id(FakeEstado("B"), unidad_a, unidad_b), "B1")
        self.assertIsNone(portador_unidad_id(FakeEstado(None), unidad_a, unidad_b))


class TestRecursoPosInicial(unittest.TestCase):
    def test_sin_portador_devuelve_la_posicion_del_recurso(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        self.assertEqual(recurso_pos_inicial(escenario), escenario.recurso)

    def test_con_portador_devuelve_la_posicion_de_esa_unidad(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        portador_id = escenario.unidades[0].id
        escenario_con_portador = replace(escenario, portador_recurso=portador_id)
        self.assertEqual(
            recurso_pos_inicial(escenario_con_portador), escenario.unidades[0].posicion)
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run: `python -m unittest tests.test_controlador -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'src.ui.controlador'`)

- [ ] **Step 3: Implementar `src/ui/controlador.py`**

`ErrorControlador(Exception)` sin lógica adicional. `unidades_con_posiciones` recorre `unidades` y
usa `dataclasses.replace(u, posicion=tuple(pos_a))` (o `pos_b`) cuando `u.id` coincide; devuelve una
tupla nueva. `portador_unidad_id` traduce el bando de `estado.portador` ("A"/"B"/None) al `id` de
`unidad_a` o `unidad_b`, o `None`. `recurso_pos_inicial` busca en `escenario.unidades` la unidad con
`id == escenario.portador_recurso` cuando ese campo no es `None`, y si no, devuelve
`escenario.recurso`.

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run: `python -m unittest tests.test_controlador -v`
Expected: OK (5 pruebas)

- [ ] **Step 5: Commit**

```bash
git add src/ui/controlador.py tests/test_controlador.py
git commit -m "feat(ui): agregar controlador con helpers de renderizado"
```

---

## Task 3: Controlador — modo búsqueda

**Files:**
- Modify: `src/ui/controlador.py`
- Test: `tests/test_controlador.py`

**Interfaces:**
- Consumes: `src.game.navegacion.ProblemaNavegacion`; `main.resolver_busqueda`,
  `main.normalizar_algoritmo_busqueda` (import `main`); `src.game.verificador.verificar_solucion`;
  `ErrorControlador` (Tarea 2).
- Produces: `resolver_busqueda_gui(escenario, unidad_id: str, objetivo: tuple, algoritmo: str, heuristica: str = "manhattan", k: int = 2) -> tuple[ResultadoBusqueda, InformeVerificacion]`.
  Usada por la pestaña Búsqueda (Tarea 7).

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# agregar a tests/test_controlador.py
from src.ui.controlador import ErrorControlador, resolver_busqueda_gui


class TestResolverBusquedaGui(unittest.TestCase):
    def test_bfs_resuelve_el_caso_del_obstaculo(self):
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        resultado, informe = resolver_busqueda_gui(
            escenario, "A1", (2, 4), "BFS")
        self.assertTrue(resultado.exito)
        self.assertEqual(resultado.costo, 8, f"esperado: 8; obtenido: {resultado.costo}")
        self.assertTrue(informe.valido, informe.problemas)

    def test_unidad_inexistente_lanza_error_controlador(self):
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        with self.assertRaises(ErrorControlador):
            resolver_busqueda_gui(escenario, "ZZZ", (2, 4), "BFS")

    def test_algoritmo_desconocido_lanza_error_controlador(self):
        escenario = cargar_escenario(ruta_config("caso_obstaculo.json"))
        with self.assertRaises(ErrorControlador):
            resolver_busqueda_gui(escenario, "A1", (2, 4), "MAGIA")
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run: `python -m unittest tests.test_controlador -v`
Expected: FAIL (`ImportError: cannot import name 'resolver_busqueda_gui'`)

- [ ] **Step 3: Implementar `resolver_busqueda_gui` en `src/ui/controlador.py`**

Busca en `escenario.unidades` la unidad con `id == unidad_id`; si no existe, lanza
`ErrorControlador(f"La unidad {unidad_id!r} no existe en el escenario.")`. Construye
`ProblemaNavegacion(escenario.tablero, unidad.posicion, tuple(objetivo))`. Llama a
`main.resolver_busqueda(problema, algoritmo, heuristica, k)` dentro de un `try/except ValueError as
error`, relanzando `ErrorControlador(str(error))`. Llama a
`verificar_solucion(escenario.tablero, resultado, unidad.posicion, tuple(objetivo))` y devuelve
`(resultado, informe)`.

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run: `python -m unittest tests.test_controlador -v`
Expected: OK (8 pruebas en total)

- [ ] **Step 5: Commit**

```bash
git add src/ui/controlador.py tests/test_controlador.py
git commit -m "feat(ui): agregar resolver_busqueda_gui al controlador"
```

---

## Task 4: Controlador — modo adversarial

**Files:**
- Modify: `src/ui/controlador.py`
- Test: `tests/test_controlador.py`

**Interfaces:**
- Consumes: `main._preparar_fase_4` (import `main`); `src.adversarial.agent.MinimaxAgent`;
  `ErrorControlador` (Tarea 2).
- Produces: `preparar_estado_inicial(escenario, profundidad=None, usar_poda=None) -> tuple[EstadoJuego, Unidad, Unidad, int, bool, tuple | None]`;
  `evaluar_adversarial(escenario, profundidad=None, usar_poda=None) -> dict` con claves `estado`,
  `accion`, `metricas`, `unidad_a`, `unidad_b`, `ignoradas` (tupla de ids fuera del modelo 1 vs 1).
  Usadas por la pestaña Adversarial (Tarea 8) y por `iniciar_partida` (Tarea 5).

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# agregar a tests/test_controlador.py
from dataclasses import replace as _replace
from src.models.board import Board
from src.scenario.escenario import Escenario
from src.ui.controlador import (
    preparar_estado_inicial, evaluar_adversarial,
)


class TestPrepararEstadoInicial(unittest.TestCase):
    def test_falta_unidad_de_un_bando_lanza_error_controlador(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        solo_a = _replace(escenario, unidades=tuple(
            u for u in escenario.unidades if u.bando == "A"))
        with self.assertRaises(ErrorControlador):
            preparar_estado_inicial(solo_a)


class TestEvaluarAdversarial(unittest.TestCase):
    def test_caso_minimo_7_profundidad_1_agarra_el_recurso(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        resultado = evaluar_adversarial(escenario, profundidad=1)
        self.assertEqual(resultado["accion"], (2, 2),
                          f"esperado: (2, 2); obtenido: {resultado['accion']}")

    def test_caso_minimo_7_profundidad_3_se_repliega(self):
        escenario = cargar_escenario(ruta_config("caso_adversarial.json"))
        resultado = evaluar_adversarial(escenario, profundidad=3)
        self.assertEqual(resultado["accion"], (1, 1),
                          f"esperado: (1, 1); obtenido: {resultado['accion']}")

    def test_sin_acciones_legales_lanza_error_controlador(self):
        tablero = Board(
            filas=1, columnas=1,
            tipos_terreno={"camino": {"costo": 1, "transitable": True}},
            terreno=[["camino"]], base_a=(0, 0), base_b=(0, 0))
        escenario = Escenario(
            tablero=tablero,
            unidades=(Unidad("A1", "A", "estandar", (0, 0)),
                      Unidad("B1", "B", "estandar", (0, 0))),
            turno="A", recurso=(0, 0), portador_recurso=None,
            profundidad_maxima_minimax=2, prueba=None)
        with self.assertRaises(ErrorControlador):
            evaluar_adversarial(escenario, profundidad=2)
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run: `python -m unittest tests.test_controlador -v`
Expected: FAIL (`ImportError: cannot import name 'preparar_estado_inicial'`)

- [ ] **Step 3: Implementar `preparar_estado_inicial` y `evaluar_adversarial` en `src/ui/controlador.py`**

`preparar_estado_inicial` llama a `main._preparar_fase_4(escenario, profundidad, usar_poda)`; si el
`estado` devuelto es `None`, lanza
`ErrorControlador("Se necesita al menos una unidad de cada bando (A y B) para los modos adversarial y partida.")`;
si no, devuelve la tupla tal cual. `evaluar_adversarial` llama a `preparar_estado_inicial`, calcula
`ignoradas = tuple(u.id for u in escenario.unidades if u.id not in (unidad_a.id, unidad_b.id))`,
crea `MinimaxAgent(estado.turno, profundidad=profundidad, usar_poda=usar_poda, orden_direcciones=orden)`,
llama a `agente.seleccionar_movimiento(estado, escenario.tablero, escenario.tablero.base_a,
escenario.tablero.base_b)`; si `accion is None`, lanza
`ErrorControlador("No hay acciones legales para el bando que debe actuar.")`; si no, devuelve el
dict con las claves especificadas en Interfaces.

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run: `python -m unittest tests.test_controlador -v`
Expected: OK (12 pruebas en total)

- [ ] **Step 5: Commit**

```bash
git add src/ui/controlador.py tests/test_controlador.py
git commit -m "feat(ui): agregar evaluacion adversarial al controlador"
```

---

## Task 5: Controlador — modo partida

**Files:**
- Modify: `src/ui/controlador.py`
- Test: `tests/test_controlador.py`

**Interfaces:**
- Consumes: `preparar_estado_inicial` (Tarea 4); `main._crear_agentes`, `main.MAX_TURNOS` (import
  `main`); `ErrorControlador` (Tarea 2).
- Produces: `@dataclass class PartidaEnCurso` con campos `escenario`, `tablero`, `base_a`, `base_b`,
  `unidad_a`, `unidad_b`, `agentes` (dict), `estado` (`EstadoJuego`), `turno_num: int`,
  `totales: dict`, `terminada: bool = False`, `ganador: str | None = None`;
  `iniciar_partida(escenario, profundidad=None, usar_poda=None) -> PartidaEnCurso`;
  `jugar_turno(partida: PartidaEnCurso) -> dict` (claves: `turno`, `bando`, `accion`, `valor`,
  `nodos_generados`, `nodos_evaluados`, `podas`, `profundidad`, `legal`, `detalle_legalidad`,
  `tiempo_ms`, `mensaje` (string, solo presente si el bando no tuvo acciones legales)). Muta
  `partida` in place. Usadas por la pestaña Partida (Tarea 9).

- [ ] **Step 1: Escribir las pruebas que fallan**

```python
# agregar a tests/test_controlador.py
from src.ui.controlador import PartidaEnCurso, iniciar_partida, jugar_turno


class TestPartida(unittest.TestCase):
    def test_mapa_partida_lo_gana_b_en_22_turnos(self):
        escenario = cargar_escenario(ruta_config("mapa_partida.json"))
        partida = iniciar_partida(escenario)
        self.assertIsInstance(partida, PartidaEnCurso)
        filas = []
        while not partida.terminada:
            filas.append(jugar_turno(partida))
        self.assertEqual(partida.ganador, "B",
                          f"esperado: B; obtenido: {partida.ganador}")
        self.assertEqual(partida.turno_num - 1, 22,
                          f"esperado: 22 turnos; obtenido: {partida.turno_num - 1}")
        self.assertEqual(len(filas), 22)

    def test_jugar_turno_despues_de_terminada_lanza_error_controlador(self):
        escenario = cargar_escenario(ruta_config("mapa_partida.json"))
        partida = iniciar_partida(escenario)
        while not partida.terminada:
            jugar_turno(partida)
        with self.assertRaises(ErrorControlador):
            jugar_turno(partida)

    def test_empate_por_limite_de_turnos_no_excede_max_turnos(self):
        import main as modulo_main
        tablero = Board(
            filas=1, columnas=3,
            tipos_terreno={"camino": {"costo": 1, "transitable": True}},
            terreno=[["camino", "camino", "camino"]], base_a=(0, 0), base_b=(0, 2))
        escenario = Escenario(
            tablero=tablero,
            unidades=(Unidad("A1", "A", "estandar", (0, 0)),
                      Unidad("B1", "B", "estandar", (0, 2))),
            turno="A", recurso=(0, 1), portador_recurso=None,
            profundidad_maxima_minimax=1, prueba=None)
        partida = iniciar_partida(escenario, profundidad=1)
        turnos_jugados = 0
        while not partida.terminada and turnos_jugados <= modulo_main.MAX_TURNOS + 1:
            jugar_turno(partida)
            turnos_jugados += 1
        self.assertTrue(partida.terminada)
        self.assertLessEqual(turnos_jugados, modulo_main.MAX_TURNOS)
```

- [ ] **Step 2: Correr las pruebas y verificar que fallan**

Run: `python -m unittest tests.test_controlador -v`
Expected: FAIL (`ImportError: cannot import name 'PartidaEnCurso'`)

- [ ] **Step 3: Implementar `PartidaEnCurso`, `iniciar_partida` y `jugar_turno` en `src/ui/controlador.py`**

`iniciar_partida` llama a `preparar_estado_inicial`, construye `agentes =
main._crear_agentes(profundidad, usar_poda, orden)` y `totales = {b: {"turnos": 0, "generados": 0,
"evaluados": 0, "podas": 0, "tiempo_ms": 0.0} for b in ("A", "B")}`, y devuelve un
`PartidaEnCurso` con `turno_num=1`. `jugar_turno(partida)`: si `partida.terminada`, lanza
`ErrorControlador("La partida ya terminó; usa 'Reiniciar partida' para jugar de nuevo.")`. Si no,
reproduce el cuerpo del bucle de `main.ejecutar_partida` (líneas ~429-454): pide la acción al agente
del bando activo; si `accion is None`, marca `partida.terminada = True`, `partida.ganador = None` y
devuelve `{"turno": partida.turno_num, "bando": bando, "accion": None, "mensaje": f"El bando {bando}
no tiene acciones legales; la partida se detiene."}`; si no, acumula en
`partida.totales[bando]`, busca `nuevo_estado` entre `partida.estado.sucesores(partida.tablero)`
(lanza `ErrorControlador` si la acción no aparece, igual que `main.ejecutar_partida`), arma la fila
de salida con las claves de Interfaces, actualiza `partida.estado = nuevo_estado`, y si
`partida.estado.es_terminal(partida.base_a, partida.base_b)` marca `terminada=True,
ganador=partida.estado.portador`; si no y `partida.turno_num >= main.MAX_TURNOS` marca
`terminada=True, ganador=None`. Incrementa `partida.turno_num` y devuelve la fila.

- [ ] **Step 4: Correr las pruebas y verificar que pasan**

Run: `python -m unittest tests.test_controlador -v`
Expected: OK (15 pruebas en total)

- [ ] **Step 5: Commit**

```bash
git add src/ui/controlador.py tests/test_controlador.py
git commit -m "feat(ui): agregar ciclo de partida al controlador"
```

---

## Task 6: GUI — ventana base, carga de escenario y `CanvasEscenario`

**Files:**
- Create: `src/ui/gui.py`

**Interfaces:**
- Consumes: `src.ui.colores.*` (Tarea 1); `src.ui.controlador.recurso_pos_inicial,
  unidades_con_posiciones, portador_unidad_id` (Tareas 2, 4, 5); `src.scenario.loader.cargar_escenario,
  EscenarioInvalido` (`cargar_escenario` solo lanza `EscenarioInvalido`; nunca deja pasar
  `ErrorDeCarga` sin envolverla).
- Produces: `class CanvasEscenario(tk.Canvas)` con método
  `dibujar(self, tablero, unidades, turno, recurso_pos, portador_id=None, camino=None, celda_resaltada=None)`;
  `class AppTacticalGrid(tk.Tk)` con atributos `self.escenario` (`Escenario | None`),
  `self._partida` (`None`, lo usa la Tarea 9), `self._camino_resuelto` (`tuple | None`, lo usa la
  Tarea 7), `self._celda_resaltada` (`tuple | None`, lo usa la Tarea 8), `self.canvas`
  (`CanvasEscenario`), `self.notebook` (`ttk.Notebook` con tres `ttk.Frame`:
  `self.pestana_busqueda`, `self.pestana_adversarial`, `self.pestana_partida`, todavía vacíos), y
  método `self._refrescar_canvas()`; `def main(): AppTacticalGrid().mainloop()`. Usados por las
  Tareas 7-9.

- [ ] **Step 1: Implementar `CanvasEscenario.dibujar`**

Dibuja, en este orden, sobre un canvas limpio (`self.delete("all")` al inicio): una celda por
casilla de `tablero.terreno`, coloreada con `colores.color_por_costo(costo, costo_min, costo_max)`
para terrenos transitables (`costo_min`/`costo_max` calculados sobre `tablero.tipos_terreno`) y
`colores.COLOR_OBSTACULO` para no transitables; un borde de `colores.COLOR_BANDO[bando]` sobre
`tablero.base_a` y `tablero.base_b`; si `camino` no es `None`, una línea de `colores.COLOR_CAMINO`
uniendo los centros de esas celdas; si `celda_resaltada` no es `None`, un borde de
`colores.COLOR_RESALTADO` sobre esa celda; un círculo por unidad de `unidades`, relleno
`colores.COLOR_BANDO[unidad.bando]`, con su `id` como texto, y contorno más grueso si
`unidad.id == portador_id`; y un marcador (diamante o círculo pequeño) de `colores.COLOR_RECURSO`
en `recurso_pos`. El tamaño de celda sale de `min(ancho_canvas // tablero.columnas, alto_canvas //
tablero.filas)` con un máximo razonable (p. ej. 32 px) para que mapas grandes (20x20) quepan sin
desbordar.

- [ ] **Step 2: Implementar `AppTacticalGrid.__init__` y la carga de escenario**

Construye la ventana: combobox con los `*.json` de `config/` (listados con `os.listdir`), botón
"Abrir archivo..." (`tkinter.filedialog.askopenfilename`), el `CanvasEscenario`, el
`ttk.Notebook` con las tres pestañas vacías, y un área de texto/label para mensajes de error. Un
manejador común `_cargar_escenario(self, ruta)` llama a `cargar_escenario(ruta)` dentro de un
`try/except EscenarioInvalido as error`: en caso de éxito reemplaza
`self.escenario`, pone `self._partida = None`, `self._camino_resuelto = None`,
`self._celda_resaltada = None`, y llama a `self._refrescar_canvas()`; en caso de error muestra
`error.errores` en el área de mensajes **sin tocar** `self.escenario`.

- [ ] **Step 3: Implementar `_refrescar_canvas`**

Si `self.escenario is None`, no hace nada. Si `self._partida is None` (vista estática, antes de
jugar ningún modo), llama a
`self.canvas.dibujar(self.escenario.tablero, self.escenario.unidades, self.escenario.turno,
controlador.recurso_pos_inicial(self.escenario), portador_id=self.escenario.portador_recurso,
camino=self._camino_resuelto, celda_resaltada=self._celda_resaltada)`. Si `self._partida` no es
`None` (pestaña Partida activa, Tarea 9), llama a `self.canvas.dibujar` con
`controlador.unidades_con_posiciones(self.escenario.unidades, self._partida.unidad_a.id,
self._partida.estado.pos_a, self._partida.unidad_b.id, self._partida.estado.pos_b)`,
`turno=self._partida.estado.turno`, `recurso_pos=self._partida.estado.recurso_pos`,
`portador_id=controlador.portador_unidad_id(self._partida.estado, self._partida.unidad_a,
self._partida.unidad_b)`.

- [ ] **Step 4: Verificación manual**

Run: `python -m src.ui.gui`
Expected: se abre una ventana; el combobox lista los JSON de `config/`; al elegir
`mapa_ejemplo.json` se dibuja el tablero (4x4) con sus terrenos, bases, recurso y 4 unidades; al
elegir `mapa_agnostico.json` se dibuja sin errores (confirma que el color por costo funciona con
terrenos de nombre propio); al abrir un archivo que no es JSON válido, aparece el error y el
tablero anterior sigue visible. Cerrar la ventana sin errores en consola.

- [ ] **Step 5: Commit**

```bash
git add src/ui/gui.py
git commit -m "feat(ui): agregar ventana base, carga de escenario y canvas del tablero"
```

---

## Task 7: GUI — pestaña Búsqueda

**Files:**
- Modify: `src/ui/gui.py`

**Interfaces:**
- Consumes: `controlador.resolver_busqueda_gui` (Tarea 3).
- Produces: dentro de `AppTacticalGrid`, los widgets y el método `_resolver_busqueda(self)` de la
  pestaña `self.pestana_busqueda`.

- [ ] **Step 1: Construir los widgets de la pestaña Búsqueda**

En `self.pestana_busqueda`: combobox de unidad (ids de `self.escenario.unidades`, repoblado cada
vez que se carga un escenario), spinboxes de fila/columna para el objetivo (prellenados desde
`escenario.prueba.get("objetivo")` si existe), combobox de algoritmo
(`BFS, DFS, UCS, A*, BEAM`), combobox de heurística y spinbox de `k` (habilitados solo si el
algoritmo elegido es `A*`/`BEAM`, deshabilitados en otro caso), botón "Resolver", un
`tk.Text` (solo lectura) para las métricas y el informe de verificación.

- [ ] **Step 2: Implementar `_resolver_busqueda`**

Lee los valores de los widgets; llama a `controlador.resolver_busqueda_gui(self.escenario,
unidad_id, (fila, columna), algoritmo, heuristica, k)` dentro de un `try/except ErrorControlador as
error`: en error, lo muestra en el área de texto; en éxito, guarda
`self._camino_resuelto = resultado.camino`, llama a `self._refrescar_canvas()`, y escribe en el
área de texto las métricas (`exito, costo, estados_generados, estados_expandidos,
maximo_frontera, tiempo_segundos` y `heuristica`/`k` si aplican) y el informe de verificación
(una línea `OK`/`ERROR` por comprobación de `informe.comprobaciones`, los `informe.avisos`, y el
veredicto `VÁLIDA`/`INVÁLIDA` de `informe.valido`).

- [ ] **Step 3: Verificación manual**

Run: `python -m src.ui.gui`
Expected: cargar `config/caso_obstaculo.json`, elegir unidad `A1`, objetivo `(2, 4)`, algoritmo
`BFS` → el panel muestra `costo: 8` y verificación `VÁLIDA`; el camino se dibuja sobre el tablero.
Repetir con `A*` y heurística `distancia_bfs` → mismo costo, menos estados expandidos (caso 4 del
documento técnico). Probar `BEAM` con `k=1` sobre `config/caso_beam.json` → `exito: false` y un
aviso de verificación (Beam no es completo), sin que la GUI se rompa.

- [ ] **Step 4: Commit**

```bash
git add src/ui/gui.py
git commit -m "feat(ui): agregar pestana de busqueda a la GUI"
```

---

## Task 8: GUI — pestaña Adversarial

**Files:**
- Modify: `src/ui/gui.py`

**Interfaces:**
- Consumes: `controlador.evaluar_adversarial` (Tarea 4).
- Produces: dentro de `AppTacticalGrid`, los widgets y el método `_evaluar_adversarial(self)` de la
  pestaña `self.pestana_adversarial`.

- [ ] **Step 1: Construir los widgets de la pestaña Adversarial**

En `self.pestana_adversarial`: spinbox de profundidad (prellenado desde
`escenario.profundidad_maxima_minimax`), checkbox "Poda alfa-beta" (prellenado desde
`escenario.prueba.get("usar_poda", True)`), botón "Evaluar jugada", `tk.Text` de solo lectura para
el resultado.

- [ ] **Step 2: Implementar `_evaluar_adversarial`**

Llama a `controlador.evaluar_adversarial(self.escenario, profundidad, usar_poda)` dentro de un
`try/except ErrorControlador as error`: en error lo muestra en el área de texto; en éxito, guarda
`self._celda_resaltada = resultado["accion"]`, llama a `self._refrescar_canvas()` (la unidad NO se
mueve: solo se resalta el destino propuesto), y escribe en el área de texto el bando que decide
(`resultado["estado"].turno`), la acción elegida, la legalidad (`metricas["accion_legal"]` y
`metricas["detalle_legalidad"]`), el valor obtenido, nodos generados/evaluados, podas totales,
profundidad efectiva, tiempo en ms, y una nota con `resultado["ignoradas"]` si no está vacío
(unidades fuera del modelo 1 vs 1).

- [ ] **Step 3: Verificación manual**

Run: `python -m src.ui.gui`
Expected: cargar `config/caso_adversarial.json`, profundidad `1` → acción `(2, 2)`, valor `+4600`
(caso 7); profundidad `3` → acción `(1, 1)`, valor `-4800`. Alternar la casilla de poda con
profundidad `3` → misma acción y valor con `Minimax puro` y con `Alfa-beta`, menos nodos
visitados con poda (caso 8). La celda resaltada cambia en el tablero sin mover la unidad.

- [ ] **Step 4: Commit**

```bash
git add src/ui/gui.py
git commit -m "feat(ui): agregar pestana adversarial a la GUI"
```

---

## Task 9: GUI — pestaña Partida

**Files:**
- Modify: `src/ui/gui.py`

**Interfaces:**
- Consumes: `controlador.iniciar_partida`, `controlador.jugar_turno`, `controlador.PartidaEnCurso`
  (Tarea 5).
- Produces: dentro de `AppTacticalGrid`, los widgets y los métodos `_reiniciar_partida(self)` y
  `_siguiente_turno(self)` de la pestaña `self.pestana_partida`.

- [ ] **Step 1: Construir los widgets de la pestaña Partida**

En `self.pestana_partida`: spinbox de profundidad, checkbox "Poda alfa-beta" (mismos valores por
defecto que la pestaña Adversarial), botones "Reiniciar partida" y "Siguiente turno", un
`ttk.Treeview` con columnas `turno, bando, acción, valor, nodos, podas, profundidad, legal, tiempo
(ms)`, y una etiqueta para el desenlace final.

- [ ] **Step 2: Implementar `_reiniciar_partida`**

Llama a `controlador.iniciar_partida(self.escenario, profundidad, usar_poda)` dentro de un
`try/except ErrorControlador as error` (muestra el error si falta un bando); en éxito guarda el
resultado en `self._partida`, limpia el `Treeview` y la etiqueta de desenlace, habilita "Siguiente
turno", y llama a `self._refrescar_canvas()`.

- [ ] **Step 3: Implementar `_siguiente_turno`**

Requiere `self._partida is not None`. Llama a `controlador.jugar_turno(self._partida)` dentro de un
`try/except ErrorControlador as error` (lo muestra y no hace nada más). En éxito: si la fila trae
`"mensaje"` (sin acciones legales), lo muestra en la etiqueta de desenlace; si no, agrega una fila
al `Treeview` con sus valores. Llama a `self._refrescar_canvas()`. Si `self._partida.terminada` es
`True`, deshabilita "Siguiente turno" y escribe en la etiqueta de desenlace el ganador
(`self._partida.ganador`) o "Empate" si es `None`, más el resumen acumulado por bando de
`self._partida.totales`.

- [ ] **Step 4: Verificación manual**

Run: `python -m src.ui.gui`
Expected: cargar `config/mapa_partida.json`, "Reiniciar partida", pulsar "Siguiente turno"
repetidamente → cada clic mueve una unidad en el tablero, agrega una fila a la tabla, y tras 22
turnos la etiqueta muestra "Gana B" con el resumen acumulado (ver `docs/documento_tecnico.md`,
sección 8.2); "Siguiente turno" queda deshabilitado. "Reiniciar partida" vuelve a habilitarlo y
limpia la tabla.

- [ ] **Step 5: Commit**

```bash
git add src/ui/gui.py
git commit -m "feat(ui): agregar pestana de partida a la GUI"
```

---

## Task 10: Documentación y regresión final

**Files:**
- Modify: `README.md`
- Modify: `docs/manual_de_usuario.md`
- Modify: `docs/estado_actual.md`

**Interfaces:**
- Ninguna (tarea de documentación y verificación; no agrega código).

- [ ] **Step 1: Actualizar `README.md`**

En la sección "Estructura", cambiar la línea de `src/ui/` de "Interfaz gráfica (en desarrollo)" a
"Interfaz gráfica Tkinter (busqueda/adversarial/partida)". Agregar a la sección "Ejecución" (o una
nueva sección "Interfaz gráfica") el comando `python -m src.ui.gui` con una línea de qué hace.

- [ ] **Step 2: Actualizar `docs/manual_de_usuario.md`**

Reemplazar la sección 11 ("Nota sobre la interfaz gráfica") por una guía breve: cómo lanzarla
(`python -m src.ui.gui`), cómo cargar un escenario (combobox o "Abrir archivo..."), y qué hace cada
una de las tres pestañas, en el mismo tono que el resto del manual.

- [ ] **Step 3: Actualizar `docs/estado_actual.md`**

En la tabla de la sección 1, cambiar la fila de `src/ui/gui.py` de "⏳ Pendiente" a "✅ Completo
(Tkinter: busqueda/adversarial/partida)", y quitarla de la sección 6 ("Pendientes conocidos").

- [ ] **Step 4: Regresión completa**

Run: `python -m unittest discover -s tests -t . -v`
Expected: todas las pruebas existentes más las de `test_colores.py` y `test_controlador.py` pasan
(OK), sin fallos.

Lanzar `python -m src.ui.gui` una última vez y recorrer las tres pestañas con al menos
`config/mapa_ejemplo.json`, `config/caso_beam.json`, `config/caso_adversarial.json` y
`config/mapa_grande.json` (20x20, confirma que el canvas escala sin desbordar), confirmando que no
aparece ninguna excepción en consola.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/manual_de_usuario.md docs/estado_actual.md
git commit -m "docs: documentar la interfaz grafica Tkinter"
```
