

class CalendarioSAT {
  constructor(containerId) {
    // Verifica que FullCalendar esté disponible
    if (typeof FullCalendar === 'undefined') {
      throw new Error('FullCalendar no se cargó correctamente');
    }

    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`Contenedor #${containerId} no encontrado`);
      return;
    }

    this.calendar = new window.FullCalendar.CalendarioSAT(this.container, {
      plugins: [
        FullCalendar.dayGridPlugin,
        FullCalendar.timeGridPlugin
      ],
      initialView: 'dayGridMonth',
      locale: 'es',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
      eventTimeFormat: {
        hour: '2-digit',
        minute: '2-digit',
        meridiem: false
      }
    });
  }

  init() {
    if (this.calendar) {
      this.calendar.render();
    }
    return this;
  }

  updateEvents(devoluciones) {
    if (!this.calendar) return;

    this.calendar.removeAllEvents();
    devoluciones.forEach(dev => {
      this.calendar.addEvent({
        title: `Devolución ${dev.id}`,
        start: dev.fecha_solicitud,
        end: dev.fecha_limite,
        color: this._getStatusColor(dev.estado),
        extendedProps: { id: dev.id }
      });
    });
  }

  _getStatusColor(estado) {
    const statusColors = {
      'completa': '#28a745',
      'pendiente': '#ffc107',
      'atrasada': '#dc3545'
    };
    return statusColors[estado] || '#17a2b8';
  }

  setEventClickHandler(handler) {
    if (this.calendar) {
      this.calendar.setOption('eventClick', (info) => {
        handler(info.event.extendedProps.id);
      });
    }
  }
}