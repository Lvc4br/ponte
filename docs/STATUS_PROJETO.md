# Situação do projeto

**Projeto:** Consulta de Taxas de Pontes  
**Categoria:** aplicativo desktop de organização e consulta de dados técnicos de engenharia  
**Foco atual:** registros de pontes/obras de arte especiais e indicadores de materiais, incluindo dados de concreto e aço  
**Branch principal:** main

## Implementado na branch main

- [x] Aplicativo desktop Windows com Python/PySide6.
- [x] Leitura de dados SQL locais das tabelas obras e analise_oaes.
- [x] Persistência local da base ativa em SQLite.
- [x] Filtros por tipo de obra, largura, vão e comprimento.
- [x] Estatísticas descritivas de indicadores disponíveis.
- [x] Importação aditiva de planilhas Excel .xlsx, com seleção de aba e prévia.
- [x] Exclusão de registros selecionados com confirmação e backup.
- [x] Preservação de campos originais, valores ausentes e intervalos textuais.
- [x] Testes automatizados em seis combinações de sistema operacional e versão Python.

## Distribuição

- [x] Release v0.1.0 publicado com pacote Windows x64.
- [ ] Publicar novo release que inclua importação Excel e gerenciamento de registros.
- [ ] Validar a versão mais recente no Windows por meio de teste funcional do usuário.

O pacote v0.1.0 é anterior às funcionalidades mais recentes da branch main. Não o apresentar como contendo importação Excel ou exclusão de registros.

## Administração de documentos e planilhas: escopo atual

O aplicativo já permite administrar registros tabulares provenientes de SQL e Excel. Ainda não é um GED: não guarda nem classifica arquivos técnicos anexos, não controla versões documentais, não possui aprovação, permissões por perfil ou auditoria de alterações.

## Próximas etapas

1. Testar importação, consulta, fechamento/reabertura e exclusão no Windows.
2. Melhorar o mapeamento de cabeçalhos e o relatório de importação.
3. Implementar cadastro e organização de documentos técnicos vinculados aos registros/planilhas.
4. Avaliar versionamento, histórico de alterações e permissões.
5. Gerar novo release após os testes funcionais.

## Proteção de dados

Não publicar SQL real, planilhas internas, bancos SQLite com dados de trabalho, documentos corporativos ou credenciais no repositório público.
