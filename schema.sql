-- Tabla de cursos
CREATE TABLE IF NOT EXISTS cursos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    año INTEGER NOT NULL
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
