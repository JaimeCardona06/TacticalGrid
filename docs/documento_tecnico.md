# TacticalGrid — Documento técnico

Juego táctico 2D por turnos con búsqueda y toma de decisiones.
Sistemas Inteligentes I — Ingeniería de Sistemas y Computación, Universidad de Caldas.

**Integrantes:** MARIANA LOPEZ FLOREZ, MAURICIO GONZALES CARMONA, Jaime Andrés Cardona Díaz.

**Versión del documento:** 1.0 — corresponde a la versión del repositorio validada con 414 pruebas automatizadas + 199 subtests.

---

## 1. Introducción y propósito

TacticalGrid es el entorno de experimentación; el sistema inteligente es quien decide dentro de él.
Sobre una cuadrícula con terrenos de costos distintos, dos bandos compiten por un recurso neutral:
recogerlo y llevarlo a la base propia antes de que el adversario lo impida.

El proyecto responde a una pregunta central: **cómo cambia la forma de decidir de un sistema
inteligente cuando pasa de encontrar una ruta, a optimizar su costo, a usar conocimiento heurístico
y, finalmente, a actuar frente a un adversario que también razona**. Cada etapa está implementada,
probada y medida:

- Búsqueda no informada: BFS y DFS.
- Búsqueda por costos: UCS.
- Búsqueda informada: A* con tres heurísticas.
- Memoria limitada: Beam Search con k = 1, 2, 4 y 8.
- Decisión adversarial: Minimax puro y Minimax con poda alfa-beta.
- Verificación independiente de soluciones y de la legalidad de las acciones.
- Selección del algoritmo en tiempo de ejecución por parte del usuario (banderas de consola o menú).

---

## 2. Modelado del problema

### 2.1 Escenario

- Cuadrícula `filas x columnas` definida por el JSON del escenario (admite cualquier dimensión válida; los escenarios de gran escala usados llegan a 20x20).
- Catálogo `tipos_terreno`: cada terreno define `costo` (positivo si es transitable) y `transitable`.
  **Los costos y la transitabilidad se leen siempre del JSON**, nunca de constantes en el código.
- La matriz `terreno` referencia el catálogo por nombre. Los nombres son libres: el sistema es
  agnóstico a ellos (probado con "arena"/"lava"/"roca" en `config/mapa_agnostico.json`).
- Bases A y B, recurso neutral y unidades con bando (`A`/`B`), tipo y posición.
- `turno` y `juego.portador_recurso` definen el estado inicial.

### 2.2 Estado de navegación (etapas uniactivas)

- **Estado:** la posición `(fila, columna)` de una unidad.
- **Acciones:** movimientos ortogonales (arriba, derecha, abajo, izquierda), en el orden fijo de `Board.DIRECCIONES`.
- **Costo:** se cobra la celda **destino** (`Board.costo_entrar`).
- **Objetivo:** alcanzar la posición meta. Las demás unidades se ignoran en estas etapas (aún no hay adversario).

### 2.3 Estado compuesto (fase adversarial)

`EstadoJuego(pos_a, pos_b, portador, turno, recurso_pos)`. Dos estados con las mismas posiciones
físicas son **estados distintos** si cambia el portador del recurso (caso mínimo 6). Incluye:

- **posiciones de TODAS las unidades** de cada bando (`pos_a`/`pos_b`: tuplas de celdas, en el orden
  del escenario),
- bando del turno,
- **portador como identidad de unidad** `(bando, índice)` (`None` si está libre) y la celda del recurso,
- **acción** = `(índice de la unidad en su bando, celda destino)`: en cada turno el bando activo
  elige qué unidad mueve y hacia dónde (modelo **N vs N**, regla "una unidad y una acción por turno").

**Ramificación y profundidad:** por turno se generan hasta `u × 4` acciones (u = unidades del bando
en turno). Con 3 unidades por bando queda acotada en **12**, así que una decisión de profundidad d
cuesta ≤ 12^d nodos sin poda y mucho menos con alfa-beta (medido: 0.3–3 ms por decisión a d=2–3 en
los mapas 3 vs 3, con cientos de nodos). El enunciado pide "al menos tres unidades por bando" y este
modelo las usa todas (`mapa_3v3.json` y `mapa_grande.json` traen 3 por bando); los escenarios 1 vs 1
conservan comportamiento y métricas.

### 2.4 Reglas del juego (deterministas)

| Situación | Regla |
|---|---|
| Movimiento | Una acción por turno: mover la unidad del bando activo a una celda vecina transitable |
| Recoger | Si la unidad pisa la celda del recurso y nadie lo lleva, pasa a ser suyo |
| Transporte | Mientras lo lleva, el recurso viaja con la unidad (su posición sigue al portador) |
| Robo | Si la unidad *entra* a la celda del rival que transporta el recurso, lo roba (ver consecuencias abajo) |
| Victoria | Gana el bando que deja el recurso en su propia base |
| Empate | Si nadie gana en `MAX_TURNOS = 100`, la partida empata (regla de cierre determinista) |
| Sin acciones | Si un bando no tiene acciones legales, la partida se detiene con aviso |
| Colisiones | No se prohíbe apilar unidades en una celda; el efecto relevante es el robo (ver limitaciones) |

**Consecuencias de la regla de robo.** Como robar es *entrar* a la celda del portador, ocurre que:

