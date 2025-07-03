import os
from datetime import datetime
from fpdf import FPDF
from jinja2 import Environment, FileSystemLoader
import sqlite3
from contextlib import closing

class PDFGenerator:
    def __init__(self, output_dir='pdf_output'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Configurar Jinja2 para plantillas
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )

    def _get_devolucion_data(self, devolucion_id):
        """Obtiene datos de la devolución desde la base de datos"""
        with closing(sqlite3.connect('devoluciones.db')) as conn:
            conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            cursor = conn.cursor()
            
            # Obtener datos básicos de la devolución
            cursor.execute('''
                SELECT id, fecha_solicitud, fecha_limite, estado, dias_restantes
                FROM devoluciones
                WHERE id = ?
            ''', (devolucion_id,))
            devolucion = cursor.fetchone()
            
            if not devolucion:
                raise ValueError(f"Devolución {devolucion_id} no encontrada")
            
            # Obtener requerimientos asociados
            cursor.execute('''
                SELECT 
                    req1_notificacion as notificacion1,
                    req1_respuesta as respuesta1,
                    req2_notificacion as notificacion2,
                    req2_respuesta as respuesta2
                FROM devoluciones
                WHERE id = ?
            ''', (devolucion_id,))
            requerimientos = cursor.fetchone()
            
            return {
                'devolucion': dict(devolucion),
                'requerimientos': dict(requerimientos) if requerimientos else None
            }

    def generate_devolucion_pdf(self, devolucion_id):
        """Genera un PDF con los detalles de la devolución"""
        try:
            # Obtener datos
            data = self._get_devolucion_data(devolucion_id)
            data['fecha_generacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Renderizar plantilla HTML
            template = self.env.get_template('devolucion_template.html')
            html_content = template.render(data)
            
            # Crear PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            
            # Convertir HTML a PDF
            pdf.write_html(html_content)
            
            # Guardar archivo
            filename = f"devolucion_{devolucion_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            pdf.output(filepath)
            
            return filepath
            
        except Exception as e:
            print(f"Error generando PDF: {str(e)}")
            raise

    def generate_requerimiento_pdf(self, devolucion_id, tipo_requerimiento):
        """Genera un PDF para un requerimiento específico"""
        try:
            data = self._get_devolucion_data(devolucion_id)
            data.update({
                'tipo_requerimiento': tipo_requerimiento,
                'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            template = self.env.get_template('requerimiento_template.html')
            html_content = template.render(data)
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            pdf.write_html(html_content)
            
            filename = f"req_{tipo_requerimiento}_devolucion_{devolucion_id}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            pdf.output(filepath)
            
            return filepath
            
        except Exception as e:
            print(f"Error generando PDF de requerimiento: {str(e)}")
            raise