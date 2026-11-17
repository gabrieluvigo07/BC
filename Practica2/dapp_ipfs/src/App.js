import React, { useCallback, useEffect, useState } from "react";
import "./App.css";
import { create } from "kubo-rpc-client";
import { ethers } from "ethers";
import { Buffer } from "buffer";

import logo from "./ethereumLogo.png";
import { addresses, abis } from "./contracts";

// --- Configuración -----------------------------------------------------------

const SEPOLIA_CHAIN_ID = 11155111;
// API del nodo IPFS local (contenedor Docker ipfs_host)
const IPFS_API = "/ip4/127.0.0.1/tcp/5001";
// Gateway del mismo nodo, para descargar la evidencia a partir de su CID
const IPFS_GATEWAY = "http://127.0.0.1:8080/ipfs/";
// Mismo orden que el enum EstadoSolicitud del contrato
const ESTADOS = ["Pendiente", "Aprobada", "Rechazada", "Caducada"];

// MetaMask inyecta window.ethereum; con él se crea la conexión a la red
const provider = window.ethereum
  ? new ethers.providers.Web3Provider(window.ethereum, "any")
  : null;

// Objeto contrato de solo lectura (para escribir se conecta con el signer)
const contrato = provider
  ? new ethers.Contract(addresses.cuarentena, abis.cuarentena, provider)
  : null;

// --- Utilidades --------------------------------------------------------------

const igual = (a, b) => a && b && a.toLowerCase() === b.toLowerCase();
const corta = (dir) => `${dir.slice(0, 6)}…${dir.slice(-4)}`;
const fecha = (segundos) => new Date(segundos * 1000).toLocaleString();

// Devuelve el nombre del error del contrato (p. ej. NoEresAnalista) si lo hay
function mensajeError(e) {
  return e.errorName || e.reason || e.error?.message || e.data?.message || e.message;
}

function textoVoto(haVotado, aprueba) {
  if (!haVotado) return "Sin votar";
  return aprueba ? "A favor" : "En contra";
}

// --- Componente --------------------------------------------------------------