1. *Compartir celda con el portador no permite robar.* Tras un robo, el despojado queda en la misma
   celda que el nuevo portador; como no existe una acción "quedarse" ni "quitar", solo puede
   salir y volver a entrar, y para entonces el portador ya se movió. Es deliberado: si quien
   comparte celda pudiera quitarlo en el acto, el recurso cambiaría de manos en cada turno y la
   partida caería en un bucle sin fin; evitarlo exigiría un indicador de protección dentro del
   estado.
2. *El portador puede entrar a la celda de una ficha rival sin perder el recurso*, porque la ficha
   rival ya está ahí y no "entra".
3. *No existe "pasar":* un bando con una sola ficha está obligado a moverla y puede quedar en
   zugzwang.
4. *Perseguir por detrás a igual velocidad nunca alcanza al portador* (sección 5.3).

Un ejemplo real es `config/caso_robo_visual.json` con la estrategia por defecto: en el turno 2 el
portador B1 entra a la celda de A1 (efecto 2); en el turno 4, su única ficha debe moverse y queda
junto a A1 (efecto 3); en el turno 5 A1 entra a su celda y le roba el recurso, y en el turno 6 B1,
que comparte celda con A1, no puede recuperarlo y se aleja (efecto 1). Las alternativas
descartadas y sus razones están en `docs/decisiones.md`; los efectos están fijados por
`tests/test_reglas_de_robo.py`.

---

## 3. Carga y validación de escenarios

`src/scenario/loader.py` y `src/scenario/validator.py` implementan el contrato JSON del enunciado
con carga **todo o nada**: `cargar_escenario` lee, valida (9 reglas) y construye un objeto
`Escenario` inmutable; si algo falla lanza `EscenarioInvalido` con la lista de errores y no se
simula nada. El algoritmo elegido por el usuario nunca se aplica sobre un escenario rechazado
(primero se valida el archivo).

Reglas validadas: filas/columnas positivas y consistentes con la matriz; terrenos usados existen en
`tipos_terreno`; transitables con costo positivo; bases, recurso y unidades dentro del mapa;
unidades sobre celdas transitables; ids únicos; bando ∈ {A, B}; turno ∈ {A, B}; `portador_recurso`
identifica una unidad existente si no es `null`; profundidad de Minimax ≥ 1.

### 3.1 Compatibilidad con escenarios externos

El programa no depende de los nombres del ejemplo del enunciado: `config/mapa_agnostico.json` usa
**arena (costo 2), lava (costo 9) y roca (intransitable)** y se resuelve, verifica y valida sin tocar
código (sección 8.4). Cualquier JSON válido del profesor se carga directamente.

---

## 4. Algoritmos de búsqueda

Todos devuelven un `ResultadoBusqueda` con las métricas del enunciado: éxito, camino, acciones,
costo, estados generados, estados expandidos, máximo de frontera, tiempo y (cuando aplica)
heurística, k y máximo de candidatos.

### 4.1 BFS (anchura)

Explora por capas con cola FIFO; el objetivo se comprueba al **expandir**. Completo y óptimo en
número de movimientos (con pasos de costo uniforme o cuando se optimiza longitud). Registra el
camino mediante enlaces `padre` y lo reconstruye al final (O(d)).

### 4.2 DFS (profundidad)

Explora con pila LIFO; completo en grafos con control de repetidos, **no** óptimo en general.
Es la línea base para mostrar que dos algoritmos completos pueden recorrer el espacio de manera muy
distinta (caso mínimo 1).

### 4.3 UCS (costo uniforme)

Cola de prioridad por costo acumulado g; el objetivo se comprueba al sacar (óptimo en costo).
En el escenario del caso 2 prefiere la ruta larga por camino barato antes que la corta por pantano.

### 4.4 A* y heurísticas

`f(n) = g(n) + h(n)`, con parada al sacar el objetivo (óptimo con h admisible). Tres heurísticas,
todas fábricas `crear(problema) -> h(estado)` para que cambiar de heurística no toque algoritmo ni problema:

| Heurística | Qué estima | Admisibilidad | Comportamiento |
|---|---|---|---|
| `manhattan` | Manhattan × costo mínimo transitable (c_min) | Admisible y consistente para cualquier escenario válido | Se degrada a UCS cuando c_min es mucho menor que los costos típicos; no ve los muros |
| `manhattan_pasos` | Manhattan sin escalar (número de pasos) | Solo si todo paso cuesta ≥ 1 (no general) | Útil para comparar y justificar la escalada |
| `distancia_bfs` | Pasos reales rodeando muros (BFS desde el objetivo) × c_min | Admisible y consistente; **domina** a Manhattan | Preprocesamiento O(f·c) una vez; expande menos cuando hay muros |

Análisis completo (qué información usa cada una, por qué es admisible/consistente, cuándo orienta
bien y cuándo pierde discriminación) en los docstrings de `src/search/heuristics.py`.

### 4.5 Beam Search (memoria limitada)

Búsqueda por niveles conservando los k mejores candidatos por `g + h`. No es completo ni óptimo:
puede descartar para siempre el camino que luego resultaba conveniente (por eso `exito=False` no
prueba que no exista ruta). Políticas del equipo: orden por `g + h`; un estado expandido no se
reconsidera; ante duplicados en un nivel se conserva el de menor g; la meta se comprueba al expandir;
el máximo de frontera queda acotado por k y se registra `maximo_candidatos` (memoria transitoria real
del nivel antes de podar).

### 4.6 Verificador independiente de soluciones

`src/game/verificador.py` recalcula todo por su cuenta (lee solo la matriz de terreno y el catálogo
crudos, sin usar métodos de Board ni de los algoritmos):

