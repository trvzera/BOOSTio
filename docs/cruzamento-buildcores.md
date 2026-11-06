# Complementação de fichas com BuildCores OpenDB

O cruzamento é independente de Mercado Livre e não pesquisa ofertas. Usa um
snapshot local, com commit fixo, UUID do registro e SHA-256 de cada arquivo. O
adaptador não executa código remoto. Preserva no download README, LICENSE e NOTICE.

## Comandos administrativos

Na pasta `backend`, com o ambiente Python do projeto:

```bash
python -m flask --app app buildcores-baixar --pasta ../output/buildcores/snapshot
python -m flask --app app buildcores-cruzar --pasta ../output/buildcores/snapshot --resumo ../output/buildcores/simulacao.json
```

O download aceita `--commit SHA_COMPLETO` para reproduzir uma revisão. Por padrão,
o cruzamento simula, sem confirmar dados. A opção `--aplicar` confirma as alterações
no banco configurado; execute primeiro numa cópia, após conferir o relatório e as
condições de uso da fonte. Não há nova migração para o enriquecimento em si; o
catálogo importado do docyx deve estar preparado.

A licença atual do OpenDB é CC BY-NC-SA 4.0. O NOTICE informa que uso comercial que
dependa de permissão requer concessão escrita dos titulares e distingue fatos
ordinários de direitos sobre a base. Este trabalho manteve os dados enriquecidos
numa cópia de teste, sem publicação ou alteração do banco principal.

## Fluxo e divisão das responsabilidades

- `BaixarSnapshotBuildcoresService`: download limitado e revisão fixa.
- `NormalizarFichaBuildcoresService`: mapeia apenas campos efetivamente observados
  nos JSONs, valida tipos e ignora zeros usados como ausência. Não calcula threads,
  não confunde PCIe com NVMe e não transfere preço ou benchmarks.
- `CompararFichasBuildcoresService`: modelo normalizado, fabricante, variantes,
  cores e especificações comparáveis. Preserva X, X3D, Ti, SUPER, OC e revisões.
  Quantidade de módulos, capacidade, DDR, velocidade e CL devem conferir em RAM.
  Clocks de fábrica e comprimento também são confrontados nas GPUs quando presentes
  no docyx. Não há aprovação baseada apenas em similaridade textual ou percentuais.
- `CruzarCatalogoBuildcoresService`: monta o índice em memória e identifica candidatos
  únicos. Mais de um candidato confirmado, candidato incompleto concorrente ou a
  mesma ficha destinada a duas peças locais impedem a atualização. Só percorre peças
  com evidência `_pc_part_dataset`; o catálogo legado não é alterado.
- `RepositorioEnriquecimentoBuildcores`: concentra consultas e atualizações. Usa o
  bloqueio existente, transações por lote de 100 e assinatura do registro completo
  para recusar alterações concorrentes. Confirma um lote ou desfaz esse lote inteiro.
  Lotes anteriores confirmados permitem retomada por reexecução idempotente.

## Identificadores e proveniência

Só códigos canônicos `identifiers.identifiers[type=mpn]` são considerados para o campo
`part_number`, com validação de formato; nomes com espaços e códigos curtos são
recusados. `metadata.part_numbers` pode conter nomes e não é copiado como MPN.
Múltiplos MPNs ficam sem escolha automática: podem ser regiões ou embalagens.
Para CPUs, não transfere MPN nem inclusão de cooler, pois o docyx não informa Box/Tray.

Preenche somente valores NULL, sem sobrescrever campos conhecidos. Guarda por campo
URL do registro, commit, UUID, SHA-256 e caminho de origem. Fatos conflitantes ficam
no relatório. Não cria peças, ofertas ou históricos de preço, não muda aprovação,
nome ou fabricante. Recalcula somente `ficha_montagem_validada` pelos mínimos técnicos
vigentes, preservando a revisão de identidade. Uma ficha sem pendências técnicas
continua dependendo da revisão de identidade e de oferta para uso na montagem.

## Resultado real na cópia local

Revisão: `3afdaa74be9c19a414fc02a8a92dba14165b3297`.

- 45.685 fichas normalizadas nas categorias suportadas; 65 não puderam ser adaptadas.
- 51.920 peças docyx analisadas.
- 2.125 correspondências aceitas pelas regras; 7 não precisavam de dados adicionais.
- 2.118 peças enriquecidas (4,08% das analisadas), com 4.617 campos preenchidos.
- 1.554 part numbers preenchidos; nenhum SKU regional escolhido entre múltiplos códigos.
- 42.206 sem candidatos na normalização atual, 5.130 com conflitos e 2.459 ambíguas.
- 0 novas peças, 0 alterações de preços/ofertas e 0 falhas de persistência.
- Nenhuma das peças enriquecidas ficou sem todas as pendências para montagem.

| Categoria | Peças enriquecidas |
|---|---:|
| CPU | 213 |
| Placa-mãe | 75 |
| RAM | 1.716 |
| Water cooler | 4 |
| Fan | 110 |

O resultado mede as regras atuais, não a cobertura máxima do BuildCores nem uma taxa
de acerto aferida por revisão humana. Nomes estendidos que não geram a mesma chave,
formatos não reconhecidos e informações ausentes produzem falsos negativos. Nenhuma
GPU foi aceita neste ensaio. Ampliar as equivalências exige testes de variantes e
verificação independente; não se deve afrouxar os critérios para aumentar contagens.

Relatórios locais: `output/buildcores/resultado.json`, `auditoria.json`,
`aplicacao.json` (reexecução) e `testes.log`. Banco enriquecido:
`output/buildcores/banco-teste.db`. Arquivos de teste e snapshot não são versionados.

Validação: 1.705 testes passaram, 18 ignorados e 20 subtestes passaram. Os 11 testes
específicos cobrem simulação, proveniência, reexecução, sufixos, kits RAM, cores,
conflitos, concorrência, rollback, download e CLI. A reexecução real na cópia confirmou
2.125 correspondências inalteradas, zero campos adicionais e zero gravações de peças.
A auditoria confirmou preservação dos valores anteriores e integridade do banco.

A medição acima usou os requisitos anteriores. Após a revisão dos mínimos técnicos,
2.089 das 2.118 fichas enriquecidas atendem à candidatura condicional. Ver
[requisitos-montagem.md](requisitos-montagem.md); isso não aprova identidades nem ofertas.