function App() {
  const [cuenta, setCuenta] = useState("");
  const [chainId, setChainId] = useState(null);
  const [roles, setRoles] = useState(null);
  const [saldoRetirable, setSaldoRetirable] = useState(null);
  const [fianza, setFianza] = useState(null);

  const [idActivo, setIdActivo] = useState("");
  const [fichero, setFichero] = useState(null);

  const [idConsulta, setIdConsulta] = useState("");
  const [resultado, setResultado] = useState(null);

  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState(false);

  // Lee del contrato los datos que dependen de la cuenta conectada
  const cargarDatos = useCallback(async (direccion) => {
    const [propietario, soc, servicio, esAnalista, saldo, importeFianza] =
      await Promise.all([
        contrato.propietario(),
        contrato.responsableSOC(),
        contrato.responsableServicio(),
        contrato.analistasAutorizados(direccion),
        contrato.saldoRetirable(direccion),
        contrato.FIANZA(),
      ]);
    setRoles({ propietario, soc, servicio, esAnalista });
    setSaldoRetirable(saldo);
    setFianza(importeFianza);
  }, []);

  // Conexión inicial con MetaMask y reacción a cambios de cuenta o de red
  useEffect(() => {
    if (!provider) return;

    async function conectar() {
      try {
        const cuentas = await provider.send("eth_requestAccounts", []);
        const red = await provider.getNetwork();
        setChainId(red.chainId);
        setCuenta(cuentas[0]);
        if (red.chainId === SEPOLIA_CHAIN_ID) await cargarDatos(cuentas[0]);
      } catch (e) {
        setError(mensajeError(e));
      }
    }
    conectar();

    const alCambiarCuenta = () => window.location.reload();
    const alCambiarRed = () => window.location.reload();
    window.ethereum.on("accountsChanged", alCambiarCuenta);
    window.ethereum.on("chainChanged", alCambiarRed);
    return () => {
      window.ethereum.removeListener("accountsChanged", alCambiarCuenta);
      window.ethereum.removeListener("chainChanged", alCambiarRed);
    };
  }, [cargarDatos]);

  // Consulta por activo: encadena tres lecturas públicas del contrato
  const consultar = useCallback(async (id) => {
    const idSolicitud = await contrato.solicitudActualPorActivo(id);
    if (idSolicitud.isZero()) {
      setResultado({ idActivo: id, sinSolicitud: true });
      return;
    }
    const [s, cid, enCuarentena] = await Promise.all([
      contrato.solicitudes(idSolicitud),
      contrato.evidenciaPorSolicitud(idSolicitud),
      contrato.estaEnCuarentena(id),
    ]);
    setResultado({
      idActivo: id,
      idSolicitud: idSolicitud.toString(),
      solicitante: s.solicitante,
      aprobadorSOC: s.aprobadorSOC,
      responsableServicio: s.responsableServicio,
      venceVotacion: ethers.BigNumber.from(s.venceVotacion).toNumber(),
      finCuarentena: ethers.BigNumber.from(s.finCuarentena).toNumber(),
      votoSOC: s.votoSOC,
      apruebaSOC: s.apruebaSOC,
      votoServicio: s.votoServicio,
      apruebaServicio: s.apruebaServicio,
      estado: s.estado,
      cid,
      enCuarentena,
    });
  }, []);

  // Envía una transacción. Antes la simula (callStatic) para que, si el
  // contrato la va a rechazar, se vea el motivo sin gastar gas.
  async function enviar(funcion, args = [], opciones = {}) {
    const conFirma = contrato.connect(provider.getSigner());
    await conFirma.callStatic[funcion](...args, opciones);
    const tx = await conFirma[funcion](...args, opciones);
    setMensaje(`Transacción enviada (${tx.hash}). Esperando confirmación…`);
    await tx.wait();
    return tx;
  }

  // Envuelve cada acción: bloquea botones, limpia avisos y muestra errores
  async function ejecutar(accion) {
    setOcupado(true);
    setError("");
    setMensaje("");
    try {
      await accion();
    } catch (e) {
      console.log(e);
      setMensaje("");
      setError(mensajeError(e));
    } finally {
      setOcupado(false);
    }
  }

  const leerFichero = (e) => {
    const datos = e.target.files[0];
    if (!datos) return setFichero(null);
    const lector = new window.FileReader();
    lector.readAsArrayBuffer(datos);
    lector.onloadend = () => setFichero(Buffer(lector.result));
  };

  // 1) sube la evidencia a IPFS  2) registra la solicitud con su CID y la fianza
  const solicitar = (e) => {
    e.preventDefault();
    ejecutar(async () => {
      if (!fichero) throw new Error("Selecciona un fichero de evidencia.");

      // Antes de subir nada a IPFS, comprueba con una simulación que el
      // contrato aceptaría la solicitud. Se usa un CID provisional porque el
      // real todavía no existe. Si el contrato la rechazaría (por ejemplo,
      // ResponsableNoSolicita), se lanza el error y el fichero no se sube.
      setMensaje("Comprobando que el contrato aceptaría la solicitud…");
      await contrato
        .connect(provider.getSigner())
        .callStatic.solicitarCuarentena(idActivo, "cid-provisional", { value: fianza });

      setMensaje("Subiendo la evidencia a IPFS…");
      const ipfs = create(IPFS_API);
      const subida = await ipfs.add(fichero);
      const cid = subida.cid.toString();
      // Copia al sistema de ficheros del nodo para verla en el panel (Files).
      // Si ese mismo fichero ya se había subido, la entrada existe y se ignora.
      try {
        await ipfs.files.cp(`/ipfs/${cid}`, `/${cid}`);
      } catch (yaExiste) {
        console.log(yaExiste.message);
      }

      setMensaje(`Evidencia en IPFS (${cid}). Confirma la transacción en MetaMask…`);
      await enviar("solicitarCuarentena", [idActivo, cid], { value: fianza });

      setMensaje(`Solicitud registrada para el activo ${idActivo}.`);
      setIdConsulta(idActivo);
      await consultar(idActivo);
      await cargarDatos(cuenta);
    });
  };

  const buscar = (e) => {
    e.preventDefault();
    ejecutar(() => consultar(idConsulta));
  };

  const accionSobreSolicitud = (funcion, args, texto) =>
    ejecutar(async () => {
      await enviar(funcion, args);
      setMensaje(texto);
      await consultar(resultado.idActivo);
      await cargarDatos(cuenta);
    });

  const retirar = () =>
    ejecutar(async () => {
      await enviar("retirar");
      setMensaje("Saldo retirado.");
      await cargarDatos(cuenta);
    });

  // --- Vista -----------------------------------------------------------------

  if (!provider) {
    return (
      <div className="App">
        <p className="aviso error">No se ha detectado MetaMask en este navegador.</p>
      </div>
    );
  }

  const redCorrecta = chainId === SEPOLIA_CHAIN_ID;
  const ahora = Math.floor(Date.now() / 1000);
  const r = resultado;
  const pendiente = r && !r.sinSolicitud && r.estado === 0;
  const plazoVencido = pendiente && ahora > r.venceVotacion;

  const misRoles = [];
  if (roles) {
    if (igual(cuenta, roles.propietario)) misRoles.push("Propietario");
    if (igual(cuenta, roles.soc)) misRoles.push("Responsable SOC");
    if (igual(cuenta, roles.servicio)) misRoles.push("Responsable del servicio");
    if (roles.esAnalista) misRoles.push("Analista autorizado");
  }

  return (
    <div className="App">
      <header className="cabecera">
        <img src={logo} className="logo" alt="logo" />
        <div>
          <h1>Cuarentena colectiva con evidencias en IPFS</h1>
          <p className="sub">
            {cuenta ? `Cuenta: ${corta(cuenta)}` : "Conectando con MetaMask…"}
            {misRoles.length > 0 && ` · ${misRoles.join(", ")}`}
            {roles && misRoles.length === 0 && " · Sin rol en el contrato"}
          </p>
        </div>
      </header>

      {chainId !== null && !redCorrecta && (
        <p className="aviso error">
          MetaMask no está en Sepolia para este sitio. Cambia de red y la página se recargará.
        </p>
      )}
      {mensaje && <p className="aviso">{mensaje}</p>}
      {error && <p className="aviso error">Error: {error}</p>}

      {redCorrecta && (
        <main>
          <section className="tarjeta">
            <h2>1. Solicitar cuarentena</h2>
            <p className="ayuda">
              La evidencia se sube a IPFS y su CID queda registrado en el contrato junto a la
              solicitud. Fianza: {fianza ? ethers.utils.formatEther(fianza) : "…"} ETH.
            </p>
            <form onSubmit={solicitar}>
              <label>
                Identificador del activo
                <input
                  type="number"
                  min="1"
                  required
                  value={idActivo}
                  onChange={(e) => setIdActivo(e.target.value)}
                />
              </label>
              <label>
                Fichero de evidencia
                <input type="file" required onChange={leerFichero} />
              </label>
              <button type="submit" disabled={ocupado}>
                Subir evidencia y solicitar
              </button>
            </form>
          </section>

          <section className="tarjeta">
            <h2>2. Consultar un activo</h2>
            <form onSubmit={buscar}>
              <label>
                Identificador del activo
                <input
                  type="number"
                  min="1"
                  required
                  value={idConsulta}
                  onChange={(e) => setIdConsulta(e.target.value)}
                />
              </label>
              <button type="submit" disabled={ocupado}>
                Consultar
              </button>
            </form>

            {r && r.sinSolicitud && (
              <p className="ayuda">El activo {r.idActivo} no tiene ninguna solicitud.</p>
            )}

            {r && !r.sinSolicitud && (
              <div className="detalle">
                <dl>
                  <dt>Solicitud</dt>
                  <dd>n.º {r.idSolicitud} (activo {r.idActivo})</dd>
                  <dt>Estado</dt>
                  <dd>
                    {ESTADOS[r.estado]}
                    {plazoVencido && " (plazo de votación vencido)"}
                  </dd>
                  <dt>En cuarentena ahora</dt>
                  <dd>{r.enCuarentena ? `Sí, hasta ${fecha(r.finCuarentena)}` : "No"}</dd>
                  <dt>Solicitante</dt>
                  <dd>{corta(r.solicitante)}</dd>
                  <dt>Voto SOC</dt>
                  <dd>{textoVoto(r.votoSOC, r.apruebaSOC)} ({corta(r.aprobadorSOC)})</dd>
                  <dt>Voto servicio</dt>
                  <dd>
                    {textoVoto(r.votoServicio, r.apruebaServicio)} ({corta(r.responsableServicio)})
                  </dd>
                  <dt>Fin de la votación</dt>
                  <dd>{fecha(r.venceVotacion)}</dd>
                  <dt>Evidencia (CID)</dt>
                  <dd>
                    <a href={IPFS_GATEWAY + r.cid} target="_blank" rel="noreferrer">
                      {r.cid}
                    </a>
                  </dd>
                </dl>

                <div className="acciones">
                  {pendiente && !plazoVencido && igual(cuenta, r.aprobadorSOC) && !r.votoSOC && (
                    <>
                      <button
                        disabled={ocupado}
                        onClick={() =>
                          accionSobreSolicitud("votarSOC", [r.idSolicitud, true], "Voto del SOC registrado: a favor.")
                        }
                      >
                        Aprobar (SOC)
                      </button>
                      <button
                        className="secundario"
                        disabled={ocupado}
                        onClick={() =>
                          accionSobreSolicitud("votarSOC", [r.idSolicitud, false], "Voto del SOC registrado: en contra.")
                        }
                      >
                        Rechazar (SOC)
                      </button>
                    </>
                  )}
                  {pendiente &&
                    !plazoVencido &&
                    igual(cuenta, r.responsableServicio) &&
                    !r.votoServicio && (
                      <>
                        <button
                          disabled={ocupado}
                          onClick={() =>
                            accionSobreSolicitud(
                              "votarResponsableServicio",
                              [r.idSolicitud, true],
                              "Voto del servicio registrado: a favor."
                            )
                          }
                        >
                          Aprobar (servicio)
                        </button>
                        <button
                          className="secundario"
                          disabled={ocupado}
                          onClick={() =>
                            accionSobreSolicitud(
                              "votarResponsableServicio",
                              [r.idSolicitud, false],
                              "Voto del servicio registrado: en contra."
                            )
                          }
                        >
                          Rechazar (servicio)
                        </button>
                      </>
                    )}
                  {plazoVencido && (
                    <button
                      className="secundario"
                      disabled={ocupado}
                      onClick={() =>
                        accionSobreSolicitud("caducarSolicitud", [r.idSolicitud], "Solicitud marcada como caducada.")
                      }
                    >
                      Marcar como caducada
                    </button>
                  )}
                </div>
              </div>
            )}
          </section>

          <section className="tarjeta">
            <h2>3. Fianzas</h2>
            <p className="ayuda">
              Saldo que puedes retirar:{" "}
              {saldoRetirable ? ethers.utils.formatEther(saldoRetirable) : "…"} ETH
            </p>
            <button disabled={ocupado || !saldoRetirable || saldoRetirable.isZero()} onClick={retirar}>
              Retirar
            </button>
          </section>
        </main>
      )}
    </div>
  );
}

export default App;