1. forma del camino, 2. inicio y fin, 3. celdas dentro del mapa y transitables,
4. pasos a celdas vecinas (4 direcciones), 5. costo = suma de costos de celdas destino,
6. acciones coherentes con los pasos, 7. métricas coherentes.

Si la búsqueda falla, comprueba con un relleno de alcanzabilidad independiente si realmente no existe
ruta: para BFS/DFS/UCS/A* fallar con ruta existente es un error; para Beam es solo un aviso (no es
completo). La opción se ejecuta en cada prueba de búsqueda y se imprime el informe `[OK]/[ERROR]`.

---

## 5. Lógica adversarial

### 5.1 Minimax y poda alfa-beta

- `minimax_puro`: explora el árbol completo hasta la profundidad dada alternando MAX (bando A) y MIN (bando B).
- `minimax_alphabeta`: mismo resultado con cortes alfa/beta; en el caso 8 recorre menos de la mitad de los nodos del árbol.
- **MIN no está en desventaja frente a MAX:** ambos bandos usan el mismo modelo de estado, las mismas reglas y la misma utilidad (siempre desde la perspectiva de A), y juegan con el mismo `MinimaxAgent` e idénticos parámetros (profundidad, poda y orden); MAX y MIN son solo roles (maximizar/minimizar) dentro del árbol.
- En cada turno el bando activo elige **qué unidad mueve y hacia dónde** (modelo N vs N): la ramificación es unidades del bando × 4 direcciones (≤ 12 con 3 por bando).
- La profundidad es configurable sin tocar código (JSON `juego.profundidad_maxima_minimax`, bandera `--profundidad` o menú).
- El orden de generación de acciones es parametrizable (`orden_direcciones`): cambiar el orden cambia la cantidad de poda (caso 9).

### 5.2 Función de utilidad (desde la perspectiva de MAX = A)

Jerarquía implementada en `src/adversarial/utility.py`:

1. **Victoria/derrota:** +10000 si A lleva el recurso a su base; −10000 si lo logra B. Dentro del
   árbol, `minimax._valor_de_hoja` suma la profundidad restante a la victoria (±(10000 + p)): ganar
   antes vale más y perder después duele menos; así el portador a un paso de su base entra en
   lugar de pasar el turno con otra unidad.
2. **A transporta:** 5000 − 100 × distancia de A a su base (quiere acercarse).
3. **B transporta:** −(5000 − 100 × distancia de B a su base) (A quiere que B esté lejos).
4. **Recurso libre:** (distancia de B al recurso − distancia de A al recurso) × 50 (carrera por la captura).

La utilidad no premia la proximidad entre unidades: el mecanismo relevante es el robo al pisar la
celda del portador (limitación discutida en la sección 10).

### 5.3 Agente, métricas y verificación de legalidad

`MinimaxAgent` envuelve la búsqueda adversarial y reporta por turno: acción, valor obtenido, tiempo,
nodos visitados/generados/evaluados, podas (alfa, beta y totales) y **profundidad efectiva**
(mayor nivel realmente evaluado; puede ser menor que la pedida si el juego termina antes).
Además, `verificar_accion` comprueba con datos crudos del tablero que la acción elegida sea legal
—la unidad indicada existe en su bando y la celda destino es su vecina ortogonal, está dentro del
mapa y es transitable—, sin confiar en los sucesores generados por la
propia búsqueda. El resultado alimenta la columna `Legal sí/NO` de la partida y la línea
`Verificación de legalidad` del modo adversarial.

**Desempate por avance (solo en las partidas).** Cuando varias acciones tienen *exactamente* el
mismo valor Minimax, el agente de partida no se queda con la primera del orden de generación (eso
hacía que, si nada cambiaba el valor, se moviera siempre la primera unidad: fichas que
"deambulan"): elige la que más acerca a su bando a su objetivo (`src/adversarial/desempate.py`).
La clave usa **distancias reales rodeando muros** (BFS), no Manhattan, y depende de quién lleva el
recurso:

| Situación | Clave (menor es mejor) |
|---|---|
| Recurso libre | (distancia de la unidad más cercana al recurso, suma de las distancias de todas) |
| Lo lleva el propio bando | (distancia del portador a su base, suma de las distancias de las demás unidades al portador) |
| Lo lleva el rival (estrategia `persecucion`, por defecto) | (distancia de la unidad más cercana al portador, suma de las distancias de todas) |
| Lo lleva el rival (estrategia `intercepcion`, opcional) | (menor **holgura de intercepción** de sus unidades, distancia de la unidad más cercana al portador, suma de las holguras) |

**Cómo roba un bando: dos estrategias, y gana la que mejor juega.** La regla de robo es del
modelo (una unidad que entra a la celda del portador rival le quita el recurso) y no cambia; lo que
el desempate decide es *cómo buscar esa oportunidad* cuando el rival lleva el recurso. Hay dos
estrategias (`ESTRATEGIAS_DE_ROBO`, parámetro `estrategia_robo` del agente y campo opcional
`prueba.estrategia_robo` del JSON; el valor `"ninguna"` apaga el desempate para poder compararlo):

- **`persecucion` (por defecto):** acercarse al portador (distancia real, rodeando muros).
- **`intercepcion`:** predecir la ruta más corta del portador a su base (`ruta_hacia_la_base`) y
  dirigirse a un punto de ella al que se llegue a tiempo. Para cada unidad se mide la **holgura de
  intercepción**

      holgura = min sobre m ≥ 1 de ( d(unidad, ruta[m]) − m )

  donde `ruta[m]` es la celda del portador tras m movimientos suyos y `d` es la distancia real
  (BFS). Una holgura ≤ 0 significa que la unidad llega a tiempo a un punto de la ruta (m − 1
  movimientos para quedar adyacente y 1 para entrar a su celda) y puede robar. Perseguir por detrás
  da siempre ≥ 1: a igual velocidad el portador se aleja y la perseguidora nunca queda adyacente
  en su turno.

