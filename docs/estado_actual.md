# TacticalGrid — Estado actual del proyecto

Resumen rápido de **qué funciona hoy, cómo se ejecuta y cómo se prueba**. Es el punto de entrada
antes de leer `docs/documento_tecnico.md` (modelado y resultados) o `docs/manual_de_usuario.md`
(guía de uso detallada); aquí solo se responde "¿en qué quedó el proyecto y cómo lo verifico?".

Última verificación: 2026-10-19, rama `dev` (suite completa en verde).

---

## 1. Resumen de estado

| Componente | Estado |
|---|---|
| Carga y validación de escenarios JSON | ✅ Completo (9 reglas, carga todo o nada) |
| Búsqueda: BFS, DFS, UCS, A* (3 heurísticas), Beam Search | ✅ Completo |
| Verificador independiente de soluciones | ✅ Completo (7 comprobaciones) |
| Adversarial: Minimax puro y alfa-beta, utilidad, agente | ✅ Completo |
| Verificación de legalidad de acciones adversariales | ✅ Completo |
| CLI (`main.py`): banderas, menú interactivo, modos busqueda/partida/adversarial | ✅ Completo |
| Suite de pruebas automatizadas | ✅ 421 pruebas + subtests, todas en verde |
| Interfaz gráfica (`src/ui/gui.py`) | ✅ Completo (Tkinter: busqueda/adversarial/partida) |
| Nombres de los integrantes en `README.md` / `documento_tecnico.md` | ✅ Completos |

**En una frase:** el motor completo (búsqueda + decisión adversarial) funciona por consola y por
una interfaz gráfica Tkinter, ambas probadas y documentadas; no hay pendientes funcionales conocidos.

---

## 2. Cómo funciona hoy (visión funcional)

1. **Entrada:** un escenario JSON en `config/` describe el tablero, los tipos de terreno (costo y
   transitabilidad), las bases, el recurso neutral, las unidades de cada bando y qué prueba correr
   (`prueba.modo`: `busqueda`, `partida` o `adversarial`).
2. **Carga:** `src/scenario/loader.py` + `validator.py` validan el JSON completo antes de simular
   nada. Si algo falla, se listan los errores y no se ejecuta ningún algoritmo.
3. **Ejecución según el modo:**
   - `busqueda`: resuelve con el algoritmo elegido (BFS/DFS/UCS/A*/Beam) la ruta de una unidad a un
     objetivo, y el verificador independiente confirma que la solución es válida.
   - `partida`: simula turno a turno una partida completa (modelo N vs N: todas las unidades de
     cada bando) con dos agentes Minimax, hasta que alguien gane o se llegue al límite de 100
     turnos (empate).
   - `adversarial`: evalúa el estado actual y decide una sola jugada con Minimax o alfa-beta,
     verificando que sea legal.
4. **Selección del algoritmo:** la decide el usuario en tiempo de ejecución (banderas de consola >
   menú interactivo > sugerencia del JSON), nunca queda fija en el código.
5. **Salida:** por consola (JSON de resultados, tabla de verificación, tabla de turnos o reporte de
   la jugada adversarial, según el modo) o por la interfaz gráfica (tablero dibujado, camino,
   métricas y verificación en los paneles de cada pestaña).

No hay persistencia entre ejecuciones: cada corrida de `main.py` o cada carga de escenario en la
GUI parte del estado inicial declarado en el JSON.

---

## 3. Cómo ejecutarlo

Requisitos: Python ≥ 3.10 (probado con 3.13.7), sin dependencias externas (`requirements.txt` no
instala nada).

Desde la raíz del repositorio:

```bash
python main.py                                  # partida rápida por defecto (config/mapa_partida.json)
python main.py config/mapa_ejemplo.json          # búsqueda del enunciado (A*)
python main.py config/caso_obstaculo.json --algoritmo BFS
python main.py config/caso_beam.json --algoritmo BEAM --k 4
python main.py config/caso_adversarial.json --algoritmo ALFA_BETA --profundidad 4
python -m src.ui.gui                             # interfaz gráfica (Tkinter)
```

Sin banderas y en terminal interactiva aparece un menú numerado para elegir el algoritmo. El
detalle completo de banderas, menú, modos y de la interfaz gráfica está en
`docs/manual_de_usuario.md` (secciones 3 a 7 y 11).

---

## 4. Cómo probarlo

### 4.1 Suite automatizada (la forma principal de verificar que todo sigue funcionando)

```bash
python -m unittest discover -s tests -t . -v
# o
python -m pytest -q
```

