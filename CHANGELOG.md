# Histórico de alterações

## Não publicado — branch main

### Adicionado
- Importação aditiva de registros de planilhas Excel no formato .xlsx.
- Bloqueio de reimportação do mesmo arquivo Excel por impressão digital SHA-256, inclusive quando renomeado.
- Registro persistente dos arquivos importados no SQLite local, com inclusão dos registros e do histórico na mesma transação.
- Seleção de aba e prévia antes da confirmação da importação.
- Persistência local independente da fonte SQL.
- Exclusão de registros selecionados com confirmação e backup.
- Detecção da linha real de cabeçalho, inclusive quando há título ou linhas vazias antes dela.
- Reconhecimento de aliases de colunas técnicas e indicadores.
- Rejeição de cabeçalhos que mapeiam mais de uma coluna para o mesmo campo.
- Filtros dimensionais que não consideram registros sem dados verificáveis como correspondências confirmadas.

### Corrigido e validado
- Proteção contra duplicidade com testes de persistência após reabrir o banco e aceitação de arquivos distintos.
- Correção do filtro de dimensões ausentes.
- Correção da identificação de cabeçalhos equivalentes duplicados.
- Testes locais no Windows: 40 aprovados.
- GitHub Actions: 6/6 combinações aprovadas (Windows/Ubuntu e Python 3.11, 3.12 e 3.13).
- Validação funcional pelo usuário: pesquisa, importação Excel e estatísticas confirmadas funcionando.

### Observações
- As alterações acima estão na branch main e ainda não fazem parte do ZIP publicado em v0.1.0.
- A validação funcional da versão atualizada no Windows foi concluída.
- O próximo passo de distribuição é gerar um novo release Windows x64 a partir da branch main.

## [0.1.0] — publicado

- Primeira distribuição portátil Windows x64.
- Aplicativo desktop de consulta de taxas e referências de pontes.
- Leitura de dados por script SQL local.
- Filtros dimensionais e estatísticas descritivas.
- Build automatizado por GitHub Actions.
