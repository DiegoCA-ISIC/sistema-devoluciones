// Estado global de la aplicación
const state = {
    devoluciones: [],
    currentDevolucion: null,
    loading: false,
    error: null,
};

// Observers para cambios de estado
const observers = [];

// Cache de elementos del DOM
const UI = {
    get empresa() { return document.getElementById('empresa'); },
    get monto() { return document.getElementById('monto'); },
    get fechaPeriodo() { return document.getElementById('fechaPeriodo'); },
    get fechaSolicitud() { return document.getElementById('fechaSolicitud'); },
    get btnNuevaDevolucion() { return document.getElementById('btnNuevaDevolucion'); },
    get resultado() { return document.getElementById('resultado'); },
    get tablaDevoluciones() { return document.getElementById('tablaDevoluciones'); },
    get panelRequerimientos() { return document.getElementById('panel-requerimientos'); },
    get loadingSpinner() { return document.getElementById('loading-spinner'); }
};

// Helpers reutilizables
const http = {
    async get(url) {
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.message || `HTTP error! status: ${response.status}`);
        }
        return response.json();
    },

    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.message || `HTTP error! status: ${response.status}`);
        }
        return response.json();
    }
};

const utils = {
    formatDate(dateStr) {
        if (!dateStr) return '-';
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return new Date(dateStr).toLocaleDateString('es-MX', options);
    },

    validarFecha(fechaStr) {
        const regex = /^\d{4}-\d{2}-\d{2}$/;
        if (!regex.test(fechaStr)) return false;

        const fecha = new Date(fechaStr);
        return !isNaN(fecha.getTime()) &&
            fecha.toISOString().slice(0, 10) === fechaStr;
    }
};

// Función principal exportada
export function inicializarApp() {
    setupEventListeners();
    cargarDatosIniciales();
    cargarEmpresas();
}



function setupEventListeners() {
    UI.btnNuevaDevolucion.addEventListener('click', registrarDevolucion);

    // Delegación de eventos para elementos dinámicos
    document.addEventListener('click', (e) => {
        if (e.target.closest('[data-action="gestionar"]')) {
            const id = e.target.closest('button').dataset.id;
            gestionarRequerimiento(id);
        }
    });

    document.getElementById('cerrar-panel').addEventListener('click', () => {
        document.getElementById('panel-requerimientos').classList.remove('show');
        document.body.style.overflow = 'auto';
    });

    document.getElementById('filtroEmpresa').addEventListener('change', renderizarDevoluciones);

}

async function cargarDatosIniciales() {
    setLoading(true);

    try {
        const data = await http.get('http://localhost:5000/api/devoluciones');
        setDevoluciones(data);
        renderizarDevoluciones();

        if (state.calendario) {
            state.calendario.updateEvents(data);
        }

    } catch (error) {
        setError(error.message);
        console.error("Error:", error);
    } finally {
        setLoading(false);
    }
}

async function registrarDevolucion() {
    if (!utils.validarFecha(UI.fechaSolicitud.value)) {
        setError('Por favor ingrese una fecha válida (YYYY-MM-DD)');
        return;
    }

    if (!UI.empresa.value || !UI.monto.value || !UI.fechaPeriodo.value) {
        setError('Todos los campos son obligatorios');
        return;
    }

    setLoading(true);

    try {
        const data = {
            fecha_solicitud: UI.fechaSolicitud.value,
            empresa: UI.empresa.value,
            monto: parseFloat(UI.monto.value),
            fecha_periodo: UI.fechaPeriodo.value
        };

        console.log("Registrando devolución:", data);

        const response = await http.post('http://localhost:5000/api/devoluciones', data);

        setCurrentDevolucion(response.id);
        mostrarExito(`Devolución registrada:\nFecha Límite: ${utils.formatDate(response.fecha_limite)}`);
        UI.panelRequerimientos.style.display = 'block';
        await cargarDatosIniciales();
    } catch (error) {
        setError(error.message);
        console.error("Error:", error);
    } finally {
        setLoading(false);
    }
}
document.getElementById('filtroEmpresa').addEventListener('change', renderizarDevoluciones);


