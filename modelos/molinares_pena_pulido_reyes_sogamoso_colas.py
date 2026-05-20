"""
Módulo Independiente: Modelo de Simulación de Sistemas de Colas (Queueing Systems) M/M/1.
Desarrollado para la validación matemática/experimental de procesos de encolamiento.
Aplicable a: cola de solicitudes de bombas, cola de eventos, cola de spawns de power-ups.
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import atexit
import shutil

# Inyección de paths para poder importar desde la carpeta hermana
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

carpeta_destino = _make_output_dir()


def simular_cola_mm1(lambda_rate: float, mu_rate: float, num_clientes: int, 
                     generador: GeneradorCongruenciaLineal) -> dict:
    """
    Simulación vectorizada eficiente de una cola M/M/1.
    """
    # Generar números aleatorios para inter-llegadas y tiempos de servicio
    nums = generador.siguiente_Ri_Congruencia_Lineal(num_clientes * 2)
    nums = np.array(nums)
    
    # Inter-llegadas exponenciales: t = -ln(U) / λ
    u1 = np.clip(nums[:num_clientes], 1e-6, 1 - 1e-6)
    inter_llegadas = -np.log(u1) / lambda_rate
    
    # Tiempos de servicio exponenciales: t = -ln(U) / μ
    u2 = np.clip(nums[num_clientes:], 1e-6, 1 - 1e-6)
    tiempos_servicio = -np.log(u2) / mu_rate
    
    # Tiempos de llegada acumulativos
    tiempos_llegada = np.cumsum(inter_llegadas)
    
    # Simular: calcular tiempos de espera
    tiempos_espera = np.zeros(num_clientes)
    tiempo_salida_anterior = 0
    
    for i in range(num_clientes):
        if tiempos_llegada[i] >= tiempo_salida_anterior:
            tiempos_espera[i] = 0
            tiempo_salida_anterior = tiempos_llegada[i] + tiempos_servicio[i]
        else:
            tiempos_espera[i] = tiempo_salida_anterior - tiempos_llegada[i]
            tiempo_salida_anterior += tiempos_servicio[i]
    
    return {
        "tiempo_espera_promedio": np.mean(tiempos_espera),
        "tiempo_espera_std": np.std(tiempos_espera),
        "tiempos_espera": tiempos_espera
    }


def calcular_metricas_teoricas(lambda_rate: float, mu_rate: float) -> dict:
    """
    Fórmulas de teoría de colas M/M/1:
    ρ = λ/μ, Wq = λ/(μ(μ-λ)), Lq = λ²/(μ(μ-λ))
    """
    rho = lambda_rate / mu_rate
    
    if rho >= 1:
        return {
            "rho": rho,
            "Wq": float('inf'),
            "Lq": float('inf'),
            "L": float('inf'),
            "W": float('inf'),
            "P0": 0
        }
    
    denom = mu_rate - lambda_rate
    Wq = lambda_rate / (mu_rate * denom)
    Lq = (lambda_rate ** 2) / (mu_rate * denom)
    
    return {
        "rho": rho,
        "Wq": Wq,
        "Lq": Lq,
        "L": lambda_rate / denom,
        "W": 1 / denom,
        "P0": 1 - rho
    }


def analizar_configuracion(id_config: int, nombre: str, lambda_rate: float, mu_rate: float,
                          num_clientes: int = 1000, semilla: int = 42, num_experimentos: int = 50):
    """Ejecuta experimentos para validar teórico vs experimental."""
    
    print("\n" + "="*70)
    print(f"CONFIGURACIÓN {id_config}: {nombre}")
    print(f"λ={lambda_rate:.3f} llegadas/unidad | μ={mu_rate:.3f} servicios/unidad | ρ={lambda_rate/mu_rate:.3f}")
    print(f"Clientes/exp: {num_clientes} | Experimentos: {num_experimentos}")
    print("-"*70)
    
    metricas_teoricas = calcular_metricas_teoricas(lambda_rate, mu_rate)
    generador = GeneradorCongruenciaLineal(semilla)
    
    # Ejecutar experimentos
    resultados_wq = []
    todos_tiempos_espera = []
    
    for exp in range(num_experimentos):
        resultado = simular_cola_mm1(lambda_rate, mu_rate, num_clientes, generador)
        resultados_wq.append(resultado["tiempo_espera_promedio"])
        todos_tiempos_espera.extend(resultado["tiempos_espera"])
    
    exp_wq = np.mean(resultados_wq)
    exp_std_wq = np.std(resultados_wq)
    
    # Error porcentual
    if abs(metricas_teoricas["Wq"]) > 1e-5:
        error = (abs(metricas_teoricas["Wq"] - exp_wq) / abs(metricas_teoricas["Wq"])) * 100
    else:
        error = abs(metricas_teoricas["Wq"] - exp_wq)
    
    # Mostrar tabla
    print(f"\n{'Métrica':<30} {'Teórico':>15} {'Experimental':>15} {'% Error':>15}")
    print("-"*70)
    print(f"{'Tiempo espera (Wq)':<30} {metricas_teoricas['Wq']:>15.6f} {exp_wq:>15.6f} {error:>14.2f}%")
    print(f"{'Desv. Est. Wq':<30} {'---':>15} {exp_std_wq:>15.6f} {'---':>15}")
    print(f"{'Factor utilización (ρ)':<30} {metricas_teoricas['rho']:>15.4f} {'---':>15} {'---':>15}")
    
    return {
        "id": id_config,
        "nombre": nombre,
        "lambda": lambda_rate,
        "mu": mu_rate,
        "rho": metricas_teoricas["rho"],
        "teorico_wq": metricas_teoricas["Wq"],
        "experimental_wq": exp_wq,
        "std_wq": exp_std_wq,
        "error_pct": error,
        "tiempos_espera": todos_tiempos_espera,
        "resultados_wq": resultados_wq
    }


def generar_graficos(configs):
    """Genera gráficos de validación."""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Validación Modelo de Colas M/M/1 (Teórico vs Experimental)", fontsize=14, fontweight='bold')
    
    # Gráfico 1: Wq teórico vs experimental
    ax = axes[0, 0]
    nombres = [c["nombre"] for c in configs]
    x = np.arange(len(nombres))
    width = 0.35
    
    teoricos = [c["teorico_wq"] for c in configs]
    experimentales = [c["experimental_wq"] for c in configs]
    
    ax.bar(x - width/2, teoricos, width, label="Teórico", color="steelblue", alpha=0.8)
    ax.bar(x + width/2, experimentales, width, label="Experimental", color="coral", alpha=0.8)
    ax.set_ylabel("Wq (Tiempo de Espera)", fontweight='bold')
    ax.set_title("Tiempo Promedio de Espera en Cola", fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=15, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    for i, e in enumerate([c["error_pct"] for c in configs]):
        ax.text(i, max(teoricos[i], experimentales[i]) * 1.08, f"{e:.1f}%", 
                ha='center', fontweight='bold', fontsize=9)
    
    # Gráfico 2: Factor de utilización
    ax = axes[0, 1]
    rhos = [c["rho"] for c in configs]
    colores = ["green" if r < 0.8 else "orange" if r < 0.95 else "red" for r in rhos]
    ax.bar(nombres, rhos, color=colores, alpha=0.7)
    ax.axhline(y=1, color='red', linestyle='--', linewidth=2, label="Límite estabilidad")
    ax.set_ylabel("ρ = λ/μ", fontweight='bold')
    ax.set_title("Factor de Utilización del Servidor", fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    for i, rho in enumerate(rhos):
        ax.text(i, rho + 0.03, f"{rho:.3f}", ha='center', fontweight='bold', fontsize=9)
    
    # Gráfico 3: Distribución de tiempos de espera
    ax = axes[1, 0]
    for cfg in configs:
        tiempos = np.array(cfg["tiempos_espera"])
        tiempos = tiempos[tiempos < np.percentile(tiempos, 95)]  # Limitar outliers
        ax.hist(tiempos, bins=30, alpha=0.5, label=cfg["nombre"][:15])
    
    ax.set_xlabel("Tiempo de Espera", fontweight='bold')
    ax.set_ylabel("Frecuencia", fontweight='bold')
    ax.set_title("Distribución de Tiempos de Espera", fontweight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Gráfico 4: Convergencia de Wq por experimento
    ax = axes[1, 1]
    for cfg in configs:
        ax.plot(cfg["resultados_wq"], marker='o', linestyle='-', alpha=0.7, label=cfg["nombre"][:15])
    
    ax.axhline(y=cfg["teorico_wq"], color='red', linestyle='--', linewidth=2, label="Teórico")
    ax.set_xlabel("# Experimento", fontweight='bold')
    ax.set_ylabel("Wq Promedio", fontweight='bold')
    ax.set_title("Convergencia de Wq", fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    ruta = os.path.join(carpeta_destino, "modelo_colas_validacion.png")
    plt.savefig(ruta, dpi=300, bbox_inches='tight')
    print(f"\n✓ Gráfico guardado: {ruta}")
    plt.close()


def main():
    """Análisis completo de colas M/M/1 con 3 configuraciones."""
    
    print("\n" + "█"*70)
    print("█  MODELO: SISTEMAS DE COLAS (QUEUEING SYSTEMS) M/M/1         █")
    print("█  Validación: Teórico vs Experimental                         █")
    print("█"*70)
    
    # 3 configuraciones de carga
    cfg1 = analizar_configuracion(
        1, "Baja Carga (ρ≈0.3)", 0.6, 2.0, 1000, 42, 50
    )
    
    cfg2 = analizar_configuracion(
        2, "Media Carga (ρ≈0.7)", 1.4, 2.0, 1000, 43, 50
    )
    
    cfg3 = analizar_configuracion(
        3, "Alta Carga (ρ≈0.85)", 1.7, 2.0, 1000, 44, 50
    )
    
    configs = [cfg1, cfg2, cfg3]
    generar_graficos(configs)
    
    # Conclusiones
    print("\n" + "="*70)
    print("CONCLUSIONES")
    print("="*70)
    print("\n✓ Fórmula crítica: Wq = λ / (μ(μ - λ))")
    print("  - Si λ → μ, entonces Wq → ∞ (inestabilidad)")
    print("  - Si μ → ∞, entonces Wq → 0 (servicio muy rápido)")
    print("\n✓ Factor ρ = λ/μ determina el comportamiento:")
    print("  - ρ < 0.5: Baja utilización, poca congestión")
    print("  - 0.5 ≤ ρ < 0.8: Moderado")
    print("  - 0.8 ≤ ρ < 1: Alto (cercano a inestabilidad)")
    print("\n✓ INTEGRACIÓN EN SIMUBOMBER:")
    print("  - Modelar: cola de solicitudes de bombas")
    print("  - Parámetros: λ (frecuencia), μ (velocidad colocación)")
    print("  - Observable en juego: longitud de cola, tiempo espera")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
