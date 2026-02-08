import { db } from '@vercel/postgres';
import { NextResponse } from 'next/server';

export async function GET() {
    try {
        const client = await db.connect();

        // 1. Crear Tabla de Alumnos
        await client.sql`
      CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE,
        course VARCHAR(50) NOT NULL
      );
    `;

        // 2. Crear Tabla de Asistencia
        await client.sql`
      CREATE TABLE IF NOT EXISTS attendance (
        id SERIAL PRIMARY KEY,
        student_id INTEGER REFERENCES students(id),
        date DATE NOT NULL,
        status VARCHAR(20) NOT NULL, -- 'present', 'absent', 'late'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, date)
      );
    `;

        // 3. Insertar Alumnos de Ejemplo (Solo si no existen)
        const { rows } = await client.sql`SELECT COUNT(*) FROM students`;
        if (Number(rows[0].count) === 0) {
            await client.sql`
        INSERT INTO students (name, course) VALUES 
        ('Alvarado, Juan', '1° Medio A'),
        ('Berríos, María', '1° Medio A'),
        ('Castro, Pedro', '1° Medio A'),
        ('Díaz, Ana', '1° Medio A'),
        ('Escobar, Luis', '1° Medio A');
      `;
        }

        return NextResponse.json({ message: 'Database seeded successfully' }, { status: 200 });
    } catch (error) {
        return NextResponse.json({ error }, { status: 500 });
    }
}
