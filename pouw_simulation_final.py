# Simulacion sencilla de un consenso Proof of Useful Work (PoUW)
# Tarea colaborativa 1 - Tecnologias de Registro Distribuido y Blockchain (UVigo)
# Gabriel Aubain y Tomas Meira
#
# El trabajo "util" es un TSP pequeno: encontrar una ruta cerrada que pase una
# vez por cada punto de entrega sin superar una distancia maxima (el umbral).
# Gabriel y Tomas buscan con 2-opt. Xulio es el lazy miner: manda la ruta sin
# optimizar y espera que nadie lo compruebe.
#
# Uso:  python pouw_simulation.py [semilla]      (por defecto, semilla 24)

import hashlib
import json
import random
import sys
import time
from dataclasses import dataclass, field

RECOMPENSA = 10


def distancia(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def longitud_ruta(puntos, ruta):
    # si la ruta se salta o repite algun punto no vale
    if sorted(ruta) != list(range(len(puntos))):
        return float("inf")
    total = 0.0
    for i in range(len(ruta)):
        total += distancia(puntos[ruta[i]], puntos[ruta[(i + 1) % len(ruta)]])
    return round(total, 2)


def vecino_mas_cercano(puntos):
    # estimacion rapida que usamos para fijar el umbral de cada tarea
    pendientes = set(range(1, len(puntos)))
    actual, total = 0, 0.0
    while pendientes:
        sig = min(pendientes, key=lambda p: distancia(puntos[actual], puntos[p]))
        total += distancia(puntos[actual], puntos[sig])
        pendientes.remove(sig)
        actual = sig
    return total + distancia(puntos[actual], puntos[0])


@dataclass
class Tarea:
    id: str
    cliente: str
    puntos: list
    umbral: float


def nueva_tarea(n, num_puntos, margen):
    # coordenadas inventadas en un cuadrado de 100x100, no son kilometros reales
    puntos = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(num_puntos)]
    umbral = round(vecino_mas_cercano(puntos) * margen, 2)
    return Tarea(f"RUTA-{n:03d}", f"Reparto medico #{n}", puntos, umbral)


@dataclass
class Bloque:
    indice: int
    hash_previo: str
    transacciones: list
    id_tarea: str
    ruta: list
    distancia: float
    minero: str
    nonce: int
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def calcular_hash(self):
        datos = (f"{self.indice}{self.hash_previo}{json.dumps(self.transacciones)}"
                 f"{self.id_tarea}{self.ruta}{self.distancia}{self.minero}{self.nonce}")
        return hashlib.sha256(datos.encode()).hexdigest()


class Minero:
    def __init__(self, nombre, potencia, perezoso=False):
        self.nombre = nombre
        self.max_iter = potencia * 10000   # mas potencia = puede probar mas cambios
        self.perezoso = perezoso
        self.bloques = 0
        self.tokens = 0

    def resolver(self, tarea, hash_previo):
        inicio = time.perf_counter()
        n = len(tarea.puntos)

        if self.perezoso:
            # no calcula nada, devuelve los puntos en el orden en que vienen
            ruta = list(range(n))
            return ruta, longitud_ruta(tarea.puntos, ruta), 0, time.perf_counter() - inicio

        # la semilla de la busqueda sale del hash del bloque anterior (idea del
        # pre-hash de Ofelimos, muy simplificada): no se puede empezar antes de tiempo
        rng = random.Random(hash_previo + self.nombre)
        ruta = list(range(n))
        rng.shuffle(ruta)
        mejor = longitud_ruta(tarea.puntos, ruta)

        it = 0
        while mejor > tarea.umbral and it < self.max_iter:
            it += 1
            # 2-opt: se invierte el tramo i..j y nos quedamos con el cambio si acorta
            i, j = sorted(rng.sample(range(n), 2))
            nueva = ruta[:i] + ruta[i:j + 1][::-1] + ruta[j + 1:]
            d = longitud_ruta(tarea.puntos, nueva)
            if d < mejor:
                ruta, mejor = nueva, d

        return ruta, mejor, it, time.perf_counter() - inicio


