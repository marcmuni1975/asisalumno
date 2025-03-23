import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

DB_PATH = "asistencia_multiples_cursos.db"

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard de Asistencia")
        
        # Configuración de umbrales de asistencia
        self.UMBRAL_REGULAR = 2  # Más de 2 asistencias
        self.UMBRAL_RIESGO = 1   # 1-2 asistencias
        
        # Definir y usar un estilo con más colores
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")  # "clam", "default", "alt", "classic", etc.

        # Ajustar colores para un estilo más colorido
        self.style.configure(
            ".",             # selector
            background="#F0F0F0",  # fondo
            foreground="#000000",  # color de letra
            fieldbackground="#FFFFFF",
            font=("Arial", 10)
        )
        # Ajustar en particular para botones y labels
        self.style.configure(
            "TButton",
            background="#4CAF50",  # verde
            foreground="#FFFFFF",
            padding=5
        )
        self.style.map("TButton", background=[("active", "#45A049")])  # verde oscuro al hacer clic
        self.style.configure(
            "TLabel",
            background="#F0F0F0",
            foreground="#000000"
        )
        # Combobox con campo de texto claro
        self.style.configure(
            "TCombobox",
            fieldbackground="#FFFFFF",  # fondo del campo editable
            foreground="#000000"
        )

        # Variables
        self.curso_seleccionado = tk.StringVar()

        # Frame superior
        top_frame = ttk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Etiqueta y ComboBox para cursos
        ttk.Label(top_frame, text="Curso:").pack(side=tk.LEFT, padx=5)
        self.combo_cursos = ttk.Combobox(top_frame, textvariable=self.curso_seleccionado, state="readonly")
        self.combo_cursos.pack(side=tk.LEFT)
        btn_cargar = ttk.Button(top_frame, text="Cargar Datos", command=self.cargar_estadisticas)
        btn_cargar.pack(side=tk.LEFT, padx=5)
        btn_exportar = ttk.Button(top_frame, text="Exportar PDF", command=self.exportar_pdf)
        btn_exportar.pack(side=tk.LEFT, padx=5)

        # Frame para las 4 estadísticas
        stats_frame = ttk.Frame(root)
        stats_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Cuatro recuadros con etiquetas y mejor formato
        stats_style = {"width": 25, "padding": 10, "relief": "solid", "borderwidth": 1}
        
        self.label_total_alumnos = ttk.Label(stats_frame, text="Total Alumnos: 0", **stats_style)
        self.label_total_alumnos.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.label_dias_registrados = ttk.Label(stats_frame, text="Días Registrados: 0", **stats_style)
        self.label_dias_registrados.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.label_asistencia_total = ttk.Label(stats_frame, text="Asistencia Total: 0", **stats_style)
        self.label_asistencia_total.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.label_porcentaje_promedio = ttk.Label(stats_frame, text="Prom. Asistencia: 0%", **stats_style)
        self.label_porcentaje_promedio.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        # Frame para filtros adicionales
        filter_frame = ttk.Frame(root)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Filtrar por:").pack(side=tk.LEFT, padx=5)
        self.filtro_var = tk.StringVar(value="todos")
        ttk.Radiobutton(filter_frame, text="Todos", variable=self.filtro_var, value="todos", command=self.aplicar_filtro).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Baja Asistencia (<75%)", variable=self.filtro_var, value="baja", command=self.aplicar_filtro).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="No Asisten", variable=self.filtro_var, value="no_asisten", command=self.aplicar_filtro).pack(side=tk.LEFT, padx=5)

        # Frame para la tabla de detalle
        detalle_frame = ttk.Frame(root)
        detalle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame para la leyenda
        legend_frame = ttk.Frame(root)
        legend_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Crear leyenda
        ttk.Label(legend_frame, text="Clasificación de Asistencia:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(legend_frame, text="Regular (>2 asistencias)", background="#90EE90", padding=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(legend_frame, text="Riesgo (1-2 asistencias)", background="#FFB6C1", padding=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(legend_frame, text="No Asiste (0 asistencias)", background="#D3D3D3", padding=5).pack(side=tk.LEFT, padx=5)

        # Scrollbars
        self.scroll_y = ttk.Scrollbar(detalle_frame, orient=tk.VERTICAL)
        self.scroll_x = ttk.Scrollbar(detalle_frame, orient=tk.HORIZONTAL)

        # Treeview con más columnas
        columnas = ("#", "alumno", "dias_presentes", "dias_totales", "porcentaje", "ultima_asistencia", "estado")
        self.tree = ttk.Treeview(
            detalle_frame, 
            columns=columnas, 
            show="headings",
            yscrollcommand=self.scroll_y.set, 
            xscrollcommand=self.scroll_x.set
        )
        self.tree.heading("#", text="#")
        self.tree.heading("alumno", text="Alumno")
        self.tree.heading("dias_presentes", text="Días Presente")
        self.tree.heading("dias_totales", text="Días Totales")
        self.tree.heading("porcentaje", text="% Asistencia")
        self.tree.heading("ultima_asistencia", text="Última Asistencia")
        self.tree.heading("estado", text="Estado")

        self.tree.column("#", width=50, anchor=tk.CENTER)
        self.tree.column("alumno", width=200)
        self.tree.column("dias_presentes", width=100, anchor=tk.CENTER)
        self.tree.column("dias_totales", width=100, anchor=tk.CENTER)
        self.tree.column("porcentaje", width=100, anchor=tk.CENTER)
        self.tree.column("ultima_asistencia", width=150, anchor=tk.CENTER)
        self.tree.column("estado", width=100, anchor=tk.CENTER)

        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Frame para gráficos
        self.graph_frame = ttk.Frame(root)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Cargar cursos en el ComboBox
        self.cargar_cursos_en_combobox()

        # Evento de clic en el Treeview
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)

    def cargar_cursos_en_combobox(self):
        """Carga la lista de cursos en el ComboBox desde la base de datos."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM cursos ORDER BY nombre")
        cursos = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.combo_cursos['values'] = cursos
        if cursos:
            self.combo_cursos.current(0)  # Selecciona el primero por defecto

    def cargar_estadisticas(self):
        """Carga y muestra las estadísticas y el detalle de asistencia para el curso seleccionado."""
        curso = self.curso_seleccionado.get()
        if not curso:
            messagebox.showwarning("Atención", "Seleccione un curso.")
            return

        id_curso = self.get_id_curso_por_nombre(curso)
        if not id_curso:
            messagebox.showwarning("Atención", "Curso inválido.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1) Total de alumnos en el curso
        cursor.execute("SELECT COUNT(*) FROM alumnos WHERE id_curso = ?", (id_curso,))
        total_alumnos = cursor.fetchone()[0]

        # 2) Días registrados (distintos) en asistencia para los alumnos de este curso
        cursor.execute("""
            SELECT COUNT(DISTINCT fecha)
            FROM asistencia
            WHERE id_alumno IN (
                SELECT id FROM alumnos WHERE id_curso = ?
            )
        """, (id_curso,))
        dias_registrados = cursor.fetchone()[0]

        # 3) Suma total de asistencias (presente=1) para el curso
        cursor.execute("""
            SELECT SUM(presente)
            FROM asistencia
            WHERE id_alumno IN (
                SELECT id FROM alumnos WHERE id_curso = ?
            )
        """, (id_curso,))
        asistencia_total = cursor.fetchone()[0]
        if asistencia_total is None:
            asistencia_total = 0

        # 4) Porcentaje promedio de asistencia
        total_posible = total_alumnos * dias_registrados
        if total_posible > 0:
            promedio_asistencia = (asistencia_total / total_posible) * 100
        else:
            promedio_asistencia = 0.0

        # Actualizamos los labels
        self.label_total_alumnos.config(text=f"Total Alumnos: {total_alumnos}")
        self.label_dias_registrados.config(text=f"Días Registrados: {dias_registrados}")
        self.label_asistencia_total.config(text=f"Asistencia Total: {asistencia_total}")
        self.label_porcentaje_promedio.config(text=f"Prom. Asistencia: {promedio_asistencia:.2f}%")

        # Cargar detalle por alumno con información adicional
        self.tree.delete(*self.tree.get_children())  # Limpiar la tabla

        cursor.execute("""
            SELECT id, nombre
            FROM alumnos
            WHERE id_curso = ?
            ORDER BY nombre
        """, (id_curso,))
        alumnos = cursor.fetchall()

        for idx, (id_alumno, nombre_alumno) in enumerate(alumnos, 1):
            # Días presentes y última asistencia
            cursor.execute("""
                SELECT SUM(presente), MAX(CASE WHEN presente = 1 THEN fecha END)
                FROM asistencia
                WHERE id_alumno = ?
            """, (id_alumno,))
            dias_presentes, ultima_asistencia = cursor.fetchone()
            
            if dias_presentes is None:
                dias_presentes = 0
            
            # Calcular porcentaje y estado
            porcentaje = (dias_presentes / dias_registrados * 100) if dias_registrados > 0 else 0
            
            # Determinar estado basado en asistencia
            estado, color = self.determinar_estado(dias_presentes, dias_registrados, ultima_asistencia)
            
            # Formatear última asistencia
            ultima_asistencia_fmt = ultima_asistencia if ultima_asistencia else "Sin registros"
            
            self.tree.insert("", "end", values=(
                idx,
                nombre_alumno,
                dias_presentes,
                dias_registrados,
                f"{porcentaje:.1f}%",
                ultima_asistencia_fmt,
                estado
            ), tags=(color,))

        # Configurar colores para los estados
        self.tree.tag_configure("Regular", background="#90EE90")  # Verde claro
        self.tree.tag_configure("Riesgo", background="#FFB6C1")   # Rojo claro
        self.tree.tag_configure("No Asiste", background="#D3D3D3") # Gris

        conn.close()
        self.aplicar_filtro()  # Aplicar el filtro actual
        
        # Crear gráficos generales
        self.crear_graficos(total_alumnos, dias_registrados, asistencia_total, promedio_asistencia)

    def determinar_estado(self, dias_presentes, dias_totales, ultima_asistencia):
        """Determina el estado de asistencia del alumno según los umbrales configurados."""
        if dias_presentes == 0:
            return "No Asiste", "#D3D3D3"
            
        # Si tiene más de 2 asistencias
        if dias_presentes > self.UMBRAL_REGULAR:
            return "Regular", "#90EE90"
        # Si tiene 1-2 asistencias
        elif dias_presentes >= self.UMBRAL_RIESGO:
            return "Riesgo", "#FFB6C1"
        else:
            return "No Asiste", "#D3D3D3"

    def aplicar_filtro(self):
        """Aplica el filtro seleccionado a la tabla de alumnos."""
        filtro = self.filtro_var.get()
        for item in self.tree.get_children():
            valores = self.tree.item(item)["values"]
            dias_presentes = int(valores[2])
            
            if filtro == "todos":
                self.tree.reattach(item, "", "end")
            elif filtro == "baja" and dias_presentes <= 1 and dias_presentes > 0:
                self.tree.reattach(item, "", "end")
            elif filtro == "no_asisten" and dias_presentes == 0:
                self.tree.reattach(item, "", "end")
            else:
                self.tree.detach(item)

    def on_tree_select(self, event):
        """Muestra información detallada del alumno seleccionado."""
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item["values"]
        alumno = valores[1]
        
        # Crear ventana emergente con información detallada
        info_window = tk.Toplevel(self.root)
        info_window.title(f"Detalle de Alumno: {valores[1]}")
        info_window.geometry("400x300")
        
        # Mostrar información detallada
        ttk.Label(info_window, text=f"Nombre: {valores[1]}", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(info_window, text=f"Días Presentes: {valores[2]} de {valores[3]}").pack(pady=5)
        ttk.Label(info_window, text=f"Porcentaje de Asistencia: {valores[4]}").pack(pady=5)
        ttk.Label(info_window, text=f"Última Asistencia: {valores[5]}").pack(pady=5)
        ttk.Label(info_window, text=f"Estado: {valores[6]}").pack(pady=5)

        # Agregar botón para cerrar
        ttk.Button(info_window, text="Cerrar", command=info_window.destroy).pack(pady=10)
        
        # Cargar gráficos del alumno
        self.cargar_graficos_alumno(alumno)

    def crear_graficos(self, total_alumnos, dias_registrados, asistencia_total, promedio_asistencia):
        """Crea gráficos de barras y pastel para visualizar las estadísticas generales."""
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        fig, axs = plt.subplots(1, 2, figsize=(10, 5))

        # Gráfico de barras
        axs[0].bar(["Total Alumnos", "Días Registrados", "Asistencia Total"], 
                   [total_alumnos, dias_registrados, asistencia_total], color=['#4CAF50', '#2196F3', '#FFC107'])
        axs[0].set_title("Estadísticas de Asistencia")
        axs[0].set_ylabel("Cantidad")

        # Gráfico de pastel
        axs[1].pie([promedio_asistencia, 100 - promedio_asistencia], labels=["Asistencia", "Inasistencia"], 
                   autopct='%1.1f%%', colors=['#4CAF50', '#F44336'])
        axs[1].set_title("Promedio de Asistencia")

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def cargar_graficos_alumno(self, nombre_alumno):
        """Carga y muestra los gráficos de asistencia para el alumno seleccionado."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM alumnos WHERE nombre = ?", (nombre_alumno,))
        id_alumno = cursor.fetchone()[0]

        # Días presentes
        cursor.execute("""
            SELECT SUM(presente)
            FROM asistencia
            WHERE id_alumno = ?
        """, (id_alumno,))
        dias_presentes = cursor.fetchone()[0]
        if dias_presentes is None:
            dias_presentes = 0

        # Días totales
        cursor.execute("""
            SELECT COUNT(DISTINCT fecha)
            FROM asistencia
            WHERE id_alumno = ?
        """, (id_alumno,))
        dias_totales = cursor.fetchone()[0]

        if dias_totales is None:
            dias_totales = 0

        # Porcentaje
        if dias_totales > 0:
            porcentaje = (dias_presentes / dias_totales) * 100
        else:
            porcentaje = 0.0

        conn.close()

        # Crear gráficos específicos del alumno
        self.crear_graficos_alumno(dias_presentes, dias_totales, porcentaje)

    def crear_graficos_alumno(self, dias_presentes, dias_totales, porcentaje):
        """Crea gráficos de barras y pastel para visualizar las estadísticas de un alumno."""
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        fig, axs = plt.subplots(1, 2, figsize=(10, 5))

        # Gráfico de barras
        axs[0].bar(["Días Presentes", "Días Totales"], 
                   [dias_presentes, dias_totales], color=['#4CAF50', '#2196F3'])
        axs[0].set_title("Asistencia del Alumno")
        axs[0].set_ylabel("Cantidad")

        # Gráfico de pastel
        axs[1].pie([porcentaje, 100 - porcentaje], labels=["Asistencia", "Inasistencia"], 
                   autopct='%1.1f%%', colors=['#4CAF50', '#F44336'])
        axs[1].set_title("Porcentaje de Asistencia")

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def get_id_curso_por_nombre(self, nombre_curso):
        """Devuelve el id de un curso dado su nombre."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cursos WHERE nombre = ?", (nombre_curso,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def exportar_pdf(self):
        """Exporta un informe detallado de asistencia a PDF."""
        if not self.curso_seleccionado.get():
            messagebox.showwarning("Advertencia", "Seleccione un curso primero")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")]
            )
            if not file_path:
                return

            # Obtener datos del curso
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            id_curso = self.get_id_curso_por_nombre(self.curso_seleccionado.get())
            if not id_curso:
                messagebox.showerror("Error", "No se pudo encontrar el curso seleccionado")
                return
            
            # Crear documento PDF
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Estilo para el membrete
            header_style = ParagraphStyle(
                'Header',
                parent=styles['Heading1'],
                fontSize=14,
                alignment=1,  # Centrado
                spaceAfter=5,
                textColor=colors.HexColor('#1B4F72')  # Azul institucional
            )
            
            subheader_style = ParagraphStyle(
                'SubHeader',
                parent=styles['Normal'],
                fontSize=12,
                alignment=1,  # Centrado
                spaceAfter=20,
                textColor=colors.HexColor('#2874A6')  # Azul más claro
            )
            
            # Membrete
            elements.append(Paragraph("CEIA Amigos del Padre Hurtado", header_style))
            elements.append(Paragraph("La Serena", subheader_style))
            elements.append(Paragraph("Reporte Asistencia - Inspectoría Jornada Noche", subheader_style))
            elements.append(Spacer(1, 20))
            
            # Línea divisoria
            elements.append(HRFlowable(
                width="100%",
                thickness=1,
                color=colors.HexColor('#1B4F72'),
                spaceBefore=1,
                spaceAfter=20
            ))
            
            # Título y fecha
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading2'],
                fontSize=12,
                spaceAfter=10,
                alignment=1
            )
            elements.append(Paragraph(f"Informe de Asistencia - {self.curso_seleccionado.get()}", title_style))
            elements.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                                   ParagraphStyle('Date', parent=styles['Normal'], alignment=1)))
            elements.append(Spacer(1, 20))
            
            # Estadísticas generales
            elements.append(Paragraph("Estadísticas Generales", styles["Heading2"]))
            elements.append(Spacer(1, 10))
            
            # Obtener estadísticas
            cursor.execute("SELECT COUNT(*) FROM alumnos WHERE id_curso = ?", (id_curso,))
            total_alumnos = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT fecha) as dias_registrados,
                       SUM(CASE WHEN presente = 1 THEN 1 ELSE 0 END) as total_asistencias
                FROM asistencia
                WHERE id_alumno IN (SELECT id FROM alumnos WHERE id_curso = ?)
            """, (id_curso,))
            
            row = cursor.fetchone()
            dias_registrados = row[0] if row[0] is not None else 0
            asistencia_total = row[1] if row[1] is not None else 0
            
            promedio_asistencia = (asistencia_total / (total_alumnos * dias_registrados) * 100) if dias_registrados > 0 and total_alumnos > 0 else 0
            
            # Tabla de estadísticas
            stats_data = [
                ["Estadística", "Valor"],
                ["Total de Alumnos", str(total_alumnos)],
                ["Días Registrados", str(dias_registrados)],
                ["Total Asistencias", str(asistencia_total)],
                ["Promedio Asistencia", f"{promedio_asistencia:.1f}%"]
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))
            
            # Agregar leyenda después de las estadísticas generales
            elements.append(Paragraph("Criterios de Clasificación:", styles["Heading3"]))
            elements.append(Spacer(1, 10))
            
            # Tabla de leyenda con criterios específicos
            legend_data = [
                ["Estado", "Criterio", "Descripción"],
                ["Regular", ">2 asistencias", "Alumno asiste con regularidad"],
                ["Riesgo", "1-2 asistencias", "Asistencia baja, requiere seguimiento"],
                ["No Asiste", "0 asistencias", "Sin asistencias registradas"]
            ]
            
            legend_table = Table(legend_data, colWidths=[1.2*inch, 1.5*inch, 2.8*inch])
            legend_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (-1, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 1), (-1, 1), colors.lightgreen),
                ('BACKGROUND', (0, 2), (-1, 2), colors.pink),
                ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
            elements.append(legend_table)
            elements.append(Spacer(1, 20))
            
            # Detalle por alumno
            elements.append(Paragraph("Detalle por Alumno", styles["Heading2"]))
            elements.append(Spacer(1, 10))
            
            # Obtener datos de alumnos
            cursor.execute("""
                SELECT a.nombre,
                       COUNT(DISTINCT CASE WHEN ast.presente = 1 THEN ast.fecha END) as dias_presentes,
                       COUNT(DISTINCT ast.fecha) as dias_totales,
                       MAX(CASE WHEN ast.presente = 1 THEN ast.fecha END) as ultima_asistencia
                FROM alumnos a
                LEFT JOIN asistencia ast ON a.id = ast.id_alumno
                WHERE a.id_curso = ?
                GROUP BY a.id, a.nombre
                ORDER BY a.nombre
            """, (id_curso,))
            
            alumnos_data = [["#", "Alumno", "Días\nPresente", "Días\nTotales", "%\nAsistencia", "Última\nAsistencia", "Estado"]]
            row_colors = [(('BACKGROUND', (0, 0), (-1, 0), colors.grey))]  # Color para el encabezado
            
            for idx, row in enumerate(cursor.fetchall(), 1):
                nombre, dias_presentes, dias_totales, ultima_asistencia = row
                dias_presentes = dias_presentes or 0
                dias_totales = dias_totales or 0
                
                porcentaje = (dias_presentes / dias_totales * 100) if dias_totales > 0 else 0
                
                # Determinar estado basado en asistencia
                estado, color = self.determinar_estado(dias_presentes, dias_totales, ultima_asistencia)
                
                alumnos_data.append([
                    str(idx),
                    Paragraph(nombre, styles['Normal']),
                    str(dias_presentes),
                    str(dias_totales),
                    f"{porcentaje:.1f}%",
                    ultima_asistencia if ultima_asistencia else "Sin registros",
                    estado
                ])
                
                # Convertir color hexadecimal a objeto Color de reportlab
                if color == "#90EE90":
                    pdf_color = colors.lightgreen
                elif color == "#FFB6C1":
                    pdf_color = colors.pink
                else:
                    pdf_color = colors.lightgrey
                
                row_colors.append(('BACKGROUND', (0, idx), (-1, idx), pdf_color))
            
            # Ajustar anchos de columna y crear tabla
            alumnos_table = Table(alumnos_data, colWidths=[0.5*inch, 2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.3*inch, 0.8*inch])
            
            style = TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('WORDWRAP', (0, 0), (-1, -1), True),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ] + row_colors)
            
            alumnos_table.setStyle(style)
            elements.append(alumnos_table)
            
            # Generar PDF
            doc.build(elements)
            messagebox.showinfo("Éxito", "PDF generado correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar PDF: {str(e)}")
            print(f"Error detallado: {str(e)}")  # Para debugging
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    root.mainloop()