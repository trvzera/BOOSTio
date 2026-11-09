# Catálogo técnico docyx/pc-part-dataset

Fonte: https://github.com/docyx/pc-part-dataset. O README informa 66.778 itens,
com última atualização em 23/07/2025. A revisão baixada está em `manifesto.json`;
não confundir a data de download com a referência dos dados.

## Execução

Na pasta `backend`, com o ambiente Python do projeto:

```bash
python -m flask --app app dataset-pecas-baixar --destino ../benchmarks/pc-part-dataset
python -m flask --app app dataset-pecas-preparar
python -m flask --app app dataset-pecas-preparar --aplicar
python -m flask --app app dataset-pecas-importar --pasta ../benchmarks/pc-part-dataset --resumo ../output/dataset-simulacao.json
python -m flask --app app dataset-pecas-importar --pasta ../benchmarks/pc-part-dataset --aplicar --resumo ../output/dataset-importacao.json
```

Crie a pasta de destino dos relatórios antes de usar `--resumo`. A opção
`--commit SHA_COMPLETO` no download reproduz uma revisão específica; sem ela,
resolve `main` uma vez e fixa todos os arquivos naquele commit. A importação é
inteiramente local, verifica os hashes e recusa snapshots misturados. Não executa
scrapers. Faça backup e teste numa cópia antes de migrar o banco da VPS.

A preparação simula por padrão. Usa a migração existente para SQLite e MySQL,
preservando linhas, índices e referências. Só permite NULL em campos necessários
para representar as ausências reais da fonte. MySQL confirma DDL implicitamente;
backup continua necessário. A importação não executa migrações automaticamente.

## Organização

- `NormalizarPecaDatasetService`: adapta as colunas reais, identifica categorias e
  valida os tipos. Não interpreta SMT como contagem de threads, PCIe como NVMe,
  TDP como potência de fonte, ausência de GPU como ausência de vídeo integrado,
  nem frequência de boost como frequência base.
- `BaixarDatasetService`: download limitado de arquivos públicos numa revisão fixa.
- `ImportarDatasetService`: valida todos os arquivos antes de iniciar, percorre as
  linhas e delega lotes à persistência. Sem consultas SQL no service.
- `RepositorioDatasetPecas`: reutiliza o bloqueio `ControleColeta`, revalida o
  índice quando outra execução o modifica e confirma lotes de até 250 registros.
  Uma falha desfaz o lote atual; lotes anteriores permanecem confirmados. É seguro
  repetir. A simulação mantém um índice virtual para detectar duplicatas também
  entre lotes e não insere componentes nem aumenta o controle de coleta.

## Categorias e conversões

Foram selecionados 14 arquivos, com 64.207 linhas na revisão
`c52a04ca9465c83997ed335f7767b09a2005dd26`:
CPU, CPU cooler, motherboard, memory, internal hard drive, video card, case,
power supply, monitor, headphones, keyboard, mouse, case fan e wireless network card.
O armazenamento é separado em HD/SSD pelo campo `type`. Coolers com `size`
positivo são direcionados a water cooler; sem tamanho de radiador, a classificação
provisória é air cooler. Essa classificação precisa de validação antes de publicar.
Não há importação de sistemas operacionais, caixas de som, webcams, acessórios,
fontes UPS ou outras categorias que não têm tabela correspondente.

Capacidade RAM = quantidade de módulos × capacidade de cada módulo. Cor, DDR,
velocidade, CL, quantidade de módulos e capacidade/interface de armazenamento
ficam no nome comercial para preservar variantes. A frequência RAM segue a unidade
MHz documentada pelo dataset; o valor original também é preservado. Threads,
socket, memória suportada pela placa-mãe, conectores, compatibilidades e outros
campos não disponíveis permanecem NULL. Nenhum preço, estoque, benchmark ou oferta
é importado. Não são criados MPNs ou GTINs a partir do nome ou do hash.

## Identidade e duplicatas

Cada peça inserida guarda arquivo, linha, URL com commit fixo, SHA-256 e dados
originais sem preço em `fontes_especificacoes._pc_part_dataset`. O hash de identidade
usa categoria e todos os campos originais exceto `price` e `price_per_gb`, permitindo
reordenação e alterações de preço sem duplicação. O código da origem nunca vira MPN.

A mesma identidade já importada fica inalterada. Linhas idênticas dentro do lote
são contadas como duplicadas. Nome comercial existente com dados ou variantes não
comprovados fica em revisão no relatório, sem inserir outro registro nem alterar
a peça atual. Não há associação aproximada, sobrescrita ou escolha arbitrária
entre candidatos. Alterações da ficha na origem exigem revisão quando há colisão
com o nome existente. Isso pode omitir SKUs legítimos que a fonte não distingue
pelo nome; os casos são contabilizados, não fundidos automaticamente.

## Estado dos componentes

Os registros são criados diretamente nas tabelas das peças, com
`status_validacao=em_revisao`, indicador técnico calculado pelos mínimos vigentes, `preco=NULL` e
`esgotado=NULL`. Não ficam disponíveis na montagem automática. O catálogo não tem
MPN/EAN estruturado nem todas as especificações necessárias: cadastrar não equivale
a validar identidade ou compatibilidade. `CAMPOS_TECNICOS_OBRIGATORIOS` preserva os
requisitos do validador, mesmo nos campos que agora aceitam NULL no banco.

O relatório distingue criações, linhas inalteradas, duplicatas, colisões para revisão,
entradas inválidas e falhas de persistência, com contagens por categoria. Uma entrada
sem campo ainda obrigatório, com valor incompatível com o tipo da coluna ou nome
maior que o limite é recusada e detalhada. Dados que não têm coluna equivalente
continuam disponíveis na evidência original.

O repositório declara licença MIT, mas seus dados foram coletados do PCPartPicker.
A disponibilidade no GitHub e a licença do repositório não comprovam por si só
a autorização comercial sobre dados de terceiros.

## Resultado da execução local

Foram lidas 64.207 linhas: 51.920 novas peças, 4.043 duplicatas, 6.433 colisões
encaminhadas para revisão no relatório e 1.811 entradas inválidas/insuficientes.
Nenhuma falha de persistência. O banco passou de 1.535 para 53.455 peças.
A verificação comparou todos os valores dos registros anteriores, incluindo usuários,
builds e ofertas, e confirmou a preservação. Também passaram `integrity_check`,
`foreign_key_check` e a busca de identidades de origem duplicadas.

Uma segunda execução integral na cópia criou zero peças e reconheceu as 51.920
identidades já importadas. O relatório detalhado local está em
`output/importacao-dataset/resultado-local.json`; a cópia de segurança está no mesmo
diretório, com nome `backup-local-*.db`. Os arquivos em `output` não são versionados.
Os registros novos estão em revisão, sem cotação ou disponibilidade presumida.
A política de mínimos e a reavaliação posterior estão em [requisitos-montagem.md](requisitos-montagem.md).

Para testar sem carregar as fontes externas configuradas no ambiente local:

```bash
ICECAT_INDICE= FABRICANTES_HABILITADOS=false python -m pytest -q
```

A execução completa passou: 1.694 testes, 18 ignorados e 20 subtestes. Os testes
MySQL que dependem de infraestrutura externa não foram executados nesta etapa.
