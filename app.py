from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
from datetime import datetime, date
import sqlite3
import calendar
import locale
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de locale para fechas en español
try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'es_CL.UTF-8')  # Intentar con locale chileno
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'es_ES')  # Intentar sin UTF-8
        except locale.Error:
            # Si nada funciona, definimos los meses manualmente
            MESES = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            def obtener_nombre_mes(numero_mes):
                return MESES.get(numero_mes, '')

# Función para obtener el nombre del mes
def obtener_nombre_mes(numero_mes):
    try:
        # Crear una fecha con el mes deseado
        fecha = datetime(2000, numero_mes, 1)
        # Obtener el nombre del mes en español
        return fecha.strftime('%B').capitalize()
    except:
        # Si falla, usar el diccionario de respaldo
        return MESES.get(numero_mes, '')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # Usar variable de entorno o generar una clave
DB_PATH = "asistencia_multiples_cursos.db"

# Asegurarse de que la tabla de usuarios existe al iniciar la aplicación
def init_db():
    logger.info('Inicializando base de datos...')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Crear tabla de usuarios si no existe
    c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nombre TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('admin', 'usuario')) NOT NULL DEFAULT 'usuario',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    logger.info('Tabla de usuarios verificada')
    
    # Verificar si existe un administrador
    admin = c.execute('SELECT id FROM usuarios WHERE rol = "admin" LIMIT 1').fetchone()
    
    # Si no hay admin, crear uno por defecto
    if not admin:
        try:
            c.execute('''
            INSERT INTO usuarios (username, password, nombre, rol)
            VALUES (?, ?, ?, ?)
            ''', ('admin', generate_password_hash('admin123'), 'Administrador', 'admin'))
            conn.commit()
            logger.info('Usuario administrador creado exitosamente')
        except sqlite3.IntegrityError:
            logger.warning('Ya existe un usuario con el nombre admin')
    else:
        logger.info('Ya existe un usuario administrador')
    
    conn.close()

# Inicializar la base de datos al arrancar
init_db()

# Decorator para requerir autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator para requerir rol de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash('No tienes permisos para acceder a esta función', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.info('Accediendo a la página de login')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logger.info(f'Intento de login para usuario: {username}')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        user = c.execute('SELECT id, password, rol FROM usuarios WHERE username = ?', 
                        (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['user_role'] = user[2]
            logger.info(f'Login exitoso para usuario: {username} con rol: {user[2]}')
            return redirect(url_for('index'))
        
        logger.warning(f'Login fallido para usuario: {username}')
        flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nombre = request.form['nombre']
        rol = request.form['rol']
        
        if session['user_role'] != 'admin':
            flash('No tienes permisos para crear usuarios', 'error')
            return redirect(url_for('index'))
        
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, ?)',
                     (username, generate_password_hash(password), nombre, rol))
            conn.commit()
            conn.close()
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('admin_panel'))
        except sqlite3.IntegrityError:
            flash('El nombre de usuario ya existe', 'error')
        except Exception as e:
            flash('Error al crear usuario', 'error')
            
    return render_template('register.html')

@app.route('/admin')
@admin_required
def admin_panel():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    users = c.execute('SELECT id, username, nombre, rol, created_at FROM usuarios').fetchall()
    conn.close()
    return render_template('admin.html', users=users)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def root():
    logger.info('Accediendo a la ruta raíz')
    if 'user_id' not in session:
        logger.info('Usuario no autenticado, redirigiendo a login')
        return redirect(url_for('login'))
    logger.info('Usuario autenticado, redirigiendo a index')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def index():
    conn = get_db_connection()
    cursos = conn.execute('SELECT * FROM cursos ORDER BY nombre').fetchall()
    conn.close()
    return render_template('index.html', cursos=cursos)

@app.route('/curso/<int:id>')
@login_required
def get_curso(id):
    conn = get_db_connection()
    curso = conn.execute('SELECT * FROM cursos WHERE id = ?', (id,)).fetchone()
    conn.close()
    if curso:
        return jsonify({
            'id': curso['id'],
            'nombre': curso['nombre'],
            'año': curso['año']
        })
    return jsonify({'error': 'Curso no encontrado'}), 404

