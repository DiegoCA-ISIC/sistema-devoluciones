import os
import logging
from pathlib import Path

# Crear directorio logs si no existe
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# Configurar logging
log_file = log_dir / "email_service.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Notificador:
    def __init__(self):
        self.config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': 'tuemail@gmail.com',
            'password': 'tucontraseña'  # Usar variables de entorno en producción
        }
    
    def enviar_alerta(self, devolucion_id, tipo_requerimiento):
        try:
            # ... (resto de tu implementación)
            logging.info(f"Email enviado para devolución {devolucion_id}")
        except Exception as e:
            logging.error(f"Error enviando email: {str(e)}")
            raise