"""
Modelo Basado en Agentes — SimuBomber: Caos
Archivo : molinares_pena_pulido_reyes_sogamoso_agentes.py
Autores : Molinares · Peña · Pulido · Reyes · Sogamoso
PRNG    : GeneradorCongruenciaLineal (Congruencia Lineal, Numerical Recipes)
          X_{n+1} = (a * X_n + c) mod m  |  a=1664525, c=1013904223, m=2^32
"""

from __future__ import annotations
import math, datetime

class GeneradorCongruenciaLineal:
    def __init__(self, semilla: int):
        """Inicializa el LCG.

        - Usa parametros fijos (a, c, m) del reporte.
        - Normaliza la semilla a int para el ciclo modular.
        """
        self.semilla = int(semilla)
        self.a = 1664525
        self.c = 1013904223
        self.m = 2**32

    def siguiente_Ri_Congruencia_Lineal(self, pasos: int = 1):
        """Genera valores Ri en [0,1).

        - pasos: cantidad de iteraciones a producir.
        - Retorna lista con cada Ri normalizado por m.
        """
        out = []
        for _ in range(pasos):
            self.semilla = (self.a * self.semilla + self.c) % self.m
            out.append(self.semilla / self.m)
        return out

def _ri(lcg): return lcg.siguiente_Ri_Congruencia_Lineal(1)[0]

DIRS = ((1,0),(-1,0),(0,1),(0,-1))
TILE = 48

class Vec2:
    __slots__ = ("x","y")
    def __init__(self, x=0.0, y=0.0):
        """Crea un vector 2D para posiciones y distancias.

        - x, y: coordenadas en espacio continuo (pixeles).
        """
        self.x=float(x); self.y=float(y)
    def dist(self, o) -> float:
        """Calcula distancia euclidiana a otro vector."""
        return math.hypot(self.x-o.x, self.y-o.y)

class Agente:
    """Zombie — random-walk puro mediante LCG."""
    KEEP_DIR = 0.60

    def __init__(self, ax, ay, W, H, seed, tipo="Zombie", speed=2, move_interval=12):
        """Inicializa el agente base.

        - ax, ay: celda inicial (coordenadas discretas en tiles).
        - W, H: dimensiones del mapa en tiles.
        - seed: semilla para el PRNG del agente.
        - tipo, speed, move_interval: ajustes de comportamiento.
        """
        self.pos   = Vec2(ax*TILE, ay*TILE)
        self.W     = W*TILE; self.H = H*TILE
        self.tipo  = tipo;   self.alive = True
        self.speed = speed;  self.move_interval = move_interval
        self.base_move_interval = move_interval
        self.direction = DIRS[0]; self.frame = 0
        self.lcg   = GeneradorCongruenciaLineal(seed)
        self.state = "wander"
        self.dist_jugador = float("inf"); self.dist_amenaza = float("inf")
        self.chase_threshold = 0; self.flee_threshold = 0; self.bias_strength = 0.0

    def aplicar_caos(self, chaos: float):
        """Ajusta la frecuencia de movimiento en funcion del caos.

        - chaos: valor continuo que acelera el agente.
        - Se impone un minimo para evitar intervalos no validos.
        """
        self.move_interval = max(6, int(self.base_move_interval - chaos * 0.4))

    def percibir(self, jugador, amenaza_pos=None):
        """Actualiza percepciones del agente.

        - jugador: vector o entidad con posicion.
        - amenaza_pos: Vec2 o tupla (x, y) de la amenaza.
        """
        self.dist_jugador = self.pos.dist(jugador)
        self.dist_amenaza = self.pos.dist(amenaza_pos) if amenaza_pos else float("inf")
        self._jugador = jugador; self._amenaza = amenaza_pos

    def _decidir_estado(self):
        """Decide el estado actual del agente.

        - flee si amenaza dentro del umbral.
        - chase si jugador dentro del umbral.
        - wander en otro caso.
        """
        if self._amenaza and self.dist_amenaza < self.flee_threshold: self.state = "flee"
        elif self.dist_jugador < self.chase_threshold:                self.state = "chase"
        else:                                                          self.state = "wander"

    def _mejor_dir(self, target, flee):
        """Calcula la direccion optima respecto al objetivo.

        - target: posicion objetivo.
        - flee: True para maximizar distancia, False para minimizar.
        """
        best, bs = DIRS[0], None
        for d in DIRS:
            sc = math.hypot(target.x - (self.pos.x+d[0]*self.speed),
                            target.y - (self.pos.y+d[1]*self.speed))
            if bs is None or (flee and sc>bs) or (not flee and sc<bs): best,bs=d,sc
        return best

    def _elegir_dir(self):
        """Elige direccion siguiendo caminata aleatoria.

        - KEEP_DIR controla la probabilidad de mantener rumbo.
        - En cambio, selecciona una direccion distinta uniforme.
        """
        if self.direction in DIRS and _ri(self.lcg) < self.KEEP_DIR: return
        cands = [d for d in DIRS if d != self.direction] or list(DIRS)
        self.direction = cands[int(_ri(self.lcg)*len(cands))]

    def _mover(self):
        """Aplica el desplazamiento y rebota en limites.

        - Si cruza el borde, revierte la direccion en ese eje.
        """
        nx = self.pos.x + self.direction[0]*self.speed
        ny = self.pos.y + self.direction[1]*self.speed
        if nx < 0 or nx+TILE > self.W: nx=self.pos.x; self.direction=(-self.direction[0],self.direction[1])
        if ny < 0 or ny+TILE > self.H: ny=self.pos.y; self.direction=(self.direction[0],-self.direction[1])
        self.pos.x=nx; self.pos.y=ny

    def update(self, jugador, amenaza_pos=None):
        """Ciclo de actualizacion por tick.

        - Percibe jugador/amenaza, decide estado y ajusta direccion.
        - Mueve segun la direccion vigente.
        """
        if not self.alive: return
        self.frame += 1
        self.percibir(jugador, amenaza_pos)
        self._decidir_estado()
        if self.frame % self.move_interval == 1: self._elegir_dir()
        self._mover()

    def contacto(self, jugador, radio=TILE*0.8):
        """Retorna True si el agente esta en contacto con el jugador.

        - radio define el umbral de colision en pixeles.
        """
        return self.dist_jugador < radio


