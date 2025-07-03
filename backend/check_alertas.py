import sqlite3
from datetime import datetime
from email_service import Notificador

def verificar_alertas():
    conn = sqlite3.connect('devoluciones.db')
    cursor = conn.cursor()
    
    # Devoluciones con menos de 5 días restantes
    cursor.execute('''
        SELECT id, fecha_solicitud, dias_restantes 
        FROM devoluciones 
        WHERE dias_restantes <= 5 AND estado = 'pendiente'
    ''')
    
    notificador = Notificador()
    
    for devolucion in cursor.fetchall():
        notificador.enviar_alerta(
            devolucion_id=devolucion[0],
            tipo_requerimiento='alerta',
            mensaje=f'''
            ¡Alerta! La devolución #{devolucion[0]} tiene {devolucion[2]} días restantes.
            Fecha solicitud: {devolucion[1]}
            '''
        )
    
    conn.close()

if __name__ == '__main__':
    verificar_alertas()