# Gestão de Obras

Aplicativo desktop para **gerenciamento de dados de obras de engenharia**. Reúne registros técnicos de diferentes obras em uma base tabular local, com importação de planilhas Excel, consulta por características dimensionais, manutenção dos registros e indicadores disponíveis. O conjunto atual de dados tem foco inicial em pontes e obras de arte especiais (OAEs), mas a interface e o objetivo do produto passam a ser apresentados como um workspace de gestão de dados de obras.

O objetivo é centralizar e facilitar a organização, consulta e manutenção dos dados técnicos de obras em um ambiente de trabalho. A interface adota uma organização visual inspirada em ferramentas profissionais como Blender (workspace escuro, painéis laterais e propriedades) e Excel (grade tabular, cabeçalhos e seleção de linhas), sem reproduzir marcas ou funcionalidades que ainda não existem. O aplicativo **não é um sistema completo de gestão eletrônica de documentos (GED)** e não realiza dimensionamento, análise ou validação estrutural.

## Situação atual do projeto

### Implementado na branch main

- Aplicativo desktop Windows desenvolvido em Python e PySide6.\n- Workspace redesenhado para gestão de dados de obras, com tema escuro, navegação lateral, abas independentes para base principal e cada planilha Excel importada, grade de registros e painel de propriedades.
- Navegação persistente entre planilhas importadas, identificadas pelo arquivo de origem e nome da aba; a visualização Todas reúne os registros da base.
- Importação de abas diferentes do mesmo arquivo Excel, com bloqueio de reimportação da mesma combinação arquivo/aba por SHA-256.
- Migração automática do SQLite para armazenar a origem dos registros, preservando os registros existentes.
- Leitura de base SQL local, aceitando tabelas obras e analise_oaes.
- Armazenamento da base ativa em SQLite local.
- Consulta com filtros por tipo de obra, largura, vão e comprimento total.
- Importação aditiva de planilhas Excel .xlsx, com detecção da linha de cabeçalho, seleção da aba e prévia antes da confirmação.
- Validação de cabeçalhos equivalentes duplicados.
- Exclusão de registros selecionados, com confirmação e backup local.
- Preservação de campos adicionais, valores ausentes e intervalos textuais.
- Registros sem dimensões verificáveis não são tratados como correspondências confirmadas quando o filtro correspondente está ativo.
- Resumo da consulta e estatísticas descritivas para indicadores disponíveis.
- Testes locais no Windows: validação anterior de 40 testes aprovados; as novas alterações de navegação e migração aguardam a execução atualizada do CI.
- Testes automatizados no GitHub Actions para Windows e Ubuntu, Python 3.11, 3.12 e 3.13 (6/6 ambientes aprovados).
- Validação funcional no Windows pelo usuário: pesquisa, importação Excel e estatísticas confirmadas funcionando.
- Pipeline de empacotamento para Windows x64 com PyInstaller.

### Estado da distribuição

- Existe um release publicado: **v0.1.0**.
- O ZIP desse release foi produzido antes da implementação mais recente de importação Excel, gerenciamento de registros e correções de pesquisa. Portanto, **não representa todas as funcionalidades atualmente presentes na branch main**.
- A versão atual da branch main foi validada localmente no Windows e passou no workflow de testes nos seis ambientes.
- O próximo passo é gerar um novo release Windows x64 com o código validado.

