"""
Programa de gestión de asistencia con columnas de días (lunes a viernes) y soporte para múltiples cursos.
- Permite:
  1) Crear y cargar una base de datos SQLite con tablas: cursos, alumnos y asistencia.
  2) Seleccionar un curso desde un ComboBox.
  3) Elegir un mes y año para mostrar únicamente los días lunes a viernes.
  4) Visualizar en una cuadrícula (alumnos vs días) y marcar presente o ausente.
  5) Guardar/actualizar la asistencia en la base de datos.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import sqlite3
import calendar
from datetime import datetime, date

DB_PATH = "asistencia_multiples_cursos.db"

class AsistenciaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Asistencia (Múltiples Cursos)")
        
        # Variables para Combobox de curso, mes y año
        self.curso_seleccionado = tk.StringVar()
        self.mes_seleccionado = tk.IntVar(value=datetime.now().month)
        self.anio_seleccionado = tk.IntVar(value=datetime.now().year)
        
        # Crear base de datos y tablas si no existen
        self.crear_db()
        self.cargar_cursos_iniciales()  # Opcional: agrega datos de ejemplo si no hay cursos
        self.cargar_alumnos_iniciales() # Opcional: agrega datos de ejemplo si no hay alumnos
        
        # Frame superior para selección de curso, mes, año, y botones
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Label y ComboBox para cursos
        tk.Label(top_frame, text="Curso:").pack(side=tk.LEFT, padx=5)
        self.combo_cursos = ttk.Combobox(top_frame, textvariable=self.curso_seleccionado, state="readonly")
        self.combo_cursos.pack(side=tk.LEFT)
        self.cargar_cursos_en_combobox()
        
        # Label, Spinbox para mes y año
        tk.Label(top_frame, text="Mes:").pack(side=tk.LEFT, padx=5)
        self.spin_mes = tk.Spinbox(top_frame, from_=1, to=12, width=5, textvariable=self.mes_seleccionado)
        self.spin_mes.pack(side=tk.LEFT)
        
        tk.Label(top_frame, text="Año:").pack(side=tk.LEFT, padx=5)
        self.spin_anio = tk.Spinbox(top_frame, from_=2000, to=2100, width=5, textvariable=self.anio_seleccionado)
        self.spin_anio.pack(side=tk.LEFT)
        
        # Botón para cargar asistencia (días y alumnos)
        btn_cargar = tk.Button(top_frame, text="Cargar Mes", command=self.cargar_asistencia)
        btn_cargar.pack(side=tk.LEFT, padx=5)
        
        # Botón para guardar asistencia
        btn_guardar = tk.Button(top_frame, text="Guardar", command=self.guardar_asistencia)
        btn_guardar.pack(side=tk.LEFT, padx=5)
        
        # Botón para cargar alumnos desde TXT
        btn_cargar_alumnos = tk.Button(top_frame, text="Cargar Alumnos", command=self.cargar_alumnos_desde_txt)
        btn_cargar_alumnos.pack(side=tk.LEFT, padx=5)
        
        # Botón para importar alumnos desde TXT
        btn_importar_alumnos = tk.Button(top_frame, text="Importar Alumnos", command=self.importar_alumnos_desde_txt)
        btn_importar_alumnos.pack(side=tk.LEFT, padx=5)
        
        # Botón para agregar alumno manualmente
        btn_agregar_alumno = tk.Button(top_frame, text="Agregar Alumno", command=self.agregar_alumno)
        btn_agregar_alumno.pack(side=tk.LEFT, padx=5)
        
        # Frame que contendrá la grilla (canvas con scroll horizontal y vertical)
        self.frame_grilla = tk.Frame(self.root)
        self.frame_grilla.pack(fill=tk.BOTH, expand=True)
        
        # Canvas y scrollbars
        self.canvas = tk.Canvas(self.frame_grilla)
        self.scroll_y = tk.Scrollbar(self.frame_grilla, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scroll_x = tk.Scrollbar(self.frame_grilla, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Diccionario para almacenar las variables de check (asistencia)
        # Clave: (id_alumno, fecha_date) -> tk.IntVar
        self.asistencia_vars = {}
        
        # Lista de días (datetime.date) de lunes a viernes para el mes cargado
        self.dias_laborales = []
        
        # Label para mostrar info (por ejemplo, si no hay alumnos, etc.)
        self.label_info = tk.Label(self.root, text="", fg="blue")
        self.label_info.pack(pady=2)
    
    def crear_db(self):
        """Crea la base de datos y las tablas si no existen."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Tabla de cursos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE
            )
        """)
        
        # Tabla de alumnos (relacionados a un curso)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alumnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                id_curso INTEGER,
                FOREIGN KEY(id_curso) REFERENCES cursos(id)
            )
        """)
        
        # Tabla de asistencia
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asistencia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_alumno INTEGER,
                fecha TEXT,
                presente INTEGER,
                FOREIGN KEY(id_alumno) REFERENCES alumnos(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def cargar_cursos_iniciales(self):
        """Opcional: inserta algunos cursos de ejemplo si la tabla está vacía."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cursos")
        count = cursor.fetchone()[0]
        if count == 0:
            # Insertar cursos de ejemplo
            cursor.execute("INSERT INTO cursos (nombre) VALUES (?)", ("1roC",))
            cursor.execute("INSERT INTO cursos (nombre) VALUES (?)", ("2doC",))
            cursor.execute("INSERT INTO cursos (nombre) VALUES (?)", ("3roC",))
            conn.commit()
        conn.close()
    
    def cargar_alumnos_iniciales(self):
        """
        Opcional: inserta algunos alumnos de ejemplo si la tabla está vacía.
        Todos se asocian al primer curso (id=1) para ilustrar.
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM alumnos")
        count = cursor.fetchone()[0]
        if count == 0:
            # Insertar alumnos de ejemplo (asociados al curso con id=1)
            alumnos_ejemplo = [
                "García López Juan Carlos",
                "Martínez Rodríguez Ana Sofía",
                "Pérez Sánchez Luis Alberto",
                "González Fernández María Isabel",
                "Sánchez Gómez Carlos Eduardo"
            ]
            for nombre in alumnos_ejemplo:
                cursor.execute("INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)", (nombre, 1))
            conn.commit()
        conn.close()
    
    def cargar_cursos_en_combobox(self):
        """Carga la lista de cursos desde la BD en el ComboBox."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM cursos ORDER BY nombre")
        cursos = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.combo_cursos['values'] = cursos
        if cursos:
            self.combo_cursos.current(0)  # Selecciona el primero por defecto
    
    def get_id_curso_por_nombre(self, nombre_curso):
        """Devuelve el id de un curso dado su nombre."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cursos WHERE nombre = ?", (nombre_curso,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def obtener_dias_laborales(self, anio, mes):
        """
        Devuelve una lista de objetos date correspondientes
        a lunes-viernes del mes dado.
        """
        cal = calendar.Calendar()
        dias = []
        for d in cal.itermonthdates(anio, mes):
            if d.month == mes and d.weekday() < 5:  # weekday(): 0->lunes, 4->viernes
                dias.append(d)
        return dias
    
    def cargar_asistencia(self):
        """
        Carga la grilla de asistencia para el curso seleccionado
        y el mes/año especificado.
        """
        curso = self.curso_seleccionado.get()
        if not curso:
            messagebox.showwarning("Atención", "Seleccione un curso.")
            return
        
        # Obtener id_curso
        id_curso = self.get_id_curso_por_nombre(curso)
        if not id_curso:
            messagebox.showwarning("Atención", "Curso inválido.")
            return
        
        # Obtener mes y año
        mes = self.mes_seleccionado.get()
        anio = self.anio_seleccionado.get()
        
        # Obtener lista de días laborales
        self.dias_laborales = self.obtener_dias_laborales(anio, mes)
        
        # Limpiar el frame para reconstruir la grilla
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.asistencia_vars.clear()
        
        # Cargar alumnos del curso
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM alumnos WHERE id_curso = ? ORDER BY nombre", (id_curso,))
        alumnos = cursor.fetchall()
        
        if not alumnos:
            self.label_info.config(text="No hay alumnos en este curso.")
            conn.close()
            return
        else:
            self.label_info.config(text=f"Alumnos del {curso} para {mes}/{anio}")
        
        # Título de columnas (primer row)
        # Columna 0: "Alumno"
        tk.Label(self.scrollable_frame, text="Alumno", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", width=30)\
            .grid(row=0, column=0, sticky="nsew")
        
        # Luego cada día laboral
        for col_idx, dia in enumerate(self.dias_laborales, start=1):
            # Encabezado con fecha en formato dd/mm
            dia_str = dia.strftime("%d/%m")
            tk.Label(self.scrollable_frame, text=dia_str, font=("Arial", 10, "bold"), borderwidth=1, relief="solid", width=8)\
                .grid(row=0, column=col_idx, sticky="nsew")
        
        # Columnas para total asistido y porcentaje asistido
        tk.Label(self.scrollable_frame, text="Total Asistido", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", width=15)\
            .grid(row=0, column=len(self.dias_laborales) + 1, sticky="nsew")
        tk.Label(self.scrollable_frame, text="% Asistido", font=("Arial", 10, "bold"), borderwidth=1, relief="solid", width=15)\
            .grid(row=0, column=len(self.dias_laborales) + 2, sticky="nsew")
        
        # Para cada alumno, fila
        for row_idx, (id_alumno, nombre_alumno) in enumerate(alumnos, start=1):
            # Nombre del alumno
            tk.Label(self.scrollable_frame, text=nombre_alumno, borderwidth=1, relief="solid", width=30)\
                .grid(row=row_idx, column=0, sticky="nsew")
            
            total_asistido = 0
            
            # Para cada día, Checkbutton
            for col_idx, dia in enumerate(self.dias_laborales, start=1):
                var_check = tk.IntVar(value=0)
                # Ver si ya existe un registro en la BD para ese alumno y día
                cursor.execute("""
                    SELECT presente FROM asistencia
                    WHERE id_alumno = ? AND fecha = ?
                """, (id_alumno, dia.isoformat()))
                row_db = cursor.fetchone()
                if row_db:
                    var_check.set(row_db[0])  # 1 o 0
                    total_asistido += row_db[0]
                
                chk = tk.Checkbutton(self.scrollable_frame, variable=var_check)
                chk.grid(row=row_idx, column=col_idx, sticky="nsew")
                
                # Guardar en diccionario
                self.asistencia_vars[(id_alumno, dia)] = var_check
            
            # Calcular porcentaje asistido
            porcentaje_asistido = (total_asistido / len(self.dias_laborales)) * 100 if self.dias_laborales else 0
            
            # Mostrar total asistido y porcentaje asistido
            tk.Label(self.scrollable_frame, text=str(total_asistido), borderwidth=1, relief="solid", width=15)\
                .grid(row=row_idx, column=len(self.dias_laborales) + 1, sticky="nsew")
            tk.Label(self.scrollable_frame, text=f"{porcentaje_asistido:.2f}%", borderwidth=1, relief="solid", width=15)\
                .grid(row=row_idx, column=len(self.dias_laborales) + 2, sticky="nsew")
            
            # Botones para editar y borrar
            btn_editar = tk.Button(self.scrollable_frame, text="Editar", command=lambda id_alumno=id_alumno: self.editar_alumno(id_alumno))
            btn_editar.grid(row=row_idx, column=len(self.dias_laborales) + 3, sticky="nsew")
            
            btn_borrar = tk.Button(self.scrollable_frame, text="Borrar", command=lambda id_alumno=id_alumno: self.borrar_alumno(id_alumno))
            btn_borrar.grid(row=row_idx, column=len(self.dias_laborales) + 4, sticky="nsew")
        
        conn.close()
    
    def agregar_alumno(self):
        """Agrega un nuevo alumno manualmente."""
        nombre_alumno = simpledialog.askstring("Agregar Alumno", "Ingrese el nombre del nuevo alumno:")
        if nombre_alumno:
            curso = self.curso_seleccionado.get()
            if not curso:
                messagebox.showwarning("Atención", "Seleccione un curso antes de agregar alumnos.")
                return
            
            id_curso = self.get_id_curso_por_nombre(curso)
            if not id_curso:
                messagebox.showwarning("Atención", "Curso inválido.")
                return
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            try:
                cursor.execute("INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)", (nombre_alumno, id_curso))
                conn.commit()
                messagebox.showinfo("Éxito", "Alumno agregado correctamente.")
                self.cargar_asistencia()  # Recargar la grilla de asistencia
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar el alumno:\n{e}")
            finally:
                conn.close()
    
    def editar_alumno(self, id_alumno):
        """Edita el nombre de un alumno."""
        nuevo_nombre = simpledialog.askstring("Editar Alumno", "Ingrese el nuevo nombre del alumno:")
        if nuevo_nombre:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE alumnos SET nombre = ? WHERE id = ?", (nuevo_nombre, id_alumno))
            conn.commit()
            conn.close()
            self.cargar_asistencia()
    
    def borrar_alumno(self, id_alumno):
        """Borra un alumno de la base de datos."""
        if messagebox.askyesno("Confirmar Borrado", "¿Está seguro de que desea borrar este alumno?"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alumnos WHERE id = ?", (id_alumno,))
            cursor.execute("DELETE FROM asistencia WHERE id_alumno = ?", (id_alumno,))
            conn.commit()
            conn.close()
            self.cargar_asistencia()
    
    def guardar_asistencia(self):
        """
        Guarda/actualiza la asistencia en la base de datos
        para todos los alumnos y días visibles.
        """
        if not self.asistencia_vars:
            messagebox.showinfo("Información", "No hay datos para guardar.")
            return
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Recorremos todos los (id_alumno, fecha) en el diccionario
        try:
            for (id_alumno, fecha_dia), var_check in self.asistencia_vars.items():
                presente = var_check.get()  # 0 o 1
                # Verificamos si existe ya un registro
                cursor.execute("""
                    SELECT id FROM asistencia
                    WHERE id_alumno = ? AND fecha = ?
                """, (id_alumno, fecha_dia.isoformat()))
                row_db = cursor.fetchone()
                
                if row_db:
                    # Actualizar
                    cursor.execute("""
                        UPDATE asistencia
                        SET presente = ?
                        WHERE id = ?
                    """, (presente, row_db[0]))
                else:
                    # Insertar
                    cursor.execute("""
                        INSERT INTO asistencia (id_alumno, fecha, presente)
                        VALUES (?, ?, ?)
                    """, (id_alumno, fecha_dia.isoformat(), presente))
            
            conn.commit()
            messagebox.showinfo("Éxito", "Asistencia guardada/actualizada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la asistencia:\n{e}")
        finally:
            conn.close()
    
    def cargar_alumnos_desde_txt(self):
        """Carga alumnos desde un archivo TXT y los inserta en la base de datos."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de alumnos",
            filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*"))
        )
        if not file_path:
            return
        
        with open(file_path, "r", encoding="utf-8") as file:
            alumnos = [line.strip() for line in file if line.strip()]
        
        if not alumnos:
            messagebox.showwarning("Atención", "El archivo está vacío o no contiene alumnos válidos.")
            return
        
        curso = self.curso_seleccionado.get()
        if not curso:
            messagebox.showwarning("Atención", "Seleccione un curso antes de cargar alumnos.")
            return
        
        id_curso = self.get_id_curso_por_nombre(curso)
        if not id_curso:
            messagebox.showwarning("Atención", "Curso inválido.")
            return
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            for nombre in alumnos:
                cursor.execute("INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)", (nombre, id_curso))
            conn.commit()
            messagebox.showinfo("Éxito", "Alumnos cargados correctamente desde el archivo.")
            self.cargar_asistencia()  # Recargar la grilla de asistencia
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar los alumnos:\n{e}")
        finally:
            conn.close()
    
    def importar_alumnos_desde_txt(self):
        """Importa alumnos desde un archivo TXT y los inserta en la base de datos."""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de alumnos",
            filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*"))
        )
        if not file_path:
            return
        
        with open(file_path, "r", encoding="utf-8") as file:
            alumnos = [line.strip() for line in file if line.strip()]
        
        if not alumnos:
            messagebox.showwarning("Atención", "El archivo está vacío o no contiene alumnos válidos.")
            return
        
        curso = self.curso_seleccionado.get()
        if not curso:
            messagebox.showwarning("Atención", "Seleccione un curso antes de importar alumnos.")
            return
        
        id_curso = self.get_id_curso_por_nombre(curso)
        if not id_curso:
            messagebox.showwarning("Atención", "Curso inválido.")
            return
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            for nombre in alumnos:
                cursor.execute("INSERT INTO alumnos (nombre, id_curso) VALUES (?, ?)", (nombre, id_curso))
            conn.commit()
            messagebox.showinfo("Éxito", "Alumnos importados correctamente desde el archivo.")
            self.cargar_asistencia()  # Recargar la grilla de asistencia
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo importar los alumnos:\n{e}")
        finally:
            conn.close()

# Ejecutar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = AsistenciaApp(root)
    root.mainloop()