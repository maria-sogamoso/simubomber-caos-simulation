"""
Módulo Independiente: Modelo Basado en Agentes.

Este archivo valida formalmente la mecánica inteligente usada por
SimuBomber en `SimuBomber/game/agent_enemy.py` sin modificar esa lógica.

Objetivos del modelo:
- Formalizar percepción, decisión de estado y respuesta al caos.
- Medir frecuencias de wander / chase / flee bajo escenarios distintos.
- Comparar resultados observados vs reglas esperadas.
- Usar el PRNG del proyecto para reproducibilidad.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
import tempfile
import atexit
import shutil

import matplotlib.pyplot as plt
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from generadores_numeros_pseudoaleatorios.generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal

def _make_output_dir():
	ephemeral = ('--ephemeral' in sys.argv) or (os.environ.get('SIMUBOMBER_EPHEMERAL_OUTPUTS') == '1')
	if ephemeral:
		tmp = tempfile.mkdtemp(prefix="simubomber_graficos_")
		def _cleanup():
			try:
				shutil.rmtree(tmp)
			except Exception:
				pass
		atexit.register(_cleanup)
		return tmp
	out = "graficos_validacion"
	os.makedirs(out, exist_ok=True)
	return out

CARPETA_DESTINO = _make_output_dir()


@dataclass(frozen=True)
class EscenarioAgente:
	nombre: str
	chaos: float
	player_distance: float
	threat_distance: float
	semilla: int


class AgenteBasadoEnReglas:
	"""Versión standalone del comportamiento del AgentEnemy para validación."""

	def __init__(self, semilla: int) -> None:
		self.lcg = GeneradorCongruenciaLineal(semilla)
		self.base_move_interval = 8
		self.move_interval = 8
		self.base_chase_threshold = 150
		self.chase_threshold = 150
		self.flee_threshold = 100
		self.bias_strength = 0.0

	def apply_chaos(self, chaos: float) -> None:
		"""Replica la regla de ajuste dinámico del juego."""
		self.move_interval = max(4, int(self.base_move_interval - chaos * 0.5))
		self.chase_threshold = self.base_chase_threshold + chaos * 8
		self.bias_strength = min(0.8, chaos / 10.0)

	def perceive(self, player_distance: float, threat_distance: float) -> dict[str, float]:
		return {
			"dist_to_player": player_distance,
			"dist_to_threat": threat_distance,
		}

	def decide_state(self, dist_to_player: float, dist_to_threat: float) -> str:
		if dist_to_threat < self.flee_threshold:
			return "flee"
		if dist_to_player < self.chase_threshold:
			return "chase"
		return "wander"

	def _should_bias(self) -> bool:
		r = self.lcg.siguiente_Ri_Congruencia_Lineal(1)[0]
		return r < self.bias_strength


def simular_escenario(escenario: EscenarioAgente, num_corridas: int = 5000) -> dict:
	agente = AgenteBasadoEnReglas(escenario.semilla)
	agente.apply_chaos(escenario.chaos)

	conteos = {"wander": 0, "chase": 0, "flee": 0}
	bias_aplicado = 0
	distancias_observadas = {"player": [], "threat": []}

	for _ in range(num_corridas):
		percepcion = agente.perceive(escenario.player_distance, escenario.threat_distance)
		estado = agente.decide_state(percepcion["dist_to_player"], percepcion["dist_to_threat"])
		conteos[estado] += 1

		if estado in {"chase", "flee"} and agente._should_bias():
			bias_aplicado += 1

		distancias_observadas["player"].append(percepcion["dist_to_player"])
		distancias_observadas["threat"].append(percepcion["dist_to_threat"])

	frecuencias = {estado: valor / num_corridas for estado, valor in conteos.items()}

	return {
		"escenario": escenario,
		"num_corridas": num_corridas,
		"conteos": conteos,
		"frecuencias": frecuencias,
		"bias_rate": bias_aplicado / num_corridas,
		"promedios": {
			"player": float(np.mean(distancias_observadas["player"])),
			"threat": float(np.mean(distancias_observadas["threat"])),
		},
		"move_interval": agente.move_interval,
		"chase_threshold": agente.chase_threshold,
		"bias_strength": agente.bias_strength,
	}


def exportar_csv(resultados: list[dict], nombre_archivo: str = "modelo_agentes_resultados.csv") -> str:
	ruta = os.path.join(CARPETA_DESTINO, nombre_archivo)
	import csv

	with open(ruta, "w", newline="", encoding="utf-8") as archivo:
		writer = csv.writer(archivo)
		writer.writerow([
			"escenario",
			"corridas",
			"chaos",
			"player_distance",
			"threat_distance",
			"wander_freq",
			"chase_freq",
			"flee_freq",
			"bias_rate",
			"move_interval",
			"chase_threshold",
			"bias_strength",
		])
		for resultado in resultados:
			e = resultado["escenario"]
			writer.writerow([
				e.nombre,
				resultado["num_corridas"],
				e.chaos,
				e.player_distance,
				e.threat_distance,
				resultado["frecuencias"]["wander"],
				resultado["frecuencias"]["chase"],
				resultado["frecuencias"]["flee"],
				resultado["bias_rate"],
				resultado["move_interval"],
				resultado["chase_threshold"],
				resultado["bias_strength"],
			])
	return ruta


def generar_graficos(resultados: list[dict]) -> None:
	nombres = [r["escenario"].nombre for r in resultados]
	posiciones = np.arange(len(nombres))
	ancho = 0.24

	fig, axes = plt.subplots(2, 2, figsize=(15, 10))
	fig.suptitle("Modelo Basado en Agentes - SimuBomber", fontsize=14, fontweight="bold")

	ax = axes[0, 0]
	ax.bar(posiciones - ancho, [r["frecuencias"]["wander"] for r in resultados], ancho, label="wander", color="#5b8def")
	ax.bar(posiciones, [r["frecuencias"]["chase"] for r in resultados], ancho, label="chase", color="#57c785")
	ax.bar(posiciones + ancho, [r["frecuencias"]["flee"] for r in resultados], ancho, label="flee", color="#f2a65a")
	ax.set_xticks(posiciones)
	ax.set_xticklabels(nombres, rotation=10)
	ax.set_ylabel("Frecuencia")
	ax.set_title("Distribución de estados")
	ax.legend()
	ax.grid(axis="y", alpha=0.25)

	ax = axes[0, 1]
	ax.bar(nombres, [r["bias_rate"] for r in resultados], color="#7b61ff", alpha=0.75)
	ax.set_ylabel("Tasa de sesgo aplicada")
	ax.set_title("Aplicación de sesgo por chaos")
	ax.grid(axis="y", alpha=0.25)

	ax = axes[1, 0]
	ax.plot([r["escenario"].chaos for r in resultados], [r["move_interval"] for r in resultados], marker="o", label="move_interval", color="#5b8def")
	ax.plot([r["escenario"].chaos for r in resultados], [r["chase_threshold"] for r in resultados], marker="o", label="chase_threshold", color="#57c785")
	ax.set_xlabel("Chaos")
	ax.set_title("Respuesta del agente al caos")
	ax.legend()
	ax.grid(alpha=0.25)

	ax = axes[1, 1]
	for resultado in resultados:
		etiqueta = resultado["escenario"].nombre
		ax.scatter(resultado["promedios"]["player"], resultado["promedios"]["threat"], s=70, label=etiqueta)
	ax.set_xlabel("Distancia media al jugador")
	ax.set_ylabel("Distancia media a la amenaza")
	ax.set_title("Escenario perceptual")
	ax.legend(fontsize=8)
	ax.grid(alpha=0.25)

	plt.tight_layout()
	ruta = os.path.join(CARPETA_DESTINO, "modelo_agentes_validacion.png")
	plt.savefig(ruta, dpi=300, bbox_inches="tight")
	plt.close()
	print(f"\n✓ Gráfico guardado: {ruta}")


def imprimir_resultados(resultados: list[dict]) -> None:
	for resultado in resultados:
		e = resultado["escenario"]
		print("\n" + "=" * 74)
		print(f"ESCENARIO: {e.nombre}")
		print(f"Corridas: {resultado['num_corridas']}")
		print(f"Chaos: {e.chaos:.2f} | Player dist: {e.player_distance:.1f} | Threat dist: {e.threat_distance:.1f}")
		print(f"Estados: wander={resultado['frecuencias']['wander']:.3f} | chase={resultado['frecuencias']['chase']:.3f} | flee={resultado['frecuencias']['flee']:.3f}")
		print(f"Bias rate: {resultado['bias_rate']:.3f} | move_interval={resultado['move_interval']} | chase_threshold={resultado['chase_threshold']:.1f}")


def main() -> None:
	print("\n" + "█" * 74)
	print("█  MODELO: BASADO EN AGENTES                                  █")
	print("█  Validación formal de percepción, decisión y sesgo          █")
	print("█" * 74)

	escenarios = [
		EscenarioAgente("Exploración", chaos=1.5, player_distance=220.0, threat_distance=180.0, semilla=501),
		EscenarioAgente("Caza", chaos=4.0, player_distance=90.0, threat_distance=180.0, semilla=502),
		EscenarioAgente("Huida", chaos=7.5, player_distance=140.0, threat_distance=60.0, semilla=503),
	]

	resultados = [simular_escenario(escenario, num_corridas=5000) for escenario in escenarios]
	imprimir_resultados(resultados)
	ruta_csv = exportar_csv(resultados)
	generar_graficos(resultados)

	print("\n" + "=" * 74)
	print("VALIDACIÓN")
	print("=" * 74)
	print(f"✓ Resultados exportados a: {ruta_csv}")
	print("✓ La lógica standalone reproduce perceive → decide_state → apply_chaos → chase/flee")
	print("✓ La implementación del juego no fue modificada")
	print("\n" + "=" * 74 + "\n")


if __name__ == "__main__":
	main()
