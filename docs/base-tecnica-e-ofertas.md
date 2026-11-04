# Base técnica independente das ofertas

## Fonte candidata: Open Icecat

A documentação oficial oferece fichas JSON/XML, identificação por fabricante e código de produto ou GTIN, índices de produtos e datas de atualização. Open Icecat cobre o conteúdo das marcas participantes; a existência de um modelo no catálogo geral não garante acesso gratuito à sua ficha.

Fontes consultadas:
- https://icecat.com/content-subscription/
- https://iceclog.com/manual-for-icecat-json-product-requests/
- https://iceclog.com/open-catalog-interface-oci-open-icecat-xml-and-full-icecat-xml-repositories/

A consulta autenticada, o índice local e o enriquecimento de anúncios desconhecidos foram implementados. Uma ficha real de RAM foi consultada e validada. A cobertura suficiente do catálogo completo ainda precisa ser medida por categoria. Comandos e limites estão em [Icecat e Mercado Livre](icecat-mercadolivre.md).

## Avaliação antes da importação

Comparar o catálogo local por fabricante, código comercial/MPN e GTIN disponíveis. Distinguir identidade exata, ficha acessível na assinatura, campos técnicos presentes, campos desconhecidos e conflitos. Não declarar correspondência por nome parecido nem confundir ID Icecat com código do fabricante. Preservar o denominador original da medição; componentes novos são contabilizados separadamente.

Validar um lote revisado de categorias diferentes antes de ampliar a importação. Preservar dados originais, identificadores da fonte, unidades, datas e evidências. Os mapeamentos de categorias e atributos precisam ser confirmados nos arquivos reais e nas referências oficiais; não presumir os IDs remotos.

## Rotina técnica semanal

A rotina semanal deve comparar o índice completo com os registros anteriores e baixar somente fichas novas ou alteradas. Consumir apenas um índice de alterações das últimas 24 horas uma vez por semana perderia alterações dos demais dias.

A rotina não cria ofertas, preços ou disponibilidade. Fichas incompletas ficam pendentes. Mudanças conflitantes de identidade ou especificações exigem revisão. Produtos retirados da fonte não devem causar exclusão automática de peças, vínculos ou históricos locais; conteúdo sujeito a retirada de acesso precisa seguir as condições da fonte, inclusive interrupção de seu uso quando exigida.

## Associação de ofertas entre lojas

O núcleo compartilhado recebe identidade, especificações e evidências em formato interno. A descoberta de anúncios, autenticação, paginação e leitura de preços pertencem aos adaptadores de cada loja. O adaptador do Mercado Livre não deve ser uma dependência do importador técnico.

O projeto já separa `AssociacaoInteligenteService`, `ImportarCatalogoService` e o repositório de persistência dos adaptadores em `mercadolivre_service`. Essa estrutura deve ser reutilizada. Um adaptador futuro de outra loja deve produzir os mesmos dados internos, sem copiar as regras de correspondência.

Depois da confirmação de uma peça técnica, enfileirar a busca de ofertas. Para uma peça já conhecida, associar um anúncio exige identidade suficiente e ausência de conflitos, não a recuperação de toda a ficha técnica em cada consulta. Atualizar ofertas já vinculadas exige revalidar identidade e persistir preço e disponibilidade observados, mantendo históricos e idempotência.

## Dependências do modelo atual

`Peca` ainda exige `preco`, `esgotado` e `consumo_energia`. Uma ficha técnica sem oferta não fornece necessariamente esses valores. Antes de permitir novos componentes técnicos, é necessário adaptar o modelo e seus consumidores para representar ausência de informação, com migração preservando os valores existentes. Não preencher preço com zero nem disponibilidade com um booleano inventado.

A elegibilidade para publicação e geração de builds deve depender dos dados necessários à finalidade. Peças sem oferta podem existir no catálogo técnico; preços ausentes não podem aparecer como gratuitos. A geração deve utilizar uma oferta elegível com preço válido, respeitando peças próprias e os mecanismos existentes de compatibilidade.

## Execução e validação

Começar com arquivos locais e simulação; depois, lote pequeno revisado numa cópia. Conferir novas peças, atualizadas, inalteradas, duplicatas evitadas, pendências e falhas separadamente. Testar reexecução e migração antes de produção. Cadastro em serviços, condições de conteúdo e acesso precisam estar resolvidos antes de ativar sincronização externa.
