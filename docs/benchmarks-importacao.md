# Importação de benchmarks de CPU e GPU

## Arquitetura e esquema

A implementação segue Flask/SQLAlchemy, services com `executar`, comandos Click e migrações incrementais explícitas já usados pelo projeto. Reutiliza `mostrar_pecas` para carregar o catálogo e a sessão `db` para confirmar lotes. Não há rota HTTP, criação de peças, download automático ou execução de scraper.

`BenchmarkMixin` compartilha metadados apenas entre `Processador` e `PlacaVideo`. Todas as colunas novas permitem NULL e não têm default zero:

| Model | Campos de pontuação (`Numeric(14,2)`) |
| --- | --- |
| Processador | `benchmark_multi_core`, `benchmark_single_thread` |
| PlacaVideo | `benchmark_g2d`, `benchmark_g3d` |

Metadados: `benchmark_teste`, `benchmark_versao`, `benchmark_nome_fonte`, `benchmark_fonte`, `benchmark_atualizado_em` (UTC), `benchmark_referencia_em` (data). Versão e data de referência permanecem NULL porque os arquivos inspecionados não as informam. A data de importação só muda quando há alteração efetiva. O importador atualiza somente colunas de benchmark, preservando inclusive `atualizado_em` geral da peça.

## Fonte efetivamente inspecionada

