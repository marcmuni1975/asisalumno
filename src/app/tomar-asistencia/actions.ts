'use server';

import { sql } from '@vercel/postgres';
import { revalidatePath } from 'next/cache';

export async function getStudents() {
    try {
        const { rows } = await sql`SELECT * FROM students ORDER BY name ASC`;
        return rows;
    } catch (error) {
        console.error('Error fetching students:', error);
        return [];
    }
}

export async function saveAttendance(date: string, attendanceData: Record<number, string>) {
    try {
        // attendanceData es un objeto { student_id: status }
        const promises = Object.entries(attendanceData).map(async ([studentId, status]) => {
            // Usamos ON CONFLICT para actualizar si ya existe registro ese día
            await sql`
        INSERT INTO attendance (student_id, date, status)
        VALUES (${Number(studentId)}, ${date}, ${status})
        ON CONFLICT (student_id, date) 
        DO UPDATE SET status = ${status};
      `;
        });

        await Promise.all(promises);
        revalidatePath('/tomar-asistencia');
        return { success: true, message: 'Asistencia guardada correctamente' };
    } catch (error) {
        console.error('Error saving attendance:', error);
        return { success: false, message: 'Error al guardar asistencia' };
    }
}
