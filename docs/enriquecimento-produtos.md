# Etapa 4 — enriquecimento com evidências

`EnriquecerProdutoService` extrai dados de atributos estruturados oficiais. `EnriquecerPendenciasService` consulta o detalhe `/products/{id}` pelo transporte e renovação de tokens existentes, confere o ID retornado e guarda a ficha e suas lacunas na pendência. Não faz scraping de páginas de fabricantes, não completa campos com IA e não aprova registros incompletos.

A fonte técnica implementada nesta etapa é o catálogo oficial do Mercado Livre. Cada campo confirmado registra URL e ID do atributo. Os adaptadores iniciais usam somente IDs observados nos snapshots existentes de CPU, GPU, RAM, placa-mãe, SSD e HD. As 17 categorias têm requisitos derivados dos campos obrigatórios de seus models; categorias/atributos sem adaptador ficam para revisão, em vez de receber especificações inventadas. Adicionar uma fonte de fabricante exige um adaptador permitido e testes próprios; uma URL no anúncio não valida automaticamente uma ficha.

A ficha nova exige todos os campos não nulos do model, inclusive fabricante, modelo, consumo, preço e disponibilidade real. CPU também exige confirmação sobre vídeo integrado e inclusão de cooler. `COOLING_TYPE` não prova inclusão de cooler. Disponibilidade só é extraída de `available_quantity` numérico, nunca do estado ativo de um produto de catálogo. Muitos anúncios não expõem esse campo: nesses casos novos componentes continuam pendentes. A inclusão de ofertas em componentes já existentes continua possível após matching comprovado, independentemente da completude necessária para criar um novo model.

Unidades são verificadas. Capacidades de armazenamento usam GB decimais (1 TB = 1000 GB); velocidades ou frequências em unidades não implementadas ficam desconhecidas. TDP é registrado como potência nominal de planejamento, não como medição de consumo real. Campos com múltiplos valores, fora do limite do model ou contraditórios ficam para revisão. Preços ausentes nunca viram zero e flags ausentes nunca viram false.

`ConsultarBenchmarkCatalogoService` consulta opcionalmente os CSVs locais ehan03/passmark pelo parser e normalização já existentes. Só aceita nome exato ou normalizado único, preserva teste/métricas e hash do arquivo, e bloqueia duplicatas conflitantes. Não estima pontuações nem deriva FPS. GPU é referência de chip, não medição de uma placa específica. Sem CSV configurado ou sem correspondência, não preenche benchmark. A disponibilidade dos arquivos no GitHub não comprova autorização comercial para dados de terceiros.

```bash
python -m flask --app app mercadolivre-enriquecer --limite 20
python -m flask --app app mercadolivre-enriquecer --limite 20 --aplicar
```

O padrão é simulação. `--benchmark-cpu CAMINHO` e `--benchmark-gpu CAMINHO` recebem arquivos locais; use volumes somente leitura no Docker. `--depois-id`, `--max-requisicoes` e `--intervalo` limitam a execução. A aplicação grava apenas evidências em `produto_pendente`, mantendo status de revisão. Falhas HTTP, limite de chamadas e falhas de persistência interrompem com resumo; fichas incompletas são contabilizadas como revisão. Nenhuma peça, oferta ou benchmark existente é alterado nesta etapa.

A validação, benchmarks e consulta complementar agora são compartilhados entre lojas. MPN não é obrigatório quando o modelo e as especificações comprovam a identidade. Há um snapshot técnico local licenciado; consulte [associacao-inteligente.md](associacao-inteligente.md) para campos, limites e proveniência. Os adaptadores não inventam preço/estoque a partir da ficha de hardware.
