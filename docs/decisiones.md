# Decisiones y convenciones compartidas

Registro único de las decisiones del equipo que el enunciado deja abiertas y de las convenciones
que citan los módulos de `src/` y la suite de pruebas. El desarrollo completo está en
`docs/documento_tecnico.md`; las dudas que sí hay que preguntarle al profesor están en
`docs/preguntas-profesor.md`.

Cada decisión debe poder defenderse en la sustentación: se indica qué se eligió y por qué.

## 1. Decisiones generales

| Decisión | Elección | Razón |
|---|---|---|
| Lenguaje | Python ≥ 3.10, solo biblioteca estándar | Es el lenguaje del repositorio; no hay que instalar nada para ejecutarlo ni para probarlo. |
| Vecindad | 4 direcciones (sin diagonales) | La heurística Manhattan supone 4 direcciones. |
| Costo de un movimiento | Se cobra el costo de la celda **destino**; el verificador usa la misma regla | Es la convención más común. Pregunta 1 de `preguntas-profesor.md`. |
| Orden de sucesores | Arriba, derecha, abajo, izquierda (`Board.DIRECCIONES`, una sola constante) | Resultados reproducibles; cambiar el orden en un solo lugar permite el experimento de "¿cambia el resultado?" en DFS, Beam y la poda. |
| Desempate en la frontera | Gana el que entró primero (contador creciente) | Reproducibilidad; evita que `heapq` compare estados. |
| Otras unidades en `busqueda` | No bloquean el paso | El enunciado dice que se ignora temporalmente al adversario; en el ejemplo oficial el objetivo (3,2) es la casilla de B1. |
| Inicio u objetivo no transitable (muro o fuera del mapa) en `busqueda` | No es error del JSON (`prueba` no está en las 9 validaciones): la búsqueda termina sin éxito y sin explorar nada ("sin ruta") | Regla determinista de "ausencia de ruta"; el escenario sigue siendo cargable. |
| Inicio igual al objetivo | Camino `[inicio]`, 0 movimientos, costo 0 | Caso límite natural: la meta se comprueba al sacar de la frontera. |
| Camino devuelto | Incluye la celda de inicio; el costo no la cuenta | Facilita la verificación del camino. |
| Formato de un sucesor | `(accion, nuevo_estado, costo)`; la acción es la dirección ("arriba", "derecha", "abajo", "izquierda") | El destino ya es el nuevo estado; la dirección dice al verificador qué movimiento se hizo. |
| Interfaz | Tkinter (`python -m src.ui.gui`) | Viene con Python; su `Canvas` basta para dibujar tablero y camino. La lógica vive en `src/ui/controlador.py`, sin tkinter, para poder probarla. |

## 2. Carga y validación del escenario

| Decisión | Elección | Razón |
|---|---|---|
| Errores de validación | Se acumulan todos; solo se corta cuando una regla es precondición de las siguientes (campos obligatorios y dimensiones) | El profesor puede traer un JSON con varios fallos y hay que explicarlos todos. Una regla que no puede evaluar algo (posición fuera del mapa, terreno desconocido) se salta porque otra regla ya lo reportó. |
| Cómo se rechaza | `cargar_escenario` lanza `EscenarioInvalido` con la lista de errores; el escenario actual solo se reemplaza si no lanzó | Una excepción no se ignora por descuido y garantiza el "todo o nada". |
| Nombres de terreno e ids de unidad | Se comparan exactamente (`"Pasto"` ≠ `"pasto"`, `"A1"` ≠ `"a1"`); el id debe ser texto no vacío | Son datos del JSON: normalizarlos podría juntar dos cosas distintas. |
| Bando y turno | Se aceptan `"A"`/`"B"` y `"a"`/`"b"`, normalizados a mayúscula con `normalizar_bando` (`src/scenario/bandos.py`); no se acepta con espacios; las claves de `bases` solo `"A"`/`"B"` | El enunciado escribe "a o b" en la validación y "A"/"B" en el JSON. Una sola función sirve para validar y para convertir, así no pueden diferir; el validador no modifica los datos. |
| `profundidad_maxima_minimax` | Ausente o `null` → 3; presente pero no entero positivo → se rechaza (comprobación extra a las 9) | Un JSON sin el campo debe cargar; una profundidad de 0, negativa o en texto rompería Minimax. |
| `tipo` de unidad ausente | Se asume `"estandar"` | El enunciado lo lista pero la validación no lo exige. |
| Campos extra en `prueba` (`algoritmo`, `heuristica`, `k`, `profundidad`, `usar_poda`, `orden_direcciones`) | Opcionales: se respetan como sugerencia si vienen; la elección del usuario (banderas, menú o interfaz) manda sobre el JSON | El formato permite campos extra que no cambien los obligatorios; un JSON del profesor sin ellos sigue funcionando. |
| Mínimos de unidades y de tamaño | No se exigen en la validación (3 por bando y 20×20 aplican a los mapas de desarrollo propios) | El ejemplo oficial tiene 2 unidades por bando y es 4×4. |
| Mapas no cuadrados | Válidos (filas y columnas se tratan por separado) | Pág. 7: la aplicación debe aceptar escenarios que cambien dimensiones. |
| Bases o recurso sobre celdas no transitables | No se rechazan (la regla 5 solo cubre unidades) | Las 9 validaciones no lo mencionan. Pregunta 2 de `preguntas-profesor.md`. |

