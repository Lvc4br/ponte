# PONTE — Banco Central de Dados de Engenharia | EGT

> **Direção do rebuild:** aplicação desktop para a EGT, com API central e PostgreSQL, iniciando pelo domínio de pontes/OAE e preparada para 30+ usuários simultâneos.

A documentação oficial desta nova direção está em [docs/EGT](docs/EGT/README.md). Ela define visão de produto, arquitetura de implantação, modelo de dados, plano de desenvolvimento e política de limpeza do repositório.

**Atenção:** o código existente neste branch é a base legada em avaliação. Ele não deve ser considerado a arquitetura final do rebuild. A nova aplicação será construída em etapas, mantendo o sistema e os dados anteriores preservados até a validação da migração.

## Decisões do rebuild
- Cliente: desktop Python/PySide6.
- Comunicação: cliente desktop → API central (FastAPI) → PostgreSQL.
- Concorrência alvo: 30+ usuários, validada por teste de carga.
- Domínio inicial: pontes e obras de arte especiais.
- Documentos: metadados relacionais e binários em armazenamento corporativo.
- Segurança: autenticação, autorização no servidor e auditoria.

## Documentação legada

# Gerenciador de Estruturas

Aplicativo desktop para gerenciamento de projetos, tabelas, dados técnicos e documentos, com foco em fluxos de trabalho de engenharia. O nome PONTE permanece como origem histórica do projeto; a aplicação não fica limitada a pontes.

## Interface atual

A interface principal utiliza três colunas:

- **Filtros técnicos:** tipo de obra, largura, vão e comprimento, com aplicação combinada dos critérios.
- **Planilha:** edição de células, seleção, ordenação, filtros por coluna, pesquisa, colunas calculadas, desfazer/refazer e operações em lote.
- **Resumo e propriedades:** estatísticas recalculadas sobre os registros efetivamente exibidos e detalhes da linha selecionada.

A área de documentos fica em um painel inferior recolhível. A barra superior concentra seleção de projeto/tabela e ações mais frequentes; ferramentas secundárias ficam agrupadas no menu Ferramentas.

## Recursos preservados

- Projetos e múltiplas tabelas por projeto.
- Colunas dinâmicas, validação de tipos e fórmulas seguras.
- Filtros técnicos, filtros por coluna, condições, pesquisa e ordenação.
- Edição de células, copiar/colar, histórico de desfazer/refazer e edição em lote.
- Importação e exportação Excel.
- Catálogo documental, vínculo de documentos, análise de arquivos e pré-visualização de PDF.
- Persistência local SQLite e recursos de backup/recuperação existentes.

## Estatísticas

Os indicadores são calculados sobre o mesmo conjunto filtrado apresentado na planilha. Valores vazios ou não numéricos são excluídos do cálculo e a quantidade de valores válidos é exibida. Para campos que armazenem intervalos como texto, é necessário normalizar os dados antes de tratá-los como uma medida numérica única.

## Instalação e execução (Windows)

Requisitos: Python 3.11 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m compileall -q app tests main.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe main.py
```

Para gerar o executável, execute `build/build_windows.bat`. O pipeline do GitHub Actions valida o código e gera o pacote Windows.

## Estrutura do repositório

- `app/`: aplicação, interface, serviços, armazenamento e importação/exportação.
- `database/`: documentação e exemplo de estrutura de banco; não contém dados reais de clientes.
- `docs/`: arquitetura, instalação, status e plano de testes.
- `build/`: scripts de empacotamento.
- `tests/`: testes automatizados.
- `.github/`: CI e automações do repositório.

## Segurança e preservação de dados

- Não versionar bancos locais, planilhas internas, documentos corporativos, credenciais ou dados pessoais.
- Faça backup do banco SQLite antes de atualizar uma instalação existente.
- O scanner não certifica documentos nem substitui a validação de engenharia.
- Macros VBA e conteúdo ativo não são executados.
- A base legada deve permanecer preservada durante a evolução.

## Documentação

- [Arquitetura](docs/ARQUITETURA_GERENCIADOR_UNIVERSAL.md)
- [Instalação Windows](docs/INSTALACAO_WINDOWS.md)
- [Plano de testes de usuário](docs/PLANO_TESTES_USUARIO.md)
- [Status do projeto](docs/STATUS_PROJETO.md)
