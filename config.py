# config.py
# ============================================================
# Constantes globales de la aplicacion: version, colores y
# abreviaturas de meses. Modifica aqui para cambiar el tema
# visual sin tocar el resto del codigo.
# ============================================================

APP_VERSION = "2.0"
APP_TITLE   = "GM Table Extractor  v" + APP_VERSION

# ── Abreviaturas de meses (para columnas mensuales) ──────────
MONTH_ABBR = {
    'ene': 'Ene', 'feb': 'Feb', 'mar': 'Mar', 'abr': 'Abr',
    'may': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Ago',
    'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'dic': 'Dic'
}

# ── Normalizacion de texto ───────────────────────────────────
import unicodedata as _ud
import re as _re

def normalize(text):
    """
    Normaliza un nombre de modelo para que el mapeo sea robusto:
        1. Convierte a string y quita espacios laterales
        2. Pasa a MAYUSCULAS
        3. Elimina tildes y diacriticos (NFD + strip Mn)
        4. Comprime espacios internos multiples a uno solo
        5. Quita caracteres que no sean alfanumericos, espacio,
           guion (-), punto (.) o signo mas (+)
           (conserva: 'JOY NB', '310C', '260S PLUS EV - SPARK EV')
    """
    if not text:
        return ''
    text = str(text).strip().upper()
    # Eliminar diacriticos
    text = _ud.normalize('NFD', text)
    text = ''.join(c for c in text if _ud.category(c) != 'Mn')
    # Comprimir espacios
    text = _re.sub(r'\s+', ' ', text)
    # Quitar caracteres no deseados (conserva alfanum, espacio, - . +)
    text = _re.sub(r'[^\w\s\-\.+]', '', text)
    return text.strip()


# ── Paleta de colores ─────────────────────────────────────────
GM_BLUE    = '#0075C9'   # azul principal GM
GM_HOVER   = '#005fa3'   # azul oscuro (hover de botones)
LIGHT_BG   = '#f5f7fa'   # fondo general de la ventana
PANEL_BG   = '#ffffff'   # fondo de paneles internos
WHITE      = '#ffffff'
TEXT_MAIN  = '#1a1a2e'   # texto principal
TEXT_SEC   = '#6b7280'   # texto secundario / placeholders
BORDER_CLR = '#dde3ec'   # bordes de paneles

# ── Colores de estado ─────────────────────────────────────────
SUCCESS    = '#1a6e2e'   # verde: operacion exitosa
WARN       = '#b45309'   # naranja: advertencia
ERROR      = '#b91c1c'   # rojo: error

# ── Colores de filas en la tabla resultado ────────────────────
TOTAL_BG   = '#fefce8'   # fondo amarillo claro para filas TOTAL
MAPPED_FG  = '#1a6e2e'   # texto verde para modelos mapeados
UNMAPPED   = '#b45309'   # texto naranja para modelos sin mapeo


# ===============================================================
#  NORMALIZACION DE TEXTO
#  Usada en dictionary.py y transformer.py para comparar nombres
#  de modelo de forma robusta (mayusculas, tildes, espacios).
# ===============================================================

import re
import unicodedata


def normalize(text):
    """
    Normaliza un nombre de modelo para comparacion robusta:
        1. Convierte a string y quita espacios laterales
        2. Convierte a mayusculas
        3. Elimina tildes y diacriticos (e -> e, a -> a, etc.)
        4. Colapsa espacios multiples en uno solo

    Ejemplos:
        'joy sedan'       -> 'JOY SEDAN'
        '  NEW  ONIX  '  -> 'NEW ONIX'
        'Captiva'         -> 'CAPTIVA'
        'N400 Move'       -> 'N400 MOVE'
        '310C  SEDAN'     -> '310C SEDAN'
    """
    if text is None:
        return ''
    # 1. String + strip
    s = str(text).strip()
    # 2. Mayusculas
    s = s.upper()
    # 3. Quitar tildes: descomponer unicode y eliminar marcas diacriticas
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    # 4. Colapsar espacios multiples
    s = re.sub(r'\s+', ' ', s).strip()
    return s