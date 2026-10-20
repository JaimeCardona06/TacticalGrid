"""
Purpose:
    Experimento reproducible: compara los modos de desempate de los agentes de partida
    (ninguno, persecución e intercepción) jugando partidas completas sobre escenarios JSON
    ALEATORIOS pero válidos (tamaños, muros, 1 a 3 unidades por bando, portador inicial).
    Con la misma semilla todos los modos juegan exactamente los mismos escenarios.

    Uso (desde la raíz del repositorio):
        python experimentos/comparar_desempates.py
        python experimentos/comparar_desempates.py --profundidad 3 --escenarios 100 --semilla 77

    Mide por modo: partidas empatadas, decisivas (con la media de turnos), robos del recurso
    entre bandos, acciones ilegales y excepciones (estas dos últimas deben ser 0).

AI usage:           Yes
AI intervention:    la IA diseñó el experimento y escribió el script y esta documentación.
Student validation: Validado por el equipo ejecutando el script y la prueba de humo
                    tests/test_experimento_desempates.py; los resultados citados en
                    docs/decisiones.md salen de este script.
"""
import argparse
import json
import os
import random
import sys
import tempfile
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from src.adversarial.agent import MinimaxAgent  # noqa: E402
from src.adversarial.desempate import INTERCEPCION, PERSECUCION  # noqa: E402
from src.scenario.loader import cargar_escenario  # noqa: E402
from src.ui.controlador import iniciar_partida, jugar_turno  # noqa: E402

TIPOS = {"camino": {"costo": 1, "transitable": True}, "pasto": {"costo": 2, "transitable": True},
         "pantano": {"costo": 7, "transitable": True}, "muro": {"transitable": False}}

# modo -> parámetros del agente
MODOS = {
    "ninguno": dict(desempatar_por_avance=False),
    "persecucion": dict(desempatar_por_avance=True, estrategia_robo=PERSECUCION),
    "intercepcion": dict(desempatar_por_avance=True, estrategia_robo=INTERCEPCION),
}


def escenario_aleatorio(rng):
    """Diccionario de escenario válido: tablero 4 a 14 por lado, 0 a 30 % de muros, 1 a 3 unidades por bando.

    Devuelve None si el tablero quedó con muy pocas celdas libres para colocar todo.
    """
    filas, columnas = rng.randint(4, 14), rng.randint(4, 14)
    porcentaje_muros = rng.choice([0.0, 0.1, 0.2, 0.3])
    terreno = [[("muro" if rng.random() < porcentaje_muros else rng.choice(["camino", "camino", "pasto", "pantano"]))
                for _ in range(columnas)] for _ in range(filas)]
    libres = [(i, j) for i in range(filas) for j in range(columnas) if terreno[i][j] != "muro"]
    n = rng.choice([1, 2, 3])
    if len(libres) < 2 * n + 3:
        return None
    celdas = rng.sample(libres, 2 * n + 3)
    base_a, base_b, recurso = celdas[0], celdas[1], celdas[2]
    unidades = [{"id": f"A{k + 1}", "bando": "A", "tipo": "estandar", "fila": celdas[3 + k][0], "columna": celdas[3 + k][1]}
                for k in range(n)]
    unidades += [{"id": f"B{k + 1}", "bando": "B", "tipo": "estandar", "fila": celdas[3 + n + k][0],
                  "columna": celdas[3 + n + k][1]} for k in range(n)]
    portador = rng.choice([None, None, "A1", "B1"])
    if portador:
        u = next(x for x in unidades if x["id"] == portador)
        recurso = (u["fila"], u["columna"])
    return {
        "version": "1.0", "mapa": {"filas": filas, "columnas": columnas}, "tipos_terreno": TIPOS, "terreno": terreno,
        "bases": {"A": {"fila": base_a[0], "columna": base_a[1]}, "B": {"fila": base_b[0], "columna": base_b[1]}},
        "recurso": {"fila": recurso[0], "columna": recurso[1]}, "unidades": unidades,
        "turno": rng.choice(["A", "B"]),
        "juego": {"portador_recurso": portador, "profundidad_maxima_minimax": 3}, "prueba": {"modo": "partida"},
    }


