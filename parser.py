# parser.py  v1.4
import re
from config import MONTH_ABBR

MONTH_ORDER = ['ene','feb','mar','abr','may','jun',
               'jul','ago','sep','oct','nov','dic']
_NUM_TO_MONTH = {1:'ene',2:'feb',3:'mar',4:'abr',5:'may',6:'jun',
                 7:'jul',8:'ago',9:'sep',10:'oct',11:'nov',12:'dic'}
_HASH_RE = re.compile(r'^#+$')

def _is_hash_cell(cell):
    return bool(_HASH_RE.match(str(cell).strip()))

def _parse_month_cell(cell):
    s = str(cell).strip()
    m = re.match(r'^(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(\d{2})$',
                 s, re.IGNORECASE)
    if m:
        return (m.group(1).lower(), m.group(2))
    m2 = re.match(r'^(\d{4})-(\d{2})-\d{2}', s)
    if m2:
        yr = int(m2.group(1))
        mo = int(m2.group(2))
        if 2015 <= yr <= 2030 and 1 <= mo <= 12:
            return (_NUM_TO_MONTH[mo], str(yr)[2:])
    return None

def _next_month(mn, suffix):
    idx = MONTH_ORDER.index(mn)
    if idx == 11:
        return MONTH_ORDER[0], str(int(suffix) + 1).zfill(2)
    return MONTH_ORDER[idx + 1], suffix

def _prev_month(mn, suffix):
    idx = MONTH_ORDER.index(mn)
    if idx == 0:
        return MONTH_ORDER[11], str(int(suffix) - 1).zfill(2)
    return MONTH_ORDER[idx - 1], suffix

def _has_letters(text):
    return bool(re.search(r'[A-Za-z]', text))

def _count_period_tokens(cells):
    score = 0
    max_year = 0
    for c in cells:
        s = str(c).strip()
        if re.match(r'^20(1[5-9]|2[0-9])(\.0)?$', s):
            score += 1
            max_year = max(max_year, int(float(s)))
            continue
        m_mo = re.match(r'^(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(\d{2})$',
                        s, re.IGNORECASE)
        if m_mo:
            score += 1
            max_year = max(max_year, 2000 + int(m_mo.group(2)))
            continue
        m_iso = re.match(r'^(20(1[5-9]|2[0-9]))-(\d{2})-\d{2}', s)
        if m_iso:
            score += 1
            max_year = max(max_year, int(m_iso.group(1)))
            continue
        if re.match(r'^Q[1-4]$', s):
            score += 1
            continue
        if s == 'CY':
            score += 1
            continue
    return score, max_year

def _infer_missing_months(hdr_row):
    row = list(hdr_row)
    for _pass in range(20):
        changed = False
        for i, cell in enumerate(row):
            if not _is_hash_cell(cell):
                continue
            prev_parsed = None
            for j in range(i - 1, -1, -1):
                p = _parse_month_cell(row[j])
                if p:
                    prev_parsed = p
                    break
                if re.match(r'^20(1[5-9]|2[0-9])(\.0)?$', str(row[j]).strip()):
                    break
            if prev_parsed:
                mn, suf = _next_month(prev_parsed[0], prev_parsed[1])
                row[i] = mn + '-' + suf
                changed = True
        for i in range(len(row) - 1, -1, -1):
            if not _is_hash_cell(row[i]):
                continue
            next_parsed = None
            for j in range(i + 1, len(row)):
                p = _parse_month_cell(row[j])
                if p:
                    next_parsed = p
                    break
                if re.match(r'^20(1[5-9]|2[0-9])(\.0)?$', str(row[j]).strip()):
                    break
            if next_parsed:
                mn, suf = _prev_month(next_parsed[0], next_parsed[1])
                row[i] = mn + '-' + suf
                changed = True
        if not changed:
            break
    return row