function renderizarDevoluciones() {
    const filtroId = document.getElementById('filtroEmpresa').value;
    const devolucionesFiltradas = filtroId
        ? state.devoluciones.filter(d => d.empresa_id == filtroId)
        : state.devoluciones;

    const fragment = document.createDocumentFragment();
    const tbody = document.createElement('tbody');

    devolucionesFiltradas.forEach(devolucion => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${devolucion.id}</td>
            <td>${utils.formatDate(devolucion.fecha_solicitud)}</td>
            <td>${utils.formatDate(devolucion.fecha_limite)}</td>
            <td>${devolucion.req1_notificacion ? utils.formatDate(devolucion.req1_notificacion) : '-'}</td>
            <td>${devolucion.req2_notificacion ? utils.formatDate(devolucion.req2_notificacion) : '-'}</td>
            <td class="${devolucion.dias_restantes < 10 ? 'text-danger' : ''}">
                ${devolucion.dias_restantes}
            </td>
            <td>
                <span class="badge ${devolucion.estado.includes('pausado') ? 'bg-warning' :
                devolucion.estado === 'vencido' ? 'bg-danger' : 'bg-success'}">
                    ${devolucion.estado.replace('_', ' ').toUpperCase()}
                </span>
            </td>
            <td>
                <button class="btn-sm" data-action="gestionar" data-id="${devolucion.id}">
                    <i class="fas fa-edit"></i> Gestionar
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    UI.tablaDevoluciones.innerHTML = `
        <thead>
            <tr>
                <th>ID</th>
                <th>Fecha Solicitud</th>
                <th>Fecha Límite</th>
                <th>1er Requerimiento</th>
                <th>2do Requerimiento</th>
                <th>Días Restantes</th>
                <th>Estado</th>
                <th>Acciones</th>
            </tr>
        </thead>
    `;
    UI.tablaDevoluciones.appendChild(tbody);
}


// Funciones de estado
function setLoading(loading) {
    state.loading = loading;
    updateUI();
}

function setDevoluciones(data) {
    state.devoluciones = data;
    updateUI();
}

function setCurrentDevolucion(id) {
    state.currentDevolucion = id;
    updateUI();
}

function setError(message) {
    state.error = message;
    updateUI();
}

function updateUI() {
    // Manejar estado de carga
    const loadingSpinner = document.getElementById('loading-spinner');
    if (!loadingSpinner) return;

    if (state.loading) {
        loadingSpinner.style.display = 'block';
    } else {
        loadingSpinner.style.display = 'none';
    }
}

// Funciones de UI
function mostrarError(mensaje) {
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: mensaje,
        timer: 3000,
        showConfirmButton: false
    });
    state.error = mensaje;

}

function mostrarExito(mensaje) {
    Swal.fire({
        icon: 'success',
        title: 'Éxito',
        text: mensaje,
        timer: 2000,
        showConfirmButton: false
    });
}

// Función para gestionar requerimientos
async function gestionarRequerimiento(devolucionId) {
    setCurrentDevolucion(devolucionId);
    UI.panelRequerimientos.classList.add('show');
    document.body.style.overflow = 'hidden';

    // Opcional: Cargar detalles adicionales
    try {
        const detalle = await http.get(`http://localhost:5000/api/devoluciones/${devolucionId}`);
        // Actualizar UI con detalles
        // Llenar campos del panel
        // Llenar las fechas de notificación y solvencia
        document.getElementById('detalle-id').textContent = detalle.id;
        document.getElementById('detalle-fecha').textContent = utils.formatDate(detalle.fecha_solicitud);
        document.getElementById('req1-notif').textContent = utils.formatDate(detalle.req1_notificacion);
        document.getElementById('req1-solv').textContent = utils.formatDate(detalle.req1_respuesta);
        document.getElementById('req2-notif').textContent = utils.formatDate(detalle.req2_notificacion);
        document.getElementById('req2-solv').textContent = utils.formatDate(detalle.req2_respuesta);
        document.getElementById('detalle-dias-transcurridos').textContent = detalle.dias_transcurridos;
        document.getElementById('detalle-dias-restantes').textContent = detalle.dias_restantes;
        actualizarBarraProgreso(detalle.dias_transcurridos);

        const estadoBadge = document.getElementById('detalle-estado');
        estadoBadge.className = 'badge';

        if (detalle.estado_calculado.startsWith('pausado')) {
            estadoBadge.classList.add('bg-warning');
        } else if (detalle.estado_calculado === 'vencido') {
            estadoBadge.classList.add('bg-danger');
        } else {
            estadoBadge.classList.add('bg-success');
        }

        // Conectar botón para registrar requerimientos
        document.getElementById('btnReq1').onclick = () => enviarRequerimiento(devolucionId, 1);
        document.getElementById('btnReq2').onclick = () => enviarRequerimiento(devolucionId, 2);


        // Agregar eventos para registrar solvencias
        document.getElementById('btnSolv1').onclick = () => registrarSolvencia(devolucionId, 1);
        document.getElementById('btnSolv2').onclick = () => registrarSolvencia(devolucionId, 2);


    } catch (error) {
        setError(error.message);
    }

    // En app.js o donde manejes la tabla
    function bindRequerimientoButtons() {
        document.querySelectorAll('[data-action="gestionar"]').forEach(btn => {
            btn.addEventListener('click', () => {
                const devolucionId = btn.dataset.id;
                // Puedes implementar un diálogo para seleccionar el tipo
                // o determinar automáticamente si es 1er o 2do requerimiento
                const tipo = determinarTipoRequerimiento(devolucionId);
                mostrarModalRequerimiento(devolucionId, tipo);
            });
        });
    }

    // Función de ejemplo para determinar el tipo
    function determinarTipoRequerimiento(devolucionId) {
        const devolucion = state.devoluciones.find(d => d.id == devolucionId);
        return devolucion.req1_notificacion ? 2 : 1; // Si ya tiene 1er req, será 2do
    }

    document.addEventListener('DOMContentLoaded', function () {
        const calendarEl = document.getElementById('calendar');

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'es',
            events: '/api/devoluciones', // Tu endpoint Flask
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            }
        });

        calendar.render();
    });
}