[Ver código-fonte](https://github.com/Lvc4br/ponte) · [Ver Releases](https://github.com/Lvc4br/ponte/releases) · [Ver testes automatizados](https://github.com/Lvc4br/ponte/actions/workflows/tests.yml)

## Escopo funcional

### 1. Organização e consulta de dados técnicos

- Carrega registros de um script SQL local.
- Reconhece as tabelas obras e analise_oaes.
- Mantém os campos originais e campos adicionais existentes na fonte.
- Filtra registros por tipo de obra, largura, vão e comprimento total.
- Considera intervalos de vão por sobreposição, quando a fonte disponibiliza limites.
- Mantém registros com dados incompletos na base, sem tratá-los como correspondências confirmadas quando um filtro depende de um valor ausente.

### 2. Administração da base e planilhas

- Permite adicionar registros de arquivos Excel .xlsx.
- Detecta a linha de cabeçalho mesmo quando existem títulos ou linhas vazias antes dela.
- Permite selecionar a aba, visualizar uma prévia e confirmar a inclusão.
- A importação é aditiva: os registros existentes não são substituídos.
- Permite selecionar e excluir um ou mais registros da base ativa.
- Solicita confirmação antes da exclusão e cria backup local da base.
- Não remove duplicidades automaticamente e não altera a planilha original.

A importação atual usa os cabeçalhos encontrados na planilha e aliases conhecidos. Ainda não há uma tela de mapeamento manual de colunas, importação de .xls, importação de PDF/Word ou gerenciamento de arquivos anexos.

### 3. Indicadores e estatísticas

O aplicativo apresenta estatísticas descritivas para os campos disponíveis, incluindo:

- em_m3_m2
- Paf_kg_m2
- Pap_kg_m2
- Af_m2_m2

As estatísticas incluem quantidade de valores válidos, cobertura, média, mediana, mínimo e máximo. Os nomes dos campos são mantidos como identificadores da fonte; não se atribui significado técnico definitivo sem documentação que confirme a definição e a fórmula.

## Dados e persistência

O arquivo SQL original fica em database/ponte.sql e não deve ser publicado no GitHub. Na inicialização, o script é validado e executado em memória; uma cópia SQLite intermediária é gravada em data/ponte.db.

A base gerenciada pelo aplicativo fica em data/registros.sqlite3. Na primeira carga válida, os registros do SQL são copiados para essa base gerenciada, caso ela ainda esteja vazia. Depois disso, inclusões e exclusões são persistidas nessa base local.

**Importante:** alterações feitas posteriormente no arquivo SQL não são mescladas automaticamente com a base gerenciada. Para evitar perda de dados, faça backup de data/registros.sqlite3 antes de qualquer manutenção manual, reinstalação ou movimentação da pasta do aplicativo.

Os bancos locais, planilhas de trabalho e SQL real são ignorados pelo Git. Releases públicos não devem conter dados corporativos ou documentos internos.

## Instalação e execução

### Versão portátil Windows

1. Baixe o ZIP na página Releases.
2. Extraia em uma pasta com permissão de gravação.
3. Coloque o SQL autorizado em database/ponte.sql, caso vá inicializar a base a partir de SQL.
4. Execute ConsultaTaxasPontes.exe.

O modelo database/ponte.sql.example não contém dados reais. O release v0.1.0 não inclui as funcionalidades e correções adicionadas posteriormente à branch principal; aguarde o novo release para obter o pacote atualizado.

### Executar pelo código-fonte

Requisitos: Python 3.11 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe main.py
```

Para gerar o executável localmente, execute build/build_windows.bat.

## Limitações e próximos aprimoramentos

O projeto está em evolução. Entre os aprimoramentos ainda não implementados estão:

- Mapeamento manual de colunas durante a importação de planilhas.
- Relatório detalhado de linhas importadas, avisos e rejeições.
- Importação de outros formatos além de .xlsx.
- Cadastro e organização de documentos técnicos anexos às planilhas.
- Metadados documentais, categorias, revisão, histórico de versões e pesquisa por documentos.
- Fluxo de aprovação, permissões por usuário e trilha de auditoria.
- Sincronização e compartilhamento multiusuário.

Esses itens não devem ser considerados funcionalidades disponíveis até que sejam implementados e testados.

## Limites de uso técnico

O aplicativo organiza, consulta e mantém registros técnicos de obras. Não dimensiona estruturas, não verifica segurança estrutural, não certifica dados de origem e não substitui a avaliação de profissional habilitado.

As estatísticas são calculadas por registro, não necessariamente por obra única. Segmentos de uma mesma obra podem aparecer como registros distintos e influenciar as estatísticas separadamente.

## Desenvolvimento e qualidade

- Código organizado em app/core, app/data, app/services e app/ui.
- Testes automatizados em tests/.
- CI executa compilação de sintaxe e testes em Windows/Ubuntu e Python 3.11–3.13.
- Build de release Windows x64 via GitHub Actions.
- Não versionar dados reais, credenciais, planilhas internas ou SQL corporativo.
