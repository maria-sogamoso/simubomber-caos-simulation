"""
Módulo Independiente: Modelo de Simulación Monte Carlo.

Aplicación en SimuBomber:
- Estimar la probabilidad de drop de power-ups después de derrotar enemigos.
- Comparar frecuencia teórica vs frecuencia observada en muchas corridas.
- Exportar resultados para el informe del taller.
"""

from __future__ import annotations

import csv
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
class EscenarioMonteCarlo:
	nombre: str
	p_no_drop: float
	p_health: float
	p_speed: float
	semilla: int

	@property
	def probabilidades(self) -> dict[str, float]:
		return {
			"none": self.p_no_drop,
			"health": self.p_health,
			"speed": self.p_speed,
		}


def sample_drop(r: float, escenario: EscenarioMonteCarlo) -> str:
	if r < escenario.p_no_drop:
		return "none"
	if r < escenario.p_no_drop + escenario.p_health:
		return "health"
	return "speed"


def simular_monte_carlo(escenario: EscenarioMonteCarlo, num_corridas: int) -> dict:
	"""Ejecuta Monte Carlo para estimar probabilidades de drop."""
	generador = GeneradorCongruenciaLineal(escenario.semilla)
	counts = {"none": 0, "health": 0, "speed": 0}
	historial_health = []
	historial_speed = []

	for corrida in range(1, num_corridas + 1):
		r = generador.siguiente_Ri_Congruencia_Lineal(1)[0]
		resultado = sample_drop(r, escenario)
		counts[resultado] += 1
		historial_health.append(counts["health"] / corrida)
		historial_speed.append(counts["speed"] / corrida)

	estimadas = {clave: valor / num_corridas for clave, valor in counts.items()}
	errores = {
		clave: abs(escenario.probabilidades[clave] - estimadas[clave]) * 100
		for clave in counts
	}

	return {
		"escenario": escenario,
		"num_corridas": num_corridas,
		"counts": counts,
		"estimadas": estimadas,
		"errores": errores,
		"historial_health": historial_health,
		"historial_speed": historial_speed,
	}


def exportar_csv(resultados: list[dict], nombre_archivo: str = "modelo_monte_carlo_resultados.csv") -> str:
	ruta = os.path.join(CARPETA_DESTINO, nombre_archivo)
	with open(ruta, "w", newline="", encoding="utf-8") as archivo:
		writer = csv.writer(archivo)
		writer.writerow([
			"escenario",
			"corridas",
			"p_no_drop_teorica",
			"p_health_teorica",
			"p_speed_teorica",
			"p_no_drop_observada",
			"p_health_observada",
			"p_speed_observada",
			"error_no_drop_pct",
			"error_health_pct",
			"error_speed_pct",
		])
		for resultado in resultados:
			escenario = resultado["escenario"]
			writer.writerow([
				escenario.nombre,
				resultado["num_corridas"],
				escenario.p_no_drop,
				escenario.p_health,
				escenario.p_speed,
				resultado["estimadas"]["none"],
				resultado["estimadas"]["health"],
				resultado["estimadas"]["speed"],
				resultado["errores"]["none"],
				resultado["errores"]["health"],
				resultado["errores"]["speed"],
			])
	return ruta