@app.route('/guardar_curso', methods=['POST'])
@login_required
def guardar_curso():
    try:
        curso_id = request.form.get('id')
        nombre = request.form.get('nombre')
        año = request.form.get('año')
        
        conn = get_db_connection()
        
        if curso_id:  # Actualizar curso existente
            conn.execute('UPDATE cursos SET nombre = ?, año = ? WHERE id = ?',
                        (nombre, año, curso_id))
        else:  # Crear nuevo curso
            cur = conn.execute('INSERT INTO cursos (nombre, año) VALUES (?, ?)',
                             (nombre, año))
            curso_id = cur.lastrowid
        
        # Procesar lista de alumnos si se proporcionó
        if 'lista_alumnos' in request.files:
            archivo = request.files['lista_alumnos']
            if archivo:
                contenido = archivo.read().decode('utf-8')
                nombres = [nombre.strip() for nombre in contenido.split('\n') if nombre.strip()]
                
                # Eliminar alumnos existentes si es una actualización
                if curso_id:
                    conn.execute('DELETE FROM alumnos WHERE id_curso = ?', (curso_id,))
                
                # Insertar nuevos alumnos
                for nombre in nombres:
                    conn.execute('INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)',
                               (nombre, curso_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/asistencia/<int:curso_id>')
@login_required
def asistencia(curso_id):
    conn = get_db_connection()
    curso = conn.execute('SELECT * FROM cursos WHERE id = ?', (curso_id,)).fetchone()
    alumnos = conn.execute('SELECT * FROM alumnos WHERE id_curso = ? ORDER BY nombre', (curso_id,)).fetchall()
    
    # Get current month and year
    today = date.today()
    month = request.args.get('month', type=int, default=today.month)
    year = request.args.get('year', type=int, default=today.year)
    
    # Get weekdays for current month
    cal = calendar.monthcalendar(year, month)
    weekdays = []
    for week in cal:
        for day in week:
            if day != 0 and date(year, month, day).weekday() < 5:  # Monday to Friday
                weekdays.append(day)
    
    # Get attendance data
    attendance_data = {}
    for alumno in alumnos:
        attendance_data[alumno['id']] = {}
        for day in weekdays:
            fecha = f"{year}-{month:02d}-{day:02d}"
            asistencia = conn.execute(
                'SELECT presente FROM asistencia WHERE id_alumno = ? AND fecha = ?',
                (alumno['id'], fecha)
            ).fetchone()
            attendance_data[alumno['id']][day] = asistencia['presente'] if asistencia else None
    
    conn.close()
    
    # Obtener el nombre del mes en español
    mes_nombre = obtener_nombre_mes(month)
    
    return render_template('asistencia.html', 
                         curso=curso, 
                         alumnos=alumnos, 
                         weekdays=weekdays,
                         attendance=attendance_data,
                         month=month,
                         year=year,
                         month_name=mes_nombre,
                         calendar=calendar)

@app.route('/dashboard/<int:curso_id>')
@login_required
def dashboard(curso_id):
    conn = get_db_connection()
    curso = conn.execute('SELECT * FROM cursos WHERE id = ?', (curso_id,)).fetchone()
    
    # Get statistics
    total_alumnos = conn.execute('SELECT COUNT(*) FROM alumnos WHERE id_curso = ?', (curso_id,)).fetchone()[0]
    dias_registrados = conn.execute('''
        SELECT COUNT(DISTINCT fecha) FROM asistencia 
        WHERE id_alumno IN (SELECT id FROM alumnos WHERE id_curso = ?)
    ''', (curso_id,)).fetchone()[0]
    
    # Get detailed attendance data
    alumnos_data = []
    alumnos = conn.execute('SELECT * FROM alumnos WHERE id_curso = ? ORDER BY nombre', (curso_id,)).fetchall()
    
    for alumno in alumnos:
        presentes = conn.execute('''
            SELECT COUNT(*) FROM asistencia 
            WHERE id_alumno = ? AND presente = 1
        ''', (alumno['id'],)).fetchone()[0]
        
        ultima_asistencia = conn.execute('''
            SELECT fecha FROM asistencia 
            WHERE id_alumno = ? AND presente = 1 
            ORDER BY fecha DESC LIMIT 1
        ''', (alumno['id'],)).fetchone()
        
        porcentaje = (presentes / dias_registrados * 100) if dias_registrados > 0 else 0
        
        alumnos_data.append({
            'id': alumno['id'],
            'nombre': alumno['nombre'],
            'dias_presentes': presentes,
            'dias_totales': dias_registrados,
            'porcentaje': porcentaje,
            'ultima_asistencia': ultima_asistencia[0] if ultima_asistencia else 'Sin asistencias',
            'estado': 'Regular' if porcentaje >= 75 else 'En Riesgo' if porcentaje > 0 else 'No Asiste'
        })
    
    conn.close()
    return render_template('dashboard.html',
                         curso=curso,
                         total_alumnos=total_alumnos,
                         dias_registrados=dias_registrados,
                         alumnos_data=alumnos_data)

@app.route('/save_attendance', methods=['POST'])
@login_required
def save_attendance():
    data = request.json
    conn = get_db_connection()
    
    try:
        for alumno_id, fechas in data['attendance'].items():
            for fecha, presente in fechas.items():
                conn.execute('''
                    INSERT OR REPLACE INTO asistencia (id_alumno, fecha, presente)
                    VALUES (?, ?, ?)
                ''', (int(alumno_id), fecha, presente))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

def generar_pdf(curso_id, mes, año):
    # Crear un buffer para el PDF
    buffer = BytesIO()
    
    # Crear el documento PDF con márgenes amplios
    doc = SimpleDocTemplate(buffer,
                          pagesize=letter,
                          leftMargin=72,    # 1 pulgada = 72 puntos
                          rightMargin=72,
                          topMargin=72,
                          bottomMargin=72)

    # Lista para almacenar los elementos del PDF
    elements = []
    styles = getSampleStyleSheet()

    # Crear tabla para el encabezado (logo y texto)
    logo_path = os.path.join('static', 'logo.png')
    if os.path.exists(logo_path):
        logo_img = Image(logo_path)
        logo_img.drawHeight = 50
        logo_img.drawWidth = 50
    else:
        logo_img = Paragraph("LOGO", styles['Title'])

    # Estilo personalizado para el encabezado
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        alignment=0  # 0=izquierda
    )

    header_text = Paragraph("""
        <para>
        <b>CEIA Amigos del Padre Hurtado</b><br/>
        <b>La Serena</b><br/>
        <font size=10>Reporte de Asistencia - {mes} {año}</font>
        </para>
    """.format(mes=obtener_nombre_mes(mes), año=año), header_style)

    # Tabla de encabezado con logo y texto
    header_table = Table([[logo_img, header_text]], colWidths=[60, None])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (1, 0), (1, 0), 20),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 30))

    # Obtener datos del curso y asistencia
    conn = get_db_connection()
    curso = conn.execute('SELECT nombre FROM cursos WHERE id = ?', (curso_id,)).fetchone()
    
    # Título del curso centrado
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=14,
        alignment=1  # Centrado
    )
    elements.append(Paragraph(f"Curso: {curso['nombre']}", title_style))
    elements.append(Spacer(1, 20))

    # Obtener datos de asistencia
    alumnos = conn.execute('''
        SELECT a.*, 
               COUNT(CASE WHEN ast.presente = 1 THEN 1 END) as presentes,
               COUNT(DISTINCT ast.fecha) as total_dias,
               MAX(CASE WHEN ast.presente = 1 THEN ast.fecha END) as ultima_asistencia
        FROM alumnos a
        LEFT JOIN asistencia ast ON a.id = ast.id_alumno
        WHERE a.id_curso = ?
        AND strftime('%Y-%m', ast.fecha) = ?
        GROUP BY a.id
        ORDER BY a.nombre
    ''', (curso_id, f"{año}-{mes:02d}")).fetchall()

    # Crear tabla de asistencia
    data = [['Alumno', 'Días\nPresentes', 'Días\nTotales', '% Asistencia', 'Última\nAsistencia', 'Estado']]
    
    for alumno in alumnos:
        porcentaje = (alumno['presentes'] / alumno['total_dias'] * 100) if alumno['total_dias'] > 0 else 0
        estado = 'Regular' if porcentaje >= 75 else 'En Riesgo' if porcentaje > 0 else 'No Asiste'
        
        # Formatear fecha
        ultima_asistencia = alumno['ultima_asistencia']
        if ultima_asistencia:
            fecha = datetime.strptime(ultima_asistencia, '%Y-%m-%d')
            ultima_asistencia = fecha.strftime('%d/%m/%Y')
        else:
            ultima_asistencia = 'Sin asistencias'

        data.append([
            alumno['nombre'],
            str(alumno['presentes']),
            str(alumno['total_dias']),
            f"{porcentaje:.1f}%",
            ultima_asistencia,
            estado
        ])

    # Calcular el ancho disponible para la tabla (página - márgenes)
    available_width = letter[0] - doc.leftMargin - doc.rightMargin
    col_widths = [
        available_width * 0.30,  # Nombre 30%
        available_width * 0.12,  # Días Presentes 12%
        available_width * 0.12,  # Días Totales 12%
        available_width * 0.15,  # % Asistencia 15%
        available_width * 0.18,  # Última Asistencia 18%
        available_width * 0.13   # Estado 13%
    ]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table_style = TableStyle([
        # Estilo del encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),  # Encabezado más pequeño
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Estilo del contenido
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Contenido más pequeño
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # Nombres a la izquierda
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Resto centrado
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),    # Menos padding
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),   # Padding lateral
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ])
    table.setStyle(table_style)

    # Agregar colores según estado
    for i in range(1, len(data)):
        estado = data[i][-1]
        if estado == 'Regular':
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#E8F5E9'))  # Verde claro
            ]))
        elif estado == 'En Riesgo':
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FFEBEE'))  # Rojo claro
            ]))
        else:  # No Asiste
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#FAFAFA'))  # Gris muy claro
            ]))

    elements.append(table)
    elements.append(Spacer(1, 40))

    # Agregar línea de firma
    elements.append(Paragraph("_" * 40, styles['Normal']))
    elements.append(Paragraph("Inspectoría - Marcelo Munizaga", styles['Normal']))

    # Construir el PDF
    doc.build(elements)
    
    # Obtener el valor del buffer
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

