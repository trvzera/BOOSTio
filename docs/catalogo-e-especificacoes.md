# Catálogo e especificações revisadas

Revisão de 24/10/2026. A base de cadastro passa de 1.535 para 1.542 produtos.
O manifesto compartilhado passa de 37 para 48 fichas técnicas. Isso não representa
revisão completa de todos os produtos do catálogo.

## Como os dados são aplicados

`frontend/data/medidas-fisicas.json` é lido tanto pelas Models Python quanto pelo
catálogo demonstrativo JavaScript. Categoria, fabricante, modelo e part number
precisam corresponder. Apelidos antigos exigem também o ID do anúncio exato.
Não há migração nem atualização em massa das especificações do banco.

As fichas guardam fonte e data da revisão. Dimensões externas não substituem
limites internos. Campos não confirmados permanecem `null`; capacidades
alternativas ou condicionais não são somadas como se fossem simultâneas.

## Lote complementar

- ARCTIC P12 PWM PST Black, **ACFAN00120A**: uma fan de 120 × 120 × 25 mm.
- ARCTIC P12 PWM PST Black Pack of 5, **ACFAN00137A**: cinco fans; não reutiliza
  preço ou anúncio da embalagem avulsa. Ainda sem anúncio exato na KaBuM.
- be quiet! Pure Wings 3 120mm PWM, **BL105**: variante PWM, não high-speed.
- Logitech M100 Black, **910-003241**: mouse USB de entrada.
- Logitech K270 ABNT2, **920-004427**: teclado com receptor Unifying, não Bluetooth.
- Logitech H390 USB-A Black, **981-000014**: redução de ruído no microfone, não ANC
  nos fones; não confundir com a variante USB-C.
- Cooler Master MasterBox 520 Black, **MB520-KGNN-S01**: variante distinta do
  antigo MCB-B520-KGNN-RGA; inclui três fans frontais e uma traseira.

Os detalhes elétricos e acústicos das fans são por unidade, salvo o consumo do
produto em kit. No P12 PST, a potência é calculada a partir da tensão e corrente
publicadas: 1,2 W por fan e 6 W pelo kit de cinco. Não é uma medição do PC.
Sone e dBA permanecem unidades distintas, sem conversão inventada.

Fontes: [ARCTIC](https://www.arctic.de/media/42/84/78/1693306001/Spec_Sheet_P12_PWM_PST_EN.pdf),
[be quiet!](https://www.bequiet.com/en/casefans/4606),
[K270](https://support.logi.com/hc/en-us/articles/360023462213-K270-Technical-Specifications),
[H390](https://support.logi.com/hc/en-ch/articles/360024878073-Specifications-USB-Headset-H390),
[M100 — anúncio da variante brasileira](https://www.kabum.com.br/produto/302167/mouse-logitech-m100-usb-1000-dpi-preto-910-003241)
e [MasterBox 520](https://www.coolermaster.com/en-global/products/masterbox-520.html).

## Correções nos produtos existentes

- Corsair QL120 **CO-9050097-WW**, anúncio 108137: uma unidade, não três.
- Lian Li SL Wireless Reverse **12RSL1W1W**, anúncio 931169: uma unidade, espessura
  de 28 mm e fluxo reverso; sem controlador no pacote avulso.
- Lian Li **O11DERGBX**, anúncio 582808: ficha do EVO RGB, não do O11 original;
  até dez posições, com alternativas 120/140 mm por região. Radiador de 420 mm
  exige acessório separado e não é aprovado pela ficha padrão.
- Corsair **2000D AIRFLOW CC-9011245-WW**, anúncio 433279: versão sem fans de fábrica.
  Duas posições traseiras dependem de GPU de um slot. Como essa condição ainda não
  é resolvida automaticamente, a capacidade simultânea permanece desconhecida;
  não aprovar oito fans indiscriminadamente.
- NR200: dimensões externas acrescentadas a partir da ficha oficial;
  continuam separados os limites de GPU, cooler, fonte e posições de fans.

Fontes: [Corsair QL120](https://www.corsair.com/eu/en/p/case-fans/co-9050097-ww/icue-ql120-rgb-120mm-pwm-single-fan-co-9050097-ww),
[Lian Li SL Wireless](https://lian-li.com/product/uni-fan-sl-wireless/),
[O11 EVO RGB](https://lian-li.com/product/o11d-evo-rgb/),
[Corsair 2000D](https://www.corsair.com/us/en/p/pc-cases/cc-9011245-ww/2000d-airflow-mini-itx-pc-case-white-cc-9011245-ww),
[NR200](https://www.coolermaster.com/en-global/products/masterbox-nr200.html) e
[Q300L](https://www.coolermaster.com/en-global/products/masterbox-q300l.html).

## Cadastro controlado e consulta de preços

No diretório `backend`, com o ambiente do projeto configurado:

```sh
python -m flask --app app pecas-complementares --simular
python -m flask --app app pecas-complementares
python -m flask --app app catalogo-auditar --amostras 5
```

O primeiro comando só consulta; o segundo insere apenas o lote revisado e não
consulta lojas. Ambos evitam duplicar part numbers e anúncios já cadastrados.
Não modificam contas, builds ou preços existentes. `pecas-popular` também inclui
o lote na preparação de bancos novos; não é executado automaticamente no import.

Produtos novos começam com preço zero, sem data e indisponíveis para sugestões.
Zero é um estado inicial do cadastro, não uma oferta gratuita. Periféricos cujo
consumo não foi confirmado expõem `null`, não consumo zero. A coleta normal de
preços e imagens continua pelos comandos existentes, respeitando os limites.

Na execução local desta revisão, foram inseridos sete registros sem modificar
os 1.535 anteriores. Seis anúncios novos foram consultados pelo coletor existente:
K270 e H390 tiveram preço e estoque confirmados; quatro estavam esgotados.
O kit ARCTIC de cinco não foi consultado por não ter anúncio exato. Isso é um
resultado pontual, não garantia de estoque ou preço futuro. Nenhuma LLM foi chamada.

## Próximas pesquisas

`catalogo-auditar` agora informa campos técnicos ausentes por categoria e amostras
de produtos afetados. A presença de um campo não certifica sua correção. Priorizar:

- Medidas e conectores das GPUs, slots/SATA/QVL das placas-mãe e revisão DDR.
- Limites reais do conjunto radiador + fans e interferências com GPU/RAM/cabos.
- Baias compartilhadas e posições condicionais, sem somar montagens alternativas.
- Dimensões e número de unidades de mais fans de entrada já disponíveis no catálogo.
- Identidade, fotos e novas cotações dos sete produtos complementares.
- Q300L: confirmar o part number do anúncio 903460, cujo título menciona vidro.
  Não transferir dimensões do Q300L original para uma eventual versão V2/V3.
  Não foram acrescentadas medidas externas ao cadastro ambíguo nesta revisão.

As duas suítes usam fixtures compartilhadas, banco temporário, verificação de
idempotência e testes de preservação de preço/estoque. A API Docker recebe os dois
manifestos que suas Models leem; não é necessário copiar todos os assets do site.
