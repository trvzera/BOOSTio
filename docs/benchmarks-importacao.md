# Importação de benchmarks de CPU e GPU

## Fonte principal: ehan03/passmark

O comando `benchmarks-importar` usa snapshots locais dos arquivos reais:

- [data/raw/cpu/cpus.csv](https://github.com/ehan03/passmark/blob/main/data/raw/cpu/cpus.csv):
  `id`, `name`, `multi_thread_rating` e `single_thread_rating` (mais atributos técnicos).
- [data/raw/gpu/gpus.csv](https://github.com/ehan03/passmark/blob/main/data/raw/gpu/gpus.csv):
  `id`, `name`, `g3d_mark` e `g2d_mark` (mais atributos técnicos).

No snapshot verificado: 5.149 CPUs e 2.702 GPUs. O leitor verifica o cabeçalho completo,
IDs positivos, formato CSV, nome e pontuações antes de persistir. Não executa scraper,
não baixa arquivos automaticamente, não cadastra novas peças e não estima FPS.

| Categoria | Campo da fonte | Campo do banco |
|---|---|---|
| CPU | `multi_thread_rating` | `benchmark_multi_core` |
| CPU | `single_thread_rating` | `benchmark_single_thread` |
| GPU | `g2d_mark` | `benchmark_g2d` |
| GPU | `g3d_mark` | `benchmark_g3d` |

Os testes continuam identificados separadamente como `PassMark CPU Mark / Single Thread`
e `PassMark G2D / G3D`, compatíveis com o seletor. Nome na fonte, URL do CSV e data UTC
de atualização são preservados. Versão e data de referência ficam NULL: datas de
lançamento, primeiro benchmark e preço não são data de coleta. Zero não significa
ausência de medição. `NA`, `N/A` ou vazio significam métrica ausente; não apagam score
existente. Uma pontuação inválida rejeita a entrada inteira. Métricas parciais não
substituem um teste/versão diferente. Reexecuções iguais não mudam timestamps.

## Associações e limites de interpretação

`backend/data/benchmarks/passmark_associacoes.json` contém associações explícitas
revisadas por fabricante + nome comercial, ID e nome da referência na fonte, além
da VRAM para GPUs. IDs locais do banco não são usados como chave. Isso permite
usar a mesma referência de CPU/chip para ofertas comerciais diferentes, sem
escolher arbitrariamente entre cadastros pelo nome abreviado.

A importação exige que nome/ID da fonte e VRAM continuem coerentes com o mapa;
confere identidade completa e sufixos (Ti, SUPER, XT, XTX, PRO, mobile e 2048SP).
Nomes comerciais diferentes dos revisados não entram por busca aproximada.
Cadastros duplicados para a mesma chave ou associações conflitantes ficam para
revisão, assim como IDs duplicados com pontuação diferente na fonte. Mesmo nome
em vários IDs da fonte também bloqueia a associação. Cópias equivalentes não
sobrescrevem resultados em ordem arbitrária.

Sem associação explícita, admite apenas nome completo exato/normalizado único.
Variantes não reconhecidas ficam pendentes, preservando os benchmarks anteriores.
Para ampliar o catálogo, revise a peça e acrescente a associação ao JSON; não
retire sufixos, PRO, capacidade ou indicadores de notebook para forçar um match.

**GPU recebe a referência média do chip/variante da fonte, não uma medição exata
daquele SKU ASUS/MSI/Gigabyte, OC, refrigeração ou configuração do comprador.**
A capacidade máxima informada na fonte, sozinha, não comprova a variante medida.
O mapa não modifica especificações do catálogo nem afirma desempenho idêntico
entre placas do mesmo chip. A associação da referência deve ser reavaliada quando
nome, variante ou VRAM do produto mudar. O relatório registra `referencia_chip_gpu`
ou `modelo_cpu`, ID da fonte e hash do mapa para rastreabilidade.

Snapshots antigos de `Algerian-Laptop-Market` continuam reconhecidos pelo cabeçalho
para reproduzir importações anteriores. Não misture formatos de fontes diferentes
na mesma execução. O formato novo é o principal e substitui as referências da fonte
anterior quando há associação válida; pendências não apagam dados antigos.

## Execução em Docker na VPS

Primeiro prepare o esquema. Para MySQL existente use a migração explícita descrita
em `docs/configuracao-producao.md` (`banco-atualizar-mysql`), com backup; não use
`banco-preparar` num MySQL existente. Se a migração dos benchmarks já foi aplicada,
não há novas colunas nesta troca de fonte. Reconstrua a API para carregar o novo
importador e o mapa de associações antes de executar.

Na raiz do projeto, obtenha e preserve os arquivos locais:

```bash
mkdir -p benchmarks
curl -fL --retry 3 https://raw.githubusercontent.com/ehan03/passmark/main/data/raw/cpu/cpus.csv -o benchmarks/cpus.csv
curl -fL --retry 3 https://raw.githubusercontent.com/ehan03/passmark/main/data/raw/gpu/gpus.csv -o benchmarks/gpus.csv
```

Simulação sem gravação:

```bash
docker compose --env-file .env.production run --rm --no-deps \
  -v "$PWD/benchmarks:/benchmarks:ro" \
  api python -m flask --app app benchmarks-importar \
  --cpu /benchmarks/cpus.csv --gpu /benchmarks/gpus.csv --simular \
  > benchmarks/simulacao.json
```

Após conferir o relatório e ter backup do banco:

```bash
docker compose --env-file .env.production run --rm --no-deps \
  -v "$PWD/benchmarks:/benchmarks:ro" \
  api python -m flask --app app benchmarks-importar \
  --cpu /benchmarks/cpus.csv --gpu /benchmarks/gpus.csv --lote 100 \
  > benchmarks/importacao.json
```

Permite apenas CPU ou apenas GPU. Não precisa de nova chamada à IA nem coletar preços.

## Uso local e relatórios

Com o ambiente e `URL_DATABASE` apontados explicitamente para o banco desejado,
dentro de `backend`:

```bash
../venv/bin/python -m flask --app app benchmarks-importar \
  --cpu /caminho/cpus.csv --gpu /caminho/gpus.csv --simular
```

Sem `--simular`, grava. O comando de importação não faz backup por conta própria;
faça uma cópia consistente do SQLite/MySQL antes da primeira importação da nova
fonte. Na atualização local desta tarefa, o backup foi criado antes das colunas e
da importação; CSVs e relatórios foram preservados em `database/benchmarks/`.

No formato novo, `atualizadas`, `propostas`, `inalteradas`, `nao_encontradas`,
`ambiguas`, `invalidas` contam **peças do catálogo**, com resumo separado em
`por_tipo.cpu` e `por_tipo.gpu`. Linhas inválidas na fonte, inclusive modelos não
cadastrados, são contadas em `arquivos.<tipo>.linhas_invalidas`. `duplicadas` conta
cópias equivalentes de linhas da fonte, sem multiplicar pelos SKUs associados.
O formato legado mantém a contagem anterior por grupos de nomes/linhas.

A leitura e validação estrutural de todos os arquivos ocorre antes de gravar.
As confirmações acontecem em lotes transacionais; falha reverte o lote atual e
informa quantas peças dos lotes anteriores já foram confirmadas. A reexecução
com o mesmo snapshot retoma pendências sem atualizar dados iguais. Nenhum campo
fora de benchmark é alterado, inclusive o `atualizado_em` geral da peça.

Hashes dos snapshots revisados:

| Arquivo | Git blob |
|---|---|
| CPU | `a51a35fa699c7c8d9a1f5b5e1e7a70ed83225308` |
| GPU | `a42a2040672ecac6ecc7cd1e5220085af35a03c5` |

O importador informa SHA-256 dos dois arquivos e do mapa. Preserve-os com o JSON
para reprodução. Download da branch `main` pode mudar no futuro; para repetição
exata use os snapshots guardados ou uma revisão Git fixa.

## Direitos de uso e testes

A disponibilidade no GitHub e a licença MIT do software desse repositório não
comprovam autorização para uso comercial dos dados PassMark de terceiros.
[PassMark oferece licenciamento de dados](https://www.passmark.com/services/market-analysis.php).

```bash
cd backend
../venv/bin/python -m pytest tests/services/benchmark_service -q
```

Os testes cobrem formato novo/legado, CLI, associação explícita, múltiplos SKUs,
VRAM/sufixos/desktop-notebook, ambiguidades, fonte alterada, inválidos, métricas
parciais, simulação, idempotência e reversão/retomada após falha no lote.

## Resultado da atualização local de 02/11/2026

Banco local de 100 CPUs e 100 GPUs: **190 peças atualizadas**, sendo **99 CPUs e
91 GPUs**, com zero entradas de peças inválidas/ambíguas. Ficaram 10 cadastros
sem associação segura (1 CPU e 9 GPUs), preservados. A cobertura final é 95%.
O banco local ainda não tinha as colunas de benchmark antes desta execução; a
preparação incremental foi aplicada após criar o backup. Isso é independente
das 63 peças anteriormente importadas pelo usuário na VPS.

Foi comparado o conteúdo de todas as 25 tabelas, ignorando somente as colunas de
benchmark: nenhum outro dado foi alterado. A simulação posterior apresentou
190 inalteradas, zero propostas. O resumo, caminho do backup e relatório das
pendências estão em `database/benchmarks/ultima-importacao.json` (dados locais
ignorados pelo Git). Nenhuma operação foi feita na VPS.
