# app.py
# ============================================================
# Clase principal GMExtractorApp: construye y gestiona toda
# la interfaz grafica (Tkinter).
#
# Modifica este archivo si:
#   - Quieres cambiar el layout de la ventana
#   - Necesitas agregar nuevos controles o secciones
#   - Quieres ajustar el comportamiento de los botones
#
# Dependencias de este modulo:
#   config.py      -> colores y constantes visuales
#   parser.py      -> parse_registration_table
#   dictionary.py  -> get_sheet_names, load_dictionary_from_sheet
#   transformer.py -> filter_and_transform, get_export_df
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import pandas as pd

from config import (
    APP_VERSION, APP_TITLE,
    GM_BLUE, GM_HOVER, LIGHT_BG, PANEL_BG, WHITE,
    TEXT_MAIN, TEXT_SEC, BORDER_CLR,
    SUCCESS, WARN, ERROR,
    TOTAL_BG, MAPPED_FG, UNMAPPED
)
from parser      import parse_registration_table
from dictionary  import get_sheet_names, load_dictionary_from_sheet, load_segments_from_sheet
from transformer import filter_and_transform, get_export_df


class GMExtractorApp(object):
    """
    Ventana principal de la aplicacion.
    Layout: barra superior azul + panel izquierdo (controles) + panel derecho (resultado).
    """

    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1280x760")
        self.root.minsize(1000, 640)
        self.root.configure(bg=LIGHT_BG)

        # ── Estado interno ────────────────────────────────────
        self.dictionary     = {}
        self.segments       = {}
        self.parsed_data    = None
        self.result_df      = None
        self._dict_filepath = None
        self._data_filepath = None

        self._apply_styles()
        self._build_ui()

    # ==========================================================
    #  ESTILOS TTK
    #  Modifica aqui fuentes, tamanos y colores de los widgets.
    # ==========================================================

    def _apply_styles(self):
        s = ttk.Style()
        try:
            s.theme_use('clam')
        except Exception:
            pass

        s.configure('.', background=LIGHT_BG, foreground=TEXT_MAIN,
                    font=('Segoe UI', 9))
        s.configure('TFrame',            background=LIGHT_BG)
        s.configure('TLabelframe',       background=PANEL_BG,
                    font=('Segoe UI', 9, 'bold'))
        s.configure('TLabelframe.Label', background=PANEL_BG, foreground=GM_BLUE)
        s.configure('TButton',           padding=[7, 4])
        s.configure('Primary.TButton',
                    font=('Segoe UI', 10, 'bold'),
                    foreground=WHITE, background=GM_BLUE, padding=[14, 7])
        s.map('Primary.TButton',
              background=[('active', GM_HOVER)],
              foreground=[('active', WHITE)])
        s.configure('Hdr.TLabel',
                    font=('Segoe UI', 10, 'bold'),
                    background=PANEL_BG, foreground=GM_BLUE)
        s.configure('Sub.TLabel',
                    font=('Segoe UI', 8),
                    background=PANEL_BG, foreground=TEXT_SEC)
        s.configure('Info.TLabel',
                    font=('Segoe UI', 8),
                    background=PANEL_BG, foreground=TEXT_MAIN)
        s.configure('Status.TLabel',
                    font=('Segoe UI', 8),
                    background=PANEL_BG)
        s.configure('Treeview',
                    font=('Segoe UI', 9), rowheight=22,
                    background=WHITE, fieldbackground=WHITE)
        s.configure('Treeview.Heading',
                    font=('Segoe UI', 8, 'bold'),
                    background=LIGHT_BG, foreground=TEXT_SEC)
        s.map('Treeview', background=[('selected', '#dbeafe')])

    # ==========================================================
    #  CONSTRUCCION DE LA UI
    # ==========================================================

    def _build_ui(self):
        """Construye el layout principal de la ventana."""

        # ── Barra superior azul GM ────────────────────────────
        topbar = tk.Frame(self.root, bg=GM_BLUE, height=44)
        topbar.pack(fill='x', side='top')
        topbar.pack_propagate(False)
        tk.Label(topbar, text="GM Table Extractor",
                 font=('Segoe UI', 13, 'bold'),
                 bg=GM_BLUE, fg=WHITE).pack(side='left', padx=16, pady=8)
        tk.Label(topbar,
                 text="Pricing & Incentives  -  GM Colombia  -  v" + APP_VERSION,
                 font=('Segoe UI', 9), bg=GM_BLUE,
                 fg='#cce5ff').pack(side='right', padx=16)

        # ── Contenedor principal: izquierdo + derecho ─────────
        main = tk.Frame(self.root, bg=LIGHT_BG)
        main.pack(fill='both', expand=True, padx=8, pady=8)
        main.columnconfigure(0, weight=0, minsize=368)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=LIGHT_BG)
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 6))
        left.columnconfigure(0, weight=1)

        right = tk.Frame(main, bg=PANEL_BG,
                         highlightbackground=BORDER_CLR, highlightthickness=1)
        right.grid(row=0, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        self._build_left_panel(left)
        self._build_right_panel(right)

    # ----------------------------------------------------------
    #  PANEL IZQUIERDO
    # ----------------------------------------------------------

    def _build_left_panel(self, parent):
        """
        Construye las 3 secciones del panel de control:
            Seccion 1: Diccionario
            Seccion 2: Tabla de Matriculas (datos + texto pegar)
            Seccion 3: Filtros + boton Generar
        """
        self._build_section_dictionary(parent)
        self._build_section_data(parent)
        self._build_section_filters(parent)

    def _build_section_dictionary(self, parent):
        """Seccion 1: carga del archivo de diccionario y seleccion de hoja."""
        sec = ttk.LabelFrame(parent, text=" 1  Diccionario ")
        sec.grid(row=0, column=0, sticky='ew', pady=(0, 6))
        sec.columnconfigure(1, weight=1)

        ttk.Button(sec, text="Cargar Base.xlsx",
                   command=self._load_dict_file).grid(
            row=0, column=0, padx=(10, 6), pady=(8, 4), sticky='w')

        ttk.Label(sec, text="Hoja:",
                  style='Info.TLabel').grid(row=0, column=1, sticky='e', padx=(0, 4))

        self.var_dict_sheet = tk.StringVar()
        self.cmb_dict_sheet = ttk.Combobox(
            sec, textvariable=self.var_dict_sheet,
            state='disabled', width=14)
        self.cmb_dict_sheet.grid(row=0, column=2, padx=(0, 10), pady=(8, 4), sticky='w')
        self.cmb_dict_sheet.bind('<<ComboboxSelected>>', self._on_dict_sheet_change)

        self.lbl_dict_status = ttk.Label(sec, text="Sin diccionario cargado.",
                                         style='Sub.TLabel')
        self.lbl_dict_status.grid(row=1, column=0, columnspan=3,
                                  sticky='w', padx=10, pady=(0, 8))

    def _build_section_data(self, parent):
        """Seccion 2: carga del archivo de datos y area de pegado."""
        sec = ttk.LabelFrame(parent, text=" 2  Tabla de Matriculas ")
        sec.grid(row=1, column=0, sticky='ew', pady=(0, 6))
        sec.columnconfigure(1, weight=1)

        ttk.Button(sec, text="Cargar Excel/TSV",
                   command=self._load_data_file).grid(
            row=0, column=0, padx=(10, 6), pady=(8, 4), sticky='w')

        ttk.Label(sec, text="Hoja:",
                  style='Info.TLabel').grid(row=0, column=1, sticky='e', padx=(0, 4))

        self.var_data_sheet = tk.StringVar()
        self.cmb_data_sheet = ttk.Combobox(
            sec, textvariable=self.var_data_sheet,
            state='disabled', width=14)
        self.cmb_data_sheet.grid(row=0, column=2, padx=(0, 10), pady=(8, 4), sticky='w')
        self.cmb_data_sheet.bind('<<ComboboxSelected>>', self._on_data_sheet_change)

        ttk.Label(sec, text="-- o pega la tabla directamente abajo --",
                  style='Sub.TLabel').grid(
            row=1, column=0, columnspan=3, sticky='w', padx=10)

        self.txt_raw = scrolledtext.ScrolledText(
            sec, height=10, font=('Consolas', 7), wrap='none',
            bg='#fafafa', fg='#333', insertbackground=GM_BLUE,
            selectbackground='#bfdbfe')
        self.txt_raw.grid(row=2, column=0, columnspan=3,
                          sticky='nsew', padx=10, pady=(4, 4))

        parse_row = tk.Frame(sec, bg=PANEL_BG)
        parse_row.grid(row=3, column=0, columnspan=3,
                       sticky='ew', padx=10, pady=(0, 8))
        ttk.Button(parse_row, text="Analizar tabla",
                   command=self._parse_pasted).pack(side='left')
        self.lbl_parse_status = ttk.Label(parse_row, text="",
                                          style='Status.TLabel')
        self.lbl_parse_status.pack(side='left', padx=8)

    def _build_section_filters(self, parent):
        """Seccion 3: filtros de periodo y boton Generar Tabla."""
        sec = ttk.LabelFrame(parent, text=" 3  Filtros ")
        sec.grid(row=2, column=0, sticky='ew', pady=(0, 6))

        # Fila 0: selectores de Ano y Granularidad
        ttk.Label(sec, text="Ano:").grid(
            row=0, column=0, padx=(10, 4), pady=7, sticky='w')
        self.var_year = tk.StringVar(value='2026')
        self.cmb_year = ttk.Combobox(
            sec, textvariable=self.var_year,
            values=['2026', '2025', '2027', '2024', 'all'],
            state='readonly', width=9)
        self.cmb_year.grid(row=0, column=1, padx=(0, 10), sticky='w')

        ttk.Label(sec, text="Granularidad:").grid(
            row=0, column=2, padx=(4, 4), sticky='w')
        self.var_gran = tk.StringVar(value='monthly')
        ttk.Combobox(sec, textvariable=self.var_gran,
                     values=['monthly', 'quarterly', 'annual', 'all'],
                     state='readonly', width=12).grid(
            row=0, column=3, padx=(0, 10), sticky='w')

        # Fila 1: checkboxes de opciones
        opts_f = tk.Frame(sec, bg=PANEL_BG)
        opts_f.grid(row=1, column=0, columnspan=4,
                    sticky='w', padx=10, pady=(0, 8))

        self.var_seg      = tk.BooleanVar(value=True)
        self.var_unmapped = tk.BooleanVar(value=True)

        for label_text, var in [
            ("Segmento",    self.var_seg),
            ("No mapeados", self.var_unmapped),
        ]:
            ttk.Checkbutton(opts_f, text=label_text,
                            variable=var).pack(side='left', padx=5)

        # Boton principal
        ttk.Button(parent, text="Generar Tabla",
                   style='Primary.TButton',
                   command=self._process).grid(
            row=3, column=0, sticky='ew', pady=(0, 4))

    # ----------------------------------------------------------
    #  PANEL DERECHO
    # ----------------------------------------------------------

    def _build_right_panel(self, parent):
        """
        Construye el panel de resultado:
            - Fila 0: meta-info + botones de exportacion
            - Fila 1: divisor visual
            - Fila 2: Treeview con scroll horizontal y vertical
        """
        # Cabecera con meta-info y botones
        hdr = tk.Frame(parent, bg=PANEL_BG)
        hdr.grid(row=0, column=0, sticky='ew', padx=12, pady=(10, 4))
        hdr.columnconfigure(0, weight=1)

        self.lbl_result_meta = ttk.Label(hdr, text="Sin resultados.",
                                         style='Sub.TLabel',
                                         background=PANEL_BG)
        self.lbl_result_meta.pack(side='left')

        for btn_text, cmd in [
            ("Exportar CSV",   self._export_csv),
            ("Exportar Excel", self._export_excel),
            ("Copiar (Excel)", self._copy_tsv),
        ]:
            ttk.Button(hdr, text=btn_text, command=cmd).pack(
                side='right', padx=(4, 0))

        # Divisor
        tk.Frame(parent, bg=BORDER_CLR, height=1).grid(
            row=1, column=0, sticky='ew')

        # Treeview con doble scroll
        tree_f = tk.Frame(parent, bg=PANEL_BG)
        tree_f.grid(row=2, column=0, sticky='nsew')
        tree_f.columnconfigure(0, weight=1)
        tree_f.rowconfigure(0, weight=1)

        self.result_tree = ttk.Treeview(
            tree_f, show='headings', selectmode='browse')
        self.result_tree.grid(row=0, column=0, sticky='nsew')

        vsb = ttk.Scrollbar(tree_f, orient='vertical',
                            command=self.result_tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        hsb = ttk.Scrollbar(tree_f, orient='horizontal',
                            command=self.result_tree.xview)
        hsb.grid(row=1, column=0, sticky='ew')
        self.result_tree.configure(yscrollcommand=vsb.set,
                                   xscrollcommand=hsb.set)

        # Tags visuales para filas del resultado
        self.result_tree.tag_configure('total',
                                       background=TOTAL_BG,
                                       font=('Segoe UI', 9, 'bold'))
        self.result_tree.tag_configure('mapped',   foreground=MAPPED_FG)
        self.result_tree.tag_configure('unmapped', foreground=UNMAPPED)

        # Placeholder cuando no hay datos
        self.lbl_empty = ttk.Label(
            tree_f,
            text="Carga el diccionario, pega la tabla y presiona Generar Tabla",
            style='Sub.TLabel', background=WHITE)
        self.lbl_empty.place(relx=0.5, rely=0.5, anchor='center')

    # ==========================================================
    #  LOGICA: DICCIONARIO
    # ==========================================================

    def _load_dict_file(self):
        """Abre dialogo para seleccionar Base.xlsx y puebla el Combobox de hojas."""
        path = filedialog.askopenfilename(
            title="Selecciona archivo de diccionario",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")])
        if not path:
            return
        try:
            sheets = get_sheet_names(path)
            self._dict_filepath          = path
            self.cmb_dict_sheet['values'] = sheets
            self.cmb_dict_sheet['state']  = 'readonly'
            # Seleccionar PERU por defecto si existe
            default = 'PERU' if 'PERU' in sheets else sheets[0]
            self.var_dict_sheet.set(default)
            self._reload_dictionary()
        except Exception as e:
            messagebox.showerror("Error al cargar diccionario",
                                 str(e), parent=self.root)

    def _on_dict_sheet_change(self, event=None):
        """Recarga el diccionario cuando el usuario cambia de hoja."""
        self._reload_dictionary()

    def _reload_dictionary(self):
        """Llama a dictionary.py para cargar el mapeo de la hoja seleccionada."""
        if not self._dict_filepath:
            return
        sheet = self.var_dict_sheet.get()
        if not sheet:
            return
        try:
            self.dictionary = load_dictionary_from_sheet(
                self._dict_filepath, sheet)
            # Cargar segmentos desde la hoja SEGMENT del mismo archivo
            try:
                self.segments = load_segments_from_sheet(
                    self._dict_filepath, 'SEGMENT')
                n_seg = len(self.segments)
            except Exception:
                self.segments = {}
                n_seg = 0
            n = len(self.dictionary)
            self._set_status(
                self.lbl_dict_status,
                str(n) + " mapeos  |  " + str(n_seg) + " segmentos  [" +
                Path(self._dict_filepath).name + " / " + sheet + "]",
                SUCCESS)
        except Exception as e:
            self._set_status(self.lbl_dict_status,
                             "Error: " + str(e), ERROR)

    # ==========================================================
    #  LOGICA: DATOS
    # ==========================================================

    def _load_data_file(self):
        """
        Abre dialogo para cargar el archivo de datos.
        Si es Excel, puebla el Combobox de hojas y carga la primera.
        Si es TSV/CSV, lo carga directamente en el area de texto.
        """
        path = filedialog.askopenfilename(
            title="Selecciona archivo de tabla",
            filetypes=[
                ("Excel",           "*.xlsx *.xls"),
                ("TSV / CSV / TXT", "*.tsv *.csv *.txt"),
                ("Todos",           "*.*"),
            ])
        if not path:
            return

        self._data_filepath = path
        ext = Path(path).suffix.lower()

        if ext in ('.xlsx', '.xls'):
            try:
                sheets = get_sheet_names(path)
                self.cmb_data_sheet['values'] = sheets
                self.cmb_data_sheet['state']  = 'readonly'
                self.var_data_sheet.set(sheets[0])
                self._reload_data_sheet()
            except Exception as e:
                messagebox.showerror("Error al cargar Excel",
                                     str(e), parent=self.root)
        else:
            # Archivo de texto plano (TSV, CSV, TXT)
            self.cmb_data_sheet['values'] = []
            self.cmb_data_sheet['state']  = 'disabled'
            self.var_data_sheet.set('')
            try:
                with open(path, encoding='utf-8-sig', errors='replace') as fh:
                    text = fh.read()
                self._set_raw_text(text)
            except Exception as e:
                messagebox.showerror("Error al cargar archivo",
                                     str(e), parent=self.root)

    def _on_data_sheet_change(self, event=None):
        """Recarga la hoja de datos cuando el usuario cambia de hoja."""
        self._reload_data_sheet()

    def _reload_data_sheet(self):
        """Lee la hoja seleccionada del Excel de datos y la pone en el area de texto."""
        if not self._data_filepath:
            return
        sheet = self.var_data_sheet.get()
        if not sheet:
            return
        try:
            df_tmp = pd.read_excel(
                self._data_filepath, sheet_name=sheet,
                header=None, dtype=str)
            text = df_tmp.to_csv(sep='\t', index=False, header=False, na_rep='')
            self._set_raw_text(text)
        except Exception as e:
            messagebox.showerror("Error al cargar hoja",
                                 str(e), parent=self.root)

    def _set_raw_text(self, text):
        """Inserta texto en el area de pegado y lanza el analisis automatico."""
        self.txt_raw.delete('1.0', 'end')
        self.txt_raw.insert('1.0', text)
        self._parse_pasted()

    def _parse_pasted(self):
        """
        Llama a parser.py con el contenido actual del area de texto.
        Actualiza el Combobox de anos con los detectados en la tabla.
        """
        raw = self.txt_raw.get('1.0', 'end').strip()
        if not raw:
            self._set_status(self.lbl_parse_status, "Sin datos.", WARN)
            return

        result = parse_registration_table(raw)
        if result is None:
            self._set_status(
                self.lbl_parse_status,
                "No se detecto fila de encabezados. "
                "Asegurate de incluir la fila con los anos (2025, 2026...).",
                ERROR)
            self.parsed_data = None
            return

        self.parsed_data = result
        years = sorted(set(c['year'] for c in result['columns'] if c.get('year')))

        # Actualizar opciones del combo de ano
        opts = [str(y) for y in years] + ['all']
        self.cmb_year['values'] = opts
        self.var_year.set('2026' if '2026' in opts else (opts[0] if opts else ''))

        self._set_status(
            self.lbl_parse_status,
            str(len(result['groups'])) + " modelos  |  "
            "Anos: " + ', '.join(str(y) for y in years),
            SUCCESS)

    # ==========================================================
    #  LOGICA: PROCESAMIENTO PRINCIPAL
    # ==========================================================

    def _process(self):
        """
        Orquesta el flujo completo:
            parser -> transformer -> render
        """
        if not self.parsed_data:
            messagebox.showwarning(
                "Sin datos",
                "Primero carga o pega la tabla y presiona 'Analizar tabla'.",
                parent=self.root)
            return

        year_str    = self.var_year.get()
        year_filter = 'all' if year_str == 'all' else int(year_str)

        df, err = filter_and_transform(
            self.parsed_data,
            self.dictionary,
            year_filter   = year_filter,
            gran_filter   = self.var_gran.get(),
            segments      = self.segments,
            incl_segment  = self.var_seg.get(),
            incl_unmapped = self.var_unmapped.get(),
        )

        if err:
            messagebox.showwarning("Sin resultados", err, parent=self.root)
            return

        self.result_df = df
        self._render_result(df)

    # ==========================================================
    #  RENDER DEL RESULTADO
    # ==========================================================

    def _render_result(self, df):
        """
        Dibuja el DataFrame en el Treeview del panel derecho.
        Las columnas internas (_mapped, _is_total) se excluyen del display.
        """
        tree = self.result_tree
        tree.delete(*tree.get_children())
        self.lbl_empty.place_forget()

        display_cols = [c for c in df.columns if not c.startswith('_')]
        tree['columns'] = display_cols

        # Configurar encabezados y anchos de columna
        for col in display_cols:
            is_text = col in ('Nameplate Country', 'Nameplate', 'Segment')
            w = 190 if is_text else (54 if 'MS%' in col else 66)
            tree.heading(col, text=col, anchor='w' if is_text else 'e')
            tree.column(col, width=w, anchor='w' if is_text else 'e',
                        minwidth=44, stretch=False)

        # Insertar filas
        for _, row in df.iterrows():
            vals      = [str(row[c]) if row[c] is not None else ''
                         for c in display_cols]
            is_total  = bool(row.get('_is_total', False))
            is_mapped = bool(row.get('_mapped',   False))
            tag = 'total' if is_total else ('mapped' if is_mapped else 'unmapped')
            tree.insert('', 'end', values=vals, tags=(tag,))

        # Actualizar meta-info
        n_total  = len(df)
        n_mapped = int(df['_mapped'].sum())   if '_mapped'   in df.columns else 0
        n_totals = int(df['_is_total'].sum()) if '_is_total' in df.columns else 0

        self.lbl_result_meta.configure(
            text=(str(n_total) + " registros  |  Mapeados: " + str(n_mapped) +
                  "  |  Totales: " + str(n_totals) +
                  "  |  Ano: " + self.var_year.get() +
                  "  |  " + self.var_gran.get()))

    # ==========================================================
    #  EXPORTACION
    # ==========================================================

    def _get_export_df(self):
        """Obtiene el DataFrame listo para exportar (sin columnas internas)."""
        if self.result_df is None:
            messagebox.showinfo("Sin datos", "Genera la tabla primero.",
                                parent=self.root)
            return None
        return get_export_df(self.result_df)

    def _copy_tsv(self):
        """Copia la tabla al portapapeles en formato TSV (pegar en Excel)."""
        df = self._get_export_df()
        if df is None:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(df.to_csv(sep='\t', index=False))
        messagebox.showinfo("Copiado",
                            "Tabla copiada al portapapeles.\nPega con Ctrl+V en Excel.",
                            parent=self.root)

    def _export_excel(self):
        """Guarda el resultado como archivo .xlsx con anchos de columna ajustados."""
        df = self._get_export_df()
        if df is None:
            return
        yr   = self.var_year.get()
        gran = self.var_gran.get()
        path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[("Excel", "*.xlsx")],
            initialfile="tabla_GM_" + yr + "_" + gran + ".xlsx")
        if not path:
            return
        try:
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Tabla GM')
                ws = writer.sheets['Tabla GM']
                for col_cells in ws.columns:
                    max_len = max(
                        (len(str(c.value or '')) for c in col_cells), default=10)
                    ws.column_dimensions[
                        col_cells[0].column_letter].width = min(max_len + 3, 42)
            messagebox.showinfo("Exportado",
                                "Archivo guardado:\n" + path, parent=self.root)
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e), parent=self.root)

    def _export_csv(self):
        """Guarda el resultado como archivo .csv separado por punto y coma."""
        df = self._get_export_df()
        if df is None:
            return
        yr   = self.var_year.get()
        gran = self.var_gran.get()
        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[("CSV (separado por ;)", "*.csv")],
            initialfile="tabla_GM_" + yr + "_" + gran + ".csv")
        if not path:
            return
        try:
            df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')
            messagebox.showinfo("Exportado",
                                "CSV guardado:\n" + path, parent=self.root)
        except Exception as e:
            messagebox.showerror("Error al exportar", str(e), parent=self.root)

    # ==========================================================
    #  UTILIDADES
    # ==========================================================

    @staticmethod
    def _set_status(label, text, color):
        """Actualiza el texto y color de un label de estado."""
        label.configure(text=text, foreground=color)