*Primera evidencia (portador pasivo).* En 3 914 configuraciones aleatorias con un portador que
sigue su ruta sin reaccionar, interceptar logra el robo en el **71.8 %** y perseguir en el
**49.7 %**; y en el escenario `config/caso_intercepcion.json` (una ficha detrás y otra por delante
de la ruta) interceptar gana donde perseguir no puede: **A le roba el recurso a B en el turno 55 y
gana en 57 turnos; con persecución B gana en 28 turnos sin ningún robo.**

*Segunda evidencia (partidas completas, la que decide).* Contra un portador que también decide con
Minimax el resultado se invierte. `experimentos/comparar_desempates.py` (250 escenarios
aleatorios válidos, 4 a 14 de lado, 0 a 30 % de muros, 1 a 3 unidades por bando, semilla 77;
0 acciones ilegales y 0 excepciones en todos los modos) da:

| Desempate | Empates (d=3) | Robos (d=3) | Empates (d=2) |
|---|---|---|---|
| Ninguno (primera acción del orden) | 43 % | 168 | 40 % |
| **Persecución (por defecto)** | **19 %** | 490 | **34 %** |
| Intercepción | 31 % | 365 | 57 % |

Una defensora que se coloca *por delante* bloquea al portador (si este avanza queda adyacente y le
roban; si espera, no progresa) y la partida se estanca, mientras que la que persigue por detrás lo
deja avanzar y aprovecha sus errores. **Conclusión:** la mejor jugada aislada (interceptar) no es la
mejor política contra un rival que reacciona; se eligió la persecución por defecto y la intercepción
queda disponible y probada para escenarios como `caso_intercepcion.json`. Con profundidad 2 los
agentes no ven que un robo se puede recuperar con una segunda ficha, y se pasan el recurso de uno a
otro (1 364 robos en 250 partidas); con profundidad 3 son 490. Es genérico: usa solo el tablero, las
bases y las posiciones del JSON, con distancias reales (muros incluidos), cualquier tamaño y
cualquier número de unidades.

El desempate **solo decide entre acciones óptimas empatadas**: nunca cambia el valor Minimax, no
cuenta en las métricas de nodos (las acciones se comparan con alfa-beta en la ventana estrecha
(valor − 0.5, valor + 0.5)) y, si la clave también empata, gana la primera del orden. La decisión
adversarial suelta (modo `adversarial`) no lo usa, para que los casos mínimos 7 a 10 comparen
Minimax y alfa-beta exactamente. Pruebas: `tests/test_desempate.py`.

**Por qué no se debilitó la regla de robo.** Hay empates "por equilibrio" (`mapa_3v3.json`,
`mapa_grande_simetrico.json`) porque, con ambos bandos adyacentes al recurso, quien lo recoge
primero es robado. Es el *mismo mecanismo* que hace funcionar el caso mínimo 7 (en
`caso_adversarial.json`, A1 y B1 están pegados al recurso y "lo mejor según Minimax no es ir
directo a él"). Cualquier regla que protegiera al primero en recoger (inmunidad de un turno,
robo solo con superioridad numérica) eliminaría ese caso exigido por el enunciado; el equilibrio es
el resultado racional de las reglas, no un fallo del agente.

---

## 6. Selección del algoritmo en tiempo de ejecución

Regla del proyecto: **el usuario elige el algoritmo**, no el JSON (el JSON solo sugiere el valor por
defecto). Precedencia: **banderas de consola > menú interactivo > sugerencia del JSON**.

- Banderas: `--algoritmo`, `--heuristica`, `--k`, `--profundidad`, `--no-preguntar`.
- Sin banderas y con terminal interactiva, se muestra un menú numerado (Enter acepta la sugerencia). Para A*/Beam se pregunta además la heurística y, en Beam, el ancho k; con `--algoritmo` dado se pregunta solo lo que falte, y `--no-preguntar` o la ausencia de terminal lo desactivan.
- Sin terminal interactiva (automatización, CI), se usa directamente el JSON.
- La interfaz gráfica (en desarrollo por otro integrante) consume la misma API:
  `resolver_busqueda(problema, algoritmo, heuristica, k)` y
  `ejecutar_busqueda(...)`, `ejecutar_partida(..., profundidad, usar_poda)`,
  `ejecutar_adversarial(..., profundidad, usar_poda)`.

---

## 7. Metodología experimental

1. **Datos reproducibles:** cada caso y experimento vive en un escenario JSON de `config/` y declara
   su estado inicial fijo (mapa, unidades, recurso, objetivo). Los tiempos se miden con
   `time.perf_counter`; las corridas de esta máquina dan milisegundos por decisión, de modo que las
   comparaciones relevantes son de nodos y podas, no de tiempo absoluto.
2. **Contraste esperado vs obtenido:** `tests/test_casos_minimos.py` ejecuta los 10 casos del
   enunciado y cada aserción incluye el valor esperado y el obtenido en su mensaje de fallo.
3. **Verificación independiente:** cada solución de búsqueda pasa por el verificador (7 comprobaciones).
4. **Suite:** 414 pruebas + 199 subtests (`python -m unittest discover -s tests -t . -v`).

