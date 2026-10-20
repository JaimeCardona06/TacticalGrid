"""TacticalGrid: interfaz gráfica Tkinter (modos búsqueda, adversarial y partida).

Consume únicamente src.ui.controlador y el motor existente (src.scenario,
src.game, src.search, src.adversarial, main). No reimplementa lógica de juego
ni de algoritmos: solo carga escenarios, llama al controlador y dibuja lo que
devuelve.

Lanzar con: python -m src.ui.gui (desde la raíz del repositorio).
"""
import os
import tkinter as tk
from tkinter import filedialog, ttk

from src.scenario.loader import EscenarioInvalido, cargar_escenario
from src.ui import colores, controlador

CONFIG_DIR = "config"
TAM_CELDA_MAX = 32
UMBRAL_RADIO_LETRA_NORMAL = 0.3   # desde este radio (fracción de la celda) el id cabe con letra normal


class CanvasEscenario(tk.Canvas):
    """Dibuja el tablero de un escenario: terrenos, bases, recurso, unidades y turno.

    No conoce botones ni pestañas; solo recibe datos ya resueltos por quien la
    llama (ver dibujar()) y pinta.
    """

    def __init__(self, master, ancho=640, alto=640, **kwargs):
        kwargs.setdefault("bg", "white")
        super().__init__(master, width=ancho, height=alto, **kwargs)
        self._ancho = ancho
        self._alto = alto

    def dibujar(self, tablero, unidades, turno, recurso_pos, portador_id=None,
                camino=None, celda_resaltada=None):
        """Redibuja todo el tablero desde cero.

        Purpose:            mostrar, en una sola llamada, el estado completo
                            del tablero que pide el enunciado: cuadrícula,
                            terrenos (por costo, agnóstico al nombre),
                            obstáculos, bases, recurso, unidades, bando de cada
                            unidad, portador del recurso y turno actual, más el
                            camino de una búsqueda y una celda resaltada (p.
                            ej. la jugada adversarial propuesta), si se dan.
        Preconditions:      tablero es un Board válido; unidades es un iterable
                            de objetos con id/bando/posicion; turno es "A" o
                            "B"; recurso_pos es (fila, columna); portador_id es
                            un id de unidad o None; camino es una secuencia de
                            posiciones (fila, columna) o None; celda_resaltada
                            es (fila, columna) o None.
        Postconditions:     borra el contenido previo del canvas y dibuja el
                            estado dado. Si varias unidades comparten celda se
                            dibujan una al lado de la otra (controlador.
                            disposicion_de_fichas) y el portador se pinta al
                            final, para que ninguna tape a otra. No modifica
                            tablero ni unidades.
        Complexity:         O(f*c + u) en tiempo, f*c = celdas del tablero, u =
                            número de unidades.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo probando la GUI contra los
                            escenarios de config/, incluido mapa_agnostico.json
                            (terrenos de nombre propio) y mapa_grande.json
                            (20x20).
        """
        self.delete("all")
        unidades = list(unidades)
        tam = max(1, min(TAM_CELDA_MAX, self._ancho // tablero.columnas,
                          self._alto // tablero.filas))

        costos = [t["costo"] for t in tablero.tipos_terreno.values() if t.get("transitable")]
        costo_min = min(costos) if costos else 0
        costo_max = max(costos) if costos else 0

        def esquina(pos):
            fila, columna = pos
            return columna * tam, fila * tam

        for fila in range(tablero.filas):
            for columna in range(tablero.columnas):
                tipo = tablero.tipos_terreno[tablero.terreno[fila][columna]]
                x0, y0 = columna * tam, fila * tam
                color = (colores.color_por_costo(tipo["costo"], costo_min, costo_max)
                         if tipo.get("transitable") else colores.COLOR_OBSTACULO)
                self.create_rectangle(x0, y0, x0 + tam, y0 + tam, fill=color, outline="#ffffff")

        for bando, base in (("A", tablero.base_a), ("B", tablero.base_b)):
            x0, y0 = esquina(base)
            self.create_rectangle(x0 + 1, y0 + 1, x0 + tam - 1, y0 + tam - 1,
                                   outline=colores.COLOR_BANDO[bando], width=3)

        if camino:
            puntos = []
            for pos in camino:
                x0, y0 = esquina(pos)
                puntos.extend((x0 + tam / 2, y0 + tam / 2))
            if len(puntos) >= 4:
                self.create_line(*puntos, fill=colores.COLOR_CAMINO, width=max(2, tam // 6))

        if celda_resaltada is not None:
            x0, y0 = esquina(celda_resaltada)
            self.create_rectangle(x0 + 2, y0 + 2, x0 + tam - 2, y0 + tam - 2,
                                   outline=colores.COLOR_RESALTADO, width=3)

        rx0, ry0 = esquina(recurso_pos)
        cx, cy = rx0 + tam / 2, ry0 + tam / 2
        r = max(2, tam / 6)
        self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=colores.COLOR_RECURSO, outline="")

        disposicion = controlador.disposicion_de_fichas(unidades)
        for unidad in sorted(unidades, key=lambda u: u.id == portador_id):   # el portador se pinta al final
            ux0, uy0 = esquina(unidad.posicion)
            fx, fy, fr = disposicion[unidad.id]
            cx, cy = ux0 + fx * tam, uy0 + fy * tam
            r = fr * tam
            ancho_contorno = 3 if unidad.id == portador_id else 1
            self.create_oval(cx - r, cy - r, cx + r, cy + r,
                              fill=colores.COLOR_BANDO.get(unidad.bando, "#999999"),
                              outline="black", width=ancho_contorno)
            if r >= 6:   # si la ficha quedó muy chica, el color del bando basta
                self.create_text(cx, cy, text=unidad.id, fill="white",
                                 font=("TkDefaultFont", 8 if fr >= UMBRAL_RADIO_LETRA_NORMAL else 6))

        self.create_text(4, 4, anchor="nw", text=f"Turno: {turno}", fill="black")


class AppTacticalGrid(tk.Tk):
    """Ventana principal: carga de escenario, canvas del tablero y las tres pestañas."""

    def __init__(self):
        super().__init__()
        self.title("TacticalGrid")

        self.escenario = None
        self._partida = None
        self._camino_resuelto = None
        self._celda_resaltada = None

        barra = ttk.Frame(self)
        barra.pack(side="top", fill="x", padx=4, pady=4)

        self.combo_escenario = ttk.Combobox(
            barra, values=self._listar_escenarios(), state="readonly", width=30)
        self.combo_escenario.pack(side="left", padx=(0, 4))
        self.combo_escenario.bind("<<ComboboxSelected>>", self._al_elegir_combo)

        ttk.Button(barra, text="Abrir archivo...", command=self._abrir_archivo).pack(side="left")

        cuerpo = ttk.Frame(self)
        cuerpo.pack(side="top", fill="both", expand=True)

        self.canvas = CanvasEscenario(cuerpo)
        self.canvas.pack(side="left", padx=4, pady=4)

        panel_derecho = ttk.Frame(cuerpo)
        panel_derecho.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        self.notebook = ttk.Notebook(panel_derecho)
        self.notebook.pack(side="top", fill="both", expand=True)
        self.pestana_busqueda = ttk.Frame(self.notebook)
        self.pestana_adversarial = ttk.Frame(self.notebook)
        self.pestana_partida = ttk.Frame(self.notebook)
        self.notebook.add(self.pestana_busqueda, text="Búsqueda")
        self.notebook.add(self.pestana_adversarial, text="Adversarial")
        self.notebook.add(self.pestana_partida, text="Partida")

        self.texto_mensajes = tk.Text(panel_derecho, height=8, state="disabled")
        self.texto_mensajes.pack(side="bottom", fill="x", pady=(4, 0))

        self._construir_pestana_busqueda()
        self._construir_pestana_adversarial()
        self._construir_pestana_partida()

    def _construir_pestana_busqueda(self):
        pestana = self.pestana_busqueda

        fila_unidad = ttk.Frame(pestana)
        fila_unidad.pack(side="top", fill="x", pady=2)
        ttk.Label(fila_unidad, text="Unidad:").pack(side="left")
        self.combo_unidad = ttk.Combobox(fila_unidad, state="readonly", width=10)
        self.combo_unidad.pack(side="left", padx=4)

        fila_objetivo = ttk.Frame(pestana)
        fila_objetivo.pack(side="top", fill="x", pady=2)
        ttk.Label(fila_objetivo, text="Objetivo (fila, col):").pack(side="left")
        self.spin_fila = tk.Spinbox(fila_objetivo, from_=0, to=0, width=5)
        self.spin_fila.pack(side="left", padx=4)
        self.spin_columna = tk.Spinbox(fila_objetivo, from_=0, to=0, width=5)
        self.spin_columna.pack(side="left", padx=4)

        fila_algoritmo = ttk.Frame(pestana)
        fila_algoritmo.pack(side="top", fill="x", pady=2)
        ttk.Label(fila_algoritmo, text="Algoritmo:").pack(side="left")
        self.combo_algoritmo = ttk.Combobox(
            fila_algoritmo, state="readonly", width=8,
            values=("BFS", "DFS", "UCS", "A*", "BEAM"))
        self.combo_algoritmo.set("BFS")
        self.combo_algoritmo.pack(side="left", padx=4)
        self.combo_algoritmo.bind("<<ComboboxSelected>>", self._actualizar_controles_busqueda)

        fila_heuristica = ttk.Frame(pestana)
        fila_heuristica.pack(side="top", fill="x", pady=2)
        ttk.Label(fila_heuristica, text="Heurística:").pack(side="left")
        self.combo_heuristica = ttk.Combobox(
            fila_heuristica, state="readonly", width=14,
            values=("manhattan", "manhattan_pasos", "distancia_bfs"))
        self.combo_heuristica.set("manhattan")
        self.combo_heuristica.pack(side="left", padx=4)
        ttk.Label(fila_heuristica, text="k:").pack(side="left")
        self.spin_k = tk.Spinbox(fila_heuristica, from_=1, to=20, width=5)
        self.spin_k.delete(0, "end")
        self.spin_k.insert(0, "2")
        self.spin_k.pack(side="left", padx=4)

        ttk.Button(pestana, text="Resolver", command=self._resolver_busqueda).pack(
            side="top", pady=4)

        self.texto_busqueda = tk.Text(pestana, height=16, state="disabled")
        self.texto_busqueda.pack(side="top", fill="both", expand=True)

        self._actualizar_controles_busqueda()

    def _construir_pestana_adversarial(self):
        pestana = self.pestana_adversarial

        fila_params = ttk.Frame(pestana)
        fila_params.pack(side="top", fill="x", pady=2)
        ttk.Label(fila_params, text="Profundidad:").pack(side="left")
        self.spin_profundidad_adv = tk.Spinbox(fila_params, from_=1, to=20, width=5)
        self.spin_profundidad_adv.pack(side="left", padx=4)
        self.var_poda_adv = tk.BooleanVar(value=True)
        ttk.Checkbutton(fila_params, text="Poda alfa-beta", variable=self.var_poda_adv).pack(
            side="left", padx=4)

        ttk.Button(pestana, text="Evaluar jugada", command=self._evaluar_adversarial).pack(
            side="top", pady=4)

        self.texto_adversarial = tk.Text(pestana, height=16, state="disabled")
        self.texto_adversarial.pack(side="top", fill="both", expand=True)

    def _poblar_pestana_adversarial(self):
        self.spin_profundidad_adv.delete(0, "end")
        self.spin_profundidad_adv.insert(0, str(self.escenario.profundidad_maxima_minimax))
        prueba = self.escenario.prueba or {}
        self.var_poda_adv.set(bool(prueba.get("usar_poda", True)))

    def _mostrar_resultado_adversarial(self, texto):
        self.texto_adversarial.configure(state="normal")
        self.texto_adversarial.delete("1.0", "end")
        self.texto_adversarial.insert("end", texto)
        self.texto_adversarial.configure(state="disabled")

    def _evaluar_adversarial(self):
        """Evalúa una jugada del bando del turno con Minimax/alfa-beta y la muestra.

        Purpose:            cumplir el modo 'adversarial' de la pestaña
                            Adversarial: leer la profundidad y la poda elegidas,
                            pedir la decisión al controlador (estado inicial,
                            todas las unidades) y mostrar la unidad y celda
                            elegidas, la legalidad y las métricas del enunciado.
        Preconditions:      self.escenario es None o un Escenario válido cargado;
                            los controles de profundidad (entero >= 1) y poda
                            (booleano) existen en la pestaña.
        Postconditions:     resalta la celda destino en el canvas y escribe el
                            informe en el panel de la pestaña (o un mensaje de
                            error si el escenario falta, la profundidad es
                            inválida o el controlador lanza ErrorControlador).
                            No mueve unidades ni modifica el escenario.
        Complexity:         O(b^d) por la decisión (b = unidades del bando en
                            turno × hasta 4 direcciones) más O(f*c + u) por el
                            redibujo del tablero.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo evaluando jugadas desde la
                            pestaña Adversarial con los escenarios de config/
                            (acciones LEGAL/ILEGAL visibles), más la
                            orquestación cubierta por tests/test_controlador.py.
        """
        if self.escenario is None:
            self._mostrar_resultado_adversarial("Carga un escenario primero.")
            return

        try:
            profundidad = int(self.spin_profundidad_adv.get())
        except ValueError:
            self._mostrar_resultado_adversarial("La profundidad debe ser un entero >= 1.")
            return
        usar_poda = self.var_poda_adv.get()

        try:
            resultado = controlador.evaluar_adversarial(
                self.escenario, profundidad=profundidad, usar_poda=usar_poda)
        except controlador.ErrorControlador as error:
            self._mostrar_resultado_adversarial(str(error))
            return

        self._celda_resaltada = resultado["destino"]
        self._abandonar_vista_partida()
        self._refrescar_canvas()

        metricas = resultado["metricas"]
        lineas = [
            f"Bando que decide: {resultado['estado'].turno}",
            f"Unidades A: {len(resultado['unidades_a'])} | "
            f"Unidades B: {len(resultado['unidades_b'])}",
            f"Acción elegida: la unidad {resultado['nombre_unidad']} "
            f"(bando {resultado['estado'].turno}) se mueve a {resultado['destino']}",
            f"Legalidad: {'LEGAL' if metricas['accion_legal'] else 'ILEGAL'} — "
            f"{metricas['detalle_legalidad']}",
            f"Valor obtenido: {metricas['valor_obtenido']:+.1f}",
            f"Nodos visitados: {metricas['nodos_visitados']}",
            f"Nodos generados: {metricas['nodos_generados']}",
            f"Nodos evaluados: {metricas['nodos_evaluados']}",
            f"Podas totales: {metricas['podas_totales']}",
            f"Profundidad efectiva: {metricas['profundidad_alcanzada']}",
            f"Tiempo: {metricas['tiempo_ms']:.2f} ms",
        ]
        self._mostrar_resultado_adversarial("\n".join(lineas))

    def _construir_pestana_partida(self):
        pestana = self.pestana_partida

        fila_params = ttk.Frame(pestana)
        fila_params.pack(side="top", fill="x", pady=2)
        ttk.Label(fila_params, text="Profundidad:").pack(side="left")
        self.spin_profundidad_partida = tk.Spinbox(fila_params, from_=1, to=20, width=5)
        self.spin_profundidad_partida.pack(side="left", padx=4)
        self.var_poda_partida = tk.BooleanVar(value=True)
        ttk.Checkbutton(fila_params, text="Poda alfa-beta", variable=self.var_poda_partida).pack(
            side="left", padx=4)

        fila_botones = ttk.Frame(pestana)
        fila_botones.pack(side="top", fill="x", pady=4)
        ttk.Button(fila_botones, text="Reiniciar partida", command=self._reiniciar_partida).pack(
            side="left", padx=(0, 4))
        self.boton_siguiente_turno = ttk.Button(
            fila_botones, text="Siguiente turno", command=self._siguiente_turno,
            state="disabled")
        self.boton_siguiente_turno.pack(side="left")

        columnas = ("turno", "bando", "unidad", "accion", "valor", "nodos", "podas",
                    "profundidad", "legal", "tiempo_ms")
        self.tabla_partida = ttk.Treeview(pestana, columns=columnas, show="headings", height=10)
        titulos = {
            "turno": "Turno", "bando": "Bando", "unidad": "Unidad", "accion": "Destino",
            "valor": "Valor", "nodos": "Nodos", "podas": "Podas", "profundidad": "Prof.",
            "legal": "Legal", "tiempo_ms": "Tiempo (ms)",
        }
        for columna in columnas:
            self.tabla_partida.heading(columna, text=titulos[columna])
            self.tabla_partida.column(columna, width=70, anchor="center")
        self.tabla_partida.pack(side="top", fill="both", expand=True, pady=(4, 4))

        self.label_desenlace = ttk.Label(pestana, text="", justify="left")
        self.label_desenlace.pack(side="top", fill="x")

    def _poblar_pestana_partida(self):
        self.spin_profundidad_partida.delete(0, "end")
        self.spin_profundidad_partida.insert(0, str(self.escenario.profundidad_maxima_minimax))
        prueba = self.escenario.prueba or {}
        self.var_poda_partida.set(bool(prueba.get("usar_poda", True)))
        self.tabla_partida.delete(*self.tabla_partida.get_children())
        self.label_desenlace.configure(text="")
        self.boton_siguiente_turno.configure(state="disabled")

    def _resumen_partida(self, encabezado):
        partida = self._partida
        lineas = [encabezado, ""]
        for bando in ("A", "B"):
            datos = partida.totales[bando]
            promedio = datos["tiempo_ms"] / datos["turnos"] if datos["turnos"] else 0.0
            lineas.append(
                f"{bando}: turnos {datos['turnos']} | generados {datos['generados']} | "
                f"evaluados {datos['evaluados']} | podas {datos['podas']} | "
                f"tiempo total {datos['tiempo_ms']:.2f} ms | promedio {promedio:.2f} ms")
        return "\n".join(lineas)

    def _reiniciar_partida(self):
        """Inicia (o reinicia) una partida en el turno 1 con los parámetros elegidos.

        Purpose:            crear la PartidaEnCurso del controlador con la
                            profundidad y la poda de la pestaña, limpiar la
                            tabla y dejar lista la partida para "Siguiente
                            turno".
        Preconditions:      self.escenario es None o un Escenario válido cargado;
                            profundidad es un entero >= 1 y poda un booleano.
        Postconditions:     si el controlador acepta, reemplaza self._partida,
                            limpia tabla y desenlace, habilita "Siguiente
                            turno" y redibuja el estado inicial; si no, muestra
                            el error. No modifica el escenario.
        Complexity:         O(u) por la preparación (u = unidades) más
                            O(f*c + u) del redibujo.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo reiniciando partidas desde la
                            pestaña Partida y por tests/test_controlador.py
                            (iniciar_partida).
        """
        if self.escenario is None:
            self.label_desenlace.configure(text="Carga un escenario primero.")
            return

        try:
            profundidad = int(self.spin_profundidad_partida.get())
        except ValueError:
            self.label_desenlace.configure(text="La profundidad debe ser un entero >= 1.")
            return
        usar_poda = self.var_poda_partida.get()

        try:
            self._partida = controlador.iniciar_partida(
                self.escenario, profundidad=profundidad, usar_poda=usar_poda)
        except controlador.ErrorControlador as error:
            self.label_desenlace.configure(text=str(error))
            return

        self.tabla_partida.delete(*self.tabla_partida.get_children())
        self.label_desenlace.configure(text="")
        self.boton_siguiente_turno.configure(state="normal")
        self._refrescar_canvas()

    def _siguiente_turno(self):
        """Juega un turno de la partida en curso y actualiza la interfaz.

        Purpose:            avanzar la partida un turno con
                            controlador.jugar_turno, agregar la fila del turno a
                            la tabla y, al terminar, deshabilitar el botón y
                            mostrar el desenlace con el resumen acumulado por
                            bando.
        Preconditions:      self._partida es una PartidaEnCurso iniciada y no
                            terminada (el botón solo se habilita en ese caso).
        Postconditions:     muta la partida en curso un turno, redibuja el
                            tablero (posiciones y portador actuales) y agrega la
                            fila a la tabla; si la partida termina, muestra
                            FINALIZADA/EMPATADA y el resumen. Ante
                            ErrorControlador, solo muestra el mensaje.
        Complexity:         O(b^d) por la decisión del agente más O(f*c + u) del
                            redibujo; O(1) en la tabla.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo jugando partidas completas
                            turno a turno desde la pestaña Partida y por
                            tests/test_controlador.py (jugar_turno).
        """
        if self._partida is None:
            return
        try:
            fila = controlador.jugar_turno(self._partida)
        except controlador.ErrorControlador as error:
            self.label_desenlace.configure(text=str(error))
            return

        encabezado_por_mensaje = fila.get("mensaje")
        if not encabezado_por_mensaje:
            self.tabla_partida.insert("", "end", values=(
                fila["turno"], fila["bando"], fila["unidad"], str(fila["accion"]),
                f"{fila['valor']:+.1f}", fila["nodos_generados"], fila["podas"],
                fila["profundidad"], "sí" if fila["legal"] else "NO", f"{fila['tiempo_ms']:.2f}",
            ))

        self._refrescar_canvas()

        if self._partida.terminada:
            self.boton_siguiente_turno.configure(state="disabled")
            if encabezado_por_mensaje:
                encabezado = encabezado_por_mensaje
            elif self._partida.ganador is not None:
                encabezado = (f"PARTIDA FINALIZADA: gana el bando {self._partida.ganador} "
                               f"en {self._partida.turno_num - 1} turnos.")
            else:
                encabezado = (f"PARTIDA EMPATADA: se alcanzó el límite de turnos "
                               f"({self._partida.turno_num - 1}).")
            self.label_desenlace.configure(text=self._resumen_partida(encabezado))

    def _actualizar_controles_busqueda(self, _evento=None):
        usa_extras = self.combo_algoritmo.get() in ("A*", "BEAM")
        estado = "readonly" if usa_extras else "disabled"
        self.combo_heuristica.configure(state=estado)
        self.spin_k.configure(state=("normal" if usa_extras else "disabled"))

    def _poblar_pestana_busqueda(self):
        ids = [u.id for u in self.escenario.unidades]
        self.combo_unidad.configure(values=ids)
        if ids:
            self.combo_unidad.set(ids[0])

        tablero = self.escenario.tablero
        self.spin_fila.configure(to=max(0, tablero.filas - 1))
        self.spin_columna.configure(to=max(0, tablero.columnas - 1))

        prueba = self.escenario.prueba or {}
        objetivo = prueba.get("objetivo")
        fila, columna = 0, 0
        if isinstance(objetivo, dict):
            fila, columna = objetivo.get("fila", 0), objetivo.get("columna", 0)
        self.spin_fila.delete(0, "end")
        self.spin_fila.insert(0, str(fila))
        self.spin_columna.delete(0, "end")
        self.spin_columna.insert(0, str(columna))

    def _mostrar_resultado_busqueda(self, texto):
        self.texto_busqueda.configure(state="normal")
        self.texto_busqueda.delete("1.0", "end")
        self.texto_busqueda.insert("end", texto)
        self.texto_busqueda.configure(state="disabled")

    def _resolver_busqueda(self):
        """Resuelve la búsqueda pedida en la pestaña Búsqueda y muestra el informe.

        Purpose:            ejecutar el algoritmo, la heurística y el k elegidos
                            sobre la unidad y el objetivo de la pestaña, pintar
                            el camino encontrado y mostrar el resultado con la
                            verificación independiente de la solución.
        Preconditions:      self.escenario es None o un Escenario válido; los
                            controles de unidad, objetivo (fila/columna
                            numéricas), algoritmo, heurística y k existen.
        Postconditions:     guarda el camino, abandona la vista de partida,
                            redibuja el tablero con el camino y escribe en el
                            panel de resultados el resumen y las comprobaciones
                            del verificador; ante entradas inválidas o
                            ErrorControlador, solo escribe el mensaje. No
                            modifica el escenario.
        Complexity:         la del algoritmo elegido más O(n) de verificación y
                            O(f*c + u) del redibujo.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo resolviendo búsquedas desde
                            la pestaña Búsqueda (informe VÁLIDA/INVÁLIDA visible)
                            y por tests/test_controlador.py en la orquestación.
        """
        if self.escenario is None:
            self._mostrar_resultado_busqueda("Carga un escenario primero.")
            return

        unidad_id = self.combo_unidad.get()
        try:
            objetivo = (int(self.spin_fila.get()), int(self.spin_columna.get()))
        except ValueError:
            self._mostrar_resultado_busqueda("El objetivo debe ser fila y columna numéricas.")
            return

        algoritmo = self.combo_algoritmo.get()
        heuristica = self.combo_heuristica.get()
        try:
            k = int(self.spin_k.get())
        except ValueError:
            k = 2

        try:
            resultado, informe = controlador.resolver_busqueda_gui(
                self.escenario, unidad_id, objetivo, algoritmo, heuristica, k)
        except controlador.ErrorControlador as error:
            self._mostrar_resultado_busqueda(str(error))
            return

        self._camino_resuelto = resultado.camino
        self._abandonar_vista_partida()
        self._refrescar_canvas()

        lineas = [
            f"Algoritmo: {resultado.algoritmo}",
            f"Éxito: {resultado.exito}",
            f"Costo: {resultado.costo}",
            f"Estados generados: {resultado.estados_generados}",
            f"Estados expandidos: {resultado.estados_expandidos}",
            f"Máximo de frontera: {resultado.maximo_frontera}",
            f"Tiempo: {resultado.tiempo_segundos:.4f} s",
        ]
        if resultado.heuristica is not None:
            lineas.append(f"Heurística: {resultado.heuristica}")
        if resultado.k is not None:
            lineas.append(f"k: {resultado.k}")
        lineas.append("")
        lineas.append("--- Verificación independiente ---")
        for descripcion, problemas in informe.comprobaciones:
            lineas.append(("[ERROR] " if problemas else "[OK]    ") + descripcion)
            for texto in problemas:
                lineas.append(f"          - {texto}")
        for aviso in informe.avisos:
            lineas.append(f"[AVISO] {aviso}")
        lineas.append("Resultado: " + ("VÁLIDA" if informe.valido else "INVÁLIDA"))
        self._mostrar_resultado_busqueda("\n".join(lineas))

    def _listar_escenarios(self):
        if not os.path.isdir(CONFIG_DIR):
            return []
        return sorted(nombre for nombre in os.listdir(CONFIG_DIR) if nombre.endswith(".json"))

    def _al_elegir_combo(self, _evento=None):
        nombre = self.combo_escenario.get()
        if nombre:
            self._cargar_escenario(os.path.join(CONFIG_DIR, nombre))

    def _abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Abrir escenario", filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
        if ruta:
            self._cargar_escenario(ruta)

    def _mostrar_mensaje(self, texto):
        self.texto_mensajes.configure(state="normal")
        self.texto_mensajes.delete("1.0", "end")
        self.texto_mensajes.insert("end", texto)
        self.texto_mensajes.configure(state="disabled")

    def _cargar_escenario(self, ruta):
        """Carga un escenario JSON con la regla todo-o-nada y refresca la ventana.

        Purpose:            validar y reemplazar el escenario activo desde una
                            ruta (desplegable o "Abrir archivo"), reiniciar el
                            estado de la GUI y repoblar las tres pestañas y el
                            canvas.
        Preconditions:      ruta es una ruta de archivo (texto); puede no existir
                            o no ser un JSON válido.
        Postconditions:     si el validador acepta, self.escenario se reemplaza,
                            se descartan partida/camino/celda resaltada y se
                            repueblan pestañas y canvas; si no, se muestran los
                            errores y se conserva el escenario anterior. No
                            modifica archivos.
        Complexity:         O(n) por la carga y validación del escenario (n =
                            tamaño) más O(f*c + u) del redibujo.
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo cargando escenarios válidos e
                            inválidos (todo-o-nada) desde la GUI y por
                            tests/test_cargador.py en la carga.
        """
        try:
            escenario = cargar_escenario(ruta)
        except EscenarioInvalido as error:
            self._mostrar_mensaje("Escenario inválido; no se cargó nada:\n" +
                                   "\n".join(error.errores))
            return

        self.escenario = escenario
        self._partida = None
        self._camino_resuelto = None
        self._celda_resaltada = None
        self._mostrar_mensaje(
            f"Escenario cargado: {ruta}\n"
            f"{escenario.tablero.filas}x{escenario.tablero.columnas} | "
            f"{len(escenario.unidades)} unidad(es) | turno {escenario.turno}")
        self._poblar_pestana_busqueda()
        self._poblar_pestana_adversarial()
        self._poblar_pestana_partida()
        self._refrescar_canvas()

    def _abandonar_vista_partida(self):
        """Si hay una partida en curso, la abandona para volver a la vista estática.

        Se llama al resolver una búsqueda o evaluar una jugada adversarial desde
        otra pestaña: sin esto, _refrescar_canvas seguiría dibujando el estado de
        la partida (rama self._partida is not None) e ignoraría el camino
        resuelto o la celda resaltada, que solo se dibujan en la vista estática.
        """
        if self._partida is not None:
            self._partida = None
            self.tabla_partida.delete(*self.tabla_partida.get_children())
            self.label_desenlace.configure(text="")
            self.boton_siguiente_turno.configure(state="disabled")

    def _refrescar_canvas(self):
        """Redibuja el canvas según la vista activa (estática o partida en curso).

        Purpose:            unificar el dibujo del tablero: en vista estática
                            pinta el escenario con el camino resuelto y la celda
                            resaltada; en partida, las posiciones actuales de
                            todas las unidades y el portador del recurso.
        Preconditions:      self.escenario es un Escenario válido cargado;
                            self._partida es None (vista estática) o una
                            PartidaEnCurso.
        Postconditions:     delega en CanvasEscenario.dibujar con los datos de la
                            vista activa; no modifica el escenario ni la
                            partida.
        Complexity:         O(f*c + u) por el dibujo (celdas y unidades).
        AI usage:           Yes
        AI intervention:    la IA escribió el método y esta documentación.
        Student validation: Validado por el equipo recorriendo las tres pestañas
                            (estático con camino/jugada y partida con portador)
                            y por tests/test_controlador.py en el mapeo de
                            unidades y portador.
        """
        if self.escenario is None:
            return
        if self._partida is None:
            self.canvas.dibujar(
                self.escenario.tablero, self.escenario.unidades, self.escenario.turno,
                controlador.recurso_pos_inicial(self.escenario),
                portador_id=self.escenario.portador_recurso,
                camino=self._camino_resuelto, celda_resaltada=self._celda_resaltada)
        else:
            unidades = controlador.unidades_con_posiciones(
                self._partida.unidades_a, self._partida.estado.pos_a,
                self._partida.unidades_b, self._partida.estado.pos_b)
            self.canvas.dibujar(
                self.escenario.tablero, unidades, self._partida.estado.turno,
                self._partida.estado.recurso_pos,
                portador_id=controlador.portador_unidad_id(
                    self._partida.estado, self._partida.unidades_a, self._partida.unidades_b))


def main():
    AppTacticalGrid().mainloop()


if __name__ == "__main__":
    main()
