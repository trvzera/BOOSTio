# Revisão manual dos vínculos Mercado Livre

A revisão abrange **todos os 1.535 registros** do banco local e ainda está em
andamento. O manifesto de aprovados é incremental; a meta de 70% corresponde a
1.075 peças, e ainda não foi atingida. O inventário completo com o estado de cada
registro está em `backend/data/revisao-mercadolivre-inventario.json`.

`nao_revisada` significa que a peça ainda aguarda revisão. `pendente` significa
que a busca inicial foi conferida, mas ainda falta resolver identidade, variante,
ficha técnica ou disponibilidade de ofertas. Somente `aprovada` entra no manifesto.
Coletar resultados de busca não equivale a revisar ou aprovar uma associação.
A tabela abaixo documenta o primeiro lote; a lista completa e atualizada está no
manifesto, com evidências e justificativas por peça.

A decisão de cada entrada é humana e está em
`backend/data/vinculos-mercadolivre-revisados.json`: referência interna, fabricante,
modelo, produto KaBuM, ficha local esperada, fontes, data, justificativa e snapshot
do catálogo conferido. O importador não faz associação por similaridade nem
transforma códigos `KABUM-*` em MPNs.

| Peça | Referência | Catálogo revisado |
| --- | --- | --- |
| Ryzen 7 7700X | SEED-CPU-04 | [MLB19711896](https://www.mercadolivre.com.br/p/MLB19711896) |
| Ryzen 9 7900X | SEED-CPU-05 | [MLB19711898](https://www.mercadolivre.com.br/p/MLB19711898) |
| Core i7-13700K | SEED-CPU-09 | [MLB19917322](https://www.mercadolivre.com.br/p/MLB19917322) |
| Core i9-14900K | SEED-CPU-10 | [MLB27830801](https://www.mercadolivre.com.br/p/MLB27830801) |
| Ryzen 3 4100 BOX | SEED-CPU-11 | [MLB21034791](https://www.mercadolivre.com.br/p/MLB21034791) |
| HyperX Pulsefire Core preto | SEED-MOUSE-04 | [MLB14141317](https://www.mercadolivre.com.br/p/MLB14141317) |
| Logitech G203 LIGHTSYNC preto | SEED-MOUSE-01 | [MLB16211422](https://www.mercadolivre.com.br/p/MLB16211422) |
| Seagate Barracuda 2 TB ST2000DM008 | SEED-HDD-02 | [MLB65685460](https://www.mercadolivre.com.br/p/MLB65685460) |
| WD Purple 4 TB WD43PURZ | SEED-HDD-05 | [MLB45974837](https://www.mercadolivre.com.br/p/MLB45974837) |
| Kingston NV2 500 GB SNV2S/500G | SEED-SSD-01 | [MLB45487429](https://www.mercadolivre.com.br/p/MLB45487429) |

## Evidência e ressalvas

As páginas KaBuM cadastradas são usadas como evidência da identidade e variante.
A revisão de um vínculo não certifica todos os campos da ficha técnica local.
Contradições relevantes são registradas e não são corrigidas por este importador. O detalhe `/products/{id}` e os anúncios `/products/{id}/items`
foram consultados na API Mercado Livre. Foram encontrados anúncios novos para
as peças do primeiro lote. Novos lotes exigem nova conferência. Preços e estoque não são fixados no manifesto; disponibilidade e
preços podem mudar, e estoque não confirmado permanece NULL.

O catálogo também tem metadados inconsistentes. As justificativas registram
explicitamente, por exemplo: TDP 128 W no i7 onde a origem informa 125 W;
Hyper-Threading desmarcado no i9 identificado por BX8071514900K; iluminação
negada no G203 apesar do código exato 910-005793; cache 64 GB no WD43PURZ;
dissipador marcado no NV2. Nesses casos a identificação foi revisada pelo código
exato e pela origem, sem importar esses atributos errados para a peça. Isso não
certifica a descrição individual de cada vendedor, inacessível pelo endpoint
`/items/{id}` nesta integração. A oferta deve ser conferida antes de comprar.

Divergências entre dois SKUs plausíveis, embalagem BOX/OEM, capacidade, DDR,
frequência ou a própria ficha local ficaram pendentes. A RAM já associada
MLB74886260 também está pendente de nova revisão porque os campos MPN e MODEL
contêm códigos diferentes. A revisão não alterou esse vínculo na VPS.

## Arquitetura e aplicação

`PopularPecasService` aplica o manifesto após cadastrar as seeds e restaurar seus
links, apenas se a tabela estiver preparada. Não faz consultas ao Mercado Livre
nem cadastra ofertas nessa etapa. Não usar o seed para atualizar a VPS existente:
o comando específico aplica somente os vínculos revisados, sem recriar peças.

A migração acrescenta `especificacoes_revisadas` JSON nullable à tabela de vínculos.
Preserva os vínculos antigos. As novas revisões bloqueiam coleta e exibição se a
ficha local mudar, além das verificações existentes de identidade e assinatura
do catálogo. Vínculos antigos sem ficha revisada mantêm a validação anterior.

Depois de publicar esta versão e fazer backup, construir a API e **migrar antes
de recriar o serviço**:

```sh
docker compose --env-file .env.production build api
docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app mercadolivre-vinculos-preparar
docker compose --env-file .env.production up -d --no-deps --force-recreate api

# Conferir a simulação antes de gravar os vínculos.
docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app mercadolivre-vinculos-importar

docker compose --env-file .env.production run --rm --no-deps -T api \
  python -m flask --app app mercadolivre-vinculos-importar --aplicar

# Consultar somente peças já vinculadas; evita buscas nas pendentes.
bash deploy/atualizar_ofertas_mercadolivre.sh --somente-vinculadas \
  --limite-pecas 100 --max-requisicoes 100 --intervalo 2

# Cadastrar uma oferta por peça (novo padrão).
bash deploy/atualizar_ofertas_mercadolivre.sh --aplicar --somente-vinculadas \
  --limite-pecas 100 --max-requisicoes 100 --intervalo 2
```

O importador é idempotente; conflitos vão para revisão e vínculos divergentes
não são sobrescritos. Cada peça tem sua transação. Falha de persistência
interrompe a aplicação e pode haver peças anteriores já confirmadas; repetir
não as duplica. Os IDs locais não são usados no manifesto, mas referência,
fabricante, modelo, produto de origem e especificações precisam corresponder.
Outra versão da ficha na VPS pode, corretamente, recusar uma entrada.

A coleta passou a selecionar uma oferta nova por padrão; o parâmetro
`--ofertas-por-peca` continua configurável. A seleção considera preço e desempates
estáveis entre anúncios novos, sem somar frete não informado. Ao aplicar a coleta
com limite um, outras ofertas anteriormente ativas daquela peça são desativadas,
sem apagar seu histórico nem marcar estoque como esgotado.

## Resultado da validação local

- Simulação do manifesto: dez propostas.
- Aplicação apenas em cópia SQLite: dez vínculos; repetição com dez inalterados.
- Simulação real da coleta: dez peças associadas, dez ofertas propostas, zero falhas.
- Nenhuma nova peça, preço de referência ou oferta gravados no banco original ou na VPS.

Os arquivos locais de evidência e relatório ficam em `output/mercadolivre/` e não
são versionados. O manifesto e as pendências são versionados para reprodução.
