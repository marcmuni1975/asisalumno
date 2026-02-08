import Link from "next/link";
import { Users, Calendar, BarChart3, Settings } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-8">
      {/* Header */}
      <header className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Asistencia CEIA
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            Panel de Control de Asistencia Escolar
          </p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
            <Users size={18} />
            Gestionar Alumnos
          </button>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 text-blue-600 rounded-lg">
              <Users size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Alumnos</p>
              <h3 className="text-2xl font-bold">28</h3>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-100 dark:bg-green-900/30 text-green-600 rounded-lg">
              <Calendar size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Días Trabajados</p>
              <h3 className="text-2xl font-bold">94</h3>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-100 dark:bg-orange-900/30 text-orange-600 rounded-lg">
              <BarChart3 size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Asistencia Promedio</p>
              <h3 className="text-2xl font-bold">87%</h3>
            </div>
          </div>
        </div>
      </div>

      {/* Main Action Area */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link
          href="/tomar-asistencia"
          className="group block p-8 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 transition-all shadow-sm hover:shadow-md"
        >
          <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-full w-fit group-hover:scale-110 transition-transform">
            <Calendar size={32} className="text-blue-600" />
          </div>
          <h2 className="text-xl font-bold mb-2">Tomar Asistencia del Día</h2>
          <p className="text-gray-500 dark:text-gray-400">
            Registrar presentes, ausentes y atrasos para la fecha actual.
          </p>
        </Link>

        <div className="p-8 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-dashed border-gray-300 dark:border-gray-700 flex flex-col items-center justify-center text-center opacity-70">
          <Settings size={32} className="text-gray-400 mb-4" />
          <h2 className="text-xl font-bold mb-2 text-gray-500">Configuración</h2>
          <p className="text-sm text-gray-400">
            Más opciones próximamente...
          </p>
        </div>
      </div>

    </main>
  );
}
