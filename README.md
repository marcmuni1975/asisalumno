# Sistema de Asistencia CEIA

Sistema de gestión de asistencia para el CEIA Amigos del Padre Hurtado.

## Características

- Gestión de múltiples cursos
- Registro de asistencia diaria
- Reportes en PDF con estadísticas
- Gestión de alumnos por curso
- Importación de listas de alumnos desde archivos TXT

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd asistencia2025
```

2. Crear un entorno virtual e instalar dependencias:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Inicializar la base de datos:
```bash
sqlite3 asistencia_multiples_cursos.db < schema.sql
```

4. Ejecutar la aplicación:
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5005`

## Despliegue en Railway

1. Crear una nueva aplicación en Railway
2. Conectar con el repositorio de GitHub
3. Railway detectará automáticamente el Procfile y requirements.txt
4. La aplicación se desplegará automáticamente

## Tecnologías utilizadas

- Python 3.13
- Flask
- SQLite
- ReportLab
- Bootstrap