## 3. Búsqueda uniactiva (navegación)

- **Modelo:** estado = `(fila, columna)` de una unidad (las demás se ignoran en estas etapas);
  acción = dirección; costo = costo de la celda **destino**; objetivo = alcanzar la meta.
- **Métricas (iguales para todos los algoritmos):**
  - `estados_generados`: estados que entraron a la frontera (incluido el inicial).
  - `estados_expandidos`: estados sacados de la frontera para analizarlos (**incluye la meta**).
    Así lo hace el UCS/A\* del profesor (`expandidos += 1` antes de mirar la meta) y es lo que
    reproduce la tabla de referencia (BFS: 14 generados y 11 expandidos).
  - `maximo_frontera`: mayor tamaño de la frontera, medido tras agregar los sucesores de cada
    expansión (y al inicio). En Beam es el tamaño del **haz** (≤ k).
  - `maximo_candidatos` (solo Beam): mayor cantidad de candidatos creados en un nivel antes de
    podar (la memoria transitoria real).
- **Camino:** diccionario `padre[estado] = (estado_padre, accion, costo)`; el camino se reconstruye
  una sola vez al final (copiarlo en cada nodo cuesta O(d) por inserción y multiplica la memoria).
- **Convenciones por algoritmo:**
  - **BFS/DFS:** visitado al GENERAR; meta comprobada al SACAR; sucesores en el orden del
    problema. En DFS la pila saca el **último** que entró, así que con el orden por defecto se
    explora primero la izquierda: es lo que hace el notebook del profesor y lo que produce la
    tabla de referencia (apilar al revés rompería la comparación sin aportar nada).
  - **UCS:** montículo ordenado por `(g, orden de llegada)`; un estado se cierra al SACARLO (con
    costos distintos, el primer camino hallado no tiene por qué ser el más barato); si mejora su g
    se reinserta (cuenta como generado) y la entrada vieja se descarta al sacarla sin contar como
    expandida (eliminación perezosa, porque `heapq` no modifica prioridades); el máximo de
    frontera incluye las entradas viejas. Con la convención "se cobra la celda destino" esa
    eliminación nunca se activa en un mapa (el costo de entrar a una celda no depende de por
    dónde se llega; comprobado en 2 000 mapas aleatorios), pero se mantiene porque UCS debe ser
    correcto si cambia la convención; se prueba con un grafo de juguete donde sí ocurre.
  - **A\*:** montículo ordenado por `(f = g + h, g, orden de llegada)`; mismas reglas que UCS;
    óptimo con h admisible (con h = 0 se comporta como UCS). La heurística es una función aparte
    que el algoritmo recibe por nombre o como fábrica; el problema solo expone `objetivo`.
  - **Beam:** ver sección 3.2.

### 3.1 Heurísticas

