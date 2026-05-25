# SimuBomber: Caos

Juego de bombas tipo Bomberman con 3 niveles temáticos y 5 modelos de simulación integrados.

## Instalación

pip install -r requirements.txt
cd SimuBomber
python main.py

## Controles

Acción / Tecla
Moverse / ↑ ↓ ← → o WASD
Colocar bomba / ESPACIO
Pausar o Salir / ESC
Seleccionar / ENTER

## Personajes

Personaje | Vidas | Velocidad | Descripción

Guerrero Élfico | 3 | 4 | Equilibrado
Gran Hechicera | 5 | 2 | Más vidas, menos veloz
Lagarto Veloz | 2 | 7 | Muy rápido, pocas vidas

## Niveles

| Nivel | Escenario | Enemigos
| 1 | Naturaleza/Prado | 3 Goblins (caminata aleatoria)
| 2 | Cementerio | 3 Goblins + 2 Imps (más rápidos)
| 3 | Mazmorra | 3 Goblins + 2 Imps + 2 Demonios de Fuego (2 vidas)

## Poderes

- **Rayo**: incrementa velocidad temporalmente
- **Corazón completo**: recupera 1 vida entera
- **Medio corazón**: recupera 0.5 de vida

## Obstáculos

- **Fijos** (paredes de piedra): no se destruyen con bombas
- **Destructibles** (arbustos/cajas): desaparecen con la explosión

## Modelos de Simulación

1. **Caminatas Aleatorias** (LCG): movimiento de enemigos tipo goblin
2. **Sistemas de Colas**: gestión de bombas activas (max 3)
3. **Monte Carlo**: probabilidad de drop de power-ups al eliminar enemigos
4. **Basado en Agentes**: estados flee/chase/wander por proximidad al jugador
5. **Dinámica de Sistemas**: nivel de caos que afecta velocidad y comportamiento de enemigos
