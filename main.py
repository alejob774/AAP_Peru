
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py
# ============================================================
# Punto de entrada de la aplicacion GM Table Extractor.
#
# Para ejecutar directamente:
#     python main.py
#
# Para compilar como ejecutable (.exe):
#     pip install pyinstaller
#     pyinstaller --onefile --windowed --name "GM_Extractor" main.py
#
# Todos los archivos del proyecto deben estar en la misma carpeta:
#     main.py        <- este archivo (solo entry point)
#     config.py      <- colores y constantes
#     parser.py      <- logica de parseo de la tabla
#     dictionary.py  <- carga del diccionario desde Excel
#     transformer.py <- filtrado y transformacion de datos
#     app.py         <- UI completa (Tkinter)
#
# Dependencias externas (instalar una sola vez):
#     pip install pandas openpyxl
# ============================================================

import tkinter as tk
from app import GMExtractorApp


if __name__ == '__main__':
    root = tk.Tk()
    app  = GMExtractorApp(root)
    root.mainloop()
