# Shopee

## Fonte

API de Afiliados (`https://open-api.affiliate.shopee.com.br/graphql`, consulta `productOfferV2`), assinada
com SHA256 (`SHOPEE_APP_ID`, `SHOPEE_APP_SECRET`). Cada resposta traz título, preço mínimo e máximo,
links, categorias e o período da oferta. **Não traz** marca, MPN, GTIN, condição nem estoque. Por isso a
associação depende do título e as ofertas ficam com `esgotado = NULL` (estoque desconhecido).

## Associação à peça

Segue o fluxo do Mercado Livre e usa o mesmo motor (`AssociacaoInteligenteService`) e o mesmo índice local:

1. **Buscas** (`consultas_da_peca`, compartilhada com o Mercado Livre): MPN, depois marca + nome comercial
   (com capacidade), depois marca + nome original. No máximo 4 requisições por peça, sem repetir
   anúncios; a busca para ao confirmar uma correspondência ou quando não há novidade.
2. **Normalização:** o título do vendedor perde propaganda (emojis, "frete grátis", "original", "lacrado",
   "garantia N meses"…). O título original fica em `contexto.titulo_original`. Anúncio com "usado",
   "seminovo", "recondicionado", "open box" ou "vitrine" vira conflito `produto_usado_ou_recondicionado`.
   Faixa de preço (mínimo diferente do máximo) indica variantes e vai para revisão.
3. **Decisão:** só entra se a correspondência for **única** e acima de 80 para a peça em questão. Categoria
   só é confirmada pelos IDs observados na API (processador, placa-mãe, placa de vídeo, memória RAM); as
   demais categorias não associam automaticamente, em vez de adivinhar IDs.
4. **Seleção:** menor preço primeiro, um anúncio por loja da Shopee, até `limite_ofertas`.
5. **Gravação:** uma transação por peça, com revalidação sob trava (`atualizar_ofertas_validadas`):
   oferta, histórico e a prova de vínculo em `produto_pendente`. Se a busca terminou sem mais páginas, as
   outras ofertas ativas da peça nessa loja são desativadas; com busca incompleta nada é desativado.
   Simulação não grava.

O preço da peça passa a ser o da menor oferta ativa, sem alterar a ficha da peça
(ver [ofertas-unificadas.md](ofertas-unificadas.md)).

## Uso

```sh
python -m flask --app app marketplaces-fila-preparar --aplicar
python -m flask --app app marketplaces-enfileirar-ofertas --loja shopee --categoria processador --execucao teste-cpu
python -m flask --app app marketplaces-enfileirar-ofertas --loja shopee --categoria processador --execucao teste-cpu --aplicar
python -m flask --app app marketplaces-worker --uma-vez
python -m flask --app app shopee-descobrir --categoria processador --termo "Ryzen 5 5500" --execucao d1
```

As tarefas simulam por padrão; `--gravar-ofertas` as faz gravar. Não rode contra o banco de produção sem
backup e sem uma simulação revisada.

## Limites conhecidos

- Estoque desconhecido: a oferta aparece no catálogo, mas a geração de builds só usa o preço de ofertas com
  estoque conhecido como disponível, então ofertas da Shopee não entram nas builds por enquanto.
- Sem MPN/GTIN, a confirmação depende de modelo + especificações extraídas do título; título genérico
  fica em revisão.
- Credenciais e comportamento real da API (limites, permissões da conta) ainda não foram verificados.