def jugar(escenario, profundidad, parametros_agente):
    """Juega una partida completa; devuelve (ganador o None, turnos, robos del recurso, acciones ilegales)."""
    partida = iniciar_partida(escenario, profundidad=profundidad)
    partida.agentes = {b: MinimaxAgent(b, profundidad=profundidad, usar_poda=True, **parametros_agente)
                       for b in ("A", "B")}
    robos = ilegales = 0
    anterior = partida.estado.portador
    while not partida.terminada:
        fila = jugar_turno(partida)
        ilegales += fila.get("legal") is False
        actual = partida.estado.portador
        if anterior and actual and actual[0] != anterior[0]:
            robos += 1
        anterior = actual
    return partida.ganador, partida.turno_num - 1, robos, ilegales


def comparar(profundidad=3, escenarios=100, semilla=77):
    """Juega los mismos escenarios aleatorios con cada modo y devuelve las estadísticas por modo.

    Purpose:            medir con partidas completas (no con casos aislados) qué desempate
                        produce menos empates y más robos.
    Preconditions:      profundidad >= 1; escenarios >= 1.
    Postconditions:     devuelve {modo: {partidas, empates, decisivas, turnos_medios_decisivas,
                        robos, ilegales, excepciones}}. Todos los modos juegan los mismos
                        escenarios (misma semilla). No modifica ningún archivo del proyecto.
    Complexity:         O(escenarios * modos * 100 turnos * costo de una decisión Minimax).
    AI usage:           Yes
    AI intervention:    la IA escribió la función y esta documentación.
    Student validation: Validado por el equipo con tests/test_experimento_desempates.py.
    """
    rng = random.Random(semilla)
    ruta = os.path.join(tempfile.mkdtemp(), "escenario.json")
    resultados = {modo: Counter() for modo in MODOS}
    turnos_decisivas = {modo: [] for modo in MODOS}
    jugados = 0
    while jugados < escenarios:
        datos = escenario_aleatorio(rng)
        if datos is None:
            continue
        jugados += 1
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo)
        for modo, parametros in MODOS.items():
            estadisticas = resultados[modo]
            estadisticas["partidas"] += 1
            try:
                ganador, turnos, robos, ilegales = jugar(cargar_escenario(ruta), profundidad, parametros)
            except Exception:  # noqa: BLE001  (se cuenta: debe ser 0)
                estadisticas["excepciones"] += 1
                continue
            estadisticas["empates" if ganador is None else "decisivas"] += 1
            estadisticas["robos"] += robos
            estadisticas["ilegales"] += ilegales
            if ganador is not None:
                turnos_decisivas[modo].append(turnos)
    for modo, estadisticas in resultados.items():
        lista = turnos_decisivas[modo]
        estadisticas["turnos_medios_decisivas"] = round(sum(lista) / len(lista), 1) if lista else 0
        for clave in ("empates", "decisivas", "robos", "ilegales", "excepciones"):
            estadisticas.setdefault(clave, 0)
    return {modo: dict(e) for modo, e in resultados.items()}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compara los desempates de los agentes de partida.")
    parser.add_argument("--profundidad", type=int, default=3, help="profundidad de Minimax (por defecto 3)")
    parser.add_argument("--escenarios", type=int, default=100, help="cantidad de escenarios aleatorios (por defecto 100)")
    parser.add_argument("--semilla", type=int, default=77, help="semilla para reproducir el experimento")
    args = parser.parse_args(argv)

    resultados = comparar(args.profundidad, args.escenarios, args.semilla)
    print(f"{args.escenarios} escenarios aleatorios, profundidad {args.profundidad}, semilla {args.semilla}\n")
    print(f"{'desempate':<14}{'empates':>9}{'decisivas':>11}{'turnos medios':>15}{'robos':>8}{'ilegales':>10}{'excepciones':>13}")
    for modo, e in resultados.items():
        porcentaje = 100 * e["empates"] / e["partidas"]
        print(f"{modo:<14}{e['empates']:>5} ({porcentaje:>2.0f}%){e['decisivas']:>9}{e['turnos_medios_decisivas']:>15}"
              f"{e['robos']:>8}{e['ilegales']:>10}{e['excepciones']:>13}")


if __name__ == "__main__":
    main()
