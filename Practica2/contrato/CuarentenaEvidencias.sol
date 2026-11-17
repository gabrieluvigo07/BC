// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.30;

// Ampliación de CuarentenaColectiva (Práctica 1): cada solicitud lleva asociado
// el CID de IPFS de la evidencia que la justifica.
contract CuarentenaEvidencias {
    enum EstadoSolicitud {
        Pendiente,
        Aprobada,
        Rechazada,
        Caducada
    }

    struct Solicitud {
        uint256 idActivo;
        address solicitante;
        address aprobadorSOC;
        address responsableServicio;
        uint64 venceVotacion;
        uint64 finCuarentena;
        bool votoSOC;
        bool apruebaSOC;
        bool votoServicio;
        bool apruebaServicio;
        EstadoSolicitud estado;
    }

    uint64 public constant PLAZO_VOTACION = 10 minutes;
    uint64 public constant DURACION_CUARENTENA = 1 hours;
    uint256 public constant FIANZA = 0.001 ether; //Bajamos la fianza para las pruebas con sepolia

    address public propietario;
    address public responsableSOC;
    address public responsableServicio;
    uint256 public totalSolicitudes;

    mapping(address => bool) public analistasAutorizados;
    mapping(uint256 => Solicitud) public solicitudes;
    mapping(uint256 => uint256) public solicitudActualPorActivo;
    mapping(address => uint256) public saldoRetirable;   
    mapping(uint256 => string) public evidenciaPorSolicitud; // CID de IPFS de la evidencia de cada solicitud (idSolicitud => CID)

    error NoEresPropietario();
    error DireccionCero();
    error AnalistaYaAutorizado();
    error ResponsablesIguales();
    error ResponsableNoAutorizado();
    error NoEresAnalista();
    error IdActivoInvalido();
    error CidVacio(); //Error nuevo si alguien intenta solicitar sin evidencia
    error FaltanResponsables();
    error ResponsableNoSolicita();
    error FianzaIncorrecta();
    error SolicitudActiva();
    error SolicitudNoExiste();
    error SolicitudNoPendiente();
    error PlazoVencido();
    error NoEresSOC();
    error NoEresResponsableServicio();
    error VotoYaEmitido();
    error SinSaldoRetirable();
    error FalloRetirada();

    event AnalistaAutorizado(address indexed analista);
    event ResponsablesConfigurados(address indexed responsableSOC, address indexed responsableServicio);
    event CuarentenaSolicitada(
        uint256 indexed idSolicitud,
        uint256 indexed idActivo,
        address indexed solicitante,
        uint64 venceVotacion
    );
    event EvidenciaRegistrada(uint256 indexed idSolicitud, string cid);
    event VotoEmitido(uint256 indexed idSolicitud, address indexed aprobador, bool aprueba); //evento nuevo para emitir el voto en la blockchain
    event CuarentenaAprobada(uint256 indexed idSolicitud, uint256 indexed idActivo, uint64 finCuarentena);
    event SolicitudRechazada(uint256 indexed idSolicitud, uint256 indexed idActivo);
    event SolicitudCaducada(uint256 indexed idSolicitud);
    event FianzaAbonada(address indexed beneficiario, uint256 indexed idSolicitud, uint256 cantidad);
    event FianzaRetirada(address indexed beneficiario, uint256 cantidad);

    modifier soloPropietario() {
        if (msg.sender != propietario) revert NoEresPropietario();
        _;
    }

    constructor() {
        propietario = msg.sender;
        analistasAutorizados[msg.sender] = true;
    }

    function autorizarAnalista(address analista) external soloPropietario {
        if (analista == address(0)) revert DireccionCero();
        if (analistasAutorizados[analista]) revert AnalistaYaAutorizado();

        analistasAutorizados[analista] = true;
        emit AnalistaAutorizado(analista);
    }

    function configurarResponsables(address nuevoSOC, address nuevoResponsableServicio) external soloPropietario {
        if (nuevoSOC == address(0) || nuevoResponsableServicio == address(0)) revert DireccionCero();
        if (nuevoSOC == nuevoResponsableServicio) revert ResponsablesIguales();
        if (!analistasAutorizados[nuevoSOC] || !analistasAutorizados[nuevoResponsableServicio]) {
            revert ResponsableNoAutorizado();
        }

        responsableSOC = nuevoSOC;
        responsableServicio = nuevoResponsableServicio;
        emit ResponsablesConfigurados(nuevoSOC, nuevoResponsableServicio);
    }

    function solicitarCuarentena(uint256 idActivo, string calldata cidEvidencia)
        external
        payable
        returns (uint256)
    {
        if (!analistasAutorizados[msg.sender]) revert NoEresAnalista();
        if (idActivo == 0) revert IdActivoInvalido();
        if (bytes(cidEvidencia).length == 0) revert CidVacio(); //Comprobacion

        address aprobadorSOC = responsableSOC;
        address aprobadorServicio = responsableServicio;
        if (aprobadorSOC == address(0) || aprobadorServicio == address(0)) revert FaltanResponsables();
        if (msg.sender == aprobadorSOC || msg.sender == aprobadorServicio) revert ResponsableNoSolicita();
        if (msg.value != FIANZA) revert FianzaIncorrecta();

        uint256 idAnterior = solicitudActualPorActivo[idActivo];
        if (idAnterior != 0) {
            Solicitud storage anterior = solicitudes[idAnterior];
            bool pendienteVigente =
                anterior.estado == EstadoSolicitud.Pendiente && block.timestamp <= anterior.venceVotacion;
            bool cuarentenaVigente =
                anterior.estado == EstadoSolicitud.Aprobada && block.timestamp < anterior.finCuarentena;

            if (pendienteVigente || cuarentenaVigente) revert SolicitudActiva();

            if (anterior.estado == EstadoSolicitud.Pendiente) {
                anterior.estado = EstadoSolicitud.Caducada;
                _abonar(anterior.solicitante, idAnterior);
                emit SolicitudCaducada(idAnterior);
            }
        }

        uint256 idSolicitud = ++totalSolicitudes;
        uint64 vence = uint64(block.timestamp + PLAZO_VOTACION);

        solicitudes[idSolicitud] = Solicitud({
            idActivo: idActivo,
            solicitante: msg.sender,
            aprobadorSOC: aprobadorSOC,
            responsableServicio: aprobadorServicio,
            venceVotacion: vence,
            finCuarentena: 0,
            votoSOC: false,
            apruebaSOC: false,
            votoServicio: false,
            apruebaServicio: false,
            estado: EstadoSolicitud.Pendiente
        });
        solicitudActualPorActivo[idActivo] = idSolicitud;
        evidenciaPorSolicitud[idSolicitud] = cidEvidencia;

        emit CuarentenaSolicitada(idSolicitud, idActivo, msg.sender, vence);
        emit EvidenciaRegistrada(idSolicitud, cidEvidencia);
        return idSolicitud;
    }

    function votarSOC(uint256 idSolicitud, bool aprueba) external {
        Solicitud storage solicitud = solicitudes[idSolicitud];
        if (solicitud.idActivo == 0) revert SolicitudNoExiste();
        if (solicitud.estado != EstadoSolicitud.Pendiente) revert SolicitudNoPendiente();
        if (block.timestamp > solicitud.venceVotacion) revert PlazoVencido();
        if (msg.sender != solicitud.aprobadorSOC) revert NoEresSOC();
        if (solicitud.votoSOC) revert VotoYaEmitido();

        solicitud.votoSOC = true;
        solicitud.apruebaSOC = aprueba;
        emit VotoEmitido(idSolicitud, msg.sender, aprueba);
        _resolverVotacion(idSolicitud, solicitud);
    }

    function votarResponsableServicio(uint256 idSolicitud, bool aprueba) external {
        Solicitud storage solicitud = solicitudes[idSolicitud];
        if (solicitud.idActivo == 0) revert SolicitudNoExiste();
        if (solicitud.estado != EstadoSolicitud.Pendiente) revert SolicitudNoPendiente();
        if (block.timestamp > solicitud.venceVotacion) revert PlazoVencido();
        if (msg.sender != solicitud.responsableServicio) revert NoEresResponsableServicio();
        if (solicitud.votoServicio) revert VotoYaEmitido();

        solicitud.votoServicio = true;
        solicitud.apruebaServicio = aprueba;
        emit VotoEmitido(idSolicitud, msg.sender, aprueba);
        _resolverVotacion(idSolicitud, solicitud);
    }

    function caducarSolicitud(uint256 idSolicitud) external {
        Solicitud storage solicitud = solicitudes[idSolicitud];
        if (solicitud.idActivo == 0) revert SolicitudNoExiste();
        if (solicitud.estado != EstadoSolicitud.Pendiente) revert SolicitudNoPendiente();
        if (block.timestamp <= solicitud.venceVotacion) revert PlazoVencido();

        solicitud.estado = EstadoSolicitud.Caducada;
        _abonar(solicitud.solicitante, idSolicitud);
        emit SolicitudCaducada(idSolicitud);
    }

    function retirar() external {
        uint256 cantidad = saldoRetirable[msg.sender];
        if (cantidad == 0) revert SinSaldoRetirable();

        saldoRetirable[msg.sender] = 0;
        (bool correcto, ) = payable(msg.sender).call{value: cantidad}("");
        if (!correcto) revert FalloRetirada();

        emit FianzaRetirada(msg.sender, cantidad);
    }

    function estaEnCuarentena(uint256 idActivo) external view returns (bool) {
        uint256 idSolicitud = solicitudActualPorActivo[idActivo];
        if (idSolicitud == 0) return false;

        Solicitud storage solicitud = solicitudes[idSolicitud];
        return solicitud.estado == EstadoSolicitud.Aprobada && block.timestamp < solicitud.finCuarentena;
    }

    function _resolverVotacion(uint256 idSolicitud, Solicitud storage solicitud) internal {
        if ((solicitud.votoSOC && !solicitud.apruebaSOC) || (solicitud.votoServicio && !solicitud.apruebaServicio)) {
            solicitud.estado = EstadoSolicitud.Rechazada;
            _abonar(propietario, idSolicitud);
            emit SolicitudRechazada(idSolicitud, solicitud.idActivo);
        } else if (solicitud.votoSOC && solicitud.apruebaSOC && solicitud.votoServicio && solicitud.apruebaServicio) {
            solicitud.estado = EstadoSolicitud.Aprobada;
            solicitud.finCuarentena = uint64(block.timestamp + DURACION_CUARENTENA);
            _abonar(solicitud.solicitante, idSolicitud);
            emit CuarentenaAprobada(idSolicitud, solicitud.idActivo, solicitud.finCuarentena);
        }
    }

    function _abonar(address beneficiario, uint256 idSolicitud) internal {
        saldoRetirable[beneficiario] += FIANZA;
        emit FianzaAbonada(beneficiario, idSolicitud, FIANZA);
    }
}

