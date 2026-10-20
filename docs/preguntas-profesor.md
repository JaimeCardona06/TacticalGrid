# Preguntas para el profesor — TacticalGrid

Solo van las dudas que el enunciado no resuelve y que cambian resultados o la validación. Todo lo demás lo decidió el equipo (ver la última sección y `decisiones.md`).

Mientras no haya respuesta, el equipo trabaja con la opción marcada como "Mientras tanto".

---

## 1. ¿Cómo se cobra un movimiento y en cuántas direcciones se mueve una unidad?

**Qué dice el enunciado:** los costos vienen del JSON (`tipos_terreno`), pero no dice cuál celda se cobra al moverse (la de origen, la de destino u otra) ni si el movimiento es en 4 u 8 direcciones.

**Por qué es indispensable:** de esto dependen el costo de todos los caminos (UCS, A*, Beam), la admisibilidad de la heurística Manhattan y los valores que el profesor espera ver o predecir en la sustentación. Por ejemplo, en el escenario de la pág. 6 el camino de A1 a (3,2) cuesta 7 si se cobra la celda destino, y otro valor distinto si se cobra la de origen.

**Pregunta concreta:**
- ¿Se cobra el costo de la celda a la que la unidad entra, la de la que sale, u otra regla?
- ¿El movimiento es de una casilla en 4 direcciones (arriba, abajo, izquierda, derecha), o se permiten diagonales?

**Mientras tanto:** costo de la celda destino y 4 direcciones.

**Qué cambia si la respuesta es otra:** el método `costo_entrar` y el orden de `DIRECCIONES` en `Board`, la heurística Manhattan y el verificador de soluciones. El resto de la arquitectura no se toca.

---

## 2. ¿Pueden las bases o el recurso estar sobre una celda no transitable?

**Qué dice el enunciado:** la validación prohíbe unidades sobre celdas no transitables (regla 5), pero no dice nada de las bases ni del recurso.

**Por qué es indispensable:** decide si un escenario con la base o el recurso sobre un muro es **inválido** (hay que rechazarlo) o **válido** (hay que cargarlo). Si lo rechazamos y el profesor lo considera válido, el escenario externo no cargaría en la sustentación; si lo aceptamos, el juego podría quedar imposible de ganar.

**Pregunta concreta:** ¿un escenario con la base A, la base B o el recurso sobre una celda no transitable debe rechazarse?

**Mientras tanto:** no se rechaza (la lista de 9 validaciones del enunciado no lo menciona).

**Qué cambia si la respuesta es "sí, rechazar":** se añade una comprobación al validador, dentro de la regla 5.

---

## Decisiones que tomó el equipo (no hace falta preguntar)

| Duda del enunciado | Decisión | Razón |
|---|---|---|
| "a o b" en minúscula en las validaciones de bando y turno, mientras el JSON usa "A" y "B" | Se aceptan mayúscula y minúscula, y se normalizan a mayúscula | Es más tolerante con escenarios externos; rechazar un `"a"` costaría más que aceptarlo |
| `profundidad_maxima_minimax` no está en la lista de campos obligatorios | Si falta, se usa 3 y se puede cambiar desde la interfaz | Un JSON sin ese campo debe cargar; 3 mantiene el árbol manejable |
| El modo `busqueda` no dice qué algoritmo ni qué k usar | Se eligen desde la interfaz; si el JSON trae campos extra (`algoritmo`, `k`, `heuristica`), se respetan | El enunciado permite campos extra que no cambien los obligatorios |
| El ejemplo oficial tiene solo 2 unidades por bando, y el enunciado pide mínimo 3 | El validador **no** exige 3 unidades; el mínimo se cumple en los mapas de desarrollo propios | Si exigiera 3 rechazaría el ejemplo de la pág. 6 |
| Mapa mínimo de 20×20 | Solo aplica a los mapas de desarrollo propios; el validador acepta cualquier dimensión positiva | Pág. 7: la aplicación debe aceptar escenarios que cambien dimensiones |
| El objetivo de `busqueda` en el ejemplo (3,2) es la casilla de B1 | En `busqueda` las otras unidades no bloquean el paso | El propio ejemplo oficial lo exige: si bloquearan, el objetivo sería inalcanzable |
| Si `camino` incluye la celda de inicio | Sí, el primer elemento es la celda de inicio; el costo no la cuenta | Facilita al verificador comprobar que el camino empieza donde debe |
