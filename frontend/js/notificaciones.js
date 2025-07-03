export class NotificacionesUI {
    constructor() {
        this.badge = document.getElementById('notificaciones-badge');
        this.lista = document.getElementById('notificaciones-lista');
        this.cargarNotificaciones();
        setInterval(() => this.cargarNotificaciones(), 300000); // Actualizar cada 5 min
    }

    async cargarNotificaciones() {
        try {
            const response = await fetch('/api/notificaciones');
            const data = await response.json();
            
            this.badge.textContent = data.length;
            this.lista.innerHTML = data.map(notif => `
                <li class="${notif.urgente ? 'urgente' : ''}">
                    <strong>${notif.titulo}</strong>
                    <p>${notif.mensaje}</p>
                    <small>${new Date(notif.fecha).toLocaleString()}</small>
                </li>
            `).join('');
        } catch (error) {
            console.error("Error cargando notificaciones:", error);
        }
    }
}