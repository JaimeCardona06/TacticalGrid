# TacticalGrid — Interfaz gráfica (Tkinter)

**Estado:** aprobado para pasar a plan de implementación.
**Fecha:** 2026-10-18.

## Propósito

El enunciado (`docs/Primer proyecto.pdf`, sección "Visualización") exige una interfaz gráfica
sencilla que permita **observar y experimentar con la inteligencia del sistema**: cuadrícula,
terrenos, obstáculos, bases, recurso, unidades, bando, portador del recurso, turno actual y el
camino encontrado por una búsqueda. La calidad artística no es un criterio de evaluación relevante
(5 % de la nota grupal); la claridad para mostrar las técnicas sí.

Hoy `src/ui/gui.py` existe pero está vacío. Este documento define qué construir ahí.

## Alcance

Dentro:
- Una ventana Tkinter que carga un escenario JSON (de `config/` o un archivo externo) y permite
  ejecutar, sobre él, los tres modos del enunciado: búsqueda, adversarial (una jugada) y partida
  (turno a turno), mostrando la cuadrícula y las métricas de cada ejecución.

Fuera (decisiones explícitas para mantenerlo simple):
- No se modifican `src/search/*`, `src/game/*`, `src/adversarial/*` ni `main.py`.
- No se visualizan estados explorados/frontera (`ResultadoBusqueda` no los expone; exponerlos
  obligaría a tocar BFS/DFS/UCS/A*/Beam, ya cubiertos por 254+ pruebas). Se muestran solo el
  camino final y las métricas agregadas (generados, expandidos, máximo de frontera, tiempo).
- No hay animación de la exploración ni reproducción automática de la partida: el modo partida
  avanza con un botón "Siguiente turno" (control manual, un turno por clic).
- No hay pruebas automatizadas de la GUI (Tkinter no tiene infraestructura de test en este
  proyecto); la verificación es manual, lanzando la app contra los escenarios de `config/`.

## Arquitectura

Un único módulo `src/ui/gui.py`, lanzado con `python -m src.ui.gui`. Dos clases:

- **`CanvasEscenario`**: dibuja el tablero sobre un `tk.Canvas`. No conoce botones ni pestañas;
  solo recibe un `Escenario` (y opcionalmente un camino o una celda destino a resaltar) y pinta.
- **`AppTacticalGrid`**: ventana principal (`tk.Tk`), controles (combobox de escenario, pestañas,
  botones), y la lógica que llama a la API del motor y empuja los resultados a `CanvasEscenario`
  y a los paneles de texto/tabla.

La GUI reutiliza, sin duplicar lógica:
- `src.scenario.loader.cargar_escenario` / `EscenarioInvalido` — carga todo o nada.
- `src.game.navegacion.ProblemaNavegacion`, `src.search.*` vía `main.resolver_busqueda`,
  `src.game.verificador.verificar_solucion` — modo búsqueda.
- `src.models.state.EstadoJuego`, `src.adversarial.agent.MinimaxAgent` — modos adversarial/partida.
- De `main.py`: `normalizar_algoritmo_busqueda`, `normalizar_algoritmo_adversarial`,
  `_unidad_por_bando`, `_orden_de_prueba` (mismos alias y misma regla 1 vs 1 que la consola).

La GUI **no** llama a `ejecutar_busqueda`/`ejecutar_partida`/`ejecutar_adversarial` de `main.py`
porque esas funciones solo imprimen en consola; reimplementa el mismo flujo devolviendo datos a
los widgets en vez de `print`.

## Renderizado del tablero

Una celda por casilla:

- **Color por costo, no por nombre de terreno**: interpolación entre verde (costo mínimo del
  catálogo del escenario) y marrón/rojo (costo máximo) para celdas transitables; gris oscuro para
  no transitables. Mantiene el sistema agnóstico a nombres de terreno (compatible con
  `mapa_agnostico.json`) sin tocar código por escenario.
- **Bases A/B**: borde de color distintivo sobre la celda.
- **Recurso**: marcador en `escenario.recurso`, o pegado a la unidad portadora si alguien lo
  transporta.
