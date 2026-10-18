# TacticalGrid — Manual de usuario

Guía práctica para ejecutar el juego, visualizar búsquedas y experimentar con los algoritmos
desde la consola.

---

## 1. Requisitos

- **Python 3.10 o superior** (probado con 3.13.7).
- **Sin dependencias externas**: no hay que instalar nada con `pip` (ver `requirements.txt`).
- Opcional: `pytest` si prefieres ese formato para las pruebas (también corren con `unittest`).

## 2. Instalación

1. Descarga o clona el repositorio.
2. Abre una terminal **en la carpeta raíz del proyecto** (donde está `main.py`).
3. Verifica la instalación ejecutando la suite de pruebas (sección 8).

No requiere configuración adicional: los escenarios viven en `config/`.

## 3. Ejecución rápida

```bash
python main.py                                        # escenario por defecto: config/mapa_partida.json
python main.py config/mapa_ejemplo.json               # prueba de búsqueda del enunciado (A*)
python main.py config/caso_obstaculo.json             # búsqueda con muro + verificación
python main.py config/caso_beam.json                  # Beam Search (k configurable)
python main.py config/caso_adversarial.json           # decisión adversarial (una jugada)
python main.py config/mapa_grande.json                # partida 20x20
python main.py config/mapa_agnostico.json             # escenario con terrenos "arena"/"lava"/"roca"
```

## 4. Modos de ejecución

El modo lo decide el campo `prueba.modo` del escenario:

| Modo | Qué hace |
|---|---|
| `busqueda` | Ejecuta un algoritmo de búsqueda para llevar una unidad al objetivo y verifica la solución. |
| `partida` | Simula la partida completa por turnos entre dos agentes Minimax y resume métricas por bando. |
| `adversarial` | Evalúa el estado actual, elige una acción con Minimax/alfa-beta y verifica su legalidad (una sola jugada). |

Si el escenario es inválido (JSON malformado o incoherente), el programa **lo rechaza completo**:
lista los errores y termina con código 1 sin simular nada.

## 5. Elegir el algoritmo (el usuario decide, no el JSON)

El JSON solo **sugiere** el algoritmo por defecto; tú puedes cambiarlo en tiempo de ejecución.
Precedencia: **banderas de consola > menú interactivo > sugerencia del JSON**.

### 5.1 Con banderas

```bash
python main.py config/caso_obstaculo.json --algoritmo BFS
python main.py config/caso_obstaculo.json --algoritmo A* --heuristica distancia_bfs
python main.py config/caso_beam.json --algoritmo BEAM --k 4
python main.py config/caso_adversarial.json --algoritmo ALFA_BETA --profundidad 4
python main.py config/caso_adversarial.json --algoritmo MINIMAX          # Minimax puro (sin poda)
```

| Bandera | Valores | Aplica a |
|---|---|---|
| `--algoritmo` | `BFS`, `DFS`, `UCS`, `A*`/`ASTAR`, `BEAM` | modo `busqueda` |
| `--algoritmo` | `MINIMAX`/`MINIMAX_PURO`/`PURO` o `ALFA_BETA`/`PODA` | modos `partida`/`adversarial` |
| `--heuristica` | `manhattan`, `manhattan_pasos`, `distancia_bfs` | A* y Beam |
| `--k` | entero ≥ 1 | Beam Search |
| `--profundidad` | entero ≥ 1 | partida/adversarial |
| `--no-preguntar` | — | usa la sugerencia del JSON sin menú (automatización) |

### 5.2 Con el menú interactivo

Si ejecutas **sin banderas** y estás en una terminal interactiva, aparece un menú:

```
$ python main.py config/caso_obstaculo.json

Algoritmos disponibles para la búsqueda:
  1) BFS (anchura)
  2) DFS (profundidad)
  3) UCS (costo uniforme)
  4) A* (heurística)   <- sugerido por el JSON
  5) Beam Search (haz)
Elige el algoritmo [1-5, Enter = A_ESTRELLA]:
```

