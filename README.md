# ConsultaTaxasPontes

Aplicativo desktop Windows para consulta de referências históricas e indicadores de taxas de pontes. Não executa dimensionamento, análise ou validação estrutural.

## Versão

Primeira versão distribuível planejada: **0.1.0** (prévia funcional). A distribuição será portátil para Windows x64, empacotada com PyInstaller.

## Funcionalidades

- Carregamento de script SQL local (database/ponte.sql) para SQLite.
- Suporte às tabelas obras e analise_oaes.
- Preservação das colunas e dos valores originais, inclusive campos ausentes e intervalos textuais.
- Filtros independentes por tipo de obra, largura, vão e comprimento total.
- Aceita vírgula decimal e ponto decimal nos filtros.
- Resumo da consulta com quantidade de resultados, registros verificáveis e registros com dados incompletos.
- Estatísticas por coluna de taxa: quantidade de valores válidos, cobertura, média, mediana, mínimo e máximo.
- Ordenação da tabela de resultados.

## Instalação da versão portátil

1. Baixe o ZIP Windows x64 na página Releases.
2. Extraia a pasta em um local no qual você tenha permissão de gravação.
3. Na pasta extraída, crie database se ainda não existir.
4. Copie o SQL autorizado para database/ponte.sql.
5. Execute ConsultaTaxasPontes.exe.

O release não inclui a base corporativa. O arquivo database/ponte.sql.example é somente um modelo. O banco local será criado em data/ponte.db, ao lado do executável.

## Desenvolvimento

Requisitos: Python 3.11 ou superior. Dependências em requirements.txt.

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m pytest -v
    .\.venv\Scripts\python.exe main.py

Build local: execute build\build_windows.bat. A saída fica em dist\ConsultaTaxasPontes.

## Qualidade e publicação

- Testes automatizados em Ubuntu e Windows, Python 3.11, 3.12 e 3.13.
- Verificação de sintaxe via compileall.
- Pipeline de release Windows x64: executa testes, empacota com PyInstaller e publica ZIP ao receber tag SemVer vMAJOR.MINOR.PATCH ou execução manual do workflow com uma versão informada.
- Não incluir dados reais, credenciais ou arquivos SQL internos em commits, issues, logs ou releases.

## Interpretação dos indicadores

As estatísticas são calculadas por registro, não por obra única. Se a base contiver segmentos da mesma obra, eles podem influenciar as estatísticas mais de uma vez. Valores ausentes e valores textuais não numéricos são ignorados apenas no cálculo do respectivo indicador; a origem não é modificada.

Os identificadores Paf_kg_m2, Pap_kg_m2 e Af_m2_m2 são exibidos sem interpretação adicional até que suas definições e fórmulas sejam confirmadas na documentação técnica. Não se calculam taxas derivadas sem fórmula validada.

## Limitações conhecidas

- A classificação de completude informa se os campos usados nos filtros estão disponíveis; não representa aprovação de engenharia.
- A comparação de tipos de obra depende do texto existente na fonte.
- Não há deduplicação automática de obras/segmentos.
- Não há validação independente da procedência ou qualidade técnica dos dados.
- O aplicativo é uma ferramenta de consulta e apoio à organização de referências, não substitui análise ou responsabilidade de profissional habilitado.
