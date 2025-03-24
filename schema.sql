-- Tabla de cursos
CREATE TABLE IF NOT EXISTS cursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    año INTEGER NOT NULL
);

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nombre TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('admin', 'usuario')) NOT NULL DEFAULT 'usuario',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de alumnos
CREATE TABLE IF NOT EXISTS alumnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    id_curso INTEGER,
    FOREIGN KEY (id_curso) REFERENCES cursos(id)
);

-- Tabla de asistencia
CREATE TABLE IF NOT EXISTS asistencia (
    id_alumno INTEGER,
    fecha TEXT,
    presente INTEGER,
    PRIMARY KEY (id_alumno, fecha),
    FOREIGN KEY (id_alumno) REFERENCES alumnos(id)
);
