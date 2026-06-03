"""
Módulo Independiente: Modelo de Dinámica de Sistemas.

Este modelo formaliza la heurística global que en SimuBomber hoy se resume
en `system_chaos_level` dentro de `SimuBomber/game/game_loop.py` y en las
trazas de `SimuBomber/game/metrics.py`.

Stocks principales:
- enemigos activos
- bombas activas
- explosiones activas
- power-ups activos

Flujos principales:
- aparición de enemigos
- eliminación de enemigos
- colocación de bombas
- detonación de bombas
- disipación de explosiones
- aparición/consumo de power-ups

Retroalimentación:
- más enemigos, bombas y explosiones aumentan el caos
- más caos acelera la aparición de enemigos y bombas
- los power-ups reducen el caos y mejoran la recuperación
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import os
import sys
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
class EscenarioDinamico:
	nombre: str
	enemigos_iniciales: float
	bombas_iniciales: float
	explosiones_iniciales: float
	powerups_iniciales: float
	spawn_enemigos_base: float
	bomb_drop_base: float
	explosion_rate_base: float
	decay_explosion_base: float
	powerup_drop_base: float
	powerup_use_base: float
	chaos_feedback: float
	recovery_feedback: float
	semilla: int


class SistemaDinamicoBomber:
	"""Simulador discreto de stocks y flujos con retroalimentación."""

	def __init__(self, escenario: EscenarioDinamico):
		self.escenario = escenario
		self.lcg = GeneradorCongruenciaLineal(escenario.semilla)

	@staticmethod
	def _clamp(value: float, lower: float, upper: float) -> float:
		return max(lower, min(upper, value))

	def _ruido(self, amplitude: float) -> float:
		r = self.lcg.siguiente_Ri_Congruencia_Lineal(1)[0]
		return (r - 0.5) * 2.0 * amplitude

	def _step(self, state: dict[str, float]) -> dict[str, float]:
		enemigos = state["enemigos"]
		bombas = state["bombas"]
		explosiones = state["explosiones"]
		powerups = state["powerups"]
		caos = state["caos"]

		pressure = 1.0 + 0.08 * caos
		recovery = 1.0 + 0.10 * powerups

		spawn_enemigos = max(0.0, self.escenario.spawn_enemigos_base * pressure + self._ruido(0.20))
		bomb_requests = max(0.0, self.escenario.bomb_drop_base * pressure + self._ruido(0.10))
		bomb_detonation = max(0.0, self.escenario.explosion_rate_base * bombas + self._ruido(0.10))
		enemy_removal = max(0.0, (0.12 + 0.03 * powerups) * enemigos + self._ruido(0.10))
		explosion_decay = max(0.0, self.escenario.decay_explosion_base * explosiones + self._ruido(0.08))
		powerup_drop = max(0.0, self.escenario.powerup_drop_base * max(0.0, enemigos) + self._ruido(0.12))
		powerup_use = max(0.0, self.escenario.powerup_use_base * recovery + self._ruido(0.05))

		enemigos_next = max(0.0, enemigos + spawn_enemigos - enemy_removal)
		bombas_next = max(0.0, bombas + bomb_requests - bomb_detonation)
		explosiones_next = max(0.0, explosiones + bomb_detonation - explosion_decay)
		powerups_next = max(0.0, powerups + powerup_drop - powerup_use)

		caos_target = 0.45 * enemigos_next + 0.30 * bombas_next + 0.25 * explosiones_next
		caos_next = self._clamp(0.62 * caos + 0.38 * caos_target - 0.20 * powerups_next, 0.0, 10.0)
		dificultad_next = self._clamp(1.0 + 0.55 * caos_next, 1.0, 10.0)

		return {
			"enemigos": enemigos_next,
			"bombas": bombas_next,
			"explosiones": explosiones_next,
			"powerups": powerups_next,
			"caos": caos_next,
			"dificultad": dificultad_next,
		}

	def simular(self, pasos: int) -> list[dict[str, float]]:
		state = {
			"enemigos": self.escenario.enemigos_iniciales,
			"bombas": self.escenario.bombas_iniciales,
			"explosiones": self.escenario.explosiones_iniciales,
			"powerups": self.escenario.powerups_iniciales,
			"caos": self._clamp(
				0.45 * self.escenario.enemigos_iniciales + 0.30 * self.escenario.bombas_iniciales + 0.25 * self.escenario.explosiones_iniciales,
				0.0,
				10.0,
			),
			"dificultad": 1.0,
		}

		trayectorias = []
		for t in range(pasos):
			state = self._step(state)
			trayectorias.append({"t": t, **state})
		return trayectorias


def simular_promedio(escenario: EscenarioDinamico, pasos: int, num_corridas: int) -> dict:
	"""Promedia múltiples corridas para validar el comportamiento agregado."""
	trayectorias = []
	for corrida in range(num_corridas):
		sim = SistemaDinamicoBomber(EscenarioDinamico(
			nombre=escenario.nombre,
			enemigos_iniciales=escenario.enemigos_iniciales,
			bombas_iniciales=escenario.bombas_iniciales,
			explosiones_iniciales=escenario.explosiones_iniciales,
			powerups_iniciales=escenario.powerups_iniciales,
			spawn_enemigos_base=escenario.spawn_enemigos_base,
			bomb_drop_base=escenario.bomb_drop_base,
			explosion_rate_base=escenario.explosion_rate_base,
			decay_explosion_base=escenario.decay_explosion_base,
			powerup_drop_base=escenario.powerup_drop_base,
			powerup_use_base=escenario.powerup_use_base,
			chaos_feedback=escenario.chaos_feedback,
			recovery_feedback=escenario.recovery_feedback,
			semilla=escenario.semilla + corrida,
		))
		trayectorias.append(sim.simular(pasos))

	promedios = []
	for paso in range(pasos):
		acumulado = {"enemigos": 0.0, "bombas": 0.0, "explosiones": 0.0, "powerups": 0.0, "caos": 0.0, "dificultad": 0.0}
		for traza in trayectorias:
			punto = traza[paso]
			for clave in acumulado:
				acumulado[clave] += punto[clave]
		for clave in acumulado:
			acumulado[clave] /= num_corridas
		acumulado["t"] = paso
		promedios.append(acumulado)

	return {
		"escenario": escenario,
		"pasos": pasos,
		"corridas": num_corridas,
		"promedios": promedios,
		"final": promedios[-1],
	}


def teorico_deterministico(escenario: EscenarioDinamico, pasos: int) -> list[dict[str, float]]:
	"""Versión sin ruido para comparar con el promedio experimental."""
	state = {
		"enemigos": escenario.enemigos_iniciales,
		"bombas": escenario.bombas_iniciales,
		"explosiones": escenario.explosiones_iniciales,
		"powerups": escenario.powerups_iniciales,
		"caos": max(0.0, 0.45 * escenario.enemigos_iniciales + 0.30 * escenario.bombas_iniciales + 0.25 * escenario.explosiones_iniciales),
		"dificultad": 1.0,
	}
	secuencia = []
	for t in range(pasos):
		caos_actual = state["caos"]
		pressure = 1.0 + 0.08 * state["caos"]
		recovery = 1.0 + 0.10 * state["powerups"]

		spawn_enemigos = max(0.0, escenario.spawn_enemigos_base * pressure)
		bomb_requests = max(0.0, escenario.bomb_drop_base * pressure)
		bomb_detonation = max(0.0, escenario.explosion_rate_base * state["bombas"])
		enemy_removal = max(0.0, (0.12 + 0.03 * state["powerups"]) * state["enemigos"])
		explosion_decay = max(0.0, escenario.decay_explosion_base * state["explosiones"])
		powerup_drop = max(0.0, escenario.powerup_drop_base * max(0.0, state["enemigos"]))
		powerup_use = max(0.0, escenario.powerup_use_base * recovery)

		state = {
			"enemigos": max(0.0, state["enemigos"] + spawn_enemigos - enemy_removal),
			"bombas": max(0.0, state["bombas"] + bomb_requests - bomb_detonation),
			"explosiones": max(0.0, state["explosiones"] + bomb_detonation - explosion_decay),
			"powerups": max(0.0, state["powerups"] + powerup_drop - powerup_use),
		}
		caos_target = 0.45 * state["enemigos"] + 0.30 * state["bombas"] + 0.25 * state["explosiones"]
		state["caos"] = max(0.0, min(10.0, 0.62 * caos_actual + 0.38 * caos_target - 0.20 * state["powerups"]))
		state["dificultad"] = max(1.0, min(10.0, 1.0 + 0.55 * state["caos"]))
		secuencia.append({"t": t, **state})
	return secuencia


def calcular_error_porc(teorico: float, experimental: float) -> float:
	if abs(teorico) < 1e-6:
		return abs(experimental - teorico)
	return abs(experimental - teorico) / abs(teorico) * 100.0


def exportar_csv(resultados: list[dict], nombre_archivo: str = "modelo_dinamica_sistemas_resultados.csv") -> str:
	ruta = os.path.join(CARPETA_DESTINO, nombre_archivo)
	with open(ruta, "w", newline="", encoding="utf-8") as archivo:
		writer = csv.writer(archivo)
		writer.writerow([
			"escenario", "paso", "enemigos", "bombas", "explosiones", "powerups",
			"caos", "dificultad"
		])
		for resultado in resultados:
			escenario = resultado["escenario"].nombre
			for fila in resultado["promedios"]:
				writer.writerow([
					escenario,
					fila["t"],
					fila["enemigos"],
					fila["bombas"],
					fila["explosiones"],
					fila["powerups"],
					fila["caos"],
					fila["dificultad"],
				])
	return ruta


def generar_graficos(resultados: list[dict], teoricos: dict[str, list[dict[str, float]]]) -> None:
	colores = {
		"enemigos": "#5b8def",
		"bombas": "#f2a65a",
		"explosiones": "#d95d67",
		"powerups": "#57c785",
		"caos": "#7b61ff",
		"dificultad": "#333333",
	}

	fig, axes = plt.subplots(2, 2, figsize=(16, 10))
	fig.suptitle("Dinámica de Sistemas en SimuBomber", fontsize=14, fontweight="bold")

	for idx, resultado in enumerate(resultados):
		serie = resultado["promedios"]
		t = [p["t"] for p in serie]
		etiqueta = resultado["escenario"].nombre
		axes[0, 0].plot(t, [p["enemigos"] for p in serie], color=colores["enemigos"], alpha=0.5 if idx else 0.9, label=f"enemigos - {etiqueta}")
		axes[0, 0].plot(t, [p["bombas"] for p in serie], color=colores["bombas"], alpha=0.5 if idx else 0.9, label=f"bombas - {etiqueta}")

		axes[0, 1].plot(t, [p["explosiones"] for p in serie], color=colores["explosiones"], alpha=0.5 if idx else 0.9, label=f"explosiones - {etiqueta}")
		axes[0, 1].plot(t, [p["powerups"] for p in serie], color=colores["powerups"], alpha=0.5 if idx else 0.9, label=f"powerups - {etiqueta}")

		axes[1, 0].plot(t, [p["caos"] for p in serie], color=colores["caos"], alpha=0.5 if idx else 0.9, label=f"caos - {etiqueta}")
		axes[1, 0].plot(t, [p["dificultad"] for p in serie], color=colores["dificultad"], alpha=0.5 if idx else 0.9, label=f"dificultad - {etiqueta}")

		teorico = teoricos[etiqueta]
		axes[1, 1].plot(t, [p["caos"] for p in serie], color=colores["caos"], alpha=0.35 if idx else 0.8, label=f"caos exp - {etiqueta}")
		axes[1, 1].plot(t, [p["caos"] for p in teorico], color=colores["caos"], linestyle="--", alpha=0.35 if idx else 0.8, label=f"caos teo - {etiqueta}")

	axes[0, 0].set_title("Stocks principales: enemigos y bombas")
	axes[0, 1].set_title("Flujos visibles: explosiones y power-ups")
	axes[1, 0].set_title("Retroalimentación global: caos y dificultad")
	axes[1, 1].set_title("Caos experimental vs teórico")

	for ax in axes.flat:
		ax.grid(alpha=0.25)
		ax.legend(fontsize=7)

	plt.tight_layout()
	ruta = os.path.join(CARPETA_DESTINO, "modelo_dinamica_sistemas_validacion.png")
	plt.savefig(ruta, dpi=300, bbox_inches="tight")
	plt.close()
	print(f"\n✓ Gráfico guardado: {ruta}")


def imprimir_resumen(resultados: list[dict], teoricos: dict[str, list[dict[str, float]]]) -> None:
	for resultado in resultados:
		escenario = resultado["escenario"]
		exp = resultado["final"]
		teo = teoricos[escenario.nombre][-1]
		print("\n" + "=" * 78)
		print(f"ESCENARIO: {escenario.nombre}")
		print(f"Corridas: {resultado['corridas']} | Pasos: {resultado['pasos']}")
		print(f"Stocks finales exp: enemigos={exp['enemigos']:.2f} | bombas={exp['bombas']:.2f} | explosiones={exp['explosiones']:.2f} | powerups={exp['powerups']:.2f}")
		print(f"Caos final exp: {exp['caos']:.2f} | Dificultad final exp: {exp['dificultad']:.2f}")
		print(f"Caos final teo: {teo['caos']:.2f} | Error: {calcular_error_porc(teo['caos'], exp['caos']):.2f}%")
		print(f"Dificultad final teo: {teo['dificultad']:.2f} | Error: {calcular_error_porc(teo['dificultad'], exp['dificultad']):.2f}%")


def main() -> None:
	print("\n" + "█" * 78)
	print("█  MODELO: DINÁMICA DE SISTEMAS                               █")
	print("█  Stocks, flujos y retroalimentación en SimuBomber            █")
	print("█" * 78)

	escenarios = [
		EscenarioDinamico(
			nombre="Balanceado",
			enemigos_iniciales=2.0,
			bombas_iniciales=1.0,
			explosiones_iniciales=0.0,
			powerups_iniciales=0.0,
			spawn_enemigos_base=0.22,
			bomb_drop_base=0.12,
			explosion_rate_base=0.25,
			decay_explosion_base=0.55,
			powerup_drop_base=0.04,
			powerup_use_base=0.03,
			chaos_feedback=0.45,
			recovery_feedback=0.20,
			semilla=701,
		),
		EscenarioDinamico(
			nombre="Presión alta",
			enemigos_iniciales=4.0,
			bombas_iniciales=3.0,
			explosiones_iniciales=1.0,
			powerups_iniciales=0.0,
			spawn_enemigos_base=0.35,
			bomb_drop_base=0.20,
			explosion_rate_base=0.30,
			decay_explosion_base=0.45,
			powerup_drop_base=0.03,
			powerup_use_base=0.02,
			chaos_feedback=0.55,
			recovery_feedback=0.15,
			semilla=702,
		),
		EscenarioDinamico(
			nombre="Recuperación",
			enemigos_iniciales=1.0,
			bombas_iniciales=0.0,
			explosiones_iniciales=0.0,
			powerups_iniciales=2.0,
			spawn_enemigos_base=0.14,
			bomb_drop_base=0.08,
			explosion_rate_base=0.20,
			decay_explosion_base=0.70,
			powerup_drop_base=0.06,
			powerup_use_base=0.05,
			chaos_feedback=0.35,
			recovery_feedback=0.28,
			semilla=703,
		),
	]

	pasos = 120
	corridas = 200

	resultados = []
	teoricos = {}
	for escenario in escenarios:
		resultado = simular_promedio(escenario, pasos, corridas)
		resultados.append(resultado)
		teoricos[escenario.nombre] = teorico_deterministico(escenario, pasos)

	imprimir_resumen(resultados, teoricos)
	ruta_csv = exportar_csv(resultados)
	generar_graficos(resultados, teoricos)

	print("\n" + "=" * 78)
	print("SENSIBILIDAD")
	print("=" * 78)
	print("✓ Si aumenta el stock de enemigos, sube el caos y también la dificultad efectiva.")
	print("✓ Si aumentan bombas y explosiones, el sistema entra en retroalimentación positiva.")
	print("✓ Los power-ups actúan como retroalimentación negativa y ayudan a estabilizar el sistema.")

	print("\n" + "=" * 78)
	print("EXPORTACIÓN")
	print("=" * 78)
	print(f"✓ Resultados exportados a: {ruta_csv}")
	print("✓ Modelo listo para el informe del taller como dinámica de sistemas formal.")
	print("\n" + "=" * 78 + "\n")


if __name__ == "__main__":
	main()
