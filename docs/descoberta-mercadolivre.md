# Catálogo automatizado — etapa 2: descoberta

`DescobrirProdutosService` vive na pasta `services/mercadolivre_service`, reaproveita o transporte validado de `BuscarOfertasMercadoLivreService`, a renovação existente de tokens e `ControleRequisicoesService`. A descoberta não faz matching, enriquecimento ou importação de componentes. Só registra anúncios em `produto_pendente`, inicialmente pendentes. Não altera ofertas, preços de peças ou históricos.

## Endpoints e limites de acesso

A documentação oficial descreve:

- [Busca de produtos](https://developers.mercadolivre.com.br/buscador-de-produtos): `/products/search` com `site_id=MLB`, `status=active`, `q` e `domain_id` opcional.
- [Busca de itens](https://developers.mercadolivre.com.br/pt_br/itens-e-buscas): `/sites/MLB/search`, palavras-chave `q` e categoria oficial no parâmetro `category`.
- `/products/{catalogo_id}/items`: listagem de anúncios de um produto de catálogo, já usada pela integração existente.

A documentação não garante acesso para toda aplicação/conta. Especialmente a busca direta e os recursos de terceiros podem devolver 403. A descoberta registra e interrompe nesses casos; não usa scraping nem muda silenciosamente de endpoint. A disponibilidade real com a conta configurada só é confirmada ao executar a simulação. Nesta etapa os testes de descoberta usam respostas simuladas; não são evidência de autorização real.

O caminho padrão `catalogo` pesquisa produtos e lista seus anúncios. O nome armazenado nesse caminho é o nome do produto de catálogo, não um título individual fornecido pelo vendedor. A resposta original identifica claramente essa origem. O caminho `anuncios` usa a busca direta e guarda o título retornado por ela. Ambos geram o mesmo formato interno de pendência: loja, anúncio externo, vendedor, título, URL original, categoria sugerida, dados originais e data real de coleta.

A categoria interna (por exemplo `memoria_ram`) é uma **sugestão**, não uma identificação comprovada. Use uma busca por categoria interna por execução. O filtro `--categoria-ml` recebe um ID oficial real e vale somente para `anuncios`; `--dominio` recebe um domínio oficial real e vale somente para `catalogo`. Não há lista inventada de IDs nem inferência de equivalência entre taxonomias.

## Preparação

Use a imagem atualizada, backup e escritores parados para a migração. A preparação da etapa 1 agora inclui a tabela aditiva `execucao_descoberta`, sem alterar registros existentes:

```bash
docker compose --env-file .env.production run --rm --no-deps -T \
  api python -m flask --app app catalogo-preparar

docker compose --env-file .env.production run --rm --no-deps -T \
  api python -m flask --app app catalogo-preparar --aplicar
```

As credenciais e os tokens são os da integração já configurada. Não há novas variáveis de ambiente. A renovação OAuth existente pode atualizar tokens mesmo durante uma simulação; a simulação não grava pendências nem auditoria de descoberta.

## Simular uma descoberta pequena

```bash
docker compose --env-file .env.production run --rm --no-deps -T \
  api python -m flask --app app mercadolivre-descobrir \
  --categoria memoria_ram --consulta 'Kingston DDR4' \
  --max-paginas 3 --max-anuncios 20 --max-requisicoes 10
```

Para gravar somente a fila e o registro da execução, acrescente `--aplicar`. Isso **não cria peças nem ofertas publicadas**. Para testar o caminho direto, acrescente `--origem anuncios`. Filtros oficiais de categoria/domínio são opcionais; verifique seus valores reais antes de usá-los.

## Paginação e controle

O serviço percorre páginas de busca e páginas de anúncios. Todas contam em `max_paginas`, inclusive páginas de busca de catálogo que não produzem pendências diretamente. Tamanhos: 20 produtos de catálogo, 50 anúncios na busca direta e 100 anúncios na listagem de catálogo. O serviço para antes de consultar offset 1000, para não tentar varrer ilimitadamente a busca. Os limites são proteções da aplicação, não cotas oficiais garantidas pelo Mercado Livre.

O total de requisições inclui repetições por HTTP 429. Intervalo padrão: 1 segundo, mínimo 0,1. Reaproveitamos até três tentativas em 429 com espera exponencial e `Retry-After`; uma espera maior que 60 segundos interrompe a execução. 401, 403, 5xx, erro de rede, formato/paginação inválida ou limite de requisições interrompem e geram diagnóstico. Nenhuma falha vira resultado vazio silenciosamente.

A execução para sem nova página ao atingir o limite de anúncios. `limitado=true` indica parada pelo limite de páginas/anúncios/offset, não cobertura completa. `interrompido=true` indica erro ou orçamento de requisições esgotado; o comando imprime o resumo e termina com erro. Um lote de consultas não promete descobrir todo o catálogo.

## Persistência e acompanhamento

Uma transação por página de anúncios. Se uma página falhar, as anteriores confirmadas permanecem. Repetir a mesma busca é seguro: a identidade é `loja + produto_id_loja`. Pendências existentes, inclusive rejeitadas/importadas, não são sobrescritas ou reabertas. Anúncios já presentes em `oferta` são contabilizados e ignorados. A restrição única também protege contra inserções concorrentes de uma pendência.

O resumo distingue `encontrados` (linhas examinadas, incluindo inválidas/repetidas), `novos` (propostas na simulação ou inserções confirmadas na aplicação), `ja_coletados`, `ja_associados`, `repetidos`, `invalidos`, `paginas`, `requisicoes`, limites e falhas. Linhas inválidas são contadas e não entram na fila. A quantidade máxima de anúncios inclui linhas inválidas/repetidas, para manter o trabalho limitado.

Com `--aplicar`, `execucao_id` aponta para `execucao_descoberta`, com parâmetros, resumo e status final. O resumo também vai ao terminal e ao logger da aplicação. Tokens, cabeçalhos, corpo de erro HTTP e detalhes de SQL não são incluídos nos registros de execução. O JSON original de anúncios válidos fica somente na pendência, com valores decimais preservados como texto. Revisão de pendências continua administrativa, sem rota pública.

Sem `--aplicar`, salve o resumo do terminal se quiser manter o diagnóstico: não existe registro da simulação no banco. Uma interrupção abrupta do processo pode deixar uma execução `executando`; agendamento, exclusão mútua e retomada persistente pertencem à etapa 6. Até lá execute uma descoberta de cada vez e repita buscas limitadas quando necessário; a deduplicação evita inserir novamente o que já foi coletado.

A etapa 6 acrescenta checkpoints persistentes e retomada por página/produto, descritos em [worker-catalogo.md](worker-catalogo.md). O resumo agora inclui `cursor`, `concluido` e `janela_limitada`. A janela até offset 1000 é uma varredura limitada, não todo o marketplace.

## Pesquisa direcionada por categoria e marca

`catalogo-planejar` gera um plano com até cinco fabricantes por categoria, priorizando os que têm mais peças publicáveis no banco e usando nome como desempate. Assim, “principais” significa presença no seu catálogo, não uma preferência fixa por marca. Rótulos sem identidade de fabricante, como Outros, Importado e Sem marca, são ignorados. Não existe uma lista fixa de marcas favorecidas: marcas repetidas por caixa/espaços são agrupadas. Cada combinação tem uma pesquisa própria, por exemplo `processador Intel`, `processador AMD Ryzen` e `SSD Kingston`. A consulta AMD prioriza o termo Ryzen; adicione consultas específicas para outras famílias, como Athlon. O texto da pesquisa não garante a família retornada pela API; o matching ainda confere o modelo completo.

```bash
# Dentro de backend, no ambiente configurado para o banco desejado:
python -m flask --app app catalogo-planejar --limite 100 --marcas-por-categoria 5 > data/catalogo/plano-direcionado.json
python -m flask --app app catalogo-worker --plano data/catalogo/plano-direcionado.json --uma-vez
# Após revisar a simulação e preparar o esquema:
python -m flask --app app catalogo-worker --plano data/catalogo/plano-direcionado.json --aplicar
```

O limite é de até **100 produtos de catálogo por pesquisa**, e não 100 vendedores do mesmo modelo. `max_produtos` limita o percurso inteiro, inclusive após retomadas, e `max_ofertas_por_produto: 1` coleta a primeira oferta retornada pela API para cada produto. Não garante menor preço nem que a oferta passará pela associação. Produtos sem ofertas também contam no percurso. O resumo distingue `produtos_percorridos`, anúncios encontrados e pendências novas.

Cada ciclo mantém o orçamento de requisições e checkpoint anteriores. São permitidos até 1.000 grupos em um plano de até 512 KB; isso não aumenta a concorrência nem o orçamento por ciclo. O worker pode alternar grupos para respeitar a agenda. Consultas sobrepostas compartilham a restrição loja/ID externo, sem duplicar anúncios. Categorias ainda sem perfil técnico suficiente continuam sujeitas à revisão existente.

Um HTTP 404 na leitura de ofertas é registrado como catálogo indisponível nessa consulta, sem assumir que não exista oferta no site. HTTP 401/403/429 e falhas de formato interrompem a execução com o diagnóstico. Uma pesquisa que retorna menos de 100 produtos não é artificialmente completada. Para repetir um teste real, use uma cópia do banco; `--aplicar` no worker grava e pode importar ofertas aprovadas. Não copie refresh tokens para renovar em dois bancos independentes: a renovação deve usar o armazenamento oficial da integração.

Nas pesquisas direcionadas, o adaptador aplica automaticamente o domínio oficial da categoria quando ele já está mapeado e nenhum domínio explícito foi informado. Não inventa IDs para as categorias ainda não mapeadas: nelas o termo é textual, e a associação posterior deve conferir a categoria retornada.

O plano também registra `marca`. Antes de consultar ofertas, a descoberta confere BRAND contra a marca esperada (incluindo a equivalência WD/Western Digital). Na ausência do atributo, exige a marca explícita no título; sem isso registra `marca_nao_confirmada`. Resultados de outra marca ou domínio são contabilizados e ignorados nessa busca. Continuam contando nos 100 resultados percorridos: o algoritmo não amplia a janela para inventar 100 resultados pertinentes quando a API não os retorna.

Para incluir todas as marcas válidas em um lote posterior, gere outro plano com `catalogo-planejar --limite 100 --todas-as-marcas`. O limite de produtos continua independente por grupo. Regenerar um plano que altere um trabalho com checkpoint exige a revisão/reinicialização já prevista pelo worker; não reaproveite cursores de outra consulta.

Mesmo em categorias sem domínio mapeado, um domínio conhecido de outra categoria é descartado antes de registrar a pendência. Isso impede, por exemplo, que uma busca de headset capture RAM e reserve o anúncio sob a categoria errada. SSD e HD compartilham o domínio da API; quando `DRIVE_STORAGE_TYPE` informa explicitamente o tipo contrário, o resultado também é descartado. Categorias que compartilham domínio ou carecem de atributos suficientes continuam sujeitas à validação posterior; o texto da consulta não comprova compatibilidade.
