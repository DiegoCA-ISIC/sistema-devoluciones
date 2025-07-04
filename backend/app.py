from flask import Flask, jsonify, request, abort, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+
import smtplib
from email.mime.text import MIMEText
from email_service import Notificador
import logging
import os
import tzdata


# Configuración inicial
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://127.0.0.1:8000", "http://localhost:8000"]}})
notificador = Notificador()

# Configuración del sistema
app.config.update({
    'DATABASE': 'devoluciones.db',
    'EMAIL_SERVER': os.getenv('EMAIL_SERVER', 'smtp.gmail.com'),
    'EMAIL_PORT': os.getenv('EMAIL_PORT', 587),
    'EMAIL_USER': os.getenv('EMAIL_USER', 'tuemail@gmail.com'),
    'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD', 'tucontraseñaapp')
})

# Función para conectar a la base de datos
def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Inicialización de la base de datos
def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devoluciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_solicitud TEXT NOT NULL,
                fecha_limite TEXT NOT NULL,
                req1_notificacion TEXT,
                req1_respuesta TEXT,
                req2_notificacion TEXT,
                req2_respuesta TEXT,
                dias_restantes INTEGER DEFAULT 40,
                estado TEXT DEFAULT 'pendiente'
            )
        ''')
         # Nueva tabla de empresas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                rfc TEXT,
                fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
         # Agrega columna empresa_id a devoluciones si no existe aún
        cursor.execute('''
            PRAGMA table_info(devoluciones)
        ''')
        columnas = [col[1] for col in cursor.fetchall()]
        
        
        if 'empresa_id' not in columnas:
            cursor.execute('''
                ALTER TABLE devoluciones ADD COLUMN empresa_id INTEGER REFERENCES empresas(id)
            ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS festivos (
                fecha TEXT PRIMARY KEY,
                descripcion TEXT
            )
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO festivos (fecha, descripcion) 
            VALUES ('2024-01-01', 'Año Nuevo')
        ''')
        if 'empresa_id' not in columnas:
            cursor.execute('''
                ALTER TABLE devoluciones ADD COLUMN empresa_id INTEGER REFERENCES empresas(id)
            ''')

        if 'periodo' not in columnas:
            cursor.execute('''
                ALTER TABLE devoluciones ADD COLUMN periodo TEXT
            ''')

        if 'monto' not in columnas:
            cursor.execute('''
                ALTER TABLE devoluciones ADD COLUMN monto REAL
            ''')

# Lógica para calcular fecha límite con días hábiles
def calcular_dias_habiles(fecha_inicio, dias_necesarios=40):
    with get_db() as conn:
        festivos = [row['fecha'] for row in conn.execute('SELECT fecha FROM festivos')]
    fecha_actual = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    dias_contados = 0
    while dias_contados < dias_necesarios:
        fecha_actual += timedelta(days=1)
        if fecha_actual.weekday() < 5 and fecha_actual.strftime('%Y-%m-%d') not in festivos:
            dias_contados += 1
    return fecha_actual.strftime('%Y-%m-%d')

# Lógica de envío de email (opcional)
def enviar_alerta(email, mensaje):
    try:
        with smtplib.SMTP(app.config['EMAIL_SERVER'], app.config['EMAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['EMAIL_USER'], app.config['EMAIL_PASSWORD'])
            msg = MIMEText(mensaje)
            msg['Subject'] = 'Alerta SAT - Fecha Límite'
            msg['From'] = app.config['EMAIL_USER']
            msg['To'] = email
            server.send_message(msg)
    except Exception as e:
        app.logger.error(f"Error enviando email: {str(e)}")
        
@app.route('/')
def serve_frontend():
    return send_from_directory('src', 'index.html')
        
@app.route('/api/empresas', methods=['POST'])
def crear_empresa():
    data = request.get_json()
    nombre = data.get('nombre')
    rfc = data.get('rfc')
    if not nombre:
        return jsonify({'error': 'Faltan datos'}), 400

    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO empresas (nombre, rfc) VALUES (?, ?)', (nombre, rfc)
        )
        conn.commit()
        return jsonify({'id': cursor.lastrowid, 'message': 'Empresa registrada'}), 201

@app.route('/api/empresas', methods=['GET'])
def obtener_empresas():
    with get_db() as conn:
        empresas = conn.execute('SELECT * FROM empresas ORDER BY nombre').fetchall()
    return jsonify([dict(row) for row in empresas])


# Registrar nueva devolución o listar todas
@app.route('/api/devoluciones', methods=['GET', 'POST'])
def gestion_devoluciones():
    if request.method == 'POST':
        data = request.get_json()
        empresa_id = data.get('empresa')
        periodo = data.get('fecha_periodo')
        monto = data.get('monto')
        
        if not empresa_id or not periodo or not monto:
            return jsonify({'error': 'Datos incompletos'}), 400
        
        fecha_solicitud = data.get('fecha_solicitud') or fecha_hoy_local()
        fecha_limite = calcular_dias_habiles(fecha_solicitud)

        with get_db() as conn:
            cursor = conn.execute('''
                INSERT INTO devoluciones (fecha_solicitud, fecha_limite, empresa_id, periodo, monto)
                VALUES (?, ?, ?, ?, ?)
            ''', (fecha_solicitud, fecha_limite, empresa_id, periodo, monto))
            conn.commit()
            return jsonify({
                'id': cursor.lastrowid,
                'fecha_limite': fecha_limite,
                'message': 'Devolución registrada'
            }), 201
    else:
        with get_db() as conn:
            devoluciones = conn.execute('SELECT * FROM devoluciones ORDER BY fecha_solicitud DESC').fetchall()
            return jsonify([dict(row) for row in devoluciones])
        
def fecha_hoy_local():
    return datetime.now(ZoneInfo("America/Mexico_City")).strftime('%Y-%m-%d')


# Actualizar devolución (solvencias o estado)
@app.route('/api/devoluciones/<int:id>', methods=['PUT'])
def actualizar_devolucion(id):
    data = request.get_json()
    updates = {}
    campos_permitidos = {
        'req1_notificacion', 'req1_respuesta',
        'req2_notificacion', 'req2_respuesta',
        'estado'
    }
    for campo in campos_permitidos:
        if campo in data:
            updates[campo] = data[campo]
    if 'req1_respuesta' in updates or 'req2_respuesta' in updates:
        dias_restantes = 40
        if updates.get('req1_respuesta'):
            dias_restantes -= 5
        if updates.get('req2_respuesta'):
            dias_restantes -= 5
        updates['dias_restantes'] = max(dias_restantes, 0)
    with get_db() as conn:
        set_clause = ', '.join(f"{k} = ?" for k in updates)
        valores = list(updates.values()) + [id]
        conn.execute(f'''
            UPDATE devoluciones 
            SET {set_clause}
            WHERE id = ?
        ''', valores)
        conn.commit()
    return jsonify({'message': 'Actualizado correctamente'})

# Agregar requerimiento y enviar notificación
@app.route('/api/devoluciones/<int:id>/requerimientos', methods=['POST'])
def agregar_requerimiento(id):
    data = request.get_json()
    tipo = data.get('tipo')
    if tipo not in [1, 2]:
        return jsonify({'error': 'Tipo inválido. Use 1 o 2'}), 400
    dias_respuesta = 20 if tipo == 1 else 10
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    campo = 'req1_notificacion' if tipo == 1 else 'req2_notificacion'
    with get_db() as conn:
        conn.execute(f'''
            UPDATE devoluciones 
            SET {campo} = ?, dias_restantes = ?
            WHERE id = ?
        ''', (fecha_actual, dias_respuesta, id))
        devolucion = conn.execute(
            'SELECT fecha_solicitud, fecha_limite FROM devoluciones WHERE id = ?', (id,)
        ).fetchone()
        conn.commit()
    mensaje = f'''Nuevo Requerimiento SAT (Tipo {tipo})