| Heurística | Definición | Por qué |
|---|---|---|
| `manhattan` (heurística 1) | `h = pasos Manhattan × c_min`, con `c_min` = menor costo entre los terrenos transitables del **catálogo** (`tipos_terreno`), leído del JSON | Manhattan sin escalar solo es admisible si todo paso cuesta ≥ 1, y la validación solo exige costo positivo (puede ser 0.5). Escalada es admisible y consistente con cualquier escenario. Se usa el catálogo (no solo los terrenos de la matriz) por ser más simple de justificar; un terreno barato sin usar baja `c_min` y debilita h, pero nunca la hace inadmisible. |
| `manhattan_pasos` | Manhattan sin escalar | Se conserva solo para comparar y demostrar su inadmisibilidad: en un mapa 2×4 con costos 0.5 el óptimo cuesta 2.0 y A\* sin escalar devuelve 2.5 (prueba en `tests/test_astar.py`). |
| `distancia_bfs` (heurística 2) | `h = pasos reales (BFS desde el objetivo, respetando muros) × c_min`; `math.inf` si desde esa celda no se llega | Nace de un **problema relajado**: Manhattan relaja muros y costos; esta relaja **solo los costos**. Es admisible, consistente y domina a Manhattan (h2 ≥ h1). Cuesta un BFS previo O(f·c) por objetivo; al comparar con Manhattan se reporta el **tiempo total** (el de `a_estrella` ya lo incluye). No se usa UCS en el preprocesamiento porque daría h\* (el costo exacto) y A\* no tendría nada que hacer. |

- **Idea descartada:** usar el costo mínimo dentro del rectángulo entre la celda y el objetivo. No
  es admisible: el camino óptimo puede salir del rectángulo para rodear terreno caro (estimaría 14
  cuando el costo real es 10).
- **Resultado a tener presente:** `distancia_bfs` expande menos que Manhattan cuando hay muros que
  obligan a rodear (`config/caso_obstaculo.json`, caso 3: 13 contra 17 expandidos, mismo costo 8), pero en mapas grandes con
  costos variables el preprocesamiento puede hacer que el tiempo total sea mayor.
- **Mejora opcional pendiente:** `h = c_objetivo + (d − 1) × c_min` (el último paso siempre cobra la
  celda objetivo); sigue siendo admisible y más ajustada, pero se prueba aparte para cambiar una
  sola cosa por experimento.

### 3.2 Beam Search

| Decisión | Elección | Razón |
|---|---|---|
| Orden de los candidatos | Por **g + h** (con la heurística elegida), no solo por h | Diferencia deliberada con el notebook 02, que ordena solo por h. Con solo h el avance es codicioso y no ve costos (cruzaría un pantano si "apunta" al objetivo); g + h usa la misma información que A\*, pero con memoria limitada. |
| Estados repetidos | Un estado ya **expandido** no se vuelve a considerar; si dos candidatos de un nivel son el mismo estado se conserva el de **menor g**; un estado podado puede volver a generarse en otro nivel | El notebook marca visitados a **todos** los candidatos al generarlos (incluso los podados), lo que bloquea para siempre estados que otro camino del haz podría haber alcanzado más barato. Esta política es la que reproduce la tabla de referencia (k = 1: 10/11/7/1; k = 2: 7/19/12/2); las del notebook no. Sin control de repetidos, k = 1 oscila sin terminar. |
| Meta | Se comprueba al **expandir** (al recorrer el haz) | Igual que UCS y A\*; las métricas de los algoritmos se cuentan igual. |
| Niveles | Se procesa **por niveles** (todos los estados del haz son del mismo nivel) | Consecuencia: es un BFS con poda, no un A\* con memoria limitada. Un k grande se comporta como BFS (menos movimientos, no menor costo): en el mapa oficial k = 4 y k = 8 pagan 14, **más** que k = 2 (7). Un haz más ancho explora más, pero eso no garantiza menor costo. |
| Completitud y optimalidad | Ninguna de las dos | Con k = 1 falla aunque exista ruta (mapa 3×3 de las pruebas); el verificador lo informa como **aviso**, no como error. |

## 4. Fase adversarial (N vs N)

- **Estado:** `EstadoJuego(pos_a, pos_b, portador, turno, recurso_pos)`, con `pos_a`/`pos_b` como
  tuplas de celdas (una por unidad del bando, en el orden del escenario).
