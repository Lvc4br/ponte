# Plano de testes de usuário — PONTE

Este roteiro será usado depois da atualização do PC. Não executar sobre a única cópia dos dados reais. Começar sempre com backup e, quando possível, com uma cópia de teste do banco.

## 1. Preparação segura

- [ ] Fechar o PONTE antigo.
- [ ] Copiar a pasta `data` e o arquivo privado `database/ponte.sql` para local seguro.
- [ ] Registrar a quantidade de registros legados antes da atualização.
- [ ] Baixar o artefato Windows gerado pelo workflow mais recente, não um ZIP antigo da branch.
- [ ] Extrair em uma pasta nova, sem sobrescrever o executável anterior.
- [ ] Instalar apenas as dependências externas necessárias: Tesseract, LibreOffice, ODA File Converter e/ou IfcOpenShell.
- [ ] Abrir o PONTE e verificar se os dados antigos continuam acessíveis.

## 2. Testes do espaço de dados

| ID | Ação | Resultado esperado | Resultado |
|---|---|---|---|
| WD-01 | Criar projeto de teste | Projeto aparece na lista | |
| WD-02 | Renomear projeto | Novo nome persiste após reabrir | |
| WD-03 | Criar duas tabelas no mesmo projeto | Tabelas independentes | |
| WD-04 | Criar colunas de texto, inteiro, decimal, booleano e data | Tipos aparecem no cabeçalho | |
| WD-05 | Inserir, editar e excluir registro | Alterações persistem | |
| WD-06 | Inserir valor de tipo incompatível | Aplicativo bloqueia e informa erro | |
| WD-07 | Criar coluna calculada | Resultado é calculado e somente leitura | |
| WD-08 | Alterar valor de origem de fórmula | Resultado calculado é atualizado | |
| WD-09 | Filtrar, ordenar e paginar via backend | Registros correspondem aos critérios | |
| WD-10 | Relacionar duas tabelas do mesmo projeto | Relacionamento é salvo | |
| WD-11 | Tentar relacionar tipos incompatíveis | Operação é recusada | |
| WD-12 | Excluir coluna usada por fórmula | Operação é bloqueada para proteger a fórmula | |
| WD-13 | Excluir tabela/projeto de teste | Exclusão em cascata somente no projeto selecionado | |

## 3. Importação e exportação

- [ ] Importar CSV com cabeçalhos, linhas vazias e caracteres acentuados.
- [ ] Importar XLSX com mais de uma aba.
- [ ] Importar XLSX com números, datas, booleanos e fórmulas.
- [ ] Exportar tabela para CSV e reabrir em editor de texto.
- [ ] Exportar tabela para XLSX e reabrir no Excel/LibreOffice.
- [ ] Confirmar que textos começando com `=`, `+`, `-` ou `@` não são executados como fórmulas.
- [ ] Comparar quantidade de linhas e valores antes/depois.

## 4. Scanner documental

Usar cópias autorizadas e sem dados sensíveis sempre que possível.

| Formato | Cenário mínimo | Verificação |
|---|---|---|
| PDF textual | Documento com texto e tabelas | Texto por página e tabelas |
| PDF digitalizado | PDF de imagem | OCR com Tesseract |
| PDF protegido | Arquivo com senha | Aviso sem travar o lote |
| DOCX | Parágrafos, tabelas, cabeçalho e rodapé | Conteúdo extraído |
| DOC | Documento binário antigo | Conversão via LibreOffice ou aviso |
| XLSX/XLSM | Várias abas e fórmulas | Abas e expressões preservadas |
| XLS/XLSB | Arquivo legado | Valores por aba |
| PPTX/PPT | Slides com texto e tabelas | Conteúdo por slide ou conversão |
| RTF/ODT/ODP | Documento legado | Conversão via LibreOffice |
| DXF | Linhas, polilinhas, blocos e cotas | Entidades/camadas extraídas |
| DWG | Desenho de referência | Conversão ODA para DXF ou aviso |
| IFC | Modelo BIM | Produtos e propriedades |
| RVT/RFA | Arquivo Revit | Aviso e fluxo de exportação para IFC/PDF |
| PNG/JPEG/TIFF | Imagem com texto | OCR quando configurado |
| CSV/JSON/XML/TXT | Arquivo estruturado | Conteúdo sem corrupção |

- [ ] Selecionar vários arquivos em um único lote.
- [ ] Selecionar uma pasta com subpastas.
- [ ] Incluir um arquivo inválido no lote e confirmar que os demais são processados.
- [ ] Reabrir a biblioteca documental e conferir persistência.
- [ ] Vincular documento analisado a um projeto.
- [ ] Confirmar que o arquivo original não foi alterado.

## 5. Backup e restauração

- [ ] Criar backup pelo menu.
- [ ] Conferir arquivo SQLite e manifesto JSON.
- [ ] Verificar o backup pelo aplicativo.
- [ ] Fazer uma alteração de teste no banco.
- [ ] Restaurar o backup de teste.
- [ ] Confirmar criação do backup de segurança automático.
- [ ] Fechar e reabrir o PONTE.
- [ ] Conferir registros legados, projetos, tabelas e biblioteca documental.

## 6. Regressão dos dados legados

- [ ] Comparar a quantidade de registros antes e depois.
- [ ] Pesquisar registros conhecidos.
- [ ] Conferir filtros dimensionais antigos.
- [ ] Conferir indicadores antigos.
- [ ] Importar uma planilha de teste e confirmar que a importação não duplica conteúdo.
- [ ] Confirmar que a exclusão de dados de teste não altera outros conjuntos.

## 7. Usabilidade e desempenho

- [ ] Criar projeto e tabela sem ajuda externa.
- [ ] Inserir e editar 20 registros.
- [ ] Importar planilha com 1.000 linhas.
- [ ] Consultar biblioteca com dezenas de documentos.
- [ ] Observar congelamentos, mensagens de erro, textos cortados e navegação.
- [ ] Repetir em monitor com resolução menor.
- [ ] Registrar dúvidas, cliques desnecessários e recursos que faltam.

## 8. Critérios para encerrar a rodada

A rodada só é aprovada se não houver perda de dados, falhas que impeçam abertura, corrupção do banco, fórmulas executadas de forma insegura ou divergência inexplicada na importação/exportação. Falhas menores de UX devem virar tarefas priorizadas. O PONTE não deve ser declarado substituto integral do Excel antes de testes comparativos com planilhas reais e fórmulas relevantes.
