# Trabajo Colaborativo I: Simulación de Consenso Proof of Useful Work (PoUW)

Este proyecto implementa una simulación de un protocolo de consenso **Proof of Useful Work (PoUW)** orientado a tareas computacionales útiles. El sistema modela la resolución de un problema de optimización combinatoria (Problema del Viajante de Comercio / TSP aplicado a rutas de reparto médico) para mostrar la **asimetría computacional** (búsqueda heurística costosa frente a verificación lineal, O(N)) y el **rechazo de mineros perezosos (*Lazy Miner Attack*)**.

* **Asignatura:** Tecnologías de Registro Distribuido y Blockchain (BC)
* **Titulación:** Máster Universitario en Ciberseguridad · Universidade de Vigo (UVigo)
* **Curso:** 2026 / 2027
* **Autores:** Gabriel Aubain & Tomás Meira
* **Repositorio:** [https://github.com/gabrieluvigo07/BC](https://github.com/gabrieluvigo07/BC)

---

## 1. Estructura del Repositorio

* **`pouw_simulation.py`**: script principal en Python 3 con todo el consenso PoUW:
  * Tareas útiles del cliente: puntos de entrega y umbral de distancia (`Tarea`).
  * Bloques de la cadena y su hash SHA-256 (`Bloque`).
  * Mineros honestos y perezosos (`Minero`).
  * Red de consenso: verificación de bloques y rondas de minado (`Red`).
* **`salida_ejemplo.txt`**: salida completa del script con la semilla por defecto (24).
* **`README.md`**: documentación, fundamentos y guía de ejecución.
* **`Entregas/`**: material de entrega (presentación y notas de apoyo).

---

## 2. Requisitos e Instalación

El simulador está hecho en **Python 3** usando solo la **librería estándar**, sin dependencias externas.

* **Requisitos:** Python 3.8 o superior.
* **Módulos empleados:** `hashlib`, `json`, `random`, `sys`, `time`, `dataclasses`.

Para clonar el repositorio:

```bash
git clone https://github.com/gabrieluvigo07/BC.git
cd BC
```

---

## 3. Guía de Ejecución

```bash
# En Windows (PowerShell / CMD):
py pouw_simulation.py

# En Linux / macOS:
python3 pouw_simulation.py

# Con otra semilla (genera otras rutas y otros resultados):
python3 pouw_simulation.py 5
```

Por defecto se usa la **semilla 24**, la de la presentación. Con la misma semilla las distancias, las iteraciones y los ganadores salen siempre iguales; solo cambian los tiempos en ms, que dependen del equipo.

### Flujo de la Simulación

El sistema crea el **bloque génesis** y simula **3 rondas de consenso** (9, 10 y 8 puntos de entrega). En cada ronda:

* Los mineros honestos **Gabriel** y **Tomás** buscan la ruta con **2-opt**. La semilla de su búsqueda se obtiene del hash del bloque anterior.
* El minero perezoso **Xulio** envía la ruta en el orden inicial, sin optimizar.
* La red **no sabe quién es honesto**: verifica todas las propuestas igual (hash, enlace con el último bloque, distancia real y umbral).
* Entre los bloques válidos gana el que ha necesitado **menos iteraciones** (con la misma potencia, el que terminaría antes). El ganador recibe 10 tokens.

Resultado con la semilla 24:

1. **Ronda 1 (`RUTA-001`):** Gabriel (306.59) y Tomás (310.2) cumplen el umbral (346.97). Gana **Tomás** con 4 iteraciones. Xulio (484.86) es rechazado.
2. **Ronda 2 (`RUTA-002`), la que se muestra en la presentación:**
   * Umbral: 317.02.
   * Gabriel: 296.43 en 137 iteraciones (válido).
   * Tomás: 292.25 en 39 iteraciones (válido). **Gana el bloque #2**.
   * Xulio: 577.38 > 317.02, **rechazado** al recalcular la distancia.
3. **Ronda 3 (`RUTA-003`):** gana **Gabriel** (314.02 ≤ 336.87) con 2 iteraciones. Xulio (455.97) es rechazado.
4. **Balance final:** Gabriel 1 bloque / 10 tokens, Tomás 2 bloques / 20 tokens, Xulio 0.

### Salida Real de Consola (semilla 24)

```text
Simulacion PoUW: rutas de reparto (TSP) con 2-opt  [semilla 24]

Ronda 1: RUTA-001 (Reparto medico #1, 9 puntos)
  Umbral: distancia <= 346.97
  Gabriel  distancia 306.59  |    61 iteraciones | busqueda    0.94 ms | verificacion 0.025 ms -> valido
  Tomas    distancia 310.2   |     4 iteraciones | busqueda    0.09 ms | verificacion 0.019 ms -> valido
  Xulio    distancia 484.86  |     0 iteraciones | busqueda    0.01 ms | verificacion 0.020 ms -> RECHAZADO: 484.86 supera el umbral 346.97
  -> Bloque #1 para Tomas (4 iteraciones, distancia 310.2)

Ronda 2: RUTA-002 (Reparto medico #2, 10 puntos)
  Umbral: distancia <= 317.02
  Gabriel  distancia 296.43  |   137 iteraciones | busqueda    1.82 ms | verificacion 0.021 ms -> valido
  Tomas    distancia 292.25  |    39 iteraciones | busqueda    0.53 ms | verificacion 0.018 ms -> valido
  Xulio    distancia 577.38  |     0 iteraciones | busqueda    0.01 ms | verificacion 0.019 ms -> RECHAZADO: 577.38 supera el umbral 317.02
  -> Bloque #2 para Tomas (39 iteraciones, distancia 292.25)

Ronda 3: RUTA-003 (Reparto medico #3, 8 puntos)
  Umbral: distancia <= 336.87
  Gabriel  distancia 314.02  |     2 iteraciones | busqueda    0.09 ms | verificacion 0.017 ms -> valido
  Tomas    distancia 331.53  |    12 iteraciones | busqueda    0.16 ms | verificacion 0.017 ms -> valido
  Xulio    distancia 455.97  |     0 iteraciones | busqueda    0.01 ms | verificacion 0.018 ms -> RECHAZADO: 455.97 supera el umbral 336.87
  -> Bloque #3 para Gabriel (2 iteraciones, distancia 314.02)

Cadena final: 4 bloques (genesis + 3)
  #1 RUTA-001  minero Tomas    distancia 310.2  hash 8cf5b94ce3d4...
  #2 RUTA-002  minero Tomas    distancia 292.25  hash f22d86bc98a8...
  #3 RUTA-003  minero Gabriel  distancia 314.02  hash ddfa462812bb...

Balance:
  Gabriel  bloques: 1   tokens: 10
  Tomas    bloques: 2   tokens: 20
  Xulio    bloques: 0   tokens: 0
```

---

## 4. Fundamentos Algorítmicos y Diseño de Seguridad

### A. La Regla de Asimetría Computacional

Para que una tarea pueda formar parte de un consenso, encontrar una solución tiene que costar bastante más que comprobarla:

**Coste de búsqueda ≫ Coste de verificación**

* **Búsqueda (minero):** el TSP es NP-hard. Los mineros honestos aplican **2-opt**: eligen dos posiciones de la ruta, invierten el tramo entre ellas y se quedan con el cambio si la distancia baja. Repiten hasta cumplir el umbral o agotar sus iteraciones (`potencia × 10000`).
* **Verificación (red):** los nodos no repiten la búsqueda. Recorren la ruta entregada sumando las distancias euclídeas entre puntos consecutivos, en tiempo lineal O(N), y comparan el resultado con lo declarado y con el umbral.

### B. Pseudocódigo del Mecanismo Asimétrico

```plaintext
Minero (cómputo pesado)
Minar(T, hash_previo):
  semilla = H(hash_previo + minero)
  ruta = barajar(T.puntos, semilla)
  iter = 0
  mientras coste(ruta) > T.umbral y iter < max_iter:
    iter += 1
    nueva = 2opt(ruta)            # invierte el tramo i..j
    si coste(nueva) < coste(ruta):
      ruta = nueva
  devolver Bloque(ruta, coste(ruta))

Red (verificación O(N))
Verificar(B, T):
  si B.hash != H(B): rechazar
  si B.hash_previo != último bloque: rechazar
  d = distancia(T.puntos, B.ruta)
  si |d - B.coste| > 0,01: rechazar   # distancia falseada
  si d > T.umbral: rechazar           # caso de Xulio
  aceptar bloque
# entre los válidos gana el de menos iteraciones y cobra 10 tokens
```

### C. Vectores de Ataque Modelados

1. **Lazy Miner Attack:**
   Un minero no gasta CPU y envía una ruta trivial (`[0, 1, ..., N-1]`) esperando cobrar la recompensa. La red recalcula la distancia y descarta el bloque (caso **Xulio**, rechazado en las tres rondas).
2. **Resistencia a precomputación:**
   La semilla de búsqueda de cada minero sale del hash del bloque anterior, así que no se puede empezar a calcular antes de que exista ese bloque. Es una versión muy simplificada del pre-hash de *Ofelimos*, no su protección completa.
3. **Integridad de datos:**
   El hash SHA-256 del bloque cubre índice, hash previo, transacciones, tarea, ruta, distancia, minero y nonce. Cualquier cambio invalida el hash, y un bloque que no enlaza con el último de la cadena se rechaza.

### D. Alcance y Límites del Demostrador

* **Monoproceso:** los mineros se ejecutan uno tras otro en un solo intérprete; no hay red P2P, latencia ni bifurcaciones.
* **Verificación directa frente a SNARGs:** con 10 puntos, recalcular la distancia es trivial. Para instancias grandes, *Ofelimos* (CRYPTO 2022) usa pruebas sucintas (**SNARGs**). Aquí se comprueba la calidad de la ruta, no cuánto trabajo hizo el minero.
* **Tiempos:** los ms que muestra la consola (≈0,4–1,6 ms de búsqueda frente a ≈0,02 ms de verificación) ilustran la asimetría, pero con instancias tan pequeñas no son una medida concluyente.
* **Pagos:** los tokens son contadores. No hay transferencia real al cliente ni sanción para Xulio; solo se queda sin recompensa.

---

## 5. Referencias Académicas

1. **Bakhshi, F., Ashtiani, M. y Azgomi, M. A. (2025).** *A systematic literature review on proof-of-useful-work consensus algorithms.* Blockchain: Research and Applications, 100387.
2. **Fitzi, M., Kiayias, A., Panagiotakos, G. y Russell, A. (2022).** *Ofelimos: Combinatorial Optimization via Proof-of-Useful-Work — A Provably Secure Blockchain Protocol.* Advances in Cryptology – CRYPTO 2022, Springer, pp. 339–369.
3. **Smuseva, D., Marin, A., Rossi, S. y Van Moorsel, A. (2025).** *Verifier’s Dilemma in Proof-of-Work Public Blockchains: A Quantitative Analysis.* ACM Transactions on Modeling and Computer Simulation (TOMACS).
4. **Fraga-Lamas, P. (2026).** *Protocolos de consenso.* Material docente de Tecnologías de Registro Distribuido y Blockchain, Máster en Ciberseguridad, Universidade de Vigo (UVigo).
5. **Baldominos, A. y Sáez, Y. (2019).** *Coin.AI: A Proof-of-Useful-Work Scheme for Blockchain-based Distributed Deep Learning.* Entropy, 21(8), 723.
6. **King, S. (2013).** *Primecoin: Cryptocurrency with Prime Number Proof-of-Work.*

---

## 6. Declaración de Uso de IA Generativa

En el desarrollo de este trabajo y de su banco de pruebas se ha utilizado asistencia de inteligencia artificial generativa con fines didácticos, de soporte en la estructuración de la documentación técnica y de revisión de la consistencia algorítmica del simulador, bajo la supervisión y criterio crítico de los autores.
