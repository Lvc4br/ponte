import re, unicodedata
ALIASES = {'largura':'largura_m','largura_m':'largura_m','vao':'vao_m','vao_m':'vao_m','vão_m':'vao_m','compr_obra_m':'compr_obra_m','comprimento_obra_m':'compr_obra_m','seção':'secao','secao':'secao'}
def normalize_header(value):
    text = unicodedata.normalize('NFKD', str(value or '').strip().lower())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'[^a-z0-9]+','_',text).strip('_')
    return ALIASES.get(text, text)