def generar_graficos(resultados: list[dict]) -> None:
	escenarios = [resultado["escenario"].nombre for resultado in resultados]
	posiciones = np.arange(len(escenarios))
	ancho = 0.25

	fig, axes = plt.subplots(1, 2, figsize=(15, 6))
	fig.suptitle("Monte Carlo para Drops de Power-Ups en SimuBomber", fontsize=14, fontweight="bold")

	ax = axes[0]
	teoricas_none = [r["escenario"].p_no_drop for r in resultados]
	teoricas_health = [r["escenario"].p_health for r in resultados]
	teoricas_speed = [r["escenario"].p_speed for r in resultados]
	observadas_none = [r["estimadas"]["none"] for r in resultados]
	observadas_health = [r["estimadas"]["health"] for r in resultados]
	observadas_speed = [r["estimadas"]["speed"] for r in resultados]

	ax.bar(posiciones - ancho, teoricas_none, ancho, label="Teórico: no drop", color="#5b8def")
	ax.bar(posiciones, teoricas_health, ancho, label="Teórico: health", color="#57c785")
	ax.bar(posiciones + ancho, teoricas_speed, ancho, label="Teórico: speed", color="#f2a65a")
	ax.bar(posiciones - ancho, observadas_none, ancho, alpha=0.35, color="#5b8def")
	ax.bar(posiciones, observadas_health, ancho, alpha=0.35, color="#57c785")
	ax.bar(posiciones + ancho, observadas_speed, ancho, alpha=0.35, color="#f2a65a")
	ax.set_xticks(posiciones)
	ax.set_xticklabels(escenarios, rotation=10)
	ax.set_ylabel("Probabilidad estimada")
	ax.set_title("Frecuencia teórica vs observada")
	ax.legend(fontsize=8)
	ax.grid(axis="y", alpha=0.25)

	ax = axes[1]
	base = resultados[0]
	ax.plot(base["historial_health"], label="P(health) acumulada", color="#57c785")
	ax.plot(base["historial_speed"], label="P(speed) acumulada", color="#f2a65a")
	ax.axhline(base["escenario"].p_health, color="#57c785", linestyle="--", alpha=0.7)
	ax.axhline(base["escenario"].p_speed, color="#f2a65a", linestyle="--", alpha=0.7)
	ax.set_title(f"Convergencia Monte Carlo - {base['escenario'].nombre}")
	ax.set_xlabel("Corridas")
	ax.set_ylabel("Probabilidad acumulada")
	ax.grid(alpha=0.25)
	ax.legend()

	plt.tight_layout()
	ruta = os.path.join(CARPETA_DESTINO, "modelo_monte_carlo_drops.png")
	plt.savefig(ruta, dpi=300, bbox_inches="tight")
	plt.close()
	print(f"\n✓ Gráfico guardado: {ruta}")


def imprimir_resultados(resultados: list[dict]) -> None:
	for resultado in resultados:
		escenario = resultado["escenario"]
		print("\n" + "=" * 72)
		print(f"ESCENARIO: {escenario.nombre}")
		print(f"Corridas: {resultado['num_corridas']}")
		print(f"Teórico:  no_drop={escenario.p_no_drop:.3f} | health={escenario.p_health:.3f} | speed={escenario.p_speed:.3f}")
		print(f"Observado: no_drop={resultado['estimadas']['none']:.3f} | health={resultado['estimadas']['health']:.3f} | speed={resultado['estimadas']['speed']:.3f}")
		print(f"Error:     no_drop={resultado['errores']['none']:.2f}% | health={resultado['errores']['health']:.2f}% | speed={resultado['errores']['speed']:.2f}%")


def main() -> None:
	print("\n" + "█" * 72)
	print("█  MODELO: SIMULACIÓN MONTE CARLO                              █")
	print("█  Aplicación: estimación de drops de power-ups                 █")
	print("█" * 72)

	escenarios = [
		EscenarioMonteCarlo("Base SimuBomber", 0.65, 0.20, 0.15, 101),
		EscenarioMonteCarlo("Generoso", 0.50, 0.30, 0.20, 202),
		EscenarioMonteCarlo("Escaso", 0.80, 0.12, 0.08, 303),
	]

	num_corridas = 5000
	resultados = [simular_monte_carlo(escenario, num_corridas) for escenario in escenarios]

	imprimir_resultados(resultados)
	ruta_csv = exportar_csv(resultados)
	generar_graficos(resultados)

	print("\n" + "=" * 72)
	print("EXPORTACIÓN")
	print("=" * 72)
	print(f"✓ Resultados exportados a: {ruta_csv}")
	print("✓ Modelo listo para integrarse con PowerUpSystem y el flujo de derrotas de enemigos")
	print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
	main()