Devolución ID: {id}
Fecha Solicitud: {devolucion['fecha_solicitud']}
Fecha Límite Original: {devolucion['fecha_limite']}'''
    try:
        enviar_alerta('destinatario@empresa.com', mensaje)
        notificador.enviar_alerta(id, tipo)
    except Exception as e:
        app.logger.error(f"Error enviando notificación: {str(e)}")
    return jsonify({
        'message': 'Requerimiento registrado',
        'fecha_notificacion': fecha_actual,
        'dias_para_responder': dias_respuesta
    })

# Calendario de eventos
@app.route('/api/devoluciones/calendario')
def get_calendario():
    with get_db() as conn:
        devoluciones = conn.execute('SELECT * FROM devoluciones').fetchall()
    eventos = []
    for d in devoluciones:
        eventos.append({
            'id': d['id'],
            'fecha_solicitud': d['fecha_solicitud'],
            'fecha_limite': d['fecha_limite'],
            'estado': d['estado'],
            'tipo': 'devolucion'
        })
        if d['req1_notificacion']:
            eventos.append({
                'id': f"{d['id']}-req1",
                'fecha_solicitud': d['req1_notificacion'],
                'fecha_limite': d['req1_respuesta'] or '',
                'estado': 'requerimiento',
                'tipo': 'requerimiento'
            })
        if d['req2_notificacion']:
            eventos.append({
                'id': f"{d['id']}-req2",
                'fecha_solicitud': d['req2_notificacion'],
                'fecha_limite': d['req2_respuesta'] or '',
                'estado': 'requerimiento',
                'tipo': 'requerimiento'
            })
    return jsonify(eventos)

# NUEVO: Obtener detalle con lógica de días y pausas
def contar_dias_habiles(inicio, fin, festivos):
    dias = 0
    actual = inicio
    while actual <= fin:
        if actual.weekday() < 5 and actual.strftime('%Y-%m-%d') not in festivos:
            dias += 1
        actual += timedelta(days=1)
    return dias

@app.route('/api/devoluciones/<int:devolucion_id>', methods=['GET'])
@app.route('/api/devoluciones/<int:devolucion_id>', methods=['GET'])
def obtener_devolucion(devolucion_id):
    try:
        conn = get_db()
        devolucion = conn.execute(
            'SELECT * FROM devoluciones WHERE id = ?', (devolucion_id,)
        ).fetchone()
        if not devolucion:
            conn.close()
            return abort(404, 'Devolución no encontrada')

        festivos = [row['fecha'] for row in conn.execute('SELECT fecha FROM festivos')]
        conn.close()

        hoy = datetime.now(ZoneInfo("America/Mexico_City")).date()
        fecha_solicitud = datetime.strptime(devolucion['fecha_solicitud'], '%Y-%m-%d').date()
        fecha_limite = datetime.strptime(devolucion['fecha_limite'], '%Y-%m-%d').date()

        req1_notif = devolucion['req1_notificacion']
        req1_resp = devolucion['req1_respuesta']
        req2_notif = devolucion['req2_notificacion']
        req2_resp = devolucion['req2_respuesta']

        pausa_actual = None
        dias_para_solventar = None
        en_pausa = False
        dias_transcurridos = 0
        segmentos = []

        if req1_notif and not req1_resp:
            notif = datetime.strptime(req1_notif, '%Y-%m-%d').date()
            en_pausa = True
            pausa_actual = 'req1'
            dias_para_solventar = 20 - contar_dias_habiles(notif, hoy, festivos)
            segmentos.append((fecha_solicitud, notif))
        elif req1_notif and req1_resp:
            notif = datetime.strptime(req1_notif, '%Y-%m-%d').date()
            resp = datetime.strptime(req1_resp, '%Y-%m-%d').date()
            segmentos.append((fecha_solicitud, notif))
            if req2_notif and not req2_resp:
                notif2 = datetime.strptime(req2_notif, '%Y-%m-%d').date()
                en_pausa = True
                pausa_actual = 'req2'
                dias_para_solventar = 10 - contar_dias_habiles(notif2, hoy, festivos)
                segmentos.append((resp, notif2))
            elif req2_notif and req2_resp:
                notif2 = datetime.strptime(req2_notif, '%Y-%m-%d').date()
                resp2 = datetime.strptime(req2_resp, '%Y-%m-%d').date()
                segmentos.append((resp, notif2))
                segmentos.append((resp2, hoy))
            else:
                segmentos.append((resp, hoy))
        else:
            segmentos.append((fecha_solicitud, hoy))

        for inicio, fin in segmentos:
            dias_transcurridos += contar_dias_habiles(inicio, fin, festivos)

        dias_restantes = max(0, 40 - dias_transcurridos)
        estado = 'vencido' if dias_transcurridos >= 40 else ('pausado_' + pausa_actual if en_pausa else 'en_proceso')

        resultado = dict(devolucion)
        resultado.update({
            'dias_transcurridos': dias_transcurridos,
            'dias_restantes': dias_restantes,
            'en_pausa': en_pausa,
            'pausa_actual': pausa_actual,
            'dias_para_solventar': dias_para_solventar,
            'estado_calculado': estado
        })

        return jsonify(resultado)

    except Exception as e:
        logging.exception("Error en /api/devoluciones/<id>")
        return jsonify({'error': 'Error interno en servidor', 'detalle': str(e)}), 500

# Ejecutar servidor
if __name__ == '__main__':
    init_db()
    from dotenv import load_dotenv
    load_dotenv()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