- **Portador:** `None` si el recurso está libre; `(bando, índice)` si lo transporta una unidad
  (en el JSON, `juego.portador_recurso` identifica la unidad por su id).
- **Acción:** `(índice de la unidad en su bando, celda destino)`; una unidad y una acción por turno.
- **Ramificación:** unidades del bando en turno × 4 direcciones (≤ 12 con 3 unidades por bando).
  El orden de generación es parametrizable (`prueba.orden_direcciones` o `orden_direcciones` en el
  agente); por defecto usa `Board.DIRECCIONES`.
- **Reglas deterministas:** recoger al pisar la celda del recurso libre; mientras lo lleva, el
  recurso viaja con el portador; robar al pisar la celda del portador rival; victoria al dejar el
  recurso en la base propia; empate con `MAX_TURNOS = 100`; se permite apilar unidades.
- **Utilidad (perspectiva de MAX = A):** +10000 si gana A / −10000 si gana B; con portador,
  ±(5000 − 100 × distancia a su base); recurso libre, 50 × (distancia de la unidad más cercana de
  B − la de A).
- **Ganar antes vale más:** al evaluar una hoja terminal, `minimax._valor_de_hoja` suma la
  profundidad restante p a la victoria (±(10000 + p)): quien gana prefiere la victoria más
  cercana y quien pierde prefiere la derrota más lejana. `evaluar_estado` sigue siendo pura (±10000);
  la profundidad solo existe en el árbol. **Por qué:** sin esto, todas las jugadas que conservaban
  una victoria dentro del horizonte valían lo mismo y el desempate por orden de generación podía
  posponerla para siempre. En `mapa_grande.json` con profundidad 3, el portador de B quedaba a un
  paso de su base, la jugada ganadora valía −10000 igual que mover cualquier otra unidad (B1 era
  la primera en el orden) y la partida empataba a 100 turnos. Con el cambio termina (gana B en 68
  turnos con profundidad 2 y con 3). Pruebas: `tests/test_victoria_rapida.py`.
- **Desempates:** a igual valor, Minimax conserva la primera acción del orden de generación; por
  eso el orden afecta la poda (caso mínimo 9). Esto sigue siendo así en la decisión adversarial
  suelta (modo `adversarial` y su pestaña de la GUI), para que los casos mínimos 7 a 10 comparen
  Minimax y alfa-beta exactamente.
- **Desempate por avance (solo en las PARTIDAS):** los agentes de partida
  (`main._crear_agentes`, que también usa la GUI) entre acciones de **exactamente** el mismo
  valor eligen la que más acerca al bando a su objetivo (`src/adversarial/desempate.py`), con
  distancias reales rodeando muros: recurso libre → la unidad más cercana avanza hacia él; lo lleva
  el propio bando → avanza el portador hacia la base; lo lleva el rival → persigue o intercepta según
  `estrategia_robo` (ver abajo). **Por qué:** sin esto, si nada cambiaba el valor se movía siempre la primera unidad
  del orden (en `mapa_grande.json`, A1 recorría la fila 0 mientras B se llevaba el recurso).
  Solo decide entre acciones óptimas empatadas (nunca cambia el valor Minimax) y no cuenta en las
  métricas de nodos. Es opt-in: `MinimaxAgent(..., desempatar_por_avance=False)` por defecto.
  Pruebas: `tests/test_desempate.py`.
- **Estrategia de robo: persecución por defecto, intercepción opcional (decidido con datos):**
  cuando el rival lleva el recurso, el desempate puede *perseguir* al portador (acercarse) o
  *interceptarlo* (ir a un punto de su ruta más corta a la base al que se llegue a tiempo,
  midiendo la holgura `min sobre m ≥ 1 de (d(unidad, ruta[m]) − m)`; ≤ 0 = llega a tiempo). Contra
  un portador pasivo, interceptar roba más (71.8 % contra 49.7 % en 3 914 configuraciones) y gana
  `config/caso_intercepcion.json`; pero en **partidas completas** (`experimentos/comparar_desempates.py`,
  250 escenarios aleatorios, semilla 77, 0 acciones ilegales) la defensora que se coloca por
  delante bloquea al portador y la partida se estanca:

  | Desempate | Empates d=3 | Robos d=3 | Empates d=2 |
  |---|---|---|---|
  | Ninguno | 43 % | 168 | 40 % |
  | **Persecución (por defecto)** | **19 %** | 490 | **34 %** |
  | Intercepción | 31 % | 365 | 57 % |

  Se elige la persecución. La estrategia se cambia con el campo opcional `prueba.estrategia_robo`
  (`"persecucion"` o `"intercepcion"`; un valor inválido avisa y usa la de por defecto) o con
  `MinimaxAgent(..., estrategia_robo=...)`. Con profundidad 2 los agentes se pasan el recurso de
  uno a otro (1 364 robos en 250 partidas) porque no ven la recuperación; con profundidad 3 son 490.
