# SimuBomber: Caos

Juego de bombas tipo Bomberman con 3 niveles temáticos y 5 modelos de simulación integrados.

## Instalación

```bash
pip install -r requirements.txt
cd SimuBomber
python main.py
```

## Controles

| Acción | Tecla |
|---|---|
| Moverse | ↑ ↓ ← → o WASD |
| Colocar bomba | ESPACIO |
| Pausar | ESC o P |
| Confirmar menú | ENTER |

## Personajes

| Personaje | Vidas | Velocidad | Descripción |
|---|---|---|---|
| Guerrero Élfico | 3 | 3 | Equilibrado |
| Gran Hechicera | 5 | 2 | Más vidas, menos veloz |
| Lagarto Veloz | 2 | 5 | Muy rápido, pocas vidas |

## Niveles

| Nivel | Escenario | Enemigos |
|---|---|---|
| 1 - Naturaleza | Bosque Maldito | 3 Zombies (caminata aleatoria) |
| 2 - Cementerio | Cementerio Oscuro | 3 Zombies + 2 Imps (persiguen/huyen) |
| 3 - Mazmorra | Mazmorra del Dragón | 3 Zombies + 2 Imps + 2 Dragones de Fuego (2 vidas) |

## Poderes

| Tipo | Efecto |
|---|---|
| Corazón completo | Recupera 1 vida |
| Medio corazón | Recupera 0.5 de vida |
| Velocidad | +3 velocidad por 4 segundos |

## Obstáculos

- **Fijos** (paredes): no se destruyen, bloquean explosiones
- **Rompibles** (arbustos/cajas): se destruyen con explosión pero la bloquean

## Modelos de Simulación

| # | Modelo | Integración en el juego | Generador PRNG |
|---|---|---|---|
| 1 | **Caminatas Aleatorias** | Movimiento aleatorio de Zombies con probabilidad 0.6 de mantener dirección | Congruencia Lineal |
| 2 | **Sistemas de Colas M/M/1** | Cola FIFO de solicitudes de bomba con métricas de llegadas, servicio y rechazos | Congruencia Lineal |
| 3 | **Monte Carlo** | Drop de power-ups al eliminar enemigos (65% nada, 15% salud, 10% salud media, 10% velocidad) | Congruencia Lineal |
| 4 | **Basado en Agentes** | Imps y Dragones con percepción, estados (wander/chase/flee) y bias direccional | Congruencia Lineal |
| 5 | **Dinámica de Sistemas** | Stocks (enemigos, bombas, explosiones, powerups) → cálculo de caos 0-10 que ajusta comportamiento | Determinístico |

## Estructura del Proyecto

```
SimuBomber/
├── main.py                 # Punto de entrada con menú
├── config.py               # Configuración global
├── assets_loader.py        # Carga y cache de sprites/tiles/sonidos
├── assets/                 # Sprites, tiles, sonidos, fuentes
├── game/
│   ├── game_loop.py        # Loop principal con 3 niveles
│   ├── map.py              # Mapa tile-based
│   ├── player.py           # Jugador con sprites animados
│   ├── movement.py         # Movimiento grid-aligned con colisión
│   ├── bomb.py             # Bombas con cola M/M/1 y explosión por rayos
│   ├── enemy.py            # 3 tipos: Zombie, Imp, Dragon
│   ├── powerup.py          # Power-ups con Monte Carlo
│   ├── hud.py              # Interfaz de usuario
│   ├── menu.py             # Menú principal y submenús
│   ├── sounds.py           # Sistema de audio
│   ├── dynamics.py         # Dinámica de sistemas (stocks & flows)
│   └── metrics.py          # Métricas de simulación
└── modelos/                # Módulos standalone para validación
```
