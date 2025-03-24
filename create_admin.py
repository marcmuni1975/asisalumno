import sqlite3
from werkzeug.security import generate_password_hash

def create_admin():
    conn = sqlite3.connect('asistencia_multiples_cursos.db')
    c = conn.cursor()
    
    # Verificar si la tabla usuarios existe
    table_exists = c.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='usuarios'
    """).fetchone()
    
    if not table_exists:
        # Crear la tabla de usuarios solo si no existe
        print("Creando tabla de usuarios...")
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
        print("Tabla de usuarios creada exitosamente")
    
    # Verificar si ya existe un administrador
    admin = c.execute('SELECT id FROM usuarios WHERE rol = "admin" LIMIT 1').fetchone()
    
    if not admin:
        # Crear usuario administrador
        try:
            c.execute('''
            INSERT INTO usuarios (username, password, nombre, rol)
            VALUES (?, ?, ?, ?)
            ''', ('admin', generate_password_hash('admin123'), 'Administrador', 'admin'))
            conn.commit()
            print("\nUsuario administrador creado exitosamente")
            print("Usuario: admin")
            print("Contraseña: admin123")
        except sqlite3.IntegrityError:
            print("\nYa existe un usuario con el nombre 'admin'")
    else:
        print("\nYa existe un usuario administrador")
    
    conn.close()

if __name__ == '__main__':
    create_admin()