- **La regla de robo NO se debilita:** entrar a la celda del portador rival le quita el recurso.
  Esa misma regla produce el empate por equilibrio en mapas simétricos (el primero en recoger con
  un rival adyacente es robado) y también sostiene el caso mínimo 7 (`caso_adversarial.json`: A1
  y B1 pegados al recurso; "lo mejor no es ir directo"). Proteger al primero en recoger (inmunidad
  de un turno, robo solo con superioridad numérica) rompería ese caso exigido por el enunciado.
- **Ventaja inicial y equilibrio:** con las reglas actuales (robo al pisar la celda del portador,
  unidades apilables, igual velocidad), recoger el recurso con un rival adyacente lo pierde. Por
  eso una ventaja de 2 pasos (o más) hasta el recurso decide la partida y la igualdad empata por
  equilibrio. Verificado cambiando solo la celda del recurso en `mapa_grande.json`:

  | Recurso en | Pasos de A3 / B3 | Resultado |
  |---|---|---|
  | (10,10) — `mapa_grande.json` | 18 / 16 | Gana B en 68 turnos |
  | (9,9) | 16 / 18 | Gana A en 67 turnos |
  | (9,10) o (10,9) — `mapa_grande_simetrico.json` | 17 / 17 | Empate a 100 turnos (nadie recoge) |

  Decisión: `mapa_grande.json` se conserva con la ventaja de B (partida decisiva, documentada) y
  `mapa_grande_simetrico.json` ofrece la versión sin ventaja. `mapa_3v3.json`, simétrico, empata
  por equilibrio. No existe un mapa a la vez perfectamente justo y decisivo.

## 5. Verificación de soluciones

- **Verificador de búsqueda** (`src/game/verificador.py`): no usa ningún método de `Board` ni de
  los algoritmos; lee solo la matriz `terreno` y el catálogo `tipos_terreno` y recalcula por su
  cuenta. Así, un error en `Board` o en un algoritmo no se hereda: se detecta (hay pruebas con
  `Board` saboteados).
- **Costos:** se comparan con `math.isclose` (0.1 + 0.2 no es exactamente 0.3).
- **Búsqueda "sin éxito":** se confirma con un relleno de alcanzabilidad independiente (sin
  costos). Si existe ruta y el algoritmo es completo (BFS, DFS, UCS, A\*) es un **problema**; si
  es Beam es solo un **aviso** (esperable: Beam no es completo).
- **Acciones adversariales:** `MinimaxAgent.verificar_accion` comprueba la legalidad con los datos
  crudos del tablero, sin confiar en los sucesores que generó la propia búsqueda.

## 6. Pendientes

| Pendiente | Dónde se resuelve |
|---|---|
| **Traza nivel por nivel de Beam** (k = 1 y k = 2) en el mapa oficial, señalando en qué nivel se poda el candidato del pantano por tener mayor g + h; la debe recorrer un integrante del equipo, no solo la IA | Documento técnico y ensayo de sustentación |
| Que cada integrante **ejecute y entienda** las pruebas que citan los campos `Student validation` (por ejemplo `python -m unittest tests.test_beam -v`), porque esas notas afirman una validación del equipo | Antes de la sustentación |
| Completar los nombres de los integrantes en `README.md` y `documento_tecnico.md` | Antes de la entrega |
| Verificar que no se generan estados inválidos durante la partida (el enunciado lo exige) | Verificador, modo partida |
| Preguntas al profesor (`preguntas-profesor.md`): cobro del movimiento y vecindad; bases/recurso sobre celdas no transitables | Cuando se pueda |
