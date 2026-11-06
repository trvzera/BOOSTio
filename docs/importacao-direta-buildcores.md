# Importação direta do BuildCores

Usa o snapshot público já baixado, fixado por commit e hashes. Complementa o catálogo
nas tabelas existentes e pode criar componentes ausentes. Não cria preços, ofertas,
históricos, usuários ou builds; não aprova identidades automaticamente.

## Execução

Na pasta `backend`, com o banco de teste configurado e o esquema de catálogo parcial
já preparado:

```bash
python -m flask --app app buildcores-importar --pasta ../output/buildcores/snapshot --resumo ../output/buildcores/importacao-simulacao.json
python -m flask --app app buildcores-importar --pasta ../output/buildcores/snapshot --aplicar --resumo ../output/buildcores/importacao-resultado.json
```

Simula por padrão. O comando usa o banco configurado na aplicação, portanto use uma
cópia e confira o destino antes de `--aplicar`. Para novo download, utilize o comando
`buildcores-baixar`, preferencialmente com `--commit SHA_COMPLETO`. A aplicação foi
feita somente em cópia local nesta tarefa. A licença CC BY-NC-SA e as condições de
uso comercial do BuildCores continuam aplicáveis; não houve deploy na VPS.

## Arquitetura

- `LerSnapshotBuildcoresService`: verifica arquivos, UUIDs, limites e hashes antes de
  começar a persistência. Categorias sem tabela equivalente são contabilizadas fora
  do escopo. Placas Ethernet não são classificadas como adaptadores Wi-Fi.
- `NormalizarFichaBuildcoresService`: adapta campos reais, sem presumir valores.
  Compartilhado com o enriquecimento. Conectividade de periféricos vem dos campos
  estruturados correspondentes; comportamento linear/tátil de switch não comprova
  mecanismo mecânico. Membrana explícita é preservada como `mecanico=False`.
- `ImportarCatalogoBuildcoresService`: valida nomes, limites e campos ainda NOT NULL;
  divide a importação em lotes de 100 e resume resultados por categoria. Reavalia
  casos inicialmente pendentes após incorporar novas identidades, até estabilizar
  ou alcançar o limite explícito de seis rodadas. Cada ficha é contada uma só vez.
- `RepositorioImportacaoBuildcores`: concentra consultas, índices e gravações, com o
  bloqueio já existente e transação por lote. Falha desfaz todo o lote atual. O cache
  é reconstruído se outra execução altera a versão do controle.

## Duplicatas e atualização

Prioriza UUID previamente associado e MPN canônico; confere fabricante, campos
conhecidos, cor e clocks de GPU quando disponíveis. Múltiplos candidatos ou valores
conflitantes vão para revisão no relatório. Sem identificador forte, usa a comparação
conservadora de modelo e especificações do cruzamento anterior.

Outra camada impede criação quando encontra nome semelhante, código comercial no
nome ou família comercial de GPU com o mesmo chip. Essa camada só bloqueia; nunca
aprova associação por similaridade. Trata descritores como `ATX Mid Tower`, tamanhos
de tela e complementos de painel como indícios de possível duplicata, sem fundir
variantes automaticamente. Algumas peças legítimas serão encaminhadas para revisão
por esse conservadorismo. A busca por tokens usa união estável, não apenas o token
momentaneamente mais raro: o crescimento do catálogo não pode apagar um alerta de
possível duplicação.

Novos registros guardam UUID em `referencia_interna` (`BUILDCORES:...`), fonte, hash,
commit e dados originais em `fontes_especificacoes._buildcores_importacao`. UUID não
vira part number. Um MPN só é preenchido quando existe um único código canônico de
formato aceitável; não escolhe entre códigos regionais/embalagens. Vários UUIDs que
sejam comprovadamente o mesmo produto podem compartilhar uma peça, com todas as
origens preservadas. Mudança de hash de ficha já importada exige revisão.

Registros existentes recebem apenas valores NULL. A importação preserva preços,
estoque, nomes e aprovação. Atribuição de cooler incluso não é transferida para CPU
docyx sem embalagem identificada. Recalcula o indicador de mínimos técnicos, mantendo
`status_validacao=em_revisao` nas peças novas. Mínimos técnicos não equivalem a oferta,
identidade aprovada ou compatibilidade completa da build.

## Relatórios e limitações

Arquivos locais em `output/buildcores/importacao-direta/`:
`resultado.json` (primeira aplicação), `aplicacao.json` (última execução),
`auditoria.json`, `testes-finais.log` e `banco-teste.db`. A cópia inicial vem de
`output/buildcores/banco-teste.db`, com o enriquecimento anterior preservado.

Entradas sem campos necessários ou com nomes maiores que os limites são recusadas,
sem inventar zero nem truncar a identidade. A fonte tem milhares de fichas de mouse
sem DPI e diversos periféricos sem conectividade; não é uma base inteiramente completa.
Uma revisão no relatório não cadastra outra peça. Resolver esses casos exige confirmar
identidades/variantes, não reduzir a exigência para alcançar uma meta numérica.

## Resultado da execução local

Snapshot `3afdaa74be9c19a414fc02a8a92dba14165b3297`, importado exclusivamente na
cópia `output/buildcores/importacao-direta/banco-teste.db`:

- 45.750 fichas nas categorias mapeadas; 3.038 fora do escopo.
- 13.563 peças novas; catálogo passou de 53.455 para 67.018 registros.
- Auditoria final: 9.376 novas atendem aos mínimos e 4.187 continuam incompletas.
- 94 peças anteriores receberam 230 campos ausentes; outras 43 complementações
  ocorreram em peças criadas nesta execução, pelas fichas equivalentes posteriores.
- 93 peças anteriores passaram a atender aos mínimos. Total: 12.751 → 22.220.
- 23.973 fichas para revisão; 5.747 inválidas; nenhuma falha de persistência.
- Reexecução: zero criações, zero complementações e 16.030 fichas inalteradas.

O contador `novas_com_minimos` do relatório de importação representa a avaliação no
momento da criação (9.366). Dez dessas peças passaram a atender aos mínimos após
complementação de fichas equivalentes na própria execução; a contagem final de
9.376 está em `auditoria.json`. Isso evita confundir resultados de etapas diferentes.
A auditoria também verificou preservação dos valores anteriores, ofertas, históricos,
usuários e builds, integridade SQLite e ausência de novos UUIDs/MPNs duplicados.
Isso não comprova que não existam variantes duplicadas sem identificador conhecido.

As peças novas permanecem em revisão, sem preço ou oferta. O banco principal e a VPS
não receberam esta importação. A meta de 30 mil peças com mínimos ainda não foi atingida.
