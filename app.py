from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
from datetime import datetime, date, timedelta
import sqlite3
import calendar
import os
import logging
import json
from functools import wraps
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from werkzeug.security import generate_password_hash, check_password_hash

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Definir la ruta de la base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'asistencia_multiples_cursos.db')

def get_db_connection():
    """Obtiene una conexión a la base de datos SQLite"""
    # Asegurarse de que el directorio de la base de datos existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Crear la conexión
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Si la base de datos está vacía, inicializarla
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    if not cursor.fetchall():
        init_db()
    
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas necesarias"""
    logger.info('Inicializando base de datos...')
    conn = sqlite3.connect(DB_PATH)
    
    # Leer el esquema SQL
    with open('schema.sql', 'r') as f:
        schema = f.read()
    
    # Ejecutar el esquema
    conn.executescript(schema)
    
    # Verificar si existe un usuario admin
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = ?', ('admin',))
    admin = cursor.fetchone()
    
    # Si no existe el admin, crearlo
    if not admin:
        logger.info('Creando usuario admin...')
        cursor.execute('''
            INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, ?)
        ''', ('admin', generate_password_hash('admin'), 'Administrador', 'admin'))
    
    conn.commit()
    conn.close()
    logger.info('Base de datos inicializada correctamente')

# Función para obtener el nombre del mes
def obtener_nombre_mes(mes):
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    if isinstance(mes, str):
        for key, value in meses.items():
            if value.lower() == mes.lower():
                return value
        return ''
    else:
        return meses.get(int(mes), '')

app = Flask(__name__,
          static_folder='static',
          static_url_path='/static',
          template_folder='templates')

# Configuración de la aplicación
app.secret_key = os.environ.get('SECRET_KEY', 'tu_clave_secreta_aqui')
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

# Asegurarse de que existan las carpetas necesarias
for folder in ['static', 'templates']:
    folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.info(f'Carpeta {folder} creada en {folder_path}')

# Verificar permisos de escritura
try:
    with open(DB_PATH, 'a'):
        pass
    logger.info('Permisos de escritura verificados para la base de datos')
except IOError as e:
    logger.error(f'Error de permisos en la base de datos: {str(e)}')

@app.route('/')
def root():
    try:
        logger.info('Accediendo a la ruta raíz')
        if 'user_id' not in session:
            logger.info('Usuario no autenticado, redirigiendo a login')
            return render_template('login.html')
        logger.info('Usuario autenticado, redirigiendo a index')
        return redirect(url_for('index'))
    except Exception as e:
        error_msg = f'Error en ruta raíz: {str(e)}'
        logger.error(error_msg)
        return error_msg, 500

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
    try:
        logger.info('Accediendo a la página de login')
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            logger.info(f'Intento de login para usuario: {username}')
            
            conn = get_db_connection()
            c = conn.cursor()
            user = c.execute('SELECT id, password, rol FROM usuarios WHERE username = ?', (username,)).fetchone()
            conn.close()
            
            if user:
                try:
                    from werkzeug.security import check_password_hash
                    if check_password_hash(user[1], password):
                        session['user_id'] = user[0]
                        session['username'] = username
                        session['user_role'] = user[2]
                        logger.info(f'Login exitoso para usuario: {username} con rol: {user[2]}')
                        return redirect(url_for('index'))
                except Exception as hash_error:
                    logger.error(f'Error al verificar contraseña: {str(hash_error)}')
                    # Si hay error con el hash, intentar comparación directa para admin
                    if username == 'admin' and password == 'admin':
                        session['user_id'] = user[0]
                        session['username'] = username
                        session['user_role'] = user[2]
                        logger.info('Login exitoso para admin usando credenciales por defecto')
                        return redirect(url_for('index'))
            
            logger.warning(f'Login fallido para usuario: {username}')
            flash('Usuario o contraseña incorrectos', 'error')
        return render_template('login.html')
    except Exception as e:
        logger.error(f'Error en login: {str(e)}')
        return f'Error: {str(e)}', 500

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
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, ?)', (username, generate_password_hash(password), nombre, rol))
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
    conn = get_db_connection()
    c = conn.cursor()
    users = c.execute('SELECT id, username, nombre, rol, created_at FROM usuarios').fetchall()
    conn.close()
    return render_template('admin.html', users=users)

@app.route('/test')
def test():
    return 'Prueba de ruta - Si ves esto, Flask está funcionando correctamente'

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
            conn.execute('UPDATE cursos SET nombre = ?, año = ? WHERE id = ?', (nombre, año, curso_id))
        else:  # Crear nuevo curso
            cur = conn.execute('INSERT INTO cursos (nombre, año) VALUES (?, ?)', (nombre, año))
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
                    conn.execute('INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)', (nombre, curso_id))
        
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
    if not curso:
        conn.close()
        flash('Curso no encontrado', 'error')
        return redirect(url_for('index'))
    
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
    
    # Get attendance data with a single SQL query
    attendance_data = {}
    for alumno in alumnos:
        attendance_data[alumno['id']] = {}
        # Construir la fecha en el formato correcto para SQLite
        fecha_inicio = f"{year}-{month:02d}-01"
        fecha_fin = f"{year}-{month:02d}-31"
        
        # Obtener todas las asistencias del mes para el alumno
        asistencias = conn.execute('''
            SELECT fecha, presente 
            FROM asistencia 
            WHERE id_alumno = ? 
            AND fecha BETWEEN ? AND ?
        ''', (alumno['id'], fecha_inicio, fecha_fin)).fetchall()
        
        # Inicializar todos los días como None
        for day in weekdays:
            attendance_data[alumno['id']][day] = None
        
        # Actualizar con los datos existentes
        for asistencia in asistencias:
            fecha = datetime.strptime(asistencia['fecha'], '%Y-%m-%d')
            if fecha.day in weekdays:
                attendance_data[alumno['id']][fecha.day] = asistencia['presente']
    
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
    # Obtener mes y año de los parámetros o usar el actual
    mes_actual = int(request.args.get('month', datetime.now().month))
    año_actual = int(request.args.get('year', datetime.now().year))
    
    # Nombres de meses en español
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    conn = get_db_connection()
    curso = conn.execute('SELECT * FROM cursos WHERE id = ?', (curso_id,)).fetchone()
    
    # Obtener días hábiles del mes (excluyendo sábados y domingos)
    dias_habiles = []
    num_dias = calendar.monthrange(año_actual, mes_actual)[1]
    for dia in range(1, num_dias + 1):
        fecha = date(año_actual, mes_actual, dia)
        if fecha.weekday() < 5:  # 0-4 son Lunes a Viernes
            dias_habiles.append(fecha)
    
    # Obtener asistencias del mes para todos los alumnos
    alumnos_data = []
    alumnos = conn.execute('SELECT * FROM alumnos WHERE id_curso = ? ORDER BY nombre', (curso_id,)).fetchall()
    
    for alumno in alumnos:
        # Obtener asistencias del mes para este alumno
        asistencias = conn.execute('''
            SELECT DISTINCT fecha 
            FROM asistencia 
            WHERE id_alumno = ? 
            AND strftime('%Y-%m', fecha) = ?
            AND presente = 1
            GROUP BY fecha
        ''', (alumno['id'], f"{año_actual}-{mes_actual:02d}")).fetchall()
        
        # Obtener la última asistencia del alumno
        ultima_asistencia = conn.execute('''
            SELECT fecha 
            FROM asistencia 
            WHERE id_alumno = ? 
            AND presente = 1 
            ORDER BY fecha DESC LIMIT 1
        ''', (alumno['id'],)).fetchone()
        
        # Contar días presentes
        dias_presentes = len(asistencias)
        
        # Calcular porcentaje
        total_dias_habiles = len(dias_habiles)
        porcentaje = (dias_presentes / total_dias_habiles * 100) if total_dias_habiles > 0 else 0
        
        # Determinar estado
        estado = 'Regular' if porcentaje >= 50 else 'En Riesgo' if porcentaje >= 25 else 'No Asiste'
        
        # Agregar datos del alumno
        alumnos_data.append({
            'nombre': alumno['nombre'],
            'dias_presentes': dias_presentes,
            'dias_totales': total_dias_habiles,
            'porcentaje': porcentaje,
            'ultima_asistencia': ultima_asistencia['fecha'] if ultima_asistencia else None,
            'estado': estado
        })
    
    return render_template('dashboard.html', 
                         curso=curso, 
                         alumnos_data=alumnos_data,
                         mes_actual=mes_actual,
                         año_actual=año_actual,
                         meses=meses)

@app.route('/save_attendance', methods=['POST'])
@login_required
def save_attendance():
    try:
        data = request.get_json()
        attendance = data.get('attendance', {})
        
        conn = get_db_connection()
        
        # Procesar cada alumno
        for alumno_id, fechas in attendance.items():
            # Procesar cada fecha
            for fecha, presente in fechas.items():
                # Si el valor es null, eliminar el registro si existe
                if presente is None:
                    conn.execute('''
                        DELETE FROM asistencia 
                        WHERE id_alumno = ? AND fecha = ?
                    ''', (alumno_id, fecha))
                else:
                    # Intentar actualizar primero
                    result = conn.execute('''
                        UPDATE asistencia 
                        SET presente = ? 
                        WHERE id_alumno = ? AND fecha = ?
                    ''', (presente, alumno_id, fecha))
                    
                    # Si no se actualizó ningún registro, insertar uno nuevo
                    if result.rowcount == 0:
                        conn.execute('''
                            INSERT INTO asistencia (id_alumno, fecha, presente)
                            VALUES (?, ?, ?)
                        ''', (alumno_id, fecha, presente))
                
                app.logger.info(f'Asistencia {"eliminada" if presente is None else "guardada"}: alumno={alumno_id}, fecha={fecha}, presente={presente}')
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f'Error al guardar asistencia: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/exportar_asistencia_pdf/<int:curso_id>')
@login_required
def exportar_asistencia_pdf(curso_id):
    # Obtener mes y año de los parámetros
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    if not month or not year:
        return "Mes y año son requeridos", 400
        
    conn = get_db_connection()
    curso = conn.execute('SELECT nombre FROM cursos WHERE id = ?', (curso_id,)).fetchone()
    
    # Obtener todos los días del mes
    num_days = calendar.monthrange(year, month)[1]
    all_days = [date(year, month, day) for day in range(1, num_days + 1)]
    weekdays = [day for day in all_days if day.weekday() < 5]  # 0-4 son lunes a viernes
    
    # Obtener alumnos
    alumnos = conn.execute('''
        SELECT id, nombre 
        FROM alumnos 
        WHERE id_curso = ? 
        ORDER BY nombre
    ''', (curso_id,)).fetchall()

    # Preparar datos para el PDF
    data = []
    for i, alumno in enumerate(alumnos, 1):
        # Obtener asistencias del mes
        asistencias = conn.execute('''
            SELECT fecha, presente 
            FROM asistencia 
            WHERE id_alumno = ? 
            AND strftime('%Y-%m', fecha) = ?
        ''', (alumno['id'], f"{year}-{month:02d}")).fetchall()
        
        # Convertir a diccionario para fácil acceso
        asistencias_dict = {a['fecha']: a['presente'] for a in asistencias}
        
        # Preparar fila con asistencias diarias
        asistencias_row = []
        for day in weekdays:
            fecha = day.strftime('%Y-%m-%d')
            if fecha in asistencias_dict:
                asistencias_row.append('✓' if asistencias_dict[fecha] == 1 else '✗')
            else:
                asistencias_row.append('')
        
        # Agregar fila a la tabla con número de alumno (usando el índice)
        data.append([
            str(i),  # Número correlativo
            alumno['nombre'],  # Nombre
        ] + asistencias_row)

    # Crear PDF con ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(letter),
        leftMargin=15,
        rightMargin=15,
        topMargin=20,
        bottomMargin=20
    )
    elements = []

    # Obtener estilos
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']

    # Título y subtítulos
    elements.append(Paragraph("CEIA Amigos del Padre Hurtado", title_style))
    elements.append(Paragraph("La Serena", normal_style))
    elements.append(Paragraph(f"Registro de Asistencia - {calendar.month_name[month]} {year}", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Curso: {curso['nombre']}", normal_style))
    elements.append(Spacer(1, 10))

    # Crear tabla
    # Encabezados con fechas
    headers = ['N°', 'Alumno'] + [d.strftime('%d') for d in weekdays]
    
    # Estilo de la tabla
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),  # Tamaño más pequeño
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Centrar números
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # Alinear nombres a la izquierda
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'), # Centrar días
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),     # Tamaño más pequeño
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ])

    # Crear y agregar tabla
    # Calcular ancho de columnas
    available_width = landscape(letter)[0] - 30  # 30 es la suma de márgenes izquierdo y derecho
    col_widths = [20]  # N° alumno
    col_widths.append(available_width * 0.3)  # Nombre (30% del espacio)
    remaining_width = available_width * 0.7  # 70% restante para los días
    day_width = remaining_width / len(weekdays)
    col_widths.extend([day_width] * len(weekdays))

    t = Table([headers] + data, colWidths=col_widths)
    t.setStyle(table_style)
    elements.append(t)

    # Generar PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    return send_file(
        BytesIO(pdf),
        download_name=f'asistencia_{curso["nombre"]}_{calendar.month_name[month]}_{year}.pdf',
        mimetype='application/pdf'
    )

@app.route('/exportar_pdf/<int:curso_id>')
@login_required
def exportar_pdf(curso_id):
    conn = get_db_connection()
    curso = conn.execute('SELECT nombre FROM cursos WHERE id = ?', (curso_id,)).fetchone()
    
    # Obtener mes y año de los parámetros o usar el actual
    mes_actual = int(request.args.get('month', datetime.now().month))
    año_actual = int(request.args.get('year', datetime.now().year))
    
    # Obtener días hábiles del mes (excluyendo sábados y domingos)
    dias_habiles = []
    num_dias = calendar.monthrange(año_actual, mes_actual)[1]
    for dia in range(1, num_dias + 1):
        fecha = date(año_actual, mes_actual, dia)
        if fecha.weekday() < 5:  # 0-4 son Lunes a Viernes
            dias_habiles.append(fecha)
    
    total_dias_habiles = len(dias_habiles)
    
    # Obtener datos de alumnos
    alumnos = conn.execute('''
        SELECT id, nombre 
        FROM alumnos 
        WHERE id_curso = ? 
        ORDER BY nombre
    ''', (curso_id,)).fetchall()

    # Preparar datos para el PDF
    data = []
    for i, alumno in enumerate(alumnos, 1):
        # Obtener asistencias del mes para este alumno
        asistencias = conn.execute('''
            SELECT DISTINCT fecha 
            FROM asistencia 
            WHERE id_alumno = ? 
            AND strftime('%Y-%m', fecha) = ?
            AND presente = 1
            GROUP BY fecha
        ''', (alumno['id'], f"{año_actual}-{mes_actual:02d}")).fetchall()
        
        # Obtener la última asistencia del alumno
        ultima_asistencia = conn.execute('''
            SELECT fecha 
            FROM asistencia 
            WHERE id_alumno = ? 
            AND presente = 1 
            ORDER BY fecha DESC LIMIT 1
        ''', (alumno['id'],)).fetchone()
        
        # Contar días presentes
        dias_presentes = len(asistencias)
        
        # Calcular porcentaje
        porcentaje = (dias_presentes / total_dias_habiles * 100) if total_dias_habiles > 0 else 0
        
        # Agregar fila a la tabla
        data.append([
            str(i),  # Número correlativo
            alumno['nombre'],
            str(dias_presentes),
            str(total_dias_habiles),
            f"{porcentaje:.1f}%",
            ultima_asistencia['fecha'] if ultima_asistencia else 'Sin asistencias',
            'Regular' if porcentaje >= 50 else 'En Riesgo' if porcentaje >= 25 else 'No Asiste'
        ])

    # Crear PDF con ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Obtener estilos
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    heading_style = styles['Heading1']

    # Agregar logo y encabezado
    logo_path = os.path.join(app.root_path, 'static', 'logo.png')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=60, height=60)
        elements.append(img)

    # Título y subtítulos
    elements.append(Paragraph("CEIA Amigos del Padre Hurtado", title_style))
    elements.append(Paragraph("La Serena", normal_style))
    elements.append(Paragraph(f"Reporte de Asistencia - {calendar.month_name[mes_actual]} {año_actual}", normal_style))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Curso: {curso['nombre']}", heading_style))
    elements.append(Spacer(1, 20))

    # Crear tabla
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ])

    # Colorear filas según estado
    for i in range(len(data)):
        if data[i][-1] == 'Regular':
            table_style.add('BACKGROUND', (0, i+1), (-1, i+1), colors.lightgreen)
        elif data[i][-1] == 'En Riesgo':
            table_style.add('BACKGROUND', (0, i+1), (-1, i+1), colors.lightgoldenrodyellow)
        else:  # No Asiste
            table_style.add('BACKGROUND', (0, i+1), (-1, i+1), colors.lightcoral)

    # Crear y agregar tabla
    headers = ['N°', 'Alumno', 'Días\nPresentes', 'Días\nTotales', '% Asistencia', 'Última\nAsistencia', 'Estado']
    t = Table([headers] + data)
    t.setStyle(table_style)
    elements.append(t)

    # Generar PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    return send_file(
        BytesIO(pdf),
        download_name=f'reporte_{curso["nombre"]}_{calendar.month_name[mes_actual]}_{año_actual}.pdf',
        mimetype='application/pdf'
    )

@app.route('/exportar_lista/<int:curso_id>')
@login_required
def exportar_lista(curso_id):
    # Obtener mes y año de los parámetros o usar el actual
    mes_actual = int(request.args.get('month', datetime.now().month))
    año_actual = int(request.args.get('year', datetime.now().year))
    
    conn = get_db_connection()
    curso = conn.execute('SELECT nombre FROM cursos WHERE id = ?', (curso_id,)).fetchone()
    
    # Obtener alumnos
    alumnos = conn.execute('''
        SELECT nombre 
        FROM alumnos 
        WHERE id_curso = ? 
        ORDER BY nombre
    ''', (curso_id,)).fetchall()
    
    # Nombres de meses en español
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Obtener todos los días del mes (excepto sábados y domingos)
    dias_mes = []
    num_dias = calendar.monthrange(año_actual, mes_actual)[1]
    for dia in range(1, num_dias + 1):
        fecha = date(año_actual, mes_actual, dia)
        if fecha.weekday() < 5:  # 0-4 son Lunes a Viernes
            dias_mes.append(fecha)
    
    # Dividir alumnos en dos grupos para dos páginas
    mitad = len(alumnos) // 2 + len(alumnos) % 2  # Asegura que la primera página tenga más si es impar
    alumnos_pagina1 = alumnos[:mitad]
    alumnos_pagina2 = alumnos[mitad:]
    
    # Crear PDF con ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    # Obtener estilos
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.fontSize = 14
    normal_style = styles['Normal']
    normal_style.fontSize = 8

    def crear_tabla_alumnos(alumnos_grupo, inicio_numeracion):
        # Crear tabla
        data = []
        # Encabezados con números de días
        headers = ['N°', 'Nombre'] + [str(dia.day) for dia in dias_mes]
        
        # Agregar filas con números y nombres
        for i, alumno in enumerate(alumnos_grupo, inicio_numeracion):
            row = [str(i), alumno['nombre']] + [''] * len(dias_mes)
            data.append(row)

        # Crear tabla
        # Encabezados con números de días
        headers = ['N°', 'Nombre'] + [str(dia.day) for dia in dias_mes]
        
        # Estilo de la tabla
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Centrar números
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # Alinear nombres a la izquierda
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'), # Centrar días
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])

        # Calcular anchos de columna
        available_width = 750  # Ancho aproximado en landscape
        num_width = 20
        name_width = 150
        day_width = (available_width - num_width - name_width) / len(dias_mes)
        
        # Crear y agregar tabla
        t = Table([headers] + data, colWidths=[num_width, name_width] + [day_width] * len(dias_mes))
        t.setStyle(table_style)
        return t

    # Primera página
    elements.append(Paragraph("CEIA Amigos del Padre Hurtado", title_style))
    elements.append(Paragraph("La Serena", normal_style))
    elements.append(Paragraph(f"Lista de Asistencia - {curso['nombre']} - {meses[mes_actual]} {año_actual}", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(crear_tabla_alumnos(alumnos_pagina1, 1))
    
    # Si hay alumnos para la segunda página
    if alumnos_pagina2:
        elements.append(PageBreak())
        elements.append(Paragraph("CEIA Amigos del Padre Hurtado", title_style))
        elements.append(Paragraph("La Serena", normal_style))
        elements.append(Paragraph(f"Lista de Asistencia - {curso['nombre']} - {meses[mes_actual]} {año_actual} (continuación)", normal_style))
        elements.append(Spacer(1, 10))
        elements.append(crear_tabla_alumnos(alumnos_pagina2, len(alumnos_pagina1) + 1))

    # Generar PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    return send_file(
        BytesIO(pdf),
        download_name=f'lista_{curso["nombre"]}_{meses[mes_actual]}_{año_actual}.pdf',
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
        conn.execute('UPDATE alumnos SET nombre = ? WHERE id = ?', (data['nombre'], data['id']))
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
        cur = conn.execute('INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)', (data['nombre'], data['curso_id']))
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
                conn.execute('INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)', (nombre, curso_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Configurar el puerto
port = int(os.environ.get('PORT', 8080))
logger.info(f'Aplicación configurada para usar puerto {port}')

if __name__ == '__main__':
    # Create static folder if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
