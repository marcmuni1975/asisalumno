'use client';

import { useState } from 'react';
import { ArrowLeft, Save, Check, X, Clock } from 'lucide-react';
import Link from 'next/link';

// Mock data inicial
const STUDENTS_MOCK = [
    { id: 1, name: 'Alvarado, Juan' },
    { id: 2, name: 'Berríos, María' },
    { id: 3, name: 'Castro, Pedro' },
    { id: 4, name: 'Díaz, Ana' },
    { id: 5, name: 'Escobar, Luis' },
    { id: 6, name: 'Fernández, Sofía' },
    { id: 7, name: 'González, Diego' },
    { id: 8, name: 'Herrera, Camila' },
];

type AttendanceStatus = 'present' | 'absent' | 'late';

export default function AttendancePage() {
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [attendance, setAttendance] = useState<Record<number, AttendanceStatus>>(() => {
        // Inicializar todos como presentes
        const initial: Record<number, AttendanceStatus> = {};
        STUDENTS_MOCK.forEach(s => initial[s.id] = 'present');
        return initial;
    });

    const handleStatusChange = (id: number, status: AttendanceStatus) => {
        setAttendance(prev => ({ ...prev, [id]: status }));
    };

    const handleSave = () => {
        alert(`Guardando asistencia del ${date}:\n` + JSON.stringify(attendance, null, 2));
        // Aquí iría la llamada a la API
    };

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
                        <p className="text-sm text-gray-500">Curso: 1° Medio A</p>
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
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2 shadow-sm"
                    >
                        <Save size={18} />
                        Guardar
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
                            {STUDENTS_MOCK.map((student, index) => (
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
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