def build_columns(hdr_row):
    hdr_row = _infer_missing_months(hdr_row)
    cols = []
    current_year = None
    cy_count = {}

    for idx, raw in enumerate(hdr_row):
        cell = str(raw).strip() if raw is not None else ''

        # Ano anual: '2017', '2026', '2017.0'
        if re.match(r'^20(1[5-9]|2[0-9])(\.0)?$', cell):
            yr = int(float(cell))
            current_year = yr
            cols.append({'idx': idx, 'label': cell, 'year': yr,
                         'type': 'annual', 'display': str(yr)})
            continue

        # Mensual espanol: ene-26
        m_es = re.match(
            r'^(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)-(\d{2})$',
            cell, re.IGNORECASE)
        if m_es:
            yr = 2000 + int(m_es.group(2))
            current_year = yr
            mn = m_es.group(1).lower()
            cols.append({'idx': idx, 'label': cell, 'year': yr,
                         'type': 'monthly',
                         'display': MONTH_ABBR.get(mn, mn) + '-' + m_es.group(2)})
            continue

        # Mensual ISO: 2026-01-01
        m_iso = re.match(r'^(20(1[5-9]|2[0-9]))-(\d{2})-\d{2}', cell)
        if m_iso:
            yr = int(m_iso.group(1))
            mo = int(m_iso.group(3))
            current_year = yr
            mn = _NUM_TO_MONTH.get(mo, 'ene')
            suf = str(yr)[2:]
            cols.append({'idx': idx, 'label': cell, 'year': yr,
                         'type': 'monthly',
                         'display': MONTH_ABBR.get(mn, mn) + '-' + suf})
            continue

        # Trimestral: Q1-Q4
        if re.match(r'^Q[1-4]$', cell):
            yr = current_year
            cols.append({'idx': idx, 'label': cell, 'year': yr,
                         'type': 'quarterly',
                         'display': cell + ('-' + str(yr) if yr else '')})
            continue

        # CY
        if cell == 'CY':
            yr = current_year
            cy_count[yr] = cy_count.get(yr, 0) + 1
            delta = ' (D)' if cy_count[yr] > 1 else ''
            cols.append({'idx': idx, 'label': 'CY', 'year': yr,
                         'type': 'annual',
                         'display': 'CY ' + str(yr) + delta})
            continue

    return cols

def _detect_name_col(rows, hdr_idx):
    """
    Detecta en que columna estan los nombres de modelo.
    El Excel tiene: col0=vacio, col1=nombre, col2=vacio, col3+=datos.
    Busca la columna con mas celdas que contengan letras.
    """
    data_rows = rows[hdr_idx + 1:]
    sample = [r for r in data_rows[:60] if any(c.strip() for c in r)][:30]

    if not sample:
        return 0

    max_cols = max((len(r) for r in sample), default=1)
    col_scores = [0] * max_cols

    for row in sample:
        for ci, cell in enumerate(row):
            val = cell.strip()
            if _has_letters(val) and not re.match(r'^MS%', val, re.IGNORECASE):
                col_scores[ci] += 1

    return col_scores.index(max(col_scores))

def parse_registration_table(raw_text):
    lines = raw_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    rows  = [line.split('\t') for line in lines]

    # 1. Encontrar el mejor encabezado
    best_idx      = -1
    best_score    = 3
    best_max_year = 0

    for i, row in enumerate(rows):
        score, max_year = _count_period_tokens(row)
        if score > best_score:
            best_score    = score
            best_max_year = max_year
            best_idx      = i
        elif score == best_score and max_year > best_max_year:
            best_max_year = max_year
            best_idx      = i

    if best_idx == -1:
        return None

    columns  = build_columns(rows[best_idx])

    # 2. Detectar columna de nombres (col0=NaN, col1=nombre en este Excel)
    name_col = _detect_name_col(rows, best_idx)

    data_rows = rows[best_idx + 1:]
    groups    = []
    i         = 0

    # 3. Parsear grupos
    while i < len(data_rows):
        row = data_rows[i]

        fc = (row[name_col].strip() if len(row) > name_col else '').strip()

        # Fila vacia
        if not any(c.strip() for c in row):
            i += 1
            continue

        # MS% suelto
        if re.match(r'^MS%', fc, re.IGNORECASE):
            i += 1
            continue

        # Sin letras o vacio en columna de nombre
        if not fc or not _has_letters(fc):
            i += 1
            continue

        # Fila de modelo
        model_name = fc
        model_vals = row
        i += 1

        seg_name  = ''
        seg_vals  = []
        ms_vals   = []
        collected = 0

        while i < len(data_rows) and collected < 10:
            nr = data_rows[i]
            nc = (nr[name_col].strip() if len(nr) > name_col else '').strip()

            if not any(c.strip() for c in nr):
                i += 1
                continue

            if re.match(r'^MS%', nc, re.IGNORECASE):
                ms_vals = nr
                i += 1
                break

            if nc and not _has_letters(nc):
                i += 1
                collected += 1
                continue

            if not seg_name and nc:
                seg_name = nc
                seg_vals = nr
                i += 1
                collected += 1
            else:
                i += 1
                collected += 1

        if model_name:
            groups.append({
                'model':      model_name,
                'segment':    seg_name,
                'model_vals': model_vals,
                'seg_vals':   seg_vals,
                'ms_vals':    ms_vals,
            })

    return {
        'columns':      columns,
        'groups':       groups,
        'hdr_idx':      best_idx,
        'hdr_score':    best_score,
        'hdr_max_year': best_max_year,
        'name_col':     name_col,
    }
