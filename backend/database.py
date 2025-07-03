import sqlite3
from datetime import datetime, timedelta

def init_database():
    """Inicializa la base de datos con estructura completa y datos de prueba"""
    try:
        conn = sqlite3.connect('devoluciones.db')
        cursor = conn.cursor()
        
        # Tabla de devoluciones (estructura mejorada)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS devoluciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_solicitud TEXT NOT NULL CHECK(date(fecha_solicitud) IS NOT NULL),
            fecha_limite TEXT NOT NULL CHECK(date(fecha_limite) IS NOT NULL),
            req1_notificacion TEXT CHECK(req1_notificacion IS NULL OR date(req1_notificacion) IS NOT NULL),
            req1_respuesta TEXT CHECK(req1_respuesta IS NULL OR date(req1_respuesta) IS NOT NULL),
            req2_notificacion TEXT CHECK(req2_notificacion IS NULL OR date(req2_notificacion) IS NOT NULL),
            req2_respuesta TEXT CHECK(req2_respuesta IS NULL OR date(req2_respuesta) IS NOT NULL),
            dias_restantes INTEGER DEFAULT 40 CHECK(dias_restantes BETWEEN 0 AND 40),
            estado TEXT DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'completado', 'cancelado')),
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabla de festivos (con más campos relevantes)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS festivos (
            fecha TEXT PRIMARY KEY CHECK(date(fecha) IS NOT NULL),
            descripcion TEXT NOT NULL,
            recurrente BOOLEAN DEFAULT 0,
            año INTEGER GENERATED ALWAYS AS (CAST(strftime('%Y', fecha) AS INTEGER)) VIRTUAL
        )
        ''')
        
        # Tabla de logs (para auditoría)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accion TEXT NOT NULL,
            tabla_afectada TEXT NOT NULL,
            id_registro INTEGER,
            detalles TEXT,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT DEFAULT 'system'
        )
        ''')
        
        # Insertar festivos oficiales SAT (ejemplo para 2024)
        festivos = [
            ('2024-01-01', 'Año Nuevo', 1),
            ('2024-02-05', 'Día de la Constitución', 0),
            ('2024-03-18', 'Natalicio de Benito Juárez', 0),
            ('2024-05-01', 'Día del Trabajo', 1),
            ('2024-09-16', 'Día de la Independencia', 1),
            ('2024-12-25', 'Navidad', 1)
        ]
        
        cursor.executemany('''
        INSERT OR IGNORE INTO festivos (fecha, descripcion, recurrente) 
        VALUES (?, ?, ?)
        ''', festivos)
        
        # Datos de prueba (opcional, solo para desarrollo)
        if False:  # Cambiar a False en producción
            from datetime import datetime, timedelta
            hoy = datetime.now().strftime('%Y-%m-%d')
            
            # Insertar devoluciones de ejemplo
            devoluciones = [
                (hoy, calcular_fecha_limite(hoy), None, None, None, None, 40, 'pendiente'),
                ('2024-01-15', '2024-03-10', '2024-01-20', '2024-01-25', None, None, 35, 'completado'),
                ('2024-02-01', '2024-03-25', '2024-02-10', '2024-02-12', '2024-02-15', '2024-02-18', 30, 'completado')
            ]
            
            cursor.executemany('''
            INSERT INTO devoluciones 
            (fecha_solicitud, fecha_limite, req1_notificacion, req1_respuesta, 
             req2_notificacion, req2_respuesta, dias_restantes, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', devoluciones)
        
        conn.commit()
        print("✅ Base de datos inicializada correctamente")
        
    except sqlite3.Error as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
    finally:
        if conn:
            conn.close()

def calcular_fecha_limite(fecha_inicio, dias=40):
    """Función auxiliar para calcular fechas límite (solo para datos de prueba)"""
    fecha = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    return (fecha + timedelta(days=dias)).strftime('%Y-%m-%d')

if __name__ == '__main__':
    init_database()