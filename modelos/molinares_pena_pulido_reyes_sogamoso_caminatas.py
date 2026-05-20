"""
Módulo Independiente: Modelo de Simulación de Caminatas Aleatorias (Random Walks) 2D.
Desarrollado para la validación matemática/experimental del comportamiento de los enemigos.
"""

import sys
import os
import math
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import atexit
import shutil

# Inyección de paths para poder importar desde la carpeta hermana sin romper el entorno
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

# Ruta de la carpeta donde se guardarán las gráficas generadas para el informe
carpeta_destino = _make_output_dir()

# Direcciones legales de Bomberman: Derecha, Izquierda, Abajo, Arriba
DIRECCIONES = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def simular_una_caminata(pasos: int, generador: GeneradorCongruenciaLineal, probs: list[float]) -> list[tuple[int, int]]:
    """Simula una única trayectoria de caminata aleatoria en 2D usando el LCG."""
    trayectoria = [(0, 0)]
    x, y = 0, 0
    
    # Obtenemos todos los números pseudoaleatorios necesarios para esta corrida
    numeros_aleatorios = generador.siguiente_Ri_Congruencia_Lineal(pasos)
    
    for r in numeros_aleatorios:
        # Selección de dirección basada en la distribución de probabilidad acumulada
        if r < probs[0]:
            dx, dy = DIRECCIONES[0]  # Derecha
        elif r < probs[0] + probs[1]:
            dx, dy = DIRECCIONES[1]  # Izquierda
        elif r < probs[0] + probs[1] + probs[2]:
            dx, dy = DIRECCIONES[2]  # Abajo
        else:
            dx, dy = DIRECCIONES[3]  # Arriba
            
        x += dx
        y += dy
        trayectoria.append((x, y))
        
    return trayectoria

def analizar_configuracion(id_config: int, nombre: str, pasos: int, probs: list[float], semilla: int):
    """Ejecuta experimentos masivos para validar el modelo matemáticamente contra la teoría."""
    # Instanciamos el generador del taller anterior
    generador = GeneradorCongruenciaLineal(semilla)
    
    # Ecuaciones Teóricas del Modelo Matemático de Caminatas Aleatorias
    # E[X] = N * (p_derecha - p_izquierda) | E[Y] = N * (p_abajo - p_arriba)
    efecto_x = probs[0] - probs[1]
    efecto_y = probs[2] - probs[3]
    teorico_media_x = pasos * efecto_x
    teorico_media_y = pasos * efecto_y
    
    # Varianza Teórica de un paso individual: E[X^2] - (E[X])^2
    var_paso_x = (probs[0] + probs[1]) - (efecto_x ** 2)
    var_paso_y = (probs[2] + probs[3]) - (efecto_y ** 2)
    teorico_var_x = pasos * var_paso_x
    teorico_var_y = pasos * var_paso_y
    
    # --- Simulación Experimental Monte Carlo (500 corridas del modelo) ---
    num_experimentos = 500
    posiciones_finales_x = []
    posiciones_finales_y = []
    ultima_trayectoria = None
    
    for _ in range(num_experimentos):
        trayectoria = simular_una_caminata(pasos, generador, probs)
        ultima_trayectoria = trayectoria # Guardamos una para graficar
        posiciones_finales_x.append(trayectoria[-1][0])
        posiciones_finales_y.append(trayectoria[-1][1])
        
    exp_media_x = np.mean(posiciones_finales_x)
    exp_media_y = np.mean(posiciones_finales_y)
    exp_var_x = np.var(posiciones_finales_x)
    exp_var_y = np.var(posiciones_finales_y)
    
    # Cálculo de Errores Porcentuales de Convergencia
    def calc_error(teorico, experimental):
        if abs(teorico) < 1e-5: return abs(teorico - experimental) # Error absoluto si el teórico es 0
        return (abs(teorico - experimental) / abs(teorico)) * 100

    err_m_x = calc_error(teorico_media_x, exp_media_x)
    err_m_y = calc_error(teorico_media_y, exp_media_y)
    err_v_x = calc_error(teorico_var_x, exp_var_x)
    err_v_y = calc_error(teorico_var_y, exp_var_y)
    
    # IMPRESIÓN FORMATEADA PARA LAS TABLAS DE TU INFORME
    print("="*60)
    print(f"CONFIGURACIÓN {id_config}: {nombre}")
    print(f"Parámetros: Pasos={pasos} | Probabilidades (D, I, A, Ar)={probs}")
    print("-"*60)
    print(f"Métrica            | Valor Teórico | Valor Experimental | % Error / Dif")
    print(f"Media Final X      | {teorico_media_x:13.3f} | {exp_media_x:18.3f} | {err_m_x:11.2f}%")
    print(f"Media Final Y      | {teorico_media_y:13.3f} | {exp_media_y:18.3f} | {err_m_y:11.2f}%")
    print(f"Varianza X         | {teorico_var_x:13.3f} | {exp_var_x:18.3f} | {err_v_x:11.2f}%")
    print(f"Varianza Y         | {teorico_var_y:13.3f} | {exp_var_y:18.3f} | {err_v_y:11.2f}%")
    print("="*60 + "\n")
    
    # GENERACIÓN DE GRÁFICAS DE COMPORTAMIENTO (Matplotlib)
    tray_np = np.array(ultima_trayectoria)
    plt.figure(figsize=(6, 5))
    plt.plot(tray_np[:, 0], tray_np[:, 1], label='Camino del Enemigo', color='purple', alpha=0.8)
    plt.scatter(0, 0, color='green', s=100, label='Inicio (0,0)', zorder=5)
    plt.scatter(tray_np[-1, 0], tray_np[-1, 1], color='red', s=100, label='Fin Simulación', zorder=5)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.title(f"Muestra Trayectoria 2D - Config {id_config}\n({nombre})")
    plt.xlabel("Coordenada X")
    plt.ylabel("Coordenada Y")
    plt.legend()
    
    # Guardar automáticamente la gráfica para el documento
    nombre_img = f"grafica_config_{id_config}.png"
    plt.savefig(f"{carpeta_destino}/{nombre_img}")
    print(f"[*] Gráfica exportada exitosamente como '{nombre_img}'")
    plt.close()

if __name__ == "__main__":
    print("[+] Iniciando validación experimental en modo Standalone (Punto 3)...")
    semilla_inicial = 123456789
    
    # Configuración 1: Caminata Isótropa (Equilibrada - Comportamiento Wander Puro)
    analizar_configuracion(1, "Wander Equilibrado", pasos=100, probs=[0.25, 0.25, 0.25, 0.25], semilla=semilla_inicial)
    
    # Configuración 2: Sesgo Horizontal a la Derecha (Comportamiento de Persecución/Chase parcial)
    analizar_configuracion(2, "Sesgo Horizontal (Chase Este)", pasos=250, probs=[0.55, 0.15, 0.15, 0.15], semilla=semilla_inicial)
    
    # Configuración 3: Sesgo Vertical hacia Abajo (Efecto de Gravedad o Fuga Estructurada)
    analizar_configuracion(3, "Sesgo Vertical (Flee Norte -> Sur)", pasos=400, probs=[0.10, 0.10, 0.70, 0.10], semilla=semilla_inicial)
    
    print("\n[+] Análisis de sensibilidad implícito: El parámetro que más impacto genera en la dispersión (varianza) es la cantidad de PASOS ejecutados (crecimiento lineal proporcional a N), mientras que el SESGO de probabilidad comprime la varianza sobre el eje con mayor peso.")