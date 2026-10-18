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
                            estado dado. No modifica tablero ni unidades.
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

        for unidad in unidades:
            ux0, uy0 = esquina(unidad.posicion)
            cx, cy = ux0 + tam / 2, uy0 + tam / 2
            r = tam * 0.35
            ancho_contorno = 3 if unidad.id == portador_id else 1
            self.create_oval(cx - r, cy - r, cx + r, cy + r,
                              fill=colores.COLOR_BANDO.get(unidad.bando, "#999999"),
                              outline="black", width=ancho_contorno)
            self.create_text(cx, cy, text=unidad.id, fill="white", font=("TkDefaultFont", 8))

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
        self._refrescar_canvas()

    def _refrescar_canvas(self):
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
                self.escenario.unidades, self._partida.unidad_a.id, self._partida.estado.pos_a,
                self._partida.unidad_b.id, self._partida.estado.pos_b)
            self.canvas.dibujar(
                self.escenario.tablero, unidades, self._partida.estado.turno,
                self._partida.estado.recurso_pos,
                portador_id=controlador.portador_unidad_id(
                    self._partida.estado, self._partida.unidad_a, self._partida.unidad_b))


def main():
    AppTacticalGrid().mainloop()


if __name__ == "__main__":
    main()
