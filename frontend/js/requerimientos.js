export function configurarModalRequerimientos() {
    const modal = document.getElementById('modal-requerimiento');
    const observaciones = document.getElementById('observaciones');
    const charCount = document.getElementById('char-count');

    if (!modal) return;

    const form = modal.querySelector('form');
    if (!form) return;
    // Contador de caracteres
    observaciones.addEventListener('input', () => {
        charCount.textContent = observaciones.value.length;
    });

    // Cierre del modal
    document.querySelectorAll('[data-modal-close]').forEach(el => {
        el.addEventListener('click', () => {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto'; // Restaura el scroll
        });
    });

    // Envío del formulario
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btnEnviar = document.getElementById('btn-enviar-req');
        btnEnviar.disabled = true;
        btnEnviar.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';

        try {
            const formData = new FormData(form);
            const adjuntos = document.getElementById('adjuntos').files;

            // Agregar archivos al FormData
            for (let i = 0; i < adjuntos.length; i++) {
                formData.append('adjuntos[]', adjuntos[i]);
            }

            const response = await fetch(`/api/devoluciones/${form.devolucion_id.value}/requerimientos`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Error en el servidor');
            }

            mostrarNotificacion('success', 'Requerimiento enviado correctamente');
            modal.style.display = 'none';
            document.dispatchEvent(new CustomEvent('requerimientoRegistrado'));

        } catch (error) {
            mostrarNotificacion('error', error.message);
            console.error('Error:', error);
        } finally {
            btnEnviar.disabled = false;
            btnEnviar.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar al SAT';
        }
    });
}

export function mostrarModalRequerimiento(devolucionId, tipo) {
    const modal = document.getElementById('modal-requerimiento');
    const form = document.getElementById('form-requerimiento');
    const tipoText = document.getElementById('tipo-requerimiento-text');
    const tipoBadge = document.getElementById('tipo-requerimiento-badge');

    // Configurar el formulario
    form.tipo.value = tipo;
    form.devolucion_id.value = devolucionId;
    form.observaciones.value = '';
    document.getElementById('char-count').textContent = '0';

    // Actualizar UI según el tipo
    if (tipo === 1) {
        tipoText.textContent = 'Primer Requerimiento';
        tipoBadge.textContent = 'Primero';
        tipoBadge.className = 'badge primary';
    } else {
        tipoText.textContent = 'Segundo Requerimiento';
        tipoBadge.textContent = 'Segundo';
        tipoBadge.className = 'badge warning';
    }

    // Mostrar modal
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Bloquear scroll
    modal.setAttribute('aria-hidden', 'false');

    // Enfocar el primer elemento interactivo
    setTimeout(() => {
        form.observaciones.focus();
    }, 100);
}

function mostrarNotificacion(tipo, mensaje) {
    // Implementa tu sistema de notificaciones
    console.log(`[${tipo}] ${mensaje}`);
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
