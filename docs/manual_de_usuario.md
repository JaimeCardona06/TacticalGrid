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
$ python main.py config/caso_beam.json

Algoritmos disponibles para la búsqueda:
  1) BFS (anchura)
  2) DFS (profundidad)
  3) UCS (costo uniforme)
  4) A* (heurística)
  5) Beam Search (haz)   <- sugerido por el JSON
Elige el algoritmo [1-5, Enter = BEAM]:            (Enter)

Heurísticas disponibles para A*/Beam:
  1) manhattan (pasos x costo mínimo)
  2) manhattan_pasos (solo pasos)
  3) distancia_bfs (rodeando muros)
Elige la heurística [1-3, Enter = manhattan]:      (Enter)

Ancho del haz k [Enter = 2]:                       (Enter)
```

- Escribe el número y Enter, o **Enter solo** para aceptar la sugerencia del JSON.
- Si el algoritmo es **A* o Beam**, se pregunta además la **heurística**; con **Beam** se
  pregunta también el ancho **k**. Lo mismo aplica si pasas `--algoritmo A*`/`BEAM` sin las otras
  banderas; `--heuristica`, `--k` y `--no-preguntar` evitan esas preguntas.
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

Un renglón por turno con: bando, **unidad que mueve y celda destino**, valor de la utilidad, nodos
generados/evaluados, podas, profundidad efectiva, **Legal sí/NO** y tiempo. Al final: ganador (o
empate a los 100 turnos) y un resumen acumulado por bando. Juegan **todas las unidades** del
escenario (modelo N vs N; con 3 vs 3 la ramificación es ≤ 12 por turno).

### 6.3 Adversarial (`adversarial`)

Evalúa una sola jugada: estado evaluado, unidad y celda elegidas, verificación de legalidad
(`LEGAL/ILEGAL` + motivo), valor y métricas (nodos, podas, profundidad efectiva, tiempo).

## 7. Experimentos guiados (para la sustentación)

| Experimento | Comando | Qué observar |
|---|---|---|
| BFS vs DFS | `python main.py config/caso_obstaculo.json --algoritmo BFS` y luego `--algoritmo DFS` | Mismos 8 pasos, caminos y exploración distintos |
| Ruta corta vs económica | `python main.py config/caso_bfs_vs_ucs.json --algoritmo BFS` y `--algoritmo UCS` | BFS: 4 pasos/costo 28; UCS: 6 pasos/costo 12 |
| Obstáculo y heurística | `python main.py config/caso_obstaculo.json --algoritmo A* --heuristica manhattan` y `--heuristica distancia_bfs` | Mismo costo 8; `distancia_bfs` expande menos |
| Memoria limitada (k) | `python main.py config/caso_beam.json --algoritmo BEAM --k 1` … `--k 8` | Con k=1 falla (aunque hay ruta); con k≥2 encuentra el costo 10 |
| Decisión adversarial | `python main.py config/caso_adversarial.json --profundidad 1` y `--profundidad 3` | Con d=1 agarra el recurso (+4600); con d=3 anticipa el robo y elige otra celda (−4800) |
| Decisión adversarial 3 vs 3 | `python main.py config/caso_adversarial_3v3.json --profundidad 2` | Una decisión con las 6 unidades; la unidad elegida se verifica LEGAL (valor 0: carrera empatada con B, A3 y B3 a 2 pasos del recurso) |
| Minimax vs alfa-beta | `--algoritmo MINIMAX` y `--algoritmo ALFA_BETA` (d=3) | Misma acción y valor; alfa-beta poda y evalúa menos nodos |
| Orden de acciones | Mismo estado con `prueba.orden_direcciones` distinto en el JSON | Cambia la cantidad de poda sin cambiar el valor |
| Profundidad | `--profundidad 1..4` | Los nodos crecen con la profundidad; la decisión puede cambiar |
| Partida 3 vs 3 | `python main.py config/mapa_3v3.json` | Las 6 unidades juegan (3 por bando), cada acción verificada. Termina en **empate por equilibrio** (100 turnos): el recurso está en el centro exacto, ambos bandos llegan a la vez y recogerlo primero lo expone al robo, así que nadie lo recoge |
| Profundidad en 3 vs 3 | `python main.py config/mapa_grande.json --profundidad 2` y luego `--profundidad 3` | Con d=2 y con d=3 B gana en 68 turnos: su portador entra a la base en cuanto puede (ganar antes vale más). B gana porque B3 parte 2 pasos más cerca del recurso; mientras tanto A3 persigue al portador (desempate por avance) |
| **Ver el desempate y el robo** | `python main.py config/caso_robo_visual.json` (o ábrelo en la GUI, pestaña Partida) y repite cambiando en el JSON `"estrategia_robo"` | `"ninguna"`: A1 deambula arriba, no hay robo y gana B en 14 turnos. `"persecucion"` (por defecto): en el turno 5 `>>> ROBO: A1 le quita el recurso a B1` (fíjate en los turnos 2 a 6: el portador entra a la celda de A1, y tras el robo B1 comparte celda con A1 y no puede quitárselo en el sitio; ver `docs/decisiones.md`) y gana A en 19. `"intercepcion"`: el robo llega en el turno 9 y gana A en 27 |
| Robo por intercepción | `python main.py config/caso_intercepcion.json` | El JSON declara `"estrategia_robo": "intercepcion"`: B lleva el recurso hacia su base y A1 le roba en el turno 55; A gana en 57 turnos. Quita ese campo (o pon `"persecucion"`) y B gana en 28 turnos sin robo |
| Comparar desempates | `python experimentos/comparar_desempates.py --profundidad 3 --escenarios 100` | Partidas completas sobre escenarios aleatorios: persecución tiene menos empates (19 % con 250 escenarios) que sin desempate (43 %) y que intercepción (31 %) |
| Ventaja inicial y equilibrio | `python main.py config/mapa_grande_simetrico.json` | Misma partida con el recurso a igual distancia de ambos bandos: empate a 100 turnos (nadie recoge). Con el recurso en (9,9) gana A en 67 turnos |
| Nombres propios de terreno | `python main.py config/mapa_agnostico.json --algoritmo UCS` | El sistema funciona con "arena"/"lava"/"roca" (costos del JSON) |

## 8. Pruebas automatizadas

```bash
python -m unittest discover -s tests -t . -v    # suite completa: 414 pruebas + 199 subtests
# o, si tienes pytest instalado:
python -m pytest -q
```

Los 10 casos mínimos del enunciado están en `tests/test_casos_minimos.py`, con sus escenarios
reproducibles en `config/caso_*.json`.

## 9. Escenarios incluidos (`config/`)

- `mapa_ejemplo.json`: escenario de la pág. 6 del enunciado (4x4).
- `mapa_partida.json`: partida rápida 1 vs 1 (6x6).
- `mapa_3v3.json`: partida 3 vs 3 (5x5; las 6 unidades activas, d=2).
- `mapa_grande.json`: partida de gran escala (20x20, 3 unidades por bando); el recurso en (10,10) da a B una ventaja de 2 pasos y gana.
- `caso_robo_visual.json`: B ya lleva el recurso y A tiene dos fichas (7x7); pensado para **ver** el desempate y el robo cambiando `prueba.estrategia_robo` entre `"ninguna"`, `"persecucion"` e `"intercepcion"`.
- `caso_intercepcion.json`: B lleva el recurso hacia su base y A debe interceptarlo (10x10, partida 2 contra 1); declara `prueba.estrategia_robo = "intercepcion"`.
- `mapa_grande_simetrico.json`: igual que `mapa_grande.json` con el recurso en (9,10), a igual distancia de ambos bandos (empata por equilibrio).
- `caso_bfs_vs_ucs.json`: ruta corta (BFS) vs ruta económica (UCS).
- `caso_obstaculo.json`: muro que obliga a rodear (BFS/DFS/heurísticas).
- `caso_beam.json`: señuelo que hace fallar a Beam con k=1.
- `caso_adversarial.json`: decisión adversarial (casos 7 a 10).
- `caso_adversarial_3v3.json`: decisión adversarial con 3 unidades por bando (5x5).
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
unidades como círculos con su id y color de bando, el recurso y el turno actual en la esquina. El
recurso se ve **siempre**: libre, es un punto amarillo en su celda; si lo lleva una ficha, es una
marca amarilla pegada a la ficha del portador (que además tiene el contorno grueso), de modo que
se ve en qué celda y en manos de quién está. Las reglas permiten que varias unidades compartan celda (así se roba el
recurso: entrando a la celda del portador); cuando eso ocurre, las fichas se dibujan **una al lado
de la otra dentro de la celda** (más pequeñas) y nunca una encima de otra, y el portador del
recurso se distingue por su contorno grueso. Una ficha sola se ve igual que siempre.

### 11.3 Las tres pestañas

- **Búsqueda:** elige la unidad, el objetivo (fila y columna), el algoritmo (BFS/DFS/UCS/A*/Beam)
  y, si aplica, la heurística y `k`. "Resolver" dibuja el camino encontrado sobre el tablero y
  muestra las métricas (éxito, costo, estados generados/expandidos, máximo de frontera, tiempo) y
  el informe de verificación independiente, igual que en consola.
- **Adversarial:** elige profundidad y si se usa poda alfa-beta. "Evaluar jugada" decide, entre
  TODAS las unidades del bando del turno (modelo N vs N), cuál se mueve y a dónde, y resalta esa
  celda destino en el tablero **sin mover la unidad**; el panel muestra qué unidad fue elegida, su
  legalidad, el valor obtenido y las métricas (nodos, podas, profundidad efectiva, tiempo).
- **Partida:** elige profundidad y poda, luego "Reiniciar partida" para preparar la partida desde
  el estado inicial del escenario (con todas las unidades de cada bando, 1 vs 1 o 3 vs 3 según el
  escenario). Cada clic en "Siguiente turno" juega un turno: mueve la unidad elegida por el agente
  en el tablero y agrega una fila a la tabla (turno, bando, **unidad**, destino, valor, nodos,
  podas, profundidad, legalidad, tiempo, **empatadas** y **evento**). Al terminar la partida
  (victoria o empate por límite de turnos) el botón se deshabilita y aparece el desenlace con el
  resumen acumulado por bando.

  *Cómo ver el robo y el desempate.* La columna **Evento** marca lo importante de cada turno y
  pinta la fila: verde `RECOGE el recurso (X)`, amarillo `ROBO: X le quita el recurso a Y` y azul
  `GANA: X deja el recurso en su base`. La columna **Empatadas** dice entre cuántas acciones de
  igual valor Minimax tuvo que elegir el agente (el desempate por avance actúa cuando es mayor que
  1; queda vacía si el desempate está apagado). La consola imprime lo mismo: una línea
  `>>> ROBO: ...` bajo el turno y el sufijo `| Emp. N`. El portador se reconoce en el tablero por su
  contorno grueso; verás cómo cambia de bando cuando hay un robo.
