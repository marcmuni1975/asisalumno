'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, Save, Check, X, Clock, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { getStudents, saveAttendance } from './actions';

type AttendanceStatus = 'present' | 'absent' | 'late';

// Definir tipo para Alumno que viene de DB
interface Student {
    id: number;
    name: string;
    course: string;
}

export default function AttendancePage() {
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [students, setStudents] = useState<Student[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [attendance, setAttendance] = useState<Record<number, AttendanceStatus>>({});

    // Cargar alumnos al iniciar
    useEffect(() => {
        async function loadData() {
            try {
                const data = await getStudents();
                setStudents(data as Student[]);

                // Inicializar asistencia
                const initial: Record<number, AttendanceStatus> = {};
                data.forEach((s: any) => initial[s.id] = 'present');
                setAttendance(initial);
            } catch (error) {
                console.error("Error loading students:", error);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, []);

    const handleStatusChange = (id: number, status: AttendanceStatus) => {
        setAttendance(prev => ({ ...prev, [id]: status }));
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const result = await saveAttendance(date, attendance);
            if (result.success) {
                alert('¡Asistencia guardada correctamente!');
            } else {
                alert('Error al guardar: ' + result.message);
            }
        } catch (e) {
            alert('Error inesperado al guardar');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <Loader2 className="animate-spin text-blue-600" size={48} />
                <span className="ml-3 text-gray-500">Cargando curso...</span>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
            {/* Header */}
            <header className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 sticky top-0 bg-gray-50 dark:bg-gray-900 z-10 py-2">
                <div className="flex items-center gap-4">
                    <Link href="/" className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-full transition-colors">
                        <ArrowLeft size={24} />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold">Tomar Asistencia</h1>
                        <p className="text-sm text-gray-500">Curso: 1° Medio A (Base de Datos)</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <input
                        type="date"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                        className="p-2 border rounded-lg bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700"
                    />
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                        {saving ? 'Guardando...' : 'Guardar'}
                    </button>
                </div>
            </header>

            {/* Table */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-gray-100 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                            <tr>
                                <th className="p-4 font-semibold text-gray-600 dark:text-gray-300 w-16">#</th>
                                <th className="p-4 font-semibold text-gray-600 dark:text-gray-300">Alumno</th>
                                <th className="p-4 font-semibold text-gray-600 dark:text-gray-300 text-center w-64">Estado</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                            {students.map((student, index) => (
                                <tr key={student.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                    <td className="p-4 text-gray-500">{index + 1}</td>
                                    <td className="p-4 font-medium">{student.name}</td>
                                    <td className="p-4">
                                        <div className="flex justify-center gap-2 bg-gray-100 dark:bg-gray-900/50 p-1 rounded-lg w-fit mx-auto">
                                            <button
                                                onClick={() => handleStatusChange(student.id, 'present')}
                                                className={`p-2 rounded-md transition-all ${attendance[student.id] === 'present'
                                                        ? 'bg-green-500 text-white shadow-sm'
                                                        : 'text-gray-400 hover:text-green-500'
                                                    }`}
                                                title="Presente"
                                            >
                                                <Check size={20} />
                                            </button>
                                            <button
                                                onClick={() => handleStatusChange(student.id, 'late')}
                                                className={`p-2 rounded-md transition-all ${attendance[student.id] === 'late'
                                                        ? 'bg-orange-400 text-white shadow-sm'
                                                        : 'text-gray-400 hover:text-orange-400'
                                                    }`}
                                                title="Atrasado"
                                            >
                                                <Clock size={20} />
                                            </button>
                                            <button
                                                onClick={() => handleStatusChange(student.id, 'absent')}
                                                className={`p-2 rounded-md transition-all ${attendance[student.id] === 'absent'
                                                        ? 'bg-red-500 text-white shadow-sm'
                                                        : 'text-gray-400 hover:text-red-500'
                                                    }`}
                                                title="Ausente"
                                            >
                                                <X size={20} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                            {students.length === 0 && (
                                <tr>
                                    <td colSpan={3} className="p-8 text-center text-gray-500">
                                        No se encontraron alumnos en la base de datos.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
