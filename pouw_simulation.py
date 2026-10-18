import hashlib
import json
import random
import time
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class UsefulTask:
    task_id: str
    client_name: str
    description: str
    cities: List[Tuple[int, int]]  # Coordenadas (x, y) de los puntos de entrega
    target_distance: float        # Umbral maximo exigido para aceptar la solucion

    @staticmethod
    def generate_random_task(task_id: int, num_cities: int = 10, difficulty_factor: float = 1.15) -> 'UsefulTask':
        cities = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(num_cities)]
        base_dist = UsefulTask._quick_estimate(cities)
        target = round(base_dist * difficulty_factor, 2)
        return UsefulTask(
            task_id=f"TASK-AI-LOGISTICS-{task_id:03d}",
            client_name=f"Hospital Central / Reparto Medico #{task_id}",
            description=f"Optimizacion de ruta medica para {num_cities} puntos",
            cities=cities,
            target_distance=target
        )

    @staticmethod
    def _quick_estimate(cities: List[Tuple[int, int]]) -> float:
        unvisited = set(range(1, len(cities)))
        curr = 0
        total = 0.0
        while unvisited:
            next_city = min(unvisited, key=lambda c: (cities[curr][0] - cities[c][0])**2 + (cities[curr][1] - cities[c][1])**2)
            total += ((cities[curr][0] - cities[next_city][0])**2 + (cities[curr][1] - cities[next_city][1])**2)**0.5
            unvisited.remove(next_city)
            curr = next_city
        total += ((cities[curr][0] - cities[0][0])**2 + (cities[curr][1] - cities[0][1])**2)**0.5
        return total

    @staticmethod
    def calculate_path_distance(cities: List[Tuple[int, int]], route: List[int]) -> float:
        if len(route) != len(cities) or set(route) != set(range(len(cities))):
            return float('inf')
        total = 0.0
        for i in range(len(route)):
            c1 = cities[route[i]]
            c2 = cities[route[(i + 1) % len(route)]]
            total += ((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)**0.5
        return round(total, 2)


@dataclass
class Block:
    index: int
    timestamp: float
    previous_hash: str
    transactions: List[str]
    task_id: str
    solution_route: List[int]
    solution_metric: float
    miner_id: str
    nonce: int
    block_hash: str

    @staticmethod
    def compute_hash(index: int, prev_hash: str, txs: List[str], task_id: str,
                     route: List[int], metric: float, miner: str, nonce: int) -> str:
        data = f"{index}{prev_hash}{json.dumps(txs)}{task_id}{route}{metric}{miner}{nonce}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


class MinerNode:
    def __init__(self, miner_id: str, compute_power: int, is_malicious: bool = False):
        self.miner_id = miner_id
        self.compute_power = compute_power
        self.is_malicious = is_malicious
        self.blocks_mined = 0
        self.rewards_earned = 0.0

    def solve_useful_work(self, task: UsefulTask, prev_hash: str) -> Tuple[List[int], float, int, float]:
        start_time = time.time()
        num_cities = len(task.cities)

        if self.is_malicious:
            # Minero perezoso (Lazy Miner): envia ruta trivial sin computar
            fake_route = list(range(num_cities))
            fake_distance = UsefulTask.calculate_path_distance(task.cities, fake_route)
            time.sleep(0.01)
            elapsed = time.time() - start_time
            return fake_route, fake_distance, 0, elapsed

        # Minero honesto: busqueda local mediante heuristica 2-opt
        best_route = list(range(num_cities))
        random.shuffle(best_route)
        best_dist = UsefulTask.calculate_path_distance(task.cities, best_route)

        iterations = 0
        max_iters = 100000 // max(1, (10 - self.compute_power))

        while iterations < max_iters and best_dist > task.target_distance:
            iterations += 1
            i, j = sorted(random.sample(range(num_cities), 2))
            new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
            new_dist = UsefulTask.calculate_path_distance(task.cities, new_route)
            if new_dist < best_dist:
                best_dist = new_dist
                best_route = new_route

        elapsed = time.time() - start_time
        return best_route, best_dist, iterations, elapsed


class PoUWBlockchainNetwork:
    def __init__(self):
        self.chain: List[Block] = []
        self.miners: List[MinerNode] = []
        self.pending_tasks: List[UsefulTask] = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(
            index=0,
            timestamp=time.time(),
            previous_hash="0" * 64,
            transactions=["Genesis: PoUW Network Initialized"],
            task_id="GENESIS-TASK",
            solution_route=[],
            solution_metric=0.0,
            miner_id="SYSTEM",
            nonce=0,
            block_hash="0" * 64
        )
        self.chain.append(genesis)

    def register_miner(self, miner: MinerNode):
        self.miners.append(miner)

    def submit_useful_task(self, task: UsefulTask):
        self.pending_tasks.append(task)

    def verify_block_useful_work(self, block: Block, task: UsefulTask) -> Tuple[bool, str, float]:
        verify_start = time.time()

        # 1. Comprobacion de integridad del hash
        expected_hash = Block.compute_hash(
            block.index, block.previous_hash, block.transactions, block.task_id,
            block.solution_route, block.solution_metric, block.miner_id, block.nonce
        )
        if block.block_hash != expected_hash:
            return False, "Hash de bloque invalido", 0.0

        # 2. Recalculo de la metrica (distancia real de la ruta)
        actual_distance = UsefulTask.calculate_path_distance(task.cities, block.solution_route)
        if abs(actual_distance - block.solution_metric) > 0.01:
            return False, f"Metrica falsificada ({block.solution_metric} != {actual_distance})", 0.0

        # 3. Validacion del umbral de dificultad de la tarea
        if actual_distance > task.target_distance:
            return False, f"Distancia {actual_distance} supera el umbral ({task.target_distance})", 0.0

        verify_time = time.time() - verify_start
        return True, "Solucion valida", verify_time

    def mine_round(self, round_num: int):
        if not self.pending_tasks:
            print("No hay tareas pendientes en la cola.")
            return

        task = self.pending_tasks.pop(0)
        prev_block = self.chain[-1]

        print(f"\nRonda {round_num}: Tarea {task.task_id} ({task.client_name})")
        print(f"  Objetivo: distancia <= {task.target_distance}")

        best_miner = None
        best_solution = None
        best_metric = float('inf')
        best_time = float('inf')

        for miner in self.miners:
            route, metric, iters, duration = miner.solve_useful_work(task, prev_block.block_hash)
            tipo = "Lazy" if miner.is_malicious else "Honesto"
            print(f"  Minero {miner.miner_id:<22} ({tipo:<7}): distancia = {metric:<7} | iteraciones = {iters:<5} | tiempo = {duration:.4f}s")

            if not miner.is_malicious and metric <= task.target_distance and duration < best_time:
                best_miner = miner
                best_solution = route
                best_metric = metric
                best_time = duration

        # En la ronda 2 se simula explicitamente la propagacion de un bloque fraudulento
        malicious_miners = [m for m in self.miners if m.is_malicious]
        if malicious_miners and round_num == 2:
            attacker = malicious_miners[0]
            fake_route, fake_metric, _, _ = attacker.solve_useful_work(task, prev_block.block_hash)
            print(f"\n  Intento de propagacion de bloque por {attacker.miner_id} (Lazy Miner):")

            attacker_block = Block(
                index=len(self.chain),
                timestamp=time.time(),
                previous_hash=prev_block.block_hash,
                transactions=[f"Tx-Client-{round_num}: 50 PoUW Tokens fee"],
                task_id=task.task_id,
                solution_route=fake_route,
                solution_metric=fake_metric,
                miner_id=attacker.miner_id,
                nonce=12345,
                block_hash=Block.compute_hash(
                    len(self.chain), prev_block.block_hash, [f"Tx-Client-{round_num}: 50 PoUW Tokens fee"],
                    task.task_id, fake_route, fake_metric, attacker.miner_id, 12345
                )
            )

            is_valid, reason, _ = self.verify_block_useful_work(attacker_block, task)
            print(f"  Verificacion de la red: RECHAZADO -> {reason}")

        if best_miner is not None:
            nonce = random.randint(1000, 99999)
            txs = [f"Tx-Recompensa: 10 PoUW -> {best_miner.miner_id}", f"Pago-Cliente: {task.client_name}"]
            b_hash = Block.compute_hash(
                len(self.chain), prev_block.block_hash, txs, task.task_id,
                best_solution, best_metric, best_miner.miner_id, nonce
            )

            new_block = Block(
                index=len(self.chain),
                timestamp=time.time(),
                previous_hash=prev_block.block_hash,
                transactions=txs,
                task_id=task.task_id,
                solution_route=best_solution,
                solution_metric=best_metric,
                miner_id=best_miner.miner_id,
                nonce=nonce,
                block_hash=b_hash
            )

            valid, msg, v_time = self.verify_block_useful_work(new_block, task)
            if valid:
                self.chain.append(new_block)
                best_miner.blocks_mined += 1
                best_miner.rewards_earned += 10.0
                print(f"  Bloque #{new_block.index} propuesto por {best_miner.miner_id}: ACEPTADO")
                print(f"    Metrica alcanzada: {new_block.solution_metric} (umbral <= {task.target_distance})")
                print(f"    Tiempo busqueda (minero): {best_time:.4f}s")
                print(f"    Tiempo verificacion (red): {v_time:.6f}s")
        else:
            print("  Ningun minero alcanzo el umbral de dificultad en esta ronda.")


def run_demo():
    print("Simulacion de Consenso Proof of Useful Work (PoUW)")
    print("Problema: Optimizacion de rutas logisticas (TSP) mediante 2-opt\n")

    network = PoUWBlockchainNetwork()

    # Registro de mineros (Gabriel y Tomas honestos, Sousa Xulio Xulio atacante)
    network.register_miner(MinerNode(miner_id="Miner-Gabriel", compute_power=8))
    network.register_miner(MinerNode(miner_id="Miner-Tomas", compute_power=9))
    network.register_miner(MinerNode(miner_id="Miner-Sousa-Xulio", compute_power=10, is_malicious=True))

    # Tareas utiles
    network.submit_useful_task(UsefulTask.generate_random_task(1, num_cities=9, difficulty_factor=1.12))
    network.submit_useful_task(UsefulTask.generate_random_task(2, num_cities=10, difficulty_factor=1.10))
    network.submit_useful_task(UsefulTask.generate_random_task(3, num_cities=8, difficulty_factor=1.15))

    for r in range(1, 4):
        network.mine_round(r)
        time.sleep(0.1)

    print("\nResumen final de la cadena:")
    print(f"Bloques en la cadena: {len(network.chain)} (1 Genesis + {len(network.chain)-1} bloques utiles)")
    for b in network.chain[1:]:
        print(f"  Bloque #{b.index}: {b.task_id} | Minero: {b.miner_id} | Distancia: {b.solution_metric}")

    print("\nBalance de mineros:")
    for m in network.miners:
        rol = "Malicioso" if m.is_malicious else "Honesto"
        print(f"  {m.miner_id:<22} ({rol:<9}): {m.blocks_mined} bloques | {m.rewards_earned} PoUW Tokens")


if __name__ == "__main__":
    run_demo()