---

## 8. Resultados

### 8.1 Los 10 casos mínimos (datos reales)

**Caso 1 — BFS vs DFS** (`config/caso_obstaculo.json`, A1 (2,0) → (2,4), muro en la columna 2):

| Algoritmo | Éxito | Pasos | Costo | Generados | Expandidos | Máx. frontera |
|---|---|---|---|---|---|---|
| BFS | Sí | 8 | 8 | 18 | 17 | 4 |
| DFS | Sí | 8 | 8 | 21 | 18 | 6 |

Ambos resuelven, con caminos distintos (BFS rodea por la fila 0; DFS entra por (2,1)) y métricas de
exploración diferentes.

**Caso 2 — Ruta corta vs ruta económica** (`config/caso_bfs_vs_ucs.json`, fila 2 completa de pantano, costo 7):

| Algoritmo | Éxito | Pasos | Costo | Camino |
|---|---|---|---|---|
| BFS | Sí | **4** | **28** | (2,0) → (2,1) → (2,2) → (2,3) → (2,4) |
| UCS | Sí | **6** | **12** | (2,0) → (1,0) → (1,1) → (1,2) → (1,3) → (1,4) → (2,4) |

La ruta con menos movimientos cruza 4 pantanos (4 × 7 = 28); la ruta económica rodea por camino (6 × 2 = 12).

**Caso 3 — Obstáculo y heurística:** entre A1 (2,0) y (2,4) la Manhattan es **4**, pero el muro obliga
a rodear: la ruta real es de **8 pasos, costo 8** (el doble de la distancia aparente).

**Caso 4 — Comparación de heurísticas** (mismo escenario, mismo costo óptimo 8):

| Heurística | Costo | Generados | Expandidos |
|---|---|---|---|
| `manhattan` | 8 | 18 | 17 |
| `manhattan_pasos` | 8 | 18 | 17 |
| `distancia_bfs` | 8 | **16** | **13** |

`distancia_bfs` (que ve el muro) domina a Manhattan y expande menos estados sin perder optimalidad.

**Caso 5 — Beam Search** (`config/caso_beam.json`; UCS confirma que existe ruta de costo 10):

| Configuración | Éxito | Costo | Generados | Expandidos | Máx. haz | Máx. candidatos |
|---|---|---|---|---|---|---|
| UCS (referencia) | Sí | 10 | 30 | 30 | 5 | — |
| Beam k=1 | **No** | — | 9 | 5 | 1 | 2 |
| Beam k=2 | Sí | 10 | 34 | 19 | 2 | 5 |
| Beam k=4 | Sí | 10 | 46 | 29 | 4 | 8 |
| Beam k=8 | Sí | 10 | 46 | 30 | 5 | 8 |

Con k=1 el haz descarta el camino bueno y **falla aunque la solución existe**; con k≥2 se recupera la
solución óptima y la exploración crece con k.

**Caso 6 — Estado compuesto:** con las mismas posiciones (A en (2,1), B en (3,2)) y el recurso en
(2,2), la utilidad difiere según el portador (0 con recurso libre vs 4700 con A transportándolo) y
los sucesores se comportan distinto: sin portador el recurso queda en (2,2); transportándolo, viaja
con A a (2,0).

**Caso 7 — Decisión adversarial** (`config/caso_adversarial.json`, A a un paso del recurso, B pegado
a él; la acción se reporta como `unidad → celda destino` y A1 es la única unidad de A):

| Profundidad | Acción de A | Valor | Legal |
|---|---|---|---|
| 1 (miope) | A1 → (2,2) — agarra el recurso | **+4600** | Sí |
| 3 | A1 → (1,1) — no avanza al recurso | **−4800** | Sí |

La evaluación miope agarra el recurso; con profundidad 3, Minimax anticipa que B se lo roba al
instante y prefiere replegarse. La mejor decisión deja de coincidir con "avanzar directamente al recurso".

**Caso 8 — Minimax vs alfa-beta** (profundidad 3, mismo estado):

| Algoritmo | Acción | Valor | Visitados | Generados | Evaluados | Podas |
|---|---|---|---|---|---|---|
| Minimax puro | A1 → (1,1) | −4800 | 59 | 58 | 42 | 0 |
| Alfa-beta | A1 → (1,1) | −4800 | **27** | 38 | 16 | **5** |

Misma decisión y mismo valor; alfa-beta evalúa menos de la mitad del árbol.

**Caso 9 — Orden de acciones** (profundidad 3):

| Orden de sucesores | Acción | Valor | Visitados | Podas |
|---|---|---|---|---|
| Arriba, derecha, abajo, izquierda | A1 → (1,1) | −4800 | 27 | 5 |
| Abajo, izquierda, arriba, derecha | A1 → (3,1) | −4800 | 43 | 4 |

Mismo valor óptimo; cambiar el orden altera la cantidad de poda (y puede cambiar la acción ante empates).

**Caso 10 — Profundidad** (mismo estado):

| Profundidad | Acción | Valor | Generados | Evaluados | Podas | Visitados | Prof. efectiva |
|---|---|---|---|---|---|---|---|
| 1 | A1 → (2,2) | +4600 | 4 | 4 | 0 | 5 | 1 |
| 2 | A1 → (1,1) | −4800 | 16 | 6 | 3 | 11 | 2 |
| 3 | A1 → (1,1) | −4800 | 38 | 16 | 5 | 27 | 3 |
| 4 | A1 → (1,1) | −4900 | 99 | 35 | 18 | 62 | 4 |

