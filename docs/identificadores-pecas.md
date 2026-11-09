# Identificadores de componentes e ofertas

- `peca.part_number`: código do fabricante (MPN), sem IDs da KaBuM ou referências de seed. Desconhecido permanece `NULL`.
- `peca.referencia_interna`: códigos antigos `SEED-*`, `REDE-*`, `KABUM-*` etc., preservados para imagens, medidas revisadas e idempotência dos cadastros.
- `oferta.produto_id_loja`: ID real do anúncio naquela loja, por exemplo `392498` na KaBuM ou `MLB...` no Mercado Livre. A unicidade continua sendo loja + ID externo.

O modelo separa referências internas recebidas em cadastros novos. A migração não extrai MPNs do slug nem inventa códigos. Só aproveita MPN já registrado numa identidade revisada válida. A importação de novas identidades revisadas passa a preencher `part_number`, mantendo a referência interna anterior. Códigos internos não são aceitos como MPN.

## Atualização de um banco existente

Faça backup e pare escritores antes da preparação. Use a nova versão da API e do frontend em conjunto.

```bash
# Na pasta backend, com o ambiente do banco desejado:
python -m flask --app app catalogo-preparar
python -m flask --app app catalogo-preparar --aplicar
python -m flask --app app catalogo-identificadores-separar > identificadores-simulacao.json
python -m flask --app app catalogo-identificadores-separar --aplicar > identificadores-aplicacao.json
```

A preparação adiciona `referencia_interna` nullable e seu índice às tabelas de componentes, seguindo o padrão SQLite/MySQL existente. A separação processa lotes e confirma uma transação por peça. É repetível; simulação não confirma dados. O ID da loja vem do link KaBuM validado ou do código legado explícito `KABUM-<numero>`. Divergências de ID/link e anúncios apontados por múltiplas peças ficam em revisão; não é escolhida uma peça por ordem arbitrária. Não são criadas ofertas para códigos SEED/REDE sem anúncio real.

IDs de peças, usuários, builds, preços e históricos permanecem. Vínculos e identidades válidos recebem a nova assinatura quando a mudança é apenas a separação da referência; vínculos já inválidos não são reativados. Não há consulta externa durante essa migração. As ofertas iniciais recebem preço e estoque desconhecidos: preços da seed não viram cotações. O preço legado da peça não é alterado. Links de afiliado existentes são preservados.

Depois de cadastrar novas peças com referências internas, execute novamente a separação para registrar as identidades de loja; a rotina de população não precisa usar IDs de loja como MPN para evitar duplicatas.

## Teste local em cópia descartável

No catálogo local de 1.535 peças, a simulação e a aplicação na cópia identificaram 1.528 referências internas, preservaram sete códigos não internos e criaram 1.534 referências de ofertas KaBuM. A repetição produziu zero alterações e zero ofertas novas. O banco original não foi alterado durante esse teste. Isso valida a separação dos identificadores, não a disponibilidade atual dos anúncios nem a correção de todos os códigos antigos de fabricante.