class Red:
    def __init__(self):
        genesis = Bloque(0, "0" * 64, ["Genesis"], "GENESIS", [], 0.0, "SISTEMA", 0)
        genesis.hash = genesis.calcular_hash()
        self.cadena = [genesis]
        self.mineros = []
        self.tareas = []

    def verificar(self, bloque, tarea):
        # Lo que hace cualquier nodo al recibir un bloque. No repite la busqueda:
        # solo recalcula la distancia, que es lineal en el numero de puntos.
        if bloque.hash != bloque.calcular_hash():
            return False, "hash incorrecto"
        if bloque.hash_previo != self.cadena[-1].hash:
            return False, "no enlaza con el ultimo bloque"
        real = longitud_ruta(tarea.puntos, bloque.ruta)
        if abs(real - bloque.distancia) > 0.01:
            return False, f"distancia falseada ({bloque.distancia} declarada, {real} real)"
        if real > tarea.umbral:
            return False, f"{real} supera el umbral {tarea.umbral}"
        return True, "ok"

    def ronda(self, num):
        tarea = self.tareas.pop(0)
        previo = self.cadena[-1]
        print(f"\nRonda {num}: {tarea.id} ({tarea.cliente}, {len(tarea.puntos)} puntos)")
        print(f"  Umbral: distancia <= {tarea.umbral}")

        # La red no sabe quien es honesto: verifica todas las propuestas igual
        validos = []
        for m in self.mineros:
            ruta, d, it, t = m.resolver(tarea, previo.hash)
            txs = [f"Recompensa: {RECOMPENSA} PoUW -> {m.nombre}", f"Pago: {tarea.cliente}"]
            b = Bloque(len(self.cadena), previo.hash, txs, tarea.id, ruta, d,
                       m.nombre, random.randint(1000, 99999))
            b.hash = b.calcular_hash()

            t0 = time.perf_counter()
            ok, motivo = self.verificar(b, tarea)
            t_verif = time.perf_counter() - t0

            estado = "valido" if ok else f"RECHAZADO: {motivo}"
            print(f"  {m.nombre:<8} distancia {d:<7} | {it:>5} iteraciones | "
                  f"busqueda {t * 1000:7.2f} ms | verificacion {t_verif * 1000:.3f} ms -> {estado}")
            if ok:
                validos.append((it, d, m, b))

        if not validos:
            print("  Nadie llega al umbral, la tarea se queda sin resolver")
            return

        # Con la misma potencia, el que necesita menos iteraciones es el que
        # terminaria antes en una red real. En caso de empate, la ruta mas corta.
        validos.sort(key=lambda v: (v[0], v[1]))
        it, d, ganador, bloque = validos[0]
        self.cadena.append(bloque)
        ganador.bloques += 1
        ganador.tokens += RECOMPENSA
        print(f"  -> Bloque #{bloque.indice} para {ganador.nombre} ({it} iteraciones, distancia {d})")


def main():
    semilla = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    random.seed(semilla)

    print(f"Simulacion PoUW: rutas de reparto (TSP) con 2-opt  [semilla {semilla}]")

    red = Red()
    red.mineros.append(Minero("Gabriel", 9))
    red.mineros.append(Minero("Tomas", 9))
    red.mineros.append(Minero("Xulio", 10, perezoso=True))

    red.tareas.append(nueva_tarea(1, 9, 1.12))
    red.tareas.append(nueva_tarea(2, 10, 1.10))
    red.tareas.append(nueva_tarea(3, 8, 1.15))

    for r in range(1, 4):
        red.ronda(r)

    print(f"\nCadena final: {len(red.cadena)} bloques (genesis + {len(red.cadena) - 1})")
    for b in red.cadena[1:]:
        print(f"  #{b.indice} {b.id_tarea}  minero {b.minero:<8} distancia {b.distancia}  hash {b.hash[:12]}...")

    print("\nBalance:")
    for m in red.mineros:
        print(f"  {m.nombre:<8} bloques: {m.bloques}   tokens: {m.tokens}")


if __name__ == "__main__":
    main()
