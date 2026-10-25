# Catálogo e especificações revisadas

Revisão de 24/10/2026. A base de cadastro passa de 1.535 para 1.542 produtos.
O manifesto compartilhado possui agora 76 fichas técnicas (48 antes desta rodada). Isso não representa
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

## Revisão de sockets, slots e build com 19 verificações pendentes

Foram adicionadas 28 fichas, com cobertura de 29 cadastros de placas-mãe e dos
modelos Rise Mode X1 White, Zotac RTX 3050 Twin Edge OC 6 GB e Gamemax Gamma 200.
A ficha existente da Corsair CX650 CP-9020278-BR recebeu os conectores publicados.
Nenhum preço, estoque, conta ou build foi alterado no banco.

Na consulta somente leitura das 100 placas-mãe locais:

- Quantidade de slots de RAM ausente: de 29 para 13 (87 placas com valor conhecido).
- Capacidade máxima de RAM ausente: de 41 para 27.
- Quantidade de M.2 ausente: de 34 para 19.
- Quantidade de portas SATA ausente: de 91 para 63.
- Todas as 100 placas e os processadores têm socket reconhecido pelo normalizador.
  Presença do socket não certifica suporte à CPU ou à BIOS instalada.

### Correções e fontes principais

- [Husky HPM610](https://www.kabum.com.br/produto/692458/placa-mae-husky-nexus-h610-lga-1700-12-13-gen-m-2-nvme-sata-ddr4-3200mhz-micro-atx-hdmi-vga-hpm610):
  dois DIMMs, 64 GB, um M.2 NVMe/SATA, três SATA. O anúncio diverge entre
  chipsets H610/Q670; esse campo permanece desconhecido.
- [ASUS PRIME H610M-A D4](https://www.asus.com/motherboards-components/motherboards/prime/prime-h610m-a-d4/techspec/):
  dois DIMMs/64 GB, não quatro/128 GB. São dois M.2 para SSD PCIe; o slot
  Key E de Wi-Fi não é contado como armazenamento.
- [MSI B550M-A PRO](https://www.msi.com/Motherboard/B550M-A-PRO/Specification):
  dois DIMMs/64 GB, um M.2 e quatro SATA. Não confundir com B550-A PRO ATX.
- [ASUS PRIME B550M-K ARGB](https://www.asus.com/uk/motherboards-components/motherboards/prime/prime-b550m-k-argb/techspec/):
  anúncio 992806/90MB1GC0-M0EAY0; dois DIMMs/64 GB, distinto da B550M-K original.
- [PCWARE IPMH610G](https://pcwarebr.com.br/drivers/IPMH610G/manual/MANUAL_IPMH610G.pdf):
  dois DIMMs/64 GB, um M.2 PCIe e quatro SATA.
- [Duex DX H310ZG M.2](https://www.duex.com.br/produtos/placa-mae/placa-mae-dx-h310zg-m2-intel-lga-1151-ddr4):
  dois DIMMs/32 GB, um M.2 NVMe e três SATA. LGA1151 não autoriza toda geração de CPU.
- [Rise Mode X1 White](https://www.kabum.com.br/produto/516120/gabinete-office-rise-mode-x1-white-mini-tower-m-atx-sem-fans-branco-rm-ga-ofx1-fw):
  até três fans, nenhuma inclusa, quatro slots de expansão e fonte ATX.
  Diâmetros/posições e folgas internas de GPU/cooler/fonte não foram publicados
  na ficha encontrada. Dimensões externas não substituem essas folgas.
- [Zotac Twin Edge OC 6 GB](https://www.zotac.com/download/mediadrivers/External/GraphicsCard/3050/Brochure/ZT-A30510H-10L-brochure.pdf):
  161,9 × 111,2 × 40,2 mm, dois slots, 70 W, alimentação pelo PCIe.
  Não aplicar as medidas da versão de 8 GB, Solo ou LP.
- [Gamma 200 atual](https://gamemax-br.com/produto/gamma200) e
  [anúncio antigo](https://www.kabum.com.br/produto/156726/cooler-para-processador-gamemax-gamma-200-rgb):
  altura de 82 mm confirmada. LGA1700/1851/AM5 constam na ficha atual e não na
  antiga. `sockets_suporte_condicional` mantém versões/kits diferentes como
  não verificados no Python, JavaScript e no prompt da LLM.

As demais fontes por modelo estão no manifesto. Contagens físicas de M.2 não
garantem todos os slots ativos com toda CPU: as notas preservam exceções de
Ryzen 8000, compartilhamento com PCIe/USB4 e desativação de SATA por M.2 SATA.

### Pendências reais preservadas

Na reprodução da build informada, as verificações sem dados suficientes caíram
de 19 para 14, sem conflito confirmado. RAM, M.2, quantidade de fans, slots da GPU
e formato da fonte passaram a ter dados. Uma nova conferência registra as condições
da ficha do gabinete. Isso não é aprovação completa da montagem.

Continuam necessários limites internos do X1 White, diâmetros e posições das fans,
revisão/kit do Gamma 200, BIOS instalada, QVL, conectores do conjunto e detalhes
de compartilhamento/instalação dos discos. Não estimar essas informações pela foto,
nome comercial, dimensões externas ou por outra revisão.

Ainda faltam slots confirmados nos anúncios 902809, 505312, 505326, 503496,
949050, 914127, 498132, 692459, 739347, 950877, 1067079, 906068 e 949265.
Há fabricantes/modelos genéricos, páginas indisponíveis e revisões sem identificação.
HPM450 tem fontes divergentes de dois/quatro DIMMs; não aplicar o valor da HPM610.
PRO H610M-B DDR5 tem resumo e seção detalhada contraditórios na página oficial:
dois slots são consistentes, mas o máximo de RAM permanece desconhecido.

O normalizador reconhece grafias como `LGA 1700`/`FCLGA1700`, expande a indicação
explícita `LGA115X` e preserva AM3/AM3+, TR4/TRX4 e LGA2011/LGA2011-3. Marca
genérica e campo ausente continuam não verificados. Nenhuma chamada à LLM ou
alteração no banco é necessária para aplicar essas fichas.

Reinicie o backend após atualizar o manifesto: a leitura das fichas fica em cache
no processo. A build é reavaliada ao consultar sua API; o JSON exportado antigo
não é atualizado sozinho. Validação desta rodada: 624 testes JavaScript,
823 Python (+20 subtestes) e 41 verificações no Chrome em 320/768/1440 px.
As APIs de conta/build foram simuladas no navegador e o catálogo real foi aberto
somente para leitura; não houve escrita no banco nem consumo de LLM.
