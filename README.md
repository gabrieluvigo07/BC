# Trabajo Colaborativo I: Simulación de Consenso Proof of Useful Work (PoUW)

Este proyecto implementa una simulación experimental de un protocolo de consenso **Proof of Useful Work (PoUW)** orientado a tareas computacionales útiles del mundo real. El sistema modela la resolución distribuida de problemas de optimización combinatoria (Problema del Viajante de Comercio / TSP aplicado a logística médica urgente), demostrando empíricamente la propiedad de **asimetría computacional** (búsqueda heurística intensiva frente a verificación ligera $O(N)$) y la **neutralización activa de ataques de mineros perezosos (*Lazy Miner Attack*)**.

* **Asignatura:** Tecnologías de Registro Distribuido y Blockchain (BC)
* **Titulación:** Máster Universitario en Ciberseguridad · Universidade de Vigo (UVigo)
* **Curso:** 2026 / 2027
* **Autores:** Gabriel Aubain & Tomás Meira
* **Repositorio:** [https://github.com/gabrieluvigo07/BC](https://github.com/gabrieluvigo07/BC)

---

## 1. Estructura del Repositorio

* **`pouw_simulation.py`**: Script principal en Python 3 que implementa la arquitectura completa del consenso PoUW:
  * Generación y registro de tareas útiles externas (`UsefulTask`).
  * Estructura e integridad de los bloques de la cadena (`Block`).
  * Nodos mineros con perfiles honestos y maliciosos (`MinerNode`).
  * Red de consenso y verificación de dificultad métrica (`PoUWBlockchainNetwork`).
* **`README.md`**: Documentación técnica, fundamentos algorítmicos y guía de ejecución.
* **`Entregas/`**: Material complementario de entrega, incluyendo la presentación oficial en diapositivas (`PoUW_presentacion_v5.pptx`) y notas de soporte.

---

## 2. Requisitos e Instalación

El simulador ha sido desarrollado en **Python 3** utilizando exclusivamente la **librería estándar**, sin requerir dependencias externas ni compiladores nativos.

* **Requisitos del sistema:** Python 3.8 o superior.
* **Módulos empleados:** `hashlib`, `json`, `random`, `time`, `dataclasses`, `typing`.

Para clonar el repositorio:

```bash
git clone https://github.com/gabrieluvigo07/BC.git
cd BC
```

---

## 3. Guía de Ejecución

El script se ejecuta directamente desde la terminal del sistema:

```bash
# En Windows (PowerShell / CMD):
py pouw_simulation.py

# En Linux / macOS:
python3 pouw_simulation.py
```

### Flujo de la Simulación

Al ejecutarse, el sistema inicializa el **Bloque Génesis** y simula de forma consecutiva **3 rondas de consenso** con tareas de dificultad variable:

1. **Ronda 1 (`TASK-AI-LOGISTICS-001`):** Tarea logística para 9 puntos de entrega. Los mineros honestos optimizan sus rutas y el bloque es adjudicado al nodo con mejor solución válida.
2. **Ronda 2 (`TASK-AI-LOGISTICS-002` - Demostración de Ciberseguridad):**
   * El minero malicioso (**Xulio**) intenta propagar un bloque fraudulento sin optimizar (*Lazy Miner*), buscando cobrar la recompensa sin consumir tiempo de CPU.
   * La red recalcula la métrica real de la ruta, detecta que supera el umbral máximo exigido ($601.77 > 298.45$) y **rechaza el bloque de inmediato**.
   * El minero honesto (**Tomás** / **Gabriel**) presenta una solución válida ($291.98 \le 298.45$) que es **aceptada y encadenada**.
3. **Ronda 3 (`TASK-AI-LOGISTICS-003`):** Nueva ronda de optimización ganada por el minero honesto.
4. **Resumen de la Cadena y Balance Económico:** Muestra la inmutabilidad de la cadena (4 bloques en total) y certifica que los nodos honestos (**Gabriel** y **Tomás**) perciben los tokens de recompensa, mientras el atacante (**Xulio**) finaliza con saldo cero.

### Salida Real de Consola

```text
Simulacion de Consenso Proof of Useful Work (PoUW)
Problema: Optimizacion de rutas logisticas (TSP) mediante 2-opt

Ronda 1: Tarea TASK-AI-LOGISTICS-001 (Hospital Central / Reparto Medico #1)
  Objetivo: distancia <= 340.17
  Minero Gabriel      (Honesto): distancia = 325.02  | iteraciones = 23    | tiempo = 0.0004s
  Minero Tomas        (Honesto): distancia = 338.26  | iteraciones = 1     | tiempo = 0.0001s
  Minero Xulio        (Lazy   ): distancia = 388.7   | iteraciones = 0     | tiempo = 0.0108s
  Bloque #1 propuesto por Tomas: ACEPTADO
    Metrica alcanzada: 338.26 (umbral <= 340.17)
    Tiempo busqueda (minero): 0.0001s
    Tiempo verificacion (red): 0.000100s

Ronda 2: Tarea TASK-AI-LOGISTICS-002 (Hospital Central / Reparto Medico #2)
  Objetivo: distancia <= 298.45
  Minero Gabriel      (Honesto): distancia = 271.32  | iteraciones = 63    | tiempo = 0.0012s
  Minero Tomas        (Honesto): distancia = 291.98  | iteraciones = 54    | tiempo = 0.0008s
  Minero Xulio        (Lazy   ): distancia = 601.77  | iteraciones = 0     | tiempo = 0.0103s

  Intento de propagacion de bloque por Xulio (Lazy Miner):
  Verificacion de la red: RECHAZADO -> Distancia 601.77 supera el umbral (298.45)
  Bloque #2 propuesto por Tomas: ACEPTADO
    Metrica alcanzada: 291.98 (umbral <= 298.45)
    Tiempo busqueda (minero): 0.0008s
    Tiempo verificacion (red): 0.000036s

Ronda 3: Tarea TASK-AI-LOGISTICS-003 (Hospital Central / Reparto Medico #3)
  Objetivo: distancia <= 300.32
  Minero Gabriel      (Honesto): distancia = 298.76  | iteraciones = 25    | tiempo = 0.0005s
  Minero Tomas        (Honesto): distancia = 292.51  | iteraciones = 8     | tiempo = 0.0002s
  Minero Xulio        (Lazy   ): distancia = 478.36  | iteraciones = 0     | tiempo = 0.0101s
  Bloque #3 propuesto por Tomas: ACEPTADO
    Metrica alcanzada: 292.51 (umbral <= 300.32)
    Tiempo busqueda (minero): 0.0002s
    Tiempo verificacion (red): 0.000051s

Resumen final de la cadena:
Bloques en la cadena: 4 (1 Genesis + 3 bloques utiles)
  Bloque #1: TASK-AI-LOGISTICS-001 | Minero: Tomas | Distancia: 338.26
  Bloque #2: TASK-AI-LOGISTICS-002 | Minero: Tomas | Distancia: 291.98
  Bloque #3: TASK-AI-LOGISTICS-003 | Minero: Tomas | Distancia: 292.51

Balance de mineros:
  Gabriel      (Honesto  ): 0 bloques | 0.0 PoUW Tokens
  Tomas        (Honesto  ): 3 bloques | 30.0 PoUW Tokens
  Xulio        (Malicioso): 0 bloques | 0.0 PoUW Tokens
```

---

## 4. Fundamentos Algorítmicos y Diseño de Seguridad

### A. La Regla de Asimetría Computacional

Para que una tarea computacional sea admisible en un consenso blockchain descentralizado, debe satisfacer la cota de asimetría:

$$\text{Coste de Búsqueda} \gg \text{Coste de Verificación}$$

* **Fase de Búsqueda (Minero):** El problema TSP es de complejidad $NP$-hard. Los mineros honestos aplican la **heurística 2-opt**, un algoritmo de búsqueda local iterativa que detecta tramos de ruta cruzados en "X", invierte subrutas intermedias y reconecta caminos en paralelo para recortar la distancia global de forma monótona decreciente.
* **Fase de Verificación (Red):** Los nodos validadores no repiten la búsqueda heurística; se limitan a recorrer la permutación entregada sumando las distancias euclidianas entre vértices consecutivos en tiempo lineal $O(N)$ y comparando el resultado frente al umbral publicado por el cliente.

### B. Pseudocódigo del Mecanismo Asimétrico

```plaintext
Columna 1: Minero (Cómputo Pesado)
Minar_PoUW (tarea T):
  ruta = ruta_aleatoria(T.ciudades)
  Mientras coste(ruta) > T.umbral:
    nueva_ruta = permutar_2opt(ruta)
    Si coste(nueva_ruta) < coste(ruta):
      ruta = nueva_ruta
  Devolver Bloque(ruta, coste(ruta), hash)

Columna 2: Red (Verificación O(N))
Verificar_Bloque (bloque B, tarea T):
  Verificar integridad de B.hash
  d_real = calcular_distancia(B.ruta)
  Si d_real == B.coste Y d_real <= T.umbral:
    Aceptar bloque en Blockchain y pagar
  Si no:
    Rechazar bloque (Neutraliza Lazy Miner)
```

### C. Vectores de Ataque Modelados

1. **Lazy Miner Attack:**  
   Un minero no gasta ciclos de reloj y remite una ruta trivial (`[0, 1, ..., N-1]`) esperando cobrar la recompensa de bloque. La red neutraliza el ataque recalculando la métrica y descartando el bloque antes de su propagación definitiva (caso **Xulio** en la simulación).
2. **Resistencia a Precomputación (Anti-Grinding):**  
   Cada bloque encadena criptográficamente el `previous_hash` dentro de la función de hash del bloque resultante (`SHA-256`), vinculando el estado del problema al bloque previo e impidiendo que un minero calcule soluciones de rondas futuras por adelantado.
3. **Integridad de Datos:**  
   La firma del bloque asegura que tanto las transacciones como el identificador de la tarea, la ruta de solución y la métrica alcanzada son inmutables; cualquier alteración en un solo dígito invalida el hash del bloque.

### D. Alcance y Límites Técnicos del Demostrador

Para una adecuada evaluación académica, se reconocen los siguientes límites de diseño en el prototipo local:
* **Entorno Monoproceso:** La simulación corre de forma secuencial en un único intérprete Python para facilitar la depuración y reproducibilidad; no implementa una red P2P distribuida con latencia ni bifurcaciones concurrentes.
* **Verificación Directa vs. SNARGs:** Para 10 ciudades, la verificación directa $O(N)$ es viable. En instancias masivas de producción (cientos de miles de variables), se requeriría incorporar argumentos sucintos no interactivos (**SNARGs**) como prescribe el protocolo *Ofelimos* (CRYPTO 2022) para evitar el *Dilema del Verificador*.
* **Métrica Temporal:** Los tiempos de verificación en consola (`~0.000036 s`) representan la rapidez de la suma euclidiana en microsegundos, sujeta a la resolución del temporizador del sistema operativo.

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