- Escribe el número y Enter, o **Enter solo** para aceptar la sugerencia del JSON.
- En los modos de juego el menú pregunta además `Minimax puro` vs `Alfa-beta` y la profundidad.
- Sin terminal interactiva (por ejemplo, en un script) no hay menú: se usa el JSON (o `--no-preguntar`).

## 6. Qué muestra cada modo

### 6.1 Búsqueda (`busqueda`)

1. Encabezado con la unidad, el inicio, el objetivo y el algoritmo elegido.
2. **Resultado** en formato JSON del enunciado: `exito`, `camino`, `costo`, `estados_generados`,
   `estados_expandidos`, `maximo_frontera`, más `acciones`, `tiempo_segundos` y (si aplica) `heuristica`, `k`.
3. **Verificación independiente**: siete comprobaciones con `[OK]`/`[ERROR]` y el veredicto
   `VÁLIDA`/`INVÁLIDA`. Para Beam sin éxito puede aparecer un `[AVISO]` si la ruta sí existía
   (es esperable: Beam no es completo).

### 6.2 Partida (`partida`)

Un renglón por turno con: bando, acción, valor de la utilidad, nodos generados/evaluados, podas,
profundidad efectiva, **Legal sí/NO** y tiempo. Al final: ganador (o empate a los 100 turnos) y un
resumen acumulado por bando.

### 6.3 Adversarial (`adversarial`)

Evalúa una sola jugada: estado evaluado, acción elegida, verificación de legalidad
(`LEGAL/ILEGAL` + motivo), valor y métricas (nodos, podas, profundidad efectiva, tiempo).

## 7. Experimentos guiados (para la sustentación)

| Experimento | Comando | Qué observar |
|---|---|---|
| BFS vs DFS | `python main.py config/caso_obstaculo.json --algoritmo BFS` y luego `--algoritmo DFS` | Mismos 8 pasos, caminos y exploración distintos |
| Ruta corta vs económica | `python main.py config/caso_bfs_vs_ucs.json --algoritmo BFS` y `--algoritmo UCS` | BFS: 4 pasos/costo 28; UCS: 6 pasos/costo 12 |
| Obstáculo y heurística | `python main.py config/caso_obstaculo.json --algoritmo A* --heuristica manhattan` y `--heuristica distancia_bfs` | Mismo costo 8; `distancia_bfs` expande menos |
| Memoria limitada (k) | `python main.py config/caso_beam.json --algoritmo BEAM --k 1` … `--k 8` | Con k=1 falla (aunque hay ruta); con k≥2 encuentra el costo 10 |
| Decisión adversarial | `python main.py config/caso_adversarial.json --profundidad 1` y `--profundidad 3` | Con d=1 agarra el recurso (+4600); con d=3 anticipa el robo y elige otra celda (−4800) |
| Minimax vs alfa-beta | `--algoritmo MINIMAX` y `--algoritmo ALFA_BETA` (d=3) | Misma acción y valor; alfa-beta poda y evalúa menos nodos |
| Orden de acciones | Mismo estado con `prueba.orden_direcciones` distinto en el JSON | Cambia la cantidad de poda sin cambiar el valor |
| Profundidad | `--profundidad 1..4` | Los nodos crecen con la profundidad; la decisión puede cambiar |
| Nombres propios de terreno | `python main.py config/mapa_agnostico.json --algoritmo UCS` | El sistema funciona con "arena"/"lava"/"roca" (costos del JSON) |

## 8. Pruebas automatizadas

```bash
python -m unittest discover -s tests -t . -v    # suite completa: 275 pruebas + 172 subtests
# o, si tienes pytest instalado:
python -m pytest -q
```

Los 10 casos mínimos del enunciado están en `tests/test_casos_minimos.py`, con sus escenarios
reproducibles en `config/caso_*.json`.

## 9. Escenarios incluidos (`config/`)

