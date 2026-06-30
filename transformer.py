# transformer.py
import re
import pandas as pd
from config import normalize

_EXCEL_ERROR_RE = re.compile(
    r'^(#+|#DIV/0!|#REF!|#N/A|#VALUE!|#NUM!|nan|None)$',
    re.IGNORECASE
)

TOTAL_PREFIXES = ('TOTAL', 'RS ', 'IND.')
TOTAL_KEYWORDS = ('AJUSTE',)

def _is_total_row(model_name):
    mu = normalize(model_name)
    if any(mu.startswith(p) for p in TOTAL_PREFIXES):
        return True
    if any(k in mu for k in TOTAL_KEYWORDS):
        return True
    return False

def _clean_value(raw):
    val = raw.strip() if isinstance(raw, str) else str(raw or '').strip()
    if _EXCEL_ERROR_RE.match(val):
        return ''
    return val

def _col_matches_filter(col, year_filter, gran_filter):
    year_ok = (year_filter == 'all') or (col['year'] == year_filter)
    if gran_filter == 'all':
        gran_ok = True
    elif gran_filter == 'annual':
        gran_ok = col['type'] == 'annual'
    else:
        gran_ok = col['type'] == gran_filter
    return year_ok and gran_ok

def filter_and_transform(
    parsed,
    dictionary,
    year_filter,
    gran_filter,
    segments      = None,
    incl_segment  = True,
    incl_unmapped = True,
):
    columns = parsed['columns']
    groups  = parsed['groups']

    if not groups:
        return None, (
            "El parser encontro 0 modelos.\n"
            "Verifica que la hoja correcta este seleccionada.")

    # 1. Filtrar columnas
    filt_cols = [c for c in columns
                 if _col_matches_filter(c, year_filter, gran_filter)]

    if not filt_cols:
        available = sorted(set(c['year'] for c in columns if c.get('year')))
        return None, (
            "No se encontraron columnas para:\n"
            "  Ano: " + str(year_filter) + "\n"
            "  Granularidad: " + gran_filter + "\n\n"
            "Anos disponibles: " + ', '.join(str(y) for y in available))

    # 2. Excluir filas TOTAL siempre
    groups = [g for g in groups if not _is_total_row(g['model'])]

    # 3. Construir registros
    records       = []
    n_skipped_map = 0

    def _is_zero_or_empty(v):
        """True si el valor es vacio, '0', '0.0', '0,0' o equivalente."""
        v = str(v).strip()
        if v == '':
            return True
        v_clean = v.replace('.', '').replace(',', '').strip()
        try:
            return float(v_clean) == 0.0
        except ValueError:
            return False

    for g in groups:
        nc         = g['model']
        nc_key     = normalize(nc)

        np_        = dictionary.get(nc_key, '')
        is_mapped  = bool(np_)
        display    = np_ if np_ else nc

        if not incl_unmapped and not is_mapped:
            n_skipped_map += 1
            continue

        # XLOOKUP: Nameplate -> Segment (desde Base.xlsx hoja SEGMENT)
        np_key         = normalize(np_) if np_ else ''
        seg_from_base  = (segments or {}).get(np_key, '')
        seg_from_table = g['segment']
        segment        = seg_from_base if seg_from_base else seg_from_table

        rec = {
            'Nameplate Country': nc,
            'Nameplate':         display,
            '_mapped':           is_mapped,
            '_is_total':         False,
        }

        if incl_segment:
            rec['Segment'] = segment

        for c in filt_cols:
            idx     = c['idx']
            raw_val = g['model_vals'][idx] if idx < len(g['model_vals']) else ''
            rec[c['display']] = _clean_value(raw_val)

        # Ignorar filas donde TODOS los valores son 0 o vacios
        period_vals = [rec[c['display']] for c in filt_cols]
        if all(_is_zero_or_empty(v) for v in period_vals):
            continue

        records.append(rec)


    if not records:
        msg  = "No hay registros despues de aplicar los filtros.\n\n"
        msg += "Saltados por 'no mapeados': " + str(n_skipped_map) + "\n"
        if n_skipped_map > 0:
            msg += "\n-> Activa 'No mapeados' o carga el diccionario."
        return None, msg

    return pd.DataFrame(records), None

def get_export_df(result_df):
    if result_df is None:
        return None
    return result_df[[c for c in result_df.columns if not c.startswith('_')]]
