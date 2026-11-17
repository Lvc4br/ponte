# Consulta de Taxas de Pontes

Aplicativo desktop para **organização, consulta e manutenção de registros técnicos de engenharia**, com foco inicial em pontes e obras de arte especiais (OAEs). O projeto trabalha com dados tabulares provenientes de scripts SQL e planilhas Excel, permitindo consultar dimensões e indicadores associados a materiais e serviços, como taxas de concreto e aço.

O objetivo é facilitar a organização de referências técnicas e planilhas de engenharia. O aplicativo **não é um sistema completo de gestão eletrônica de documentos (GED)** e não realiza dimensionamento, análise ou validação estrutural.

## Situação atual do projeto

### Implementado na branch main

- Aplicativo desktop Windows desenvolvido em Python e PySide6.
- Leitura de base SQL local, aceitando tabelas obras e analise_oaes.
- Armazenamento da base ativa em SQLite local.
- Consulta com filtros por tipo de obra, largura, vão e comprimento total.
- Importação aditiva de planilhas Excel .xlsx, com seleção da aba e prévia antes da confirmação.
- Exclusão de registros selecionados, com confirmação e backup local.
- Preservação de campos adicionais, valores ausentes e intervalos textuais.
- Resumo da consulta e estatísticas descritivas para indicadores disponíveis.
- Testes automatizados no GitHub Actions para Windows e Ubuntu, Python 3.11, 3.12 e 3.13.
- Pipeline de empacotamento para Windows x64 com PyInstaller.

### Estado da distribuição

- Existe um release publicado: **v0.1.0**.
- O ZIP desse release foi produzido antes da implementação mais recente de importação Excel e gerenciamento de registros. Portanto, **não representa todas as funcionalidades atualmente presentes na branch main**.
- A branch main contém código mais recente, incluindo importação Excel e exclusão de registros. O workflow de testes mais recente passou nos seis ambientes da matriz.
- É necessário gerar um novo release para distribuir a versão com essas funcionalidades.

[Ver código-fonte](https://github.com/Lvc4br/ponte) · [Ver Releases](https://github.com/Lvc4br/ponte/releases) · [Ver testes automatizados](https://github.com/Lvc4br/ponte/actions/workflows/tests.yml)

## Escopo funcional

### 1. Organização e consulta de dados técnicos

- Carrega registros de um script SQL local.
- Reconhece as tabelas obras e analise_oaes.
- Mantém os campos originais e campos adicionais existentes na fonte.
- Filtra registros por tipo de obra, largura, vão e comprimento total.
- Considera intervalos de vão por sobreposição, quando a fonte disponibiliza limites.
- Mantém registros com dados incompletos para não perder informação.

### 2. Administração da base e planilhas

- Permite adicionar registros de arquivos Excel .xlsx.
- Permite selecionar a aba, visualizar uma prévia e confirmar a inclusão.
- A importação é aditiva: os registros existentes não são substituídos.
- Permite selecionar e excluir um ou mais registros da base ativa.
- Solicita confirmação antes da exclusão e cria backup local da base.
- Não remove duplicidades automaticamente e não altera a planilha original.

A importação atual usa os cabeçalhos encontrados na planilha e alguns aliases conhecidos. Ainda não há uma tela de mapeamento manual de colunas, importação de .xls, importação de PDF/Word ou gerenciamento de arquivos anexos.

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

O modelo database/ponte.sql.example não contém dados reais. O release v0.1.0 não inclui as funcionalidades adicionadas posteriormente à branch principal; consulte o estado dos workflows e aguarde um release atualizado para obter o pacote mais recente.

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

O aplicativo organiza e consulta referências históricas. Não dimensiona estruturas, não verifica segurança estrutural, não certifica dados de origem e não substitui a avaliação de profissional habilitado.

As estatísticas são calculadas por registro, não necessariamente por obra única. Segmentos de uma mesma obra podem aparecer como registros distintos e influenciar as estatísticas separadamente.

## Desenvolvimento e qualidade

- Código organizado em app/core, app/data, app/services e app/ui.
- Testes automatizados em tests/.
- CI executa compilação de sintaxe e testes em Windows/Ubuntu e Python 3.11–3.13.
- Build de release Windows x64 via GitHub Actions.
- Não versionar dados reais, credenciais, planilhas internas ou SQL corporativo.
