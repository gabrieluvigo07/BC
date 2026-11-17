import React, { useEffect, useState } from "react";
// Versión del ejercicio 1 (contrato IpfsStorage). Se conserva como referencia;
// la app que se ejecuta es App.js (ejercicio 2).
import './AppEjercicio1.css';
import { create } from 'kubo-rpc-client'
import { ethers } from "ethers"
import { Buffer } from "buffer"

import logo from "./ethereumLogo.png"
import { addresses, abis } from "./contracts"

const ZERO_ADDRESS =
  "0x0000000000000000000000000000000000000000000000000000000000000000";

const defaultProvider = new ethers.providers.Web3Provider(window.ethereum);
// version 6
//const defaultProvider = new ethers.BrowserProvider(window.ethereum);

const ipfsContract = new ethers.Contract(
  addresses.ipfs,
  abis.ipfs,
  defaultProvider
);

async function readCurrentUserFile() {
  const result = await ipfsContract.userFiles(
    defaultProvider.getSigner().getAddress()
  );
  console.log({ result });
  return result;
}

function App() {

  const [ipfsHash, setIpfsHash] = useState("");

  useEffect(() => {
    window.ethereum.enable();
  }, []);

  const [file, setFile] = useState(null);

  useEffect(() => {
    async function readFile() {
      const file = await readCurrentUserFile();

      if (file !== ZERO_ADDRESS) setIpfsHash(file);
    }
    readFile();
  }, []);

  async function setFileIPFS(hash) {
    const ipfsWithSigner = ipfsContract.connect(defaultProvider.getSigner());
    console.log("TX contract");
    const tx = await ipfsWithSigner.setFileIPFS(hash);
    console.log({ tx });

    setIpfsHash(hash);
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      console.log(file)
      // conectar a la instancia en local de ipfs
      const client = await create('/ip4/127.0.0.1/tcp/5001')
      // añadir le archivo a ipfs
      const result = await client.add(file)
      // añadir al fs del nodo ipfs en local para poder visualizarlo en el dashboard
      await client.files.cp(`/ipfs/${result.cid}`, `/${result.cid}`)
      console.log(result.cid)
      // añadir el CID de ipfs a ethereum a traves del smart contract
      await setFileIPFS(result.cid.toString());
    } catch (error) {
      console.log(error.message);
    }
  };

  const retrieveFile = (e) => {
    const data = e.target.files[0];
    const reader = new window.FileReader();
    reader.readAsArrayBuffer(data);
    console.log(data);
    reader.onloadend = () => {
      console.log("Buffer data: ", Buffer(reader.result));
      setFile(Buffer(reader.result));
    }
    e.preventDefault();
  }

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Upload a file to store it on IPFS and save the hash on ethereum.
        </p>
        <form className="form" onSubmit={handleSubmit}>
          <input type="file" name="data" onChange={retrieveFile} />
          <button type="submit" className="btn">Upload</button>
        </form>
        {ipfsHash && <p>CID guardado en Ethereum: {ipfsHash}</p>}
      </header>
    </div>
  );
}

export default App;
