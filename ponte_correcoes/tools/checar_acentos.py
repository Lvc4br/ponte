"""Detecta e corrige acentos quebrados ("?") e arquivos fora de UTF-8.

Uso (na raiz do projeto):
    python tools/checar_acentos.py              # só relata
    python tools/checar_acentos.py --corrigir   # corrige (cria .bak de cada arquivo)
"""
import re
import sys
from pathlib import Path

EXTENSOES = {".py", ".qss", ".json", ".txt", ".md", ".css", ".html"}
IGNORAR = {".venv", "venv", ".git", "build", "dist", "__pycache__", "node_modules"}

# Palavras vistas quebradas na interface -> forma correta.
PALAVRAS = {
    "T?CNICOS": "TÉCNICOS", "T?CNICAS": "TÉCNICAS", "T?CNICA": "TÉCNICA",
    "T?CNICO": "TÉCNICO", "GEST?O": "GESTÃO", "ESTAT?STICO": "ESTATÍSTICO",
    "ESTAT?STICA": "ESTATÍSTICA", "Estat?stico": "Estatístico",
    "Estat?stica": "Estatística", "estat?stica": "estatística",
    "num?ricos": "numéricos", "num?rica": "numérica", "num?rico": "numérico",
    "Conte?dos": "Conteúdos", "Conte?do": "Conteúdo", "conte?dos": "conteúdos",
    "conte?do": "conteúdo", "C?lculos": "Cálculos", "c?lculos": "cálculos",
    "c?lula": "célula", "C?lula": "Célula", "P?gina": "Página",
    "V?lidos": "Válidos", "V?lido": "Válido", "v?lidos": "válidos",
    "M?nimo": "Mínimo", "M?ximo": "Máximo", "M?dia": "Média",
    "V?o": "Vão", "v?o": "vão",
    "An?lise": "Análise", "an?lise": "análise",
    "Documenta??o": "Documentação",
}

# Palavras curtas só são trocadas quando isoladas (evita mexer em outros textos).
PALAVRAS_ISOLADAS = {r"\bs\?o\b": "são", r"\bn\?o\b": "não", r"\bN\?o\b": "Não"}

# Botões cujo símbolo inicial virou "?" (trocados por ASCII, que nunca quebra).
REGEXES = [
    (re.compile(r'(["\'])\? (Novo projeto|Nova tabela|Coluna|Registro)'), r"\1+ \2"),
    (re.compile(r'(["\'])\? P(?:á|\?)gina(["\'])'), r"\1< Página\2"),
    (re.compile(r'(["\'])P(?:á|\?)gina \?(["\'])'), r"\1Página >\2"),
    (re.compile(r"(\baplicados) \? (planilha)"), r"\1 à \2"),
]

SUSPEITO = re.compile(r'[A-Za-zÀ-ÿ]\?[A-Za-zÀ-ÿ]|["\']\? ')


def corrigir_texto(texto: str) -> str:
    for errado in sorted(PALAVRAS, key=len, reverse=True):
        texto = texto.replace(errado, PALAVRAS[errado])
    for padrao, certo in PALAVRAS_ISOLADAS.items():
        texto = re.sub(padrao, certo, texto)
    for padrao, subst in REGEXES:
        texto = padrao.sub(subst, texto)
    return texto


def arquivos(raiz: Path):
    for p in raiz.rglob("*"):
        if p.is_file() and p.suffix in EXTENSOES and not (set(p.parts) & IGNORAR):
            yield p


def main() -> int:
    corrigir = "--corrigir" in sys.argv
    problemas = 0
    este = Path(__file__).resolve()
    for p in arquivos(Path(".")):
        if p.resolve() == este or p.name.startswith("test_checar"):
            continue
        bruto = p.read_bytes()
        try:
            texto = bruto.decode("utf-8")
        except UnicodeDecodeError:
            problemas += 1
            print(f"NÃO É UTF-8: {p}")
            if not corrigir:
                continue
            p.with_suffix(p.suffix + ".bak").write_bytes(bruto)
            texto = bruto.decode("cp1252", errors="replace")
            p.write_text(texto, encoding="utf-8")
            print("   convertido de cp1252 para UTF-8 (backup .bak)")
        for n, linha in enumerate(texto.splitlines(), 1):
            if SUSPEITO.search(linha):
                problemas += 1
                print(f"{p}:{n}: {linha.strip()[:110]}")
        if corrigir:
            novo = corrigir_texto(texto)
            if novo != texto:
                p.with_suffix(p.suffix + ".bak").write_bytes(texto.encode("utf-8"))
                p.write_text(novo, encoding="utf-8")
                print(f"CORRIGIDO: {p}")
    if not problemas:
        print("Nenhum problema de acentuação nos arquivos.")
        print("Se a tela ainda mostra '?', o erro está na leitura em tempo de execução:")
        print("procure open() sem encoding='utf-8' e .encode('ascii', 'replace').")
    return 1 if problemas and not corrigir else 0


if __name__ == "__main__":
    raise SystemExit(main())