Última corrida real (2026-10-19): **421 pruebas, 0 fallos, ~10 s**
(`python -m unittest discover -s tests -t .`, salida `Ran 421 tests ... OK`).

Los 10 casos mínimos exigidos por el enunciado están aislados en `tests/test_casos_minimos.py`,
cada uno con su escenario reproducible en `config/caso_*.json`, y comparan explícitamente el valor
esperado contra el obtenido. `tests/test_colores.py`, `tests/test_controlador.py` y
`tests/test_marcas_busqueda.py` cubren la capa de orquestación y las marcas de la GUI (sin tkinter
salvo las pruebas de canvas, que lo omiten si no hay pantalla).

### 4.2 Pruebas manuales guiadas (para demostrar comportamiento, no solo "pasa/no pasa")

La tabla de experimentos guiados de `docs/manual_de_usuario.md` (sección 7) da un comando por
comportamiento clave: BFS vs DFS, ruta corta vs económica, efecto de la heurística, Beam con
distintos `k`, Minimax vs alfa-beta, efecto de la profundidad, compatibilidad con terrenos propios.
Son el complemento manual a la suite automatizada cuando se quiere *ver* por qué cambia un resultado,
no solo confirmar que no se rompió nada. Los mismos experimentos pueden reproducirse desde la
interfaz gráfica (`python -m src.ui.gui`, sección 11 del manual).

### 4.3 Qué NO está cubierto todavía

- Las pruebas de los widgets Tkinter son parciales: `tests/test_marcas_busqueda.py` cubre las
  marcas de inicio/objetivo, el botón Limpiar y el cambio de pestaña; el recorrido visual completo
  de la GUI (layout, tablas, etc.) sigue siendo manual, lanzándola y recorriendo las tres pestañas.
- No hay pruebas de carga/rendimiento más allá de los escenarios 20x20 (`mapa_grande.json` y
  `mapa_grande_busqueda.json`); los tiempos reportados son orientativos y dependen de la máquina
  (ver limitaciones en `documento_tecnico.md`, sección 10).
- No hay prueba automatizada de la oscilación de `mapa_partida.json` con profundidad 1–2 (empate a
  100 turnos porque la utilidad Manhattan ignora los muros); está documentada como limitación 8 del
  documento técnico y en el manual. Con la profundidad sugerida 3, B gana en 22 turnos.

---

## 5. Mapa rápido del código

```
main.py                  Punto de entrada: parseo de banderas/menú y despacho por modo
src/scenario/             Carga y validación del contrato JSON (todo o nada)
src/models/               Board (mapa, costos, vecinos) y EstadoJuego (estado compuesto)
src/search/                BFS, DFS, UCS, A*, Beam Search y heurísticas
src/game/                  Problema de navegación + verificador independiente de soluciones
src/adversarial/           Minimax puro, alfa-beta, utilidad y agente con verificación de legalidad
src/ui/colores.py          Paleta de colores por costo (agnóstica al nombre del terreno)
src/ui/controlador.py      Orquestación de la GUI sobre el motor, sin tkinter (testeable)
src/ui/gui.py              Interfaz gráfica Tkinter: tablero, búsqueda, adversarial, partida
config/                    Escenarios JSON (desarrollo, casos mínimos, compatibilidad)
tests/                     Suite completa (unittest, compatible con pytest)
docs/                      Este documento + documento técnico + manual de usuario + enunciado
```

API del motor que consumen tanto `main.py` como la GUI (`src/ui/controlador.py`), sin que ninguna
de las dos duplique lógica de búsqueda o adversarial:
`resolver_busqueda(problema, algoritmo, heuristica, k)`, `ejecutar_busqueda(...)`,
`ejecutar_partida(..., profundidad, usar_poda)`, `ejecutar_adversarial(..., profundidad, usar_poda)`.

---

## 6. Pendientes conocidos

No hay pendientes funcionales conocidos: el motor, la GUI, la suite y la documentación están
completos y verificados.

---

## 7. Más documentación

- `docs/manual_de_usuario.md`: guía de uso por consola y por la interfaz gráfica (modos, banderas,
  menú, pestañas de la GUI, experimentos guiados).
- `docs/decisiones.md`: registro único de las decisiones del equipo (con su razón) y de los
  pendientes; `docs/preguntas-profesor.md`: dudas del enunciado que hay que consultar.
- `docs/documento_tecnico.md`: modelado del problema, algoritmos, resultados de los 10 casos
  mínimos, análisis de complejidad, limitaciones y reporte de uso de IA.
- `docs/Primer proyecto.pdf`: enunciado original del proyecto.