- **Unidades**: círculo con su `id` y color por bando; contorno resaltado en la portadora.
- **Turno actual**: texto fijo sobre el canvas.
- **Camino de búsqueda**: resaltado aparte, fácil de limpiar al resolver de nuevo.

## Flujo por modo

Carga de escenario: combobox con los JSON de `config/` + botón "Abrir archivo..." (diálogo
estándar de Tkinter, para el escenario externo que entregue el profesor en la sustentación).
`EscenarioInvalido` se captura y sus errores se muestran en un diálogo + log, sin reemplazar el
escenario ya cargado. Al cargar con éxito se dibuja el tablero y se habilitan las tres pestañas
(`ttk.Notebook`); la pestaña activa por defecto es la que sugiere `prueba.modo`, pero las tres
están siempre disponibles (el profesor puede pedir "corre A* sobre este escenario" sin que el
JSON traiga ese modo).

**Pestaña Búsqueda:** combobox de unidad (`escenario.unidades`), spinboxes fila/columna para el
objetivo (prellenados desde `prueba.objetivo` si existe), combobox de algoritmo
(BFS/DFS/UCS/A*/BEAM), combobox de heurística y spinbox de `k` (habilitados solo cuando el
algoritmo elegido los usa). Botón "Resolver": `ProblemaNavegacion` → `resolver_busqueda` →
`verificar_solucion`; pinta el camino y llena un panel con éxito, costo, generados, expandidos,
máximo de frontera, tiempo, y el informe de verificación (OK/ERROR por comprobación + veredicto).

**Pestaña Adversarial:** spinbox de profundidad y checkbox de poda alfa-beta (prellenados desde
el JSON). Botón "Evaluar jugada": arma el `EstadoJuego` inicial (primera unidad por bando, misma
regla 1 vs 1 que `main._preparar_fase_4`), llama a `MinimaxAgent.seleccionar_movimiento` y muestra
acción elegida, legalidad, valor, nodos generados/evaluados, podas y profundidad efectiva;
resalta la celda destino propuesta **sin mover la unidad** (evaluar no avanza la partida).

**Pestaña Partida:** mismos controles de profundidad/poda, más "Reiniciar partida" y "Siguiente
turno". Cada clic en "Siguiente turno" juega un turno (mismo cuerpo que el bucle de
`ejecutar_partida`): el agente del bando activo decide, se aplica la acción, se actualiza el
estado; se mueve la unidad en el canvas, se actualiza el portador si cambia, y se agrega una fila
a una tabla (`ttk.Treeview`) con bando/acción/valor/nodos/podas/profundidad/legal/tiempo. Al
llegar a estado terminal o a `MAX_TURNOS`, se deshabilita el botón y se muestra ganador/empate más
el resumen acumulado por bando.

## Manejo de errores

- Escenario inválido: errores listados en diálogo + log; el escenario previamente cargado no se
  toca (todo o nada, igual que la CLI).
- Errores de ejecución (falta unidad de un bando, sin acciones legales, algoritmo/heurística
  desconocidos): se muestran en el panel de resultado de la pestaña activa, sin excepción no
  controlada hacia el usuario.

## Pruebas

No hay suite automatizada para la GUI. Verificación manual tras implementar: abrir la app,
cargar cada escenario de `config/` (incluido `mapa_agnostico.json`, para confirmar el color por
costo con terrenos de nombre propio) y ejercitar las tres pestañas; confirmar que un escenario
inválido se rechaza sin romper la ventana. El resto del proyecto sigue cubierto por
`python -m unittest discover -s tests -t .` (no se toca ningún módulo existente).

## Documentación a actualizar

- `README.md`: reemplazar la nota "Interfaz gráfica (en desarrollo)" por instrucciones de
  ejecución (`python -m src.ui.gui`).
- `docs/manual_de_usuario.md`: sección 11 ("Nota sobre la interfaz gráfica") pasa de "en
  desarrollo" a una guía breve de uso de la GUI.
- `docs/estado_actual.md`: actualizar la fila de estado de la GUI en la tabla de la sección 1.
