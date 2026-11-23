# Preservação do pacote recebido — 2026-11-23

## Identificação do original
- Nome do anexo: `gerenciamento de dados(1).zip`
- Tamanho: 129.682.407 bytes (123,67 MiB)
- Entradas ZIP: 2.710
- Conteúdo descompactado: aproximadamente 241,0 MiB
- Integridade ZIP: aprovada (`testzip` não encontrou membro corrompido)
- SHA-256: `e6ad4b96364bd2aa60c6f2fd0f67977cb3ee4eb86226db9d7e3ababb2805905f`

## Conteúdo de código identificado
### Implementação B — candidata principal
- Diretório no pacote: `ponte-repo/`
- Framework: PySide6
- Branch local: `fix/estimativa-taxas-engenharia`
- HEAD: `396f7d1ec0200f9d76865585d9b08e61db1250ab`
- Histórico recente: `c758f04`, `64674b2`, `4f1c41d`, `396f7d1`
- Testes executados nesta sessão: 97 aprovados em 8,87 s.
- Working tree: 61 arquivos aparecem modificados; a auditoria anterior registrou que a diferença é apenas de finais de linha (CRLF/LF), sem alteração semântica nesses arquivos.

### Implementação C — referência histórica
- Raiz do pacote: `app.py`, `ponte_core.py`
- Framework: Tkinter
- Branch local: `feature/ponte-plataforma-engenharia`
- HEAD: `4a5457ef65b9552870dc16aadfa3d563d44e3bc6`
- Há alterações locais em `Ponte.spec` e diretórios gerados/não rastreados. Preservar como referência; não substituir a implementação B.

## Limite de publicação do arquivo binário
O ZIP original tem mais de 100 MB. O limite normal de arquivos Git do GitHub é 100 MB, e a integração GitHub disponível nesta sessão não oferece envio de anexos binários/release assets. Portanto, o ZIP original **não foi adicionado ao repositório**. Este manifesto e a auditoria são o registro versionado; o anexo original permanece nesta conversa. Não afirmar que o ZIP foi enviado ao GitHub.

## Política de preservação
- Não apagar o ZIP original nem os diretórios locais do usuário.
- Não incluir executáveis, DLLs, builds, bancos de dados locais, documentos privados, credenciais ou caches no repositório.
- A cópia-fonte filtrada foi preparada com 188 arquivos (aprox. 0,65 MiB), removendo artefatos de build/runtime. Ela é uma cópia de trabalho de preservação, não substitui o ZIP original.
- Não criar branch remota a partir do HEAD local B sem antes publicar/verificar os objetos Git locais: o commit `396f7d1` ainda não existe no repositório remoto.
- Próxima ação: transportar os commits B para o branch de reconstrução em alterações pequenas, com revisão e testes, mantendo `main` intacta.

## Próximos bloqueios técnicos
1. Reproduzir e corrigir exclusão órfã de registros ligados às obras.
2. Tornar importação e gravação de fingerprints/dados tipados atômicas.
3. Validar backup/restore contra schema e documentos completos.
4. Completar comparabilidade técnica com tipologia, sistema estrutural, materiais e contexto.
5. Formalizar definições e unidades dos indicadores com a EGT antes de habilitar uso decisório.
