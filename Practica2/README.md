# Práctica 2: Almacenamiento y distribución con IPFS

Tecnologías de Registro Distribuido y Blockchain — Máster Interuniversitario en Ciberseguridad.

La memoria completa está en [`memoria/memoria_practica2.pdf`](memoria/memoria_practica2.pdf).

## Contenido

| Carpeta | Qué contiene |
|---|---|
| `contrato/` | `CuarentenaEvidencias.sol`, contrato del ejercicio 2 (ampliación de *CuarentenaColectiva*, Práctica 1) |
| `dapp_ipfs/` | Aplicación web (React). `src/App.js` es el ejercicio 2 y `src/AppEjercicio1.js` el ejercicio 1 |
| `evidencias/` | Fichero de evidencia de ejemplo (datos ficticios) usado en las pruebas |
| `memoria/` | Memoria en formato PDF|

## Contratos desplegados (Sepolia)

- `IpfsStorage` (ejercicio 1): `0x84D04cE764dED4bB91c7E2F7553abE6521a24c89`
- `CuarentenaEvidencias` (ejercicio 2): `0x5cAE08FA1754f0b8d5E07184D6d1c90983A090a6`

## Cómo ejecutar la aplicación

Requisitos: Docker, Node.js 18.13.0 y MetaMask con la red Sepolia.

1. Nodo IPFS:
   ```
   docker run -d --name ipfs_host -v $PWD:/export -v $PWD:/data/ipfs \
     -p 4001:4001 -p 4001:4001/udp -p 127.0.0.1:8080:8080 -p 127.0.0.1:5001:5001 ipfs/kubo
   docker exec ipfs_host ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin \
     '["http://localhost:3000", "http://127.0.0.1:5001", "https://webui.ipfs.io"]'
   docker restart ipfs_host
   ```
   (ejecutar desde una carpeta vacía dedicada a los datos del nodo)
2. Aplicación:
   ```
   cd dapp_ipfs
   npm install
   npm start
   ```
3. Abrir `http://localhost:3000` con MetaMask en Sepolia.
