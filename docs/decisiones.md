# Decisiones y convenciones compartidas

Referencia corta de las convenciones que citan los módulos de `src/` y la suite de pruebas.
El desarrollo completo está en `docs/documento_tecnico.md`.

## Búsqueda uniactiva (navegación)

- **Modelo:** estado = `(fila, columna)` de una unidad (las demás se ignoran en estas etapas);
  acción = dirección ("arriba", "derecha", "abajo", "izquierda"); costo = costo de la celda
  **destino**; objetivo = alcanzar la meta.
- **Orden de vecinos:** `Board.DIRECCIONES = ((-1,0), (0,1), (1,0), (0,-1))` (arriba, derecha,
  abajo, izquierda). Cambiar el orden puede cambiar el camino de DFS y los desempates de BFS.
- **Métricas (iguales para todos los algoritmos):**
  - `estados_generados`: estados que entraron a la frontera (incluido el inicial).
  - `estados_expandidos`: estados sacados de la frontera para analizarlos (incluye la meta).
  - `maximo_frontera`: mayor tamaño de la frontera (tras generar sucesores, y al inicio).
  - `maximo_candidatos` (solo Beam): mayor cantidad de candidatos creados en un nivel antes de podar.
- **Convenciones por algoritmo:**
  - **BFS/DFS:** visitado al GENERAR; meta comprobada al SACAR; sucesores en el orden del problema.
  - **UCS:** montículo ordenado por `(g, orden de llegada)`; cerrado al sacar; si un estado mejora
    su g se reinserta (cuenta como generado) y la entrada vieja se descarta al sacarla sin contar
    como expandida; el máximo de frontera incluye las entradas viejas.
  - **A\*:** montículo ordenado por `(f = g + h, g, orden de llegada)`; mismas reglas que UCS;
    óptimo con h admisible (con h = 0 se comporta como UCS).
  - **Beam:** se ordena por `g + h`; se conservan los k mejores por nivel; un estado ya expandido
    no se repite; a igual estado en un nivel se conserva el de menor g; la meta se comprueba al
    expandir; desempate por orden de generación; no es completo ni óptimo.

## Fase adversarial (N vs N)

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
- **Utilidad (perspectiva de MAX = A):** +10000 victoria / −10000 derrota; con portador,
  ±(5000 − 100 × distancia a su base); recurso libre, 50 × (distancia de la unidad más cercana de
  B − la de A).
- **Desempates:** a igual valor, Minimax conserva la primera acción del orden de generación; por
  eso el orden afecta la poda (caso mínimo 9) y con profundidad limitada pueden aparecer empates
  de valor (limitación documentada en el documento técnico).