Los nodos crecen con la profundidad; el valor y la acción cambian al "ver" más jugadas (d=1 es
optimista porque no ve el robo). La profundidad efectiva reportada siempre iguala la realmente
evaluada.

### 8.2 Experimentos adicionales

- **BFS ≠ UCS:** caso 2 (tabla anterior): mismo escenario, BFS minimiza movimientos y UCS minimiza costo.
- **Variación de k en Beam:** caso 5; además `k=2` encuentra la solución con solo 34 nodos generados
  frente a 30 de UCS, mientras `k=1` no explora lo suficiente (9 nodos) y falla.
- **Comparación de heurísticas:** caso 4; `distancia_bfs` es la única que "ve" el muro.
- **Partidas completas (1 vs 1):** `mapa_partida.json` (6x6) — gana B en 22 turnos (A: 195 nodos
  generados, 95 evaluados, 27 podas, ~0.3 ms; B: 224 / 118 / 29, ~0.3 ms). El ganador y los turnos
  son los del modelo 1 vs 1 original; los nodos cambiaron respecto a versiones anteriores porque
  ganar antes vale más (sección 5.2) modifica la poda y el desempate por avance (sección 5.3)
  puede elegir otra acción entre las de igual valor.
- **Robo por intercepción (1 contra 2, `config/caso_intercepcion.json`, 10x10 sin obstáculos):** B
  ya lleva el recurso en (2,2) hacia su base (9,9); A tiene A1 detrás del portador y A2 por delante
  de su ruta. El JSON declara `"estrategia_robo": "intercepcion"`: **A1 roba en el turno 55 y A gana
  en 57 turnos**. Con la estrategia por defecto (`persecucion`) B gana en 28 turnos sin que nadie
  robe. Es el caso donde interceptar gana; en conjunto (sección 5.3) la persecución juega mejor.
- **Comparación de desempates en partidas completas:** `python experimentos/comparar_desempates.py`
  (tabla de la sección 5.3): persecución 19 % de empates frente a 43 % sin desempate y 31 % con
  intercepción (250 escenarios aleatorios, d=3).
- **Partidas completas (3 vs 3, todas las unidades activas y verificadas):**
  - `mapa_3v3.json` (5x5, d=2): **empata a 100 turnos** (A: 50 decisiones, 7350 nodos generados /
    3692 evaluados / 520 podas; B: 50, 7382 / 3068 / 543; ~1.5 ms por decisión). Es un empate por
    **equilibrio**: el recurso está en el centro exacto y los dos bandos llegan a la vez, cada
    uno queda adyacente al recurso y recogerlo primero lo expone al robo, así que nadie lo recoge
    (y como no existe "pasar", una ficha de cada bando se mueve de ida y vuelta). Verificado: con
    el desempate anterior (primera unidad del orden), B movía B1 hacia su base en el turno 2 en
    vez de acercar a B3 al recurso, y A lo recogía sin riesgo en el turno 3 y ganaba en 11 turnos.
  - `mapa_grande.json` (20x20) con `--profundidad 2`: gana B en 68 turnos (34 decisiones por bando,
    ~3.5k nodos generados por bando, ~2 a 5 ms por decisión).
  - `mapa_grande.json` (20x20) con la profundidad 3 sugerida por el JSON: **gana B en 68 turnos**,
    igual que con profundidad 2 (~7 a 11 ms por decisión, ~28k nodos generados por bando).
    *Hallazgo y corrección 1:* una versión anterior de la utilidad empataba aquí a 100 turnos,
    porque desde que el portador de B quedó a un paso de su base *todas* las jugadas de B valían
    −10000 en el horizonte (la victoria entraba al árbol por cualquier línea) y el desempate por
    orden de generación elegía mover otra unidad, posponiendo la victoria para siempre. Se corrigió
    haciendo que ganar antes valga más (sección 5.2); regresión en `tests/test_victoria_rapida.py`.
    *Hallazgo y corrección 2:* mientras B se llevaba el recurso, A movía siempre su primera
    unidad (A1 recorría la fila 0) porque todas sus jugadas valían lo mismo; ahora desempata por
    avance y solo se mueve la unidad más cercana, A3, persiguiendo al portador (sección 5.3).
  - **Ventaja inicial y equilibrio** (`mapa_grande.json` cambiando solo la celda del recurso;
    todos los resultados verificados): B3 parte 2 pasos más cerca del recurso que A3 (16 contra
    18; el recurso en (10,10) no está en el centro, que queda entre las celdas 9 y 10), y por eso
    gana B. Con el recurso en (9,9), A lleva esa ventaja y **gana A en 67 turnos**. Con el
    recurso en (9,10) o (10,9) las distancias son iguales (`config/mapa_grande_simetrico.json`) y
    la partida **empata por equilibrio**. Con estas reglas (robo al pisar la celda del portador,
    unidades apilables, igual velocidad) una ventaja de 2 pasos decide la partida y la igualdad
    produce un empate racional; no existe un mapa a la vez perfectamente justo y decisivo.

### 8.3 Verificación de las soluciones

Todas las soluciones exitosas de BFS, DFS, UCS, A* y Beam pasan las 7 comprobaciones del verificador
(`Resultado de la verificación: VÁLIDA`), y la suite incluye mapas aleatorios que re-ejecutan esta
comprobación. Las acciones del agente adversarial se verifican por separado en cada turno (`Legal sí`).

### 8.4 Compatibilidad con nombres de terreno propios

