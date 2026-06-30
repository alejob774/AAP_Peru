# dictionary.py
import pandas as pd
from config import normalize

COL_SOURCE   = 'NAMEPLATE COUNTRY'
COL_TARGET   = 'NAMEPLATE'
COL_SEGMENT  = 'SEGMENT'

def get_sheet_names(filepath):
    return pd.ExcelFile(filepath).sheet_names

def load_dictionary_from_sheet(filepath, sheet_name):
    """
    Carga el mapeo NAMEPLATE COUNTRY -> NAMEPLATE.
    Las claves se normalizan con normalize() para que el matching
    sea robusto frente a mayusculas, tildes y espacios extra.
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name, dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]

    required = {COL_SOURCE, COL_TARGET}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(
            "La hoja '" + sheet_name + "' no tiene las columnas: " +
            ', '.join(sorted(missing)) + "\n" +
            "Columnas encontradas: " + ', '.join(df.columns))

    mapping = {}
    for _, row in df.iterrows():
        source = str(row[COL_SOURCE]).strip()
        target = str(row[COL_TARGET]).strip()
        if not source or source.lower() == 'nan':
            continue
        if not target or target.lower() == 'nan':
            continue
        key = normalize(source)          # <-- normalizar la clave
        if key not in mapping:
            mapping[key] = target        # valor se deja tal cual (nombre destino)
    return mapping

def load_segments_from_sheet(filepath, sheet_name='SEGMENT'):
    """
    Carga el mapeo NAMEPLATE -> SEGMENT.
    La clave es NAMEPLATE (nombre destino), NO NAMEPLATE COUNTRY.
    Asi funciona como un XLOOKUP: Nameplate -> Segment.
    """
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, dtype=str)
    except Exception:
        return {}

    df.columns = [c.strip().upper() for c in df.columns]

    if COL_TARGET not in df.columns or COL_SEGMENT not in df.columns:
        return {}

    segments = {}
    for _, row in df.iterrows():
        nameplate = str(row[COL_TARGET]).strip()   # <-- clave = NAMEPLATE
        segment   = str(row[COL_SEGMENT]).strip()
        if not nameplate or nameplate.lower() == 'nan':
            continue
        if not segment or segment.lower() == 'nan':
            continue
        key = normalize(nameplate)
        if key not in segments:
            segments[key] = segment
    return segments

