# ConsultaTaxasPontes

Aplicativo desktop em Python/PySide6 para consultar taxas históricas de obras de pontes. O sistema organiza referências históricas; não realiza dimensionamento, análise ou validação estrutural.

## Fonte de dados nesta versão

A fonte de dados é um script SQL local: `database/ponte.sql`.

1. Copie `database/ponte.sql.example` para `database/ponte.sql`.
2. Edite o arquivo e inclua os comandos SQL que criam a tabela `obras` e inserem os registros autorizados.
3. Inicie o aplicativo. O programa executa o script em memória, valida a tabela e reconstrói o banco SQLite local em `data/ponte.db`.
4. Ao clicar em **Recarregar arquivo SQL**, o banco local é reconstruído novamente a partir do script.

O arquivo real `database/ponte.sql` e o banco `data/ponte.db` são ignorados pelo Git. Não publique dados corporativos no repositório.

## Estrutura SQL esperada

A tabela deve se chamar `obras`. O modelo em `database/ponte.sql.example` contém os campos conhecidos, incluindo tipo de obra, largura, intervalo de vão, comprimento e taxas históricas. Os campos cuja definição ainda não foi confirmada são armazenados sem interpretação adicional.

Para vãos informados como intervalo, use `vao_min_m` e `vao_max_m`. Para cada registro, insira os valores numéricos correspondentes. Campos históricos desconhecidos podem permanecer NULL.

## Funcionalidades implementadas nesta etapa

- Carregamento de uma base a partir de script SQL local.
- Criação/reconstrução de banco SQLite local.
- Filtros por tipo de obra, intervalo de largura, vão e comprimento total.
- Comparação de intervalos de vãos.
- Preservação de campos nulos.
- Exibição dos registros compatíveis em tabela.

## Requisitos e instalação

Python 3.11 ou superior recomendado. Dependências em `requirements.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Executável

Execute `build\build_windows.bat`. A configuração de empacotamento ainda deverá ser revisada para incluir o script SQL local.

## Limitações

Esta versão ainda precisa ser validada com os dados reais autorizados. Estatísticas de taxas, classificação definitiva de tipos de obra, interpretação de colunas não documentadas e comparação de proximidade serão etapas posteriores. O aplicativo não estima valores ausentes nem altera os registros de origem.