async function enviarRequerimiento(devolucionId, tipo) {
    try {
        const ruta = `http://localhost:5000/api/devoluciones/${devolucionId}/requerimientos`;
        const data = { tipo };

        const respuesta = await http.post(ruta, data);

        mostrarExito(`Requerimiento tipo ${tipo} registrado correctamente.`);
        await cargarDatosIniciales();
        gestionarRequerimiento(devolucionId); // refrescar datos del panel

    } catch (error) {
        setError(`Error al registrar requerimiento: ${error.message}`);
    }
}


async function registrarSolvencia(devolucionId, tipo) {
    const campo = tipo === 1 ? 'req1_respuesta' : 'req2_respuesta';
    const hoy = obtenerFechaLocal(); // Formato YYYY-MM-DD

    try {
        const response = await fetch(`http://localhost:5000/api/devoluciones/${devolucionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [campo]: hoy })
        });

        if (!response.ok) {
            throw new Error('No se pudo registrar la solvencia');
        }

        mostrarExito(`Solvencia del requerimiento ${tipo} registrada.`);
        gestionarRequerimiento(devolucionId); // Refresca el panel

    } catch (error) {
        setError(error.message);
    }
}

function mostrarAlertaPanel(mensaje, tipo = 'success') {
    const alerta = document.getElementById('alerta-panel');
    alerta.textContent = mensaje;
    alerta.className = `alert alert-${tipo}`;
    alerta.classList.remove('d-none');

    setTimeout(() => {
        alerta.classList.add('d-none');
    }, 3000);
}


function obtenerFechaLocal() {
    const hoy = new Date();
    hoy.setMinutes(hoy.getMinutes() - hoy.getTimezoneOffset()); // Compensa la zona horaria
    return hoy.toISOString().split('T')[0];
}

function actualizarBarraProgreso(diasTranscurridos) {
    const totalDias = 40;
    const porcentaje = Math.min((diasTranscurridos / totalDias) * 100, 100).toFixed(0);

    const barra = document.getElementById("barra-progreso");
    const texto = document.getElementById("porcentaje-progreso");

    barra.style.width = `${porcentaje}%`;
    texto.textContent = `${porcentaje}% del plazo utilizado`;

    if (porcentaje < 75) {
        barra.style.backgroundColor = '#2ecc71'; // verde
    } else if (porcentaje < 100) {
        barra.style.backgroundColor = '#f39c12'; // naranja
    } else {
        barra.style.backgroundColor = '#e74c3c'; // rojo
    }
}

document.getElementById('btnRegistrarEmpresa').addEventListener('click', async () => {
    const nombre = document.getElementById('nombreEmpresa').value.trim();
    const rfc = document.getElementById('rfcEmpresa').value.trim().toUpperCase();

    if (!nombre) return mostrarError('El nombre de la empresa y el RFC no pueden estar vacíos.');
try {
        const response = await fetch('http://localhost:5000/api/empresas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, rfc: rfc || null })
        });

        if (!response.ok) {
            throw new Error('No se pudo registrar la empresa.');
        }

        mostrarExito('Empresa registrada correctamente.');
        document.getElementById('nombreEmpresa').value = '';
        document.getElementById('rfcEmpresa').value = '';
        await cargarEmpresas(); // Para refrescar el select
    } catch (error) {
        mostrarError(error.message);
    }
});


async function cargarEmpresas() {
    try {
        const empresas = await http.get('http://localhost:5000/api/empresas');

        // Llenar <select> del formulario de devolución
        const selectEmpresa = document.getElementById('empresa');
        selectEmpresa.innerHTML = '<option value="">Selecciona una empresa</option>';

        // Llenar <select> del filtro
        const filtroEmpresa = document.getElementById('filtroEmpresa');
        filtroEmpresa.innerHTML = '<option value="">Todas</option>';

        empresas.forEach(e => {
            const option1 = document.createElement('option');
            option1.value = e.id;
            option1.textContent = e.nombre;
            selectEmpresa.appendChild(option1);

            const option2 = document.createElement('option');
            option2.value = e.id;
            option2.textContent = e.nombre;
            filtroEmpresa.appendChild(option2);
        });

    } catch (error) {
        console.error('Error al cargar empresas:', error.message);
    }
}