`config/mapa_agnostico.json`: catálogo "arena" (2), "lava" (9), "roca" (intransitable). BFS cruza la
lava (4 pasos, costo 36); UCS y A* rodean por arena (8 pasos, costo 23, verificación VÁLIDA). Un
nombre usado que no exista en el catálogo es rechazado por el validador.

---

## 9. Análisis de complejidad

| Componente | Tiempo | Espacio | Notas |
|---|---|---|---|
| `Board` (vecinos, costo, transitabilidad) | O(1) por celda | O(f·c) el tablero | Lectura O(1) del catálogo |
| Sucesores de navegación | O(1) (≤ 4 vecinos) | O(1) | |
| Sucesores del estado adversarial | O(u · d) | O(u) | u = unidades del bando en turno, d ≤ 4; recoger/robar en O(1) |
| BFS / DFS | O(V + E) | O(V) | E ≤ 4V en cuadrícula |
| UCS | O(E log E) | O(V) | Montículo (heap de prioridades) |
| A* | O(E log E) peor caso; menos con buena h | O(V) | h admisible/consistente ⇒ óptimo |
| `distancia_bfs` (preprocesamiento) | O(f·c) una vez | O(f·c) | Luego h en O(1) |
| Beam Search | O(V · b log b), b = k·4 candidatos/nivel | O(k) de frontera + O(V) de cerrados | No completo ni óptimo |
| Minimax puro | O(b^d) | O(d) pila | b = u × 4 (≤ 12 con 3 vs 3) |
| Alfa-beta | O(b^d) peor caso; O(b^(d/2)) con buen orden | O(d) | Mismo resultado que puro |
| Verificador | O(n) con n = longitud del camino; O(f·c) si no hay éxito | O(n) | Independiente de Board y algoritmos |

---

## 10. Limitaciones

1. **Empates de valor con profundidad limitada:** cuando ninguna jugada cambia el valor dentro del
   horizonte, la elección entre jugadas empatadas no la decide Minimax. La victoria ya no se
   pospone (ganar antes vale más, sección 5.2) y en las partidas las acciones empatadas se
   desempatan por avance (sección 5.3), de modo que un bando que ya no puede evitar la derrota
   se acerca al portador en lugar de deambular. Perseguir por detrás no alcanza a un portador
   de igual velocidad (como las fichas de A en `mapa_grande.json`) y, aun con el desempate, el
   19 % a 34 % de las partidas aleatorias terminan en empate (bloqueos y recuperaciones
   repetidas del recurso); si la clave también empata decide el orden de generación. Es el mismo mecanismo que hace del orden de
   acciones un experimento (caso 9); un término de persecución en la utilidad lo mitigaría (ver 2).
2. **La utilidad no penaliza la proximidad entre unidades**: las acciones de intercepción emergen
   del robo, no de un término explícito de distancia entre rivales. Cambiar los pesos es directo
   (sección 5.2) y es un experimento recomendado para la sustentación.
3. **Se permite apilar unidades** en una celda; solo se prohíben celdas no transitables. Es una
   decisión determinista coherente con el robo, pero puede producir estados "superpuestos".
4. **Beam Search no es completo**: fallar no prueba ausencia de ruta (el verificador lo trata como aviso).
5. **Tiempos absolutos** dependen de la máquina; las comparaciones del informe usan nodos, podas y
   profundidad efectiva, no milisegundos.
6. **Empate por límite de turnos** (100) es una regla de cierre del equipo, no del enunciado.
7. **Escenarios equilibrados terminan en empate:** con robo al pisar la celda del portador, unidades
   apilables e igual velocidad, el primero en recoger el recurso con un rival adyacente lo pierde, así
   que si ambos bandos llegan a la vez nadie lo recoge (`mapa_3v3.json`,
   `mapa_grande_simetrico.json`). Es el comportamiento racional de las reglas, no un fallo del agente;
   para una partida decisiva un bando necesita partir al menos 2 pasos más cerca (sección 8.2).

---

## 11. Reporte de uso de inteligencia artificial