Repositório: [Algerian-Laptop-Market](https://github.com/yassircherdouh/Algerian-Laptop-Market).

| Arquivo | Cabeçalho real | Métricas importadas |
| --- | --- | --- |
| [data/cpu_passmark.csv](https://github.com/yassircherdouh/Algerian-Laptop-Market/blob/main/data/cpu_passmark.csv) | `name,cpumark,single_thread,cores,threads` | PassMark CPU Mark (multi-core) e Single Thread, separadamente |
| [data/gpu_passmark.csv](https://github.com/yassircherdouh/Algerian-Laptop-Market/blob/main/data/gpu_passmark.csv) | `name,g2d,g3d` | PassMark G2D e G3D, separadamente |

Inspeção em 30/10/2026: 6.255 linhas de CPU e 2.958 de GPU. O CSV de CPU tem 573 ocorrências adicionais de nomes repetidos. Isso exige detectar conflitos, não escolher a última linha. `cores` e `threads` não são pontuações e não alteram as especificações cadastradas. Não se inferem versão do PerformanceTest nem data de coleta a partir de commits, cabeçalhos HTTP ou datas locais. Não há cálculo de FPS, percentual ou comparação entre escalas.

Identificadores Git blob dos arquivos inspecionados:

- CPU: `708b30581a1bc0941b8fbcc5dedc1387657f1fbc`
- GPU: `6f497d0f917a8a77ae5d03dd04b7bbe36ffe6a9a`

A disponibilidade dos arquivos no GitHub **não comprova autorização para uso comercial dos dados de terceiros**, incluindo os dados PassMark. Verifique os direitos e condições aplicáveis antes desse uso.

## Execução administrativa

Na raiz do projeto, selecione explicitamente o ambiente e a conexão desejados conforme a configuração já adotada (`APP_ENV` e `URL_DATABASE`). Confira a conexão antes de qualquer gravação. Os comandos abaixo usam o ambiente configurado; não são instruções para importar em produção nesta tarefa.

Prepare o esquema pelo mecanismo existente:

```bash
cd backend
../venv/bin/flask --app app banco-preparar
```

Em SQLite em arquivo, `banco-preparar` faz backup antes das migrações. A migração `benchmarks_pecas` é incremental, idempotente e transacional, inclusive para DDL. Em banco novo, `create_all` já inclui as colunas. Conforme o padrão atual, `banco-preparar` recusa MySQL existente; esta migração não implementa atualização de MySQL existente.

Obtenha os dois CSVs como arquivos locais, sem executar os scripts do repositório. Preserve os snapshots usados (idealmente de uma revisão fixa) junto com o relatório JSON. O importador não acessa a rede e informa o SHA-256 de cada arquivo para reprodução.

Simulação:

```bash
../venv/bin/flask --app app benchmarks-importar \
  --cpu /caminho/cpu_passmark.csv \
  --gpu /caminho/gpu_passmark.csv \
  --simular > /tmp/benchmarks-simulacao.json
```

Importação autorizada para o banco escolhido:

```bash
../venv/bin/flask --app app benchmarks-importar \
  --cpu /caminho/cpu_passmark.csv \
  --gpu /caminho/gpu_passmark.csv \
  --lote 100 > /tmp/benchmarks-importacao.json
```

É permitido fornecer somente `--cpu` ou somente `--gpu`. `--simular` não grava nem altera objetos da sessão. Exige esquema já preparado, como a execução normal.

O JSON contém `atualizadas` (gravações confirmadas), `propostas`, `inalteradas`, `nao_encontradas`, `ambiguas`, `invalidas`, `duplicadas`, hashes e detalhes das propostas/pendências. Propostas mostram valores anteriores e novos; a data UTC será atribuída na gravação. Quantidades de atualizadas/propostas/inalteradas são por peça; não encontradas e ambíguas são por grupo de nome normalizado (ou colisão de destino); inválidas contam linhas do grupo rejeitado. `duplicadas` conta cópias equivalentes descartadas. Os totais não devem ser somados para inferir o número de linhas.

## Associação e validação

- Primeiro nome exato (`modelo` ou `fabricante + modelo`); depois nome normalizado. Múltiplos IDs são pendência para revisão, sem escolha automática.
- Normalização trata caixa, espaços, marcas registradas, hífens entre palavras, grafia `i5-13400`/`i5 13400` e sufixos separados ou unidos como `4060 Ti`/`4060Ti`. Mantém geração, números, F/K/X/XT/XTX/Ti/SUPER e indicadores notebook/mobile/Laptop GPU. Não usa substring, distância textual nem extrai modelo de nomes comerciais extensos.
- Duplicatas com pontuações diferentes bloqueiam o grupo inteiro, mesmo que uma linha seja exata. Duplicatas equivalentes usam nome de origem escolhido por ordem lexical, de forma estável. Grupos diferentes apontando à mesma peça também são bloqueados.
- Aceita UTF-8 com ou sem BOM, CSV com aspas e ponto decimal, incluindo milhares com vírgula dentro de campo entre aspas. Rejeita formato inesperado, cabeçalhos duplicados, colunas faltantes/extras, números negativos, zero, NaN/infinito ou fora da precisão suportada.
- Uma métrica ausente não apaga valor existente; linha sem nenhuma pontuação ou com qualquer pontuação inválida é rejeitada integralmente. Importação parcial sobre teste/versão existente diferente é rejeitada para evitar misturar escalas. Importação completa substitui o conjunto e seus metadados.
- Cabeçalhos são estritos para detectar mudanças de contrato; novos formatos precisam de revisão do importador. Nomes com clock, descrições comerciais ou prefixos adicionais podem ficar sem associação propositalmente. A revisão pode corrigir o cadastro ou preparar um snapshot local revisado, mantendo a rastreabilidade documental.

## Falhas, volume e validação

Os arquivos completos e os índices do catálogo são carregados em memória (volume observado inferior a 10 mil linhas), permitindo detectar duplicatas antes de persistir. Todos os arquivos são lidos e seus formatos validados antes de gravar. As alterações são confirmadas em lotes configuráveis, cada um em uma transação. Uma falha de persistência reverte o lote atual e interrompe com erro e quantidade já confirmada; lotes anteriores permanecem. A reexecução idempotente com os mesmos arquivos retoma as pendências sem atualizar timestamps dos dados iguais. Erros de leitura/formato também produzem saída CLI não zero.

Testes automatizados:

```bash
cd backend
../venv/bin/python -m pytest tests/services/benchmark_service/test_importar_benchmarks.py -q
```

Cobrem correspondência exata/normalizada, sufixos e notebook, ambiguidades, duplicatas, números e arquivos inválidos, preservação de valores, simulação, idempotência, CLI, migração incremental/rollback e falhas por lote. Os CSVs reais também foram processados em um SQLite temporário em memória com duas peças de teste: simulação com duas propostas, importação com duas atualizações e reexecução com zero atualizações. Nenhuma importação com gravação foi realizada no banco de produção.