class ImpAgente(Agente):
    """Imp — reactivo: persigue al jugador, huye de explosiones."""
    KEEP_DIR = 0.25

    def __init__(self, ax, ay, W, H, seed):
        """Inicializa el imp con umbrales de persecucion y huida."""
        super().__init__(ax, ay, W, H, seed, "Imp", speed=3, move_interval=8)
        self.chase_threshold=280; self.flee_threshold=90; self.bias_strength=0.30

    def aplicar_caos(self, chaos):
        """Ajusta movimiento y sesgo segun el caos.

        - A mayor chaos, menor intervalo y mayor agresividad.
        """
        self.move_interval   = max(4, int(self.base_move_interval - chaos*0.7))
        self.chase_threshold = 280 + chaos*12
        self.bias_strength   = min(0.92, chaos/10.0 + 0.3)

    def _elegir_dir(self):
        """Elige direccion con sesgo hacia jugador o amenaza.

        - Usa LCG para decidir si aplica sesgo direccional.
        """
        super()._elegir_dir()
        R = _ri(self.lcg)
        if self.state=="chase" and self._jugador and R < self.bias_strength:
            self.direction = self._mejor_dir(self._jugador, flee=False)
        elif self.state=="flee" and self._amenaza and R < self.bias_strength:
            t = Vec2(*self._amenaza) if isinstance(self._amenaza, tuple) else self._amenaza
            self.direction = self._mejor_dir(t, flee=True)

    def update(self, jugador, amenaza_pos=None):
        """Ciclo de actualizacion del imp.

        - Igual que Agente, pero con sesgos reactivos.
        """
        if not self.alive: return
        self.frame += 1
        self.percibir(jugador, amenaza_pos)
        self._decidir_estado()
        if self.frame % self.move_interval == 1: self._elegir_dir()
        self._mover()