Declaración transparente conforme al enunciado ("La omisión deliberada del uso realizado se
considerará una inconsistencia en la documentación del desarrollo"):

**Herramienta:** asistente de IA generativa integrado al entorno de desarrollo (OpenCode), usado
como apoyo en todas las fases del proyecto.

**Alcance del uso:**

- Redacción de la documentación técnica de métodos con el formato exigido (Purpose, Preconditions,
  Postconditions, Complexity, AI usage, AI intervention, Student validation) en los módulos de
  búsqueda, adversarial, verificación y carga de escenarios.
- Asistencia en la estructuración de módulos (interfaz problema–algoritmos, fábricas de heurísticas),
  en la refactorización (métricas unificadas, profundidad efectiva, parámetros explícitos para la GUI)
  y en la redacción de pruebas automatizadas (casos mínimos y de compatibilidad).
- Generación de borradores de escenarios de prueba (caso_beam, caso_adversarial, mapa_agnóstico),
  verificados empíricamente por el equipo antes de congelarlos.
- **Preferencia por ganar antes (Claude Code, Anthropic):** a partir de una observación del equipo
  (en `mapa_grande.json` una ficha de A parecía detenerse junto a un muro y la partida nunca
  terminaba), la IA reprodujo la partida, descartó la pared como causa y encontró que la
  victoria se posponía por empates de valor; propuso y escribió `minimax._valor_de_hoja`
  (±(10000 + profundidad restante)), la documentación de ese método y
  `tests/test_victoria_rapida.py`. Antes de aceptarlo se comprobó en una copia del proyecto que
  las pruebas existentes seguían en verde y que las pruebas nuevas **fallan** sin el cambio.
- **Desempate por avance (Claude Code, Anthropic):** a partir de la misma observación, la IA
  midió que las fichas de A "deambulaban" porque todas sus jugadas valían −3200 y se elegía la
  primera del orden, descartó la pared como causa (A3 tenía el camino libre), y diseñó y escribió
  `src/adversarial/desempate.py`, el método `MinimaxAgent._desempatar` y
  `tests/test_desempate.py`; también creó `config/mapa_grande_simetrico.json`. Después, ante la petición del equipo de una mejor forma de robar, midió que perseguir por detrás logra el robo en
  el 49.7 % de 3 914 configuraciones aleatorias con un portador pasivo, implementó la intercepción
  (`ruta_hacia_la_base`, `holgura_de_intercepcion`), creó `config/caso_intercepcion.json` y el
  experimento reproducible `experimentos/comparar_desempates.py`; al medir partidas completas
  comprobó que la intercepción juega *peor* (31 % de empates contra 19 % de la persecución) y
  recomendó dejar la persecución por defecto y la intercepción como estrategia opcional. Se comprobó en una
  copia que las pruebas que describen el comportamiento **fallan** sin el desempate, y se
  verificó con partidas completas que el desempate cambió el resultado de `mapa_3v3.json`
  (de victoria de A a empate por equilibrio) por una causa concreta y explicada (sección 8.2).
- **Fichas apiladas en la GUI (Claude Code, Anthropic):** ante el comentario de dos integrantes
  ("a veces hay que mover la ficha que estorba al llegar a la base"), la IA verificó con 1 440
  estados que las reglas nunca bloquean el paso (el portador siempre entra a su base), midió que
  el canvas pintaba las fichas de una misma celda en el mismo punto (la última tapaba a las
  demás, incluido el portador) y escribió `controlador.disposicion_de_fichas`, el cambio en
  `CanvasEscenario.dibujar` y `tests/test_disposicion_fichas.py`. Se comprobó que las pruebas del
  dibujo fallan con el código anterior y se jugaron cuatro escenarios completos en la GUI real
  sin ninguna ficha tapada. Después, al revisar `caso_robo_visual.json`, se vio que el recurso se
  pintaba *debajo* de la ficha que lo lleva y no se distinguía dónde estaba; ahora se pinta
  encima (marca amarilla pegada al portador).
- **Consecuencias de la regla de robo (Claude Code, Anthropic):** al replicar con el equipo los
  turnos 2 a 6 de `caso_robo_visual.json` (el despojado comparte celda con el nuevo portador y no
  puede recuperar el recurso en el sitio), la IA explicó la secuencia exacta, planteó las
  alternativas y sus costos, y, tras la decisión del equipo de mantener la regla, la documentó
  (`docs/decisiones.md`, sección 2.4) y escribió `tests/test_reglas_de_robo.py` para que lo
  documentado no pueda desviarse del código.
- **Eventos de partida y escenario de demostración (Claude Code, Anthropic):** ante la petición
  del equipo de poder *ver* el desempate y el robo, la IA buscó entre 600 escenarios aleatorios
  pequeños uno donde las tres variantes se distinguen (`config/caso_robo_visual.json`), escribió
  `main.describir_evento`, el modo `"ninguna"`, la columna de eventos de la consola y la tabla de
  la GUI, y `tests/test_eventos_de_partida.py`. Los resultados citados (14, 19 y 27 turnos) salen
  de partidas reales de esas pruebas.

**Validación realizada por el equipo (Student validation):**

- Ejecución y verificación de la suite completa: **414 pruebas y 199 subtests en verde**
  (`python -m unittest discover -s tests -t . -v`), incluyendo los 10 casos mínimos con contraste
  explícito esperado vs obtenido.
- Simulación de partidas completas en consola (1 vs 1 y 3 vs 3, en 5x5, 6x6 y 20x20) comprobando que
  cada acción reportada es legal y que las métricas coinciden con las esperadas.
- Revisión del modelo de estado y de las reglas (recoger, transportar, robar, victoria, empate) con
  escenarios de control construidos a mano.
- Verificación de que los resultados de cada algoritmo coinciden con el comportamiento esperado
  (BFS vs UCS, efecto de k en Beam, dominancia de `distancia_bfs`, equivalencia Minimax/alfa-beta).

**Responsabilidad:** cada integrante del equipo puede explicar, modificar y defender todo el código
del repositorio, incluido el generado con apoyo de IA, y conoce los experimentos aquí documentados.

---

## 12. Referencias internas

- `main.py`: punto de entrada, selección de algoritmo y despacho por modos.
- `src/models/`: `Board` (mapa, costos, vecinos) y `EstadoJuego` (estado compuesto).
- `src/scenario/`: loader y validador del contrato JSON.
- `src/search/`: BFS, DFS, UCS, A*, Beam y heurísticas.
- `src/game/`: problema de navegación y verificador independiente.
- `src/adversarial/`: Minimax, alfa-beta, utilidad y agente con verificación de legalidad.
- `tests/`: suite completa, incluidos los 10 casos mínimos (`test_casos_minimos.py`), el modelo
  N vs N (`test_nvn.py`) y la compatibilidad de nombres de terreno (`test_mapa_agnostico.py`).
- `config/`: escenarios de desarrollo, experimentos (incluido el 3 vs 3) y compatibilidad.
- `docs/decisiones.md`: convenciones compartidas (métricas, desempates y modelo adversarial N vs N).
