# TacticalGrid

Juego táctico 2D por turnos sobre una cuadrícula, con búsqueda (BFS, DFS, UCS,
A*, Beam Search) y decisión adversarial (Minimax y poda alfa-beta).
Proyecto de Sistemas Inteligentes I — Ingeniería de Sistemas y Computación, UCaldas.

## Integrantes

- _Completar: nombre del integrante 1_
- _Completar: nombre del integrante 2_
- _Completar: nombre del integrante 3_

## Requisitos

- **Python >= 3.10** (probado con 3.13.7).
- **Sin dependencias externas**: todo el código usa solo la biblioteca estándar
  (ver `requirements.txt`); no hay que instalar paquetes con `pip`.
- Opcional para desarrollo: `pytest` (la suite también corre con `unittest`).

## Ejecución

Desde la raíz del proyecto:

```bash
python main.py                                  # escenario por defecto: config/mapa_partida.json
python main.py config/mapa_ejemplo.json         # prueba de búsqueda del enunciado (A*)
python main.py config/caso_obstaculo.json       # búsqueda con muro + verificación de la solución
python main.py config/caso_beam.json            # Beam Search (k configurable en el JSON)
python main.py config/caso_adversarial.json     # decisión adversarial (Minimax/alfa-beta)
python main.py config/mapa_3v3.json             # partida 3 vs 3 (5x5, las 6 unidades activas)
python main.py config/mapa_grande.json          # partida 20x20 (escenario de gran escala)
```

El modo lo decide el campo `prueba.modo` del escenario:

| Modo | Qué hace |
|---|---|
| `busqueda` | Ejecuta BFS/DFS/UCS/A*/Beam sobre la unidad y el objetivo de `prueba`, y verifica la solución. |
| `partida` | Simula la partida por turnos entre dos agentes Minimax y resume métricas por bando. |
| `adversarial` | Evalúa el estado actual, elige una acción con Minimax/alfa-beta y verifica su legalidad. |

Un escenario inválido se rechaza completo (se listan los errores y no se simula nada con él).

## Selección del algoritmo (en tiempo de ejecución)

El algoritmo lo elige **el usuario**, no el JSON (el JSON solo sugiere el valor por defecto):

```bash
python main.py config/caso_obstaculo.json --algoritmo BFS
python main.py config/caso_obstaculo.json --algoritmo A* --heuristica distancia_bfs
python main.py config/caso_beam.json --algoritmo BEAM --k 4
python main.py config/caso_adversarial.json --algoritmo ALFA_BETA --profundidad 4
python main.py config/caso_adversarial.json --algoritmo MINIMAX          # Minimax puro
python main.py config/mapa_partida.json    # sin banderas: menú interactivo en consola
```

| Bandera | Valores | Aplica a |
|---|---|---|
| `--algoritmo` | `BFS`, `DFS`, `UCS`, `A*`/`ASTAR`, `BEAM` | modo `busqueda` |
| `--algoritmo` | `MINIMAX`/`MINIMAX_PURO` (puro) o `ALFA_BETA` (con poda) | modos `partida`/`adversarial` |
| `--heuristica` | `manhattan`, `manhattan_pasos`, `distancia_bfs` | A* y Beam |
| `--k` | entero ≥ 1 | Beam Search |
| `--profundidad` | entero ≥ 1 | partida/adversarial |
| `--no-preguntar` | — | usa la sugerencia del JSON sin menú (automatización) |

Sin banderas y con terminal interactiva, `main.py` muestra un **menú numerado** para elegir el algoritmo (Enter acepta la sugerencia del JSON); si el algoritmo es A* o Beam, pregunta además la heurística y, en Beam, el ancho `k` (las banderas `--heuristica`/`--k` y `--no-preguntar` evitan esas preguntas).

## Pruebas

```bash
python -m unittest discover -s tests -t . -v   # suite completa (290 pruebas + subtests)
# o, si tienes pytest instalado:
python -m pytest -q
```

Los 10 casos mínimos del enunciado están en `tests/test_casos_minimos.py`, con
sus escenarios reproducibles en `config/caso_*.json`.

## Escenarios (`config/`)

- `mapa_ejemplo.json`: escenario de la pág. 6 del enunciado (4x4).
- `mapa_partida.json`: partida rápida 1 vs 1 (6x6).
- `mapa_3v3.json`: partida 3 vs 3 (5x5, todas las unidades activas).
- `mapa_grande.json`: escenario de gran escala (20x20, 3 unidades por bando).
- `caso_bfs_vs_ucs.json`: ruta corta vs. ruta económica por costos de terreno.
- `caso_obstaculo.json`: muro que obliga a rodear (casos de heurísticas).
- `caso_beam.json`: cambio de comportamiento según k.
- `caso_adversarial.json`: decisión adversarial (casos mínimos 7 a 10).
- `mapa_agnostico.json`: compatibilidad con nombres de terreno propios ("arena", "lava", "roca").

## Estructura

```
main.py                  Punto de entrada (modos busqueda/partida/adversarial)
src/models/              Board y EstadoJuego
src/scenario/            Carga y validación de escenarios JSON
src/search/              BFS, DFS, UCS, A*, Beam Search y heurísticas
src/game/                Problema de navegación y verificador de soluciones
src/adversarial/         Minimax, poda alfa-beta, utilidad y agente
src/ui/                  Interfaz gráfica (en desarrollo)
config/                  Escenarios JSON de desarrollo y casos mínimos
tests/                   Suite de pruebas (unittest)
docs/                    Enunciado, documento técnico y documentación
```

## Documentación

- `docs/documento_tecnico.md`: modelado del problema, algoritmos de búsqueda, lógica adversarial,
  resultados de los 10 casos mínimos, análisis de complejidad y reporte de uso de IA.
- `docs/manual_de_usuario.md`: guía de uso por consola (modos, banderas, menú interactivo y
  experimentos guiados).
- `docs/decisiones.md`: convenciones compartidas (métricas, desempates y modelo adversarial N vs N).
- `docs/Primer proyecto.pdf`: enunciado del proyecto.
