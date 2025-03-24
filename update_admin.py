import sqlite3
from werkzeug.security import generate_password_hash
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "asistencia_multiples_cursos.db"

def update_admin_password():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Generar nuevo hash usando pbkdf2
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        
        # Actualizar la contraseña del admin
        c.execute('UPDATE usuarios SET password = ? WHERE username = ?', 
                 (hashed_password, 'admin'))
        
        conn.commit()
        logger.info('Contraseña de admin actualizada exitosamente')
        
    except Exception as e:
        logger.error(f'Error al actualizar contraseña: {str(e)}')
    finally:
        conn.close()

if __name__ == '__main__':
    update_admin_password()
