# Consulta de preço por anúncio

```python
from app import app
from services.mercadolivre_scapring_service.buscar_preco_service import BuscarPrecoMercadoLivreService

with app.app_context():
    preco = BuscarPrecoMercadoLivreService().executar("MLB4771805087")
```

O retorno é `Decimal` em reais, obtido de `amount` em
`GET /items/{anuncio_id}/sale_price?context=channel_marketplace`.
Representa o preço de venda no marketplace, sem frete. Não se presume um preço
específico de Pix, parcelamento ou cupom pessoal.

Use o ID do **anúncio**, não do catálogo. No link fornecido, `/p/MLB64959148`
identifica o catálogo e `pdp_filters=item_id:MLB4771805087` identifica o anúncio.

`ConsultarApiMercadoLivreService.executar` centraliza a comunicação utilizada
pela busca e pelo serviço de preço: token salvo no banco, renovação por expiração,
uma renovação quando recebe 401, timeout de 15 segundos e até três tentativas para
429 com espera. Com banco sem tokens, usa o refresh token inicial do `.env`.

O serviço de preço não altera peças. Para a futura atualização, obtenha o preço
antes de chamar `peca.atualizar_preco(float(preco))`, pois o modelo atual usa Float.
Em caso de erro HTTP, timeout ou preço indisponível, preserve o preço anterior.
Os modelos atuais ainda não têm um campo específico para guardar o ID do anúncio;
esse vínculo será necessário para iterar o banco. A consulta de preço não cria
esse vínculo automaticamente.

## Verificação

Na pasta `backend`:

```powershell
python -m pytest tests/services/mercadolivre_scapring_service -q -p no:cacheprovider
python test.py MLB4771805087
```

O primeiro comando usa banco temporário em memória e respostas HTTP simuladas.
O segundo usa o app, banco e credenciais reais, podendo renovar os tokens, e
retorna código de saída 1 se a consulta falhar. Não atualiza preços no banco.

Teste real em 05/10/2026: `/users/me` retornou 200; `/items/MLB4771805087`,
`/items/MLB4771805087/sale_price` e `/items/MLB4771805087/prices` retornaram 403.
O ID de catálogo retornou dados em `/products/MLB64959148`, sem `buy_box_winner`.
Assim, a obtenção real de preço continua bloqueada por acesso à API; não houve
um teste de sucesso com preço real. A causa específica do 403 não foi informada
pela API. É necessário verificar a permissão desse recurso junto ao Mercado Livre.

Documentação: https://developers.mercadolivre.com.br/devcenter/api-de-precos