@app.route('/export_pdf/<int:curso_id>')
@login_required
def export_pdf(curso_id):
    conn = get_db_connection()
    curso = conn.execute('SELECT * FROM cursos WHERE id = ?', (curso_id,)).fetchone()
    
    # Obtener el mes actual o el especificado
    month = request.args.get('month', type=int, default=date.today().month)
    year = request.args.get('year', type=int, default=date.today().year)
    mes_nombre = obtener_nombre_mes(month)
    
    pdf = generar_pdf(curso_id, month, year)
    
    conn.close()
    return send_file(
        BytesIO(pdf),
        download_name=f'reporte_{curso["nombre"]}_{mes_nombre}_{year}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

@app.route('/curso/<int:id>/alumnos')
@login_required
def gestionar_alumnos(id):
    conn = get_db_connection()
    curso = conn.execute('SELECT * FROM cursos WHERE id = ?', (id,)).fetchone()
    alumnos = conn.execute('SELECT * FROM alumnos WHERE id_curso = ? ORDER BY nombre', (id,)).fetchall()
    conn.close()
    return render_template('alumnos.html', curso=curso, alumnos=alumnos)

@app.route('/actualizar_alumno', methods=['POST'])
@login_required
def actualizar_alumno():
    try:
        data = request.json
        conn = get_db_connection()
        conn.execute('UPDATE alumnos SET nombre = ? WHERE id = ?',
                    (data['nombre'], data['id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/eliminar_alumno', methods=['POST'])
@login_required
def eliminar_alumno():
    try:
        data = request.json
        conn = get_db_connection()
        # Primero eliminamos las asistencias del alumno
        conn.execute('DELETE FROM asistencia WHERE id_alumno = ?', (data['id'],))
        # Luego eliminamos al alumno
        conn.execute('DELETE FROM alumnos WHERE id = ?', (data['id'],))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/agregar_alumno', methods=['POST'])
@login_required
def agregar_alumno():
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.execute('INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)',
                         (data['nombre'], data['curso_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/importar_alumnos', methods=['POST'])
@login_required
def importar_alumnos():
    try:
        curso_id = request.form.get('curso_id')
        if 'lista_alumnos' not in request.files:
            return jsonify({'success': False, 'error': 'No se proporcionó archivo'})
        
        archivo = request.files['lista_alumnos']
        if archivo:
            contenido = archivo.read().decode('utf-8')
            nombres = [nombre.strip() for nombre in contenido.split('\n') if nombre.strip()]
            
            conn = get_db_connection()
            for nombre in nombres:
                conn.execute('INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)',
                           (nombre, curso_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f'Iniciando aplicación en puerto {port}')
    app.run(host='0.0.0.0', port=port)
