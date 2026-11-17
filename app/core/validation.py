from app.core.models import NumericRange

def parse_number(value):
    if value is None or isinstance(value, bool): return None
    if isinstance(value, (int, float)): return float(value)
    text = str(value).strip().replace(' ', '')
    if not text or text.lower() in {'nan','none','n/a','-'}: return None
    if ',' in text and '.' not in text: text = text.replace(',', '.')
    elif ',' in text and '.' in text: text = text.replace('.', '').replace(',', '.')
    try: return float(text)
    except ValueError: return None

def parse_range(value):
    if value is None: return None
    if isinstance(value, (int,float)): return NumericRange(float(value), float(value))
    text = str(value).strip().replace('–','-').replace('—','-')
    parts = [p.strip() for p in text.split('-')]
    if len(parts) == 2:
        a,b = parse_number(parts[0]), parse_number(parts[1])
        if a is not None and b is not None: return NumericRange(min(a,b), max(a,b))
    n = parse_number(text)
    return NumericRange(n,n) if n is not None else None
