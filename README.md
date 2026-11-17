# ConsultaTaxasPontes

Aplicativo desktop em Python/PySide6 para consultar taxas históricas de obras de pontes a partir de planilhas Excel. O sistema organiza referências históricas; não realiza dimensionamento, análise ou validação estrutural.

## Funcionalidades iniciais

- Importação de Excel, aba padrão `Base_limpa`, cabeçalho na segunda linha.
- Mapeamento de cabeçalhos e normalização de decimais brasileiros.
- Filtros por intervalos de largura, vão e comprimento total.
- Comparação por sobreposição para vãos registrados como intervalos (ex.: `41,25 - 41,80`).
- Preservação de valores originais e registros com campos ausentes.
- Exibição dos resultados e exportação para Excel.

## Requisitos

Python 3.11 ou superior recomendado. Dependências em `requirements.txt`.

## Instalação no Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Executável

Execute `build\build_windows.bat`. O resultado será criado em `dist\ConsultaTaxasPontes`.

## Estrutura

- `app/core`: modelos, validação e lógica de correspondência.
- `app/data`: leitura e mapeamento de colunas Excel.
- `app/services`: pesquisa e exportação.
- `app/ui`: interface PySide6.
- `tests`: testes automatizados.
- `docs`: arquitetura e instalação.

## Dados

Não inclua planilhas corporativas, dados confidenciais ou arquivos de terceiros no repositório público sem autorização. Os arquivos Excel são ignorados pelo Git por padrão.

## Limitações conhecidas

Esta é uma primeira versão funcional da base do aplicativo. A interpretação de colunas não documentadas e validação com a planilha real ainda precisam ser confirmadas. O aplicativo não estima valores ausentes nem altera registros de origem.