- `mapa_ejemplo.json`: escenario de la pág. 6 del enunciado (4x4).
- `mapa_partida.json`: partida rápida (6x6).
- `mapa_grande.json`: partida de gran escala (20x20, 3 unidades por bando).
- `caso_bfs_vs_ucs.json`: ruta corta (BFS) vs ruta económica (UCS).
- `caso_obstaculo.json`: muro que obliga a rodear (BFS/DFS/heurísticas).
- `caso_beam.json`: señuelo que hace fallar a Beam con k=1.
- `caso_adversarial.json`: decisión adversarial (casos 7 a 10).
- `mapa_agnostico.json`: terrenos con nombres propios ("arena", "lava", "roca").

## 10. Problemas comunes

| Síntoma | Causa y solución |
|---|---|
| "El escenario se rechaza completo…" | El JSON es inválido (malformado o incoherente). Corrige los errores listados; el algoritmo elegido no se ejecuta hasta que el escenario cargue. |
| "Algoritmo de búsqueda desconocido: 'X'. Usa: …" | Nombre mal escrito en `--algoritmo`; usa uno de la lista. |
| "No hay acciones legales…" | La unidad está encerrada (muros). Revisa el mapa. |
| Beam no encuentra solución | Con k pequeño puede descartar el camino bueno; aumenta `--k`. |
| Acentos raros en consola | Usa una terminal UTF-8 (Windows Terminal o PowerShell moderno); el programa ya reconfigura la salida a UTF-8. |
| Quiero probar mi propio mapa | Copia un JSON de `config/`, edítalo (dimensión, terrenos, costos, unidades, objetivo) y pásalo como primer argumento. Se valida todo o nada. |

## 11. Interfaz gráfica

Además de la consola, el proyecto trae una interfaz gráfica Tkinter (sin dependencias nuevas) que
consume las mismas funciones del motor que `main.py`; nada de lo descrito en las secciones
anteriores cambia por usar una u otra.

### 11.1 Lanzarla

```bash
python -m src.ui.gui
```

### 11.2 Cargar un escenario

Arriba de la ventana hay un desplegable con los JSON de `config/` (elige uno y se carga de
inmediato) y un botón "Abrir archivo..." para cargar cualquier otro escenario, por ejemplo el que
entregue el profesor durante la sustentación. Si el escenario es inválido, el área de mensajes
lista los errores y el escenario mostrado en el tablero no cambia (carga todo o nada, igual que en
consola).

El tablero se dibuja a la izquierda: terreno por costo (verde = más barato, marrón = más caro, sin
mirar el nombre del terreno), obstáculos en gris oscuro, bases con borde de color por bando,
unidades como círculos con su id y color de bando, el recurso como un punto amarillo, y el turno
actual en la esquina.

### 11.3 Las tres pestañas

- **Búsqueda:** elige la unidad, el objetivo (fila y columna), el algoritmo (BFS/DFS/UCS/A*/Beam)
  y, si aplica, la heurística y `k`. "Resolver" dibuja el camino encontrado sobre el tablero y
  muestra las métricas (éxito, costo, estados generados/expandidos, máximo de frontera, tiempo) y
  el informe de verificación independiente, igual que en consola.
- **Adversarial:** elige profundidad y si se usa poda alfa-beta. "Evaluar jugada" decide una acción
  para el bando del turno y resalta la celda destino en el tablero **sin mover la unidad**; el
  panel muestra la acción, su legalidad, el valor obtenido y las métricas (nodos, podas,
  profundidad efectiva, tiempo).
- **Partida:** elige profundidad y poda, luego "Reiniciar partida" para preparar la partida desde
  el estado inicial del escenario. Cada clic en "Siguiente turno" juega un turno: mueve la unidad
  correspondiente en el tablero y agrega una fila a la tabla (bando, acción, valor, nodos, podas,
  profundidad, legalidad, tiempo). Al terminar la partida (victoria o empate por límite de turnos)
  el botón se deshabilita y aparece el desenlace con el resumen acumulado por bando.