class DragonAgente(ImpAgente):
    """Dragon — 2 vidas; se transforma (Flam) tras el primer golpe."""
    def __init__(self, ax, ay, W, H, seed):
        """Inicializa el dragon con vidas y umbrales propios."""
        super().__init__(ax, ay, W, H, seed)
        self.tipo="Dragon"; self.speed=2
        self.base_move_interval=15; self.move_interval=15
        self.chase_threshold=200; self.lives=2; self.on_fire=False

    def recibir_golpe(self):
        """Aplica dano y maneja el cambio de fase.

        - Primer golpe activa modo fuego y aumenta velocidad.
        - Segundo golpe elimina el agente.
        """
        self.lives -= 1
        if self.lives <= 0: self.alive=False; return True
        self.on_fire=True; self.speed+=2; return False


class SimulacionAgentes:
    def __init__(self, N_z=3, N_i=1, N_d=1, T=300, W=20, H=15, chaos=0.0, seed_base=42):
        """Configura la simulacion, poblacion y parametros globales.

        - N_z, N_i, N_d: cantidad de agentes por tipo.
        - T, W, H: ticks y dimensiones del mapa en tiles.
        - chaos: nivel de caos que modula comportamiento.
        - seed_base: semilla base para PRNGs.
        """
        self.T=T; self.chaos=chaos
        lcg_pos = GeneradorCongruenciaLineal(seed_base+9999)
        def rpos():
            return int(_ri(lcg_pos)*(W-2))+1, int(_ri(lcg_pos)*(H-2))+1
        self.agentes = []
        for i in range(N_z): ax,ay=rpos(); self.agentes.append(Agente(ax,ay,W,H,seed_base+i))
        for i in range(N_i): ax,ay=rpos(); self.agentes.append(ImpAgente(ax,ay,W,H,seed_base+100+i))
        for i in range(N_d): ax,ay=rpos(); self.agentes.append(DragonAgente(ax,ay,W,H,seed_base+200+i))
        self.jugador = Vec2(W*TILE//2, H*TILE//2)
        self.W=W*TILE; self.H=H*TILE
        self._lcg_j = GeneradorCongruenciaLineal(seed_base+77777)
        self.historial_supervivencia=[]; self.historial_estados=[]
        self.historial_dist_media=[]; self.colisiones=0; self.explosiones_tick=[]

    def _mover_jugador(self):
        """Mueve al jugador con caminata aleatoria simple."""
        d = DIRS[int(_ri(self._lcg_j)*4)]
        self.jugador.x = max(0, min(self.W-TILE, self.jugador.x+d[0]*3))
        self.jugador.y = max(0, min(self.H-TILE, self.jugador.y+d[1]*3))

    def ejecutar(self):
        """Ejecuta la simulacion y registra metricas por tick.

        - Genera explosiones periodicas como amenaza.
        - Actualiza agentes, colisiones y estadisticas.
        """
        amenaza = None
        for t in range(self.T):
            self._mover_jugador()
            if t % 80 == 0 and t > 0:
                amenaza = Vec2(self.jugador.x+2*TILE, self.jugador.y)
                self.explosiones_tick.append(t)
                for a in self.agentes:
                    if not a.alive: continue
                    if isinstance(a, DragonAgente):
                        if a.pos.dist(amenaza) < 2*TILE: a.recibir_golpe()
                    elif a.pos.dist(amenaza) < 1.5*TILE: a.alive=False
            else: amenaza=None
            vivos=[a for a in self.agentes if a.alive]
            estados={"wander":0,"chase":0,"flee":0}
            for a in vivos:
                a.aplicar_caos(self.chaos); a.update(self.jugador, amenaza)
                estados[a.state]=estados.get(a.state,0)+1
                if a.contacto(self.jugador): self.colisiones+=1
            sv=len(vivos)/len(self.agentes) if self.agentes else 0
            dm=sum(a.pos.dist(self.jugador) for a in vivos)/len(vivos) if vivos else 0.0
            self.historial_supervivencia.append(sv)
            self.historial_estados.append(estados)
            self.historial_dist_media.append(dm)

    def resumen(self):
        """Devuelve un resumen final de la simulacion.

        - Incluye colisiones, supervivencia y distancia media.
        """
        return {
            "colisiones_jugador":    self.colisiones,
            "supervivencia_final":   round(self.historial_supervivencia[-1]*100,2),
            "distancia_media_final": round(self.historial_dist_media[-1],2),
            "explosiones":           len(self.explosiones_tick),
            "agentes_vivos":         sum(1 for a in self.agentes if a.alive),
            "agentes_total":         len(self.agentes),
        }


def _barra(val, maximo=1.0, ancho=40):
    """Construye una barra ascii proporcional a un valor.

    - val: valor actual.
    - maximo: valor de referencia.
    """
    n=int(val/maximo*ancho); return "█"*n+"░"*(ancho-n)

def imprimir_resumen(cfg_label, params, sim):
    """Imprime un resumen textual de una configuracion.

    - cfg_label: etiqueta del escenario.
    - params: parametros de la corrida.
    - sim: instancia de simulacion con resultados.
    """
    r=sim.resumen()
    print(f"\n{'='*60}")
    print(f"  CONFIGURACIÓN {cfg_label}")
    print(f"{'-'*60}")
    print(f"  Zombies={params['N_z']}  Imps={params['N_i']}  "
          f"Dragons={params['N_d']}  Chaos={params['chaos']}  Ticks={params['T']}")
    print(f"{'-'*60}")
    print(f"  Colisiones c/jugador  : {r['colisiones_jugador']}")
    print(f"  Supervivencia final   : {r['supervivencia_final']} %")
    print(f"      {_barra(r['supervivencia_final']/100)}")
    print(f"  Distancia media final : {r['distancia_media_final']} px")
    print(f"  Explosiones ocurridas : {r['explosiones']}")
    print(f"  Agentes vivos         : {r['agentes_vivos']} / {r['agentes_total']}")
    print(f"{'='*60}")

def imprimir_grafico_consola(sim, titulo="Supervivencia"):
    """Imprime un grafico ascii de la supervivencia en el tiempo.

    - Reduce muestras para caber en la consola.
    """
    sv=sim.historial_supervivencia; rows=10; cols=60
    step=max(1,len(sv)//cols); vals=sv[::step][:cols]
    print(f"\n  -- {titulo} --")
    for row in range(rows,-1,-1):
        thr=row/rows
        line="".join("▐" if v>=thr else " " for v in vals)
        print(f"  {thr:4.1f}|{line}")
    print(f"       {'─'*cols}")
    print(f"       0{' '*(cols//2-3)}Tick{' '*(cols//2-1)}{len(sv)}")

def imprimir_estados_consola(sim, titulo="Estados por tick"):
    """Imprime un grafico ascii de estados por tick.

    - W/C/F indican wander, chase y flee.
    """
    hist=sim.historial_estados; step=max(1,len(hist)//60)
    muestras=hist[::step][:60]; total=len(sim.agentes)
    print(f"\n  -- {titulo} (W=wander C=chase F=flee) --")
    for row in range(total,-1,-1):
        line=""
        for s in muestras:
            vivos=s.get("wander",0)+s.get("chase",0)+s.get("flee",0)
            if vivos>=row and row>0:
                acc_w=s.get("wander",0); acc_c=acc_w+s.get("chase",0)
                if row<=s.get("flee",0): line+="F"
                elif row<=acc_c:         line+="C"
                else:                    line+="W"
            else: line+=" "
        print(f"  {row:2}|{line}")
    print(f"     {'─'*60}")


def main():
    """Ejecuta tres configuraciones de prueba y muestra resultados."""
    print("="*60)
    print("  MODELO BASADO EN AGENTES — SimuBomber: Caos")
    print("  PRNG: Congruencia Lineal (a=1664525, c=1013904223, m=2^32)")
    print(f"  Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    configuraciones = [
        dict(N_z=3, N_i=1, N_d=1, T=300, W=20, H=15, chaos=0.0,  seed_base=42),
        dict(N_z=4, N_i=2, N_d=1, T=300, W=20, H=15, chaos=5.0,  seed_base=42),
        dict(N_z=5, N_i=3, N_d=2, T=300, W=20, H=15, chaos=10.0, seed_base=42),
    ]

    for idx, cfg in enumerate(configuraciones, 1):
        sim = SimulacionAgentes(**cfg)
        sim.ejecutar()
        imprimir_resumen(str(idx), cfg, sim)
        imprimir_grafico_consola(sim, f"Supervivencia — CFG {idx}")
        imprimir_estados_consola(sim, f"Estados — CFG {idx}")

    print("\n  Simulacion completada exitosamente.\n")

if __name__ == "__main__":
    main()
