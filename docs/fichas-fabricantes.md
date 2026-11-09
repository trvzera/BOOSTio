# Complemento técnico pelos fabricantes

A importação de anúncios desconhecidos consulta primeiro o Icecat. Quando a ficha
continua incompleta e o recurso está habilitado, procura páginas nos sitemaps
oficiais de AMD, Corsair, Crucial e Logitech. A função compartilha o mesmo contrato
técnico, validação e transação usados pela importação de ofertas de qualquer loja.

## Habilitação

No ambiente do backend ou worker:

```dotenv
FABRICANTES_HABILITADOS=true
FABRICANTES_CACHE=/caminho/privado/cache-fabricantes
```

O recurso fica desabilitado por padrão. No Docker, monte esse caminho em um volume
privado para preservar o cache. A importação continua exigindo `--permitir-novos`.
Os comandos e a rotina periódica já existentes usam esse complemento quando
habilitado. Não foi instalado agendamento adicional.

Para consultar sem cadastrar uma peça:

```bash
cd backend
../venv/bin/python -m flask --app app fabricantes-consultar \
  --categoria memoria_ram --marca Corsair --modelo CMW16GX4M2C3200C16 \
  --titulo 'Corsair Vengeance RGB Pro CMW16GX4M2C3200C16' \
  --mpn CMW16GX4M2C3200C16
```

## Funcionamento e limites

O resolver lê robots.txt e os sitemaps anunciados, priorizando páginas inglesas.
Códigos no título ajudam a descobrir candidatos. Identidade, variantes e campos
são conferidos novamente depois de baixar a página. A Corsair exige o SKU exato
em um segmento da URL, preservando diferenças como edição TUF e cor.

O leitor usa JSON-LD Product para identificar SKU, MPN e GTIN e pares de tabela ou
definição para especificações. O caso AMD permite o código Tray ou Boxed somente
quando a embalagem é explícita no anúncio e o código consta na ficha. Uma marca
provável extraída do título permite pesquisa, mas a divergência com o atributo
original continua exigindo revisão.

Os mapeamentos iniciais atendem os pares AMD/processador, Corsair/RAM,
Crucial/SSD e Logitech/mouse. Categorias e rótulos adicionais exigem novos
mapeamentos baseados em páginas conferidas. Ausências permanecem pendentes.

Há cache de páginas por sete dias, gravação atômica, limite global de 48 chamadas
por instância e até oito sitemaps por busca. Cada chamada aguarda pelo menos dois
segundos, respeitando também Crawl-delay e Request-rate quando declarados.
Limites maiores que 60 segundos exigem reagendamento. A coleta aceita somente
HTTPS no domínio oficial, recusa redirecionamentos para consulta posterior e
limita o documento a 16 MB. Páginas bloqueadas, CAPTCHA e regras que proíbem
coleta geram pendência. Nenhum JavaScript da página é executado.

Campos já conhecidos não são substituídos silenciosamente. Cada campo coletado
recebe URL, provedor e SHA-256. As especificações originais também ficam nas
evidências. MT/s não é convertido automaticamente para o campo de MHz existente.
Uma ficha com velocidade apenas em MT/s pode continuar incompleta para cadastro.

## Validação realizada

A consulta real encontrou automaticamente o SKU CMW16GX4M2C3200C16 no sitemap e
na página inglesa da Corsair, validando kit, DDR, formato e latência. A frequência
em MHz continuou pendente porque a ficha informa Tested Speed em MT/s.

Na amostra real, AMD ficou sem página adequada nas buscas limitadas,
a coleta da página Logitech foi recusada pelas regras do fabricante,
e Crucial bloqueou a consulta. As páginas diretas da AMD também terminaram por
timeout. Esses resultados não comprovam ausência dos produtos nos fabricantes.
Os parsers AMD/Crucial/Logitech ainda precisam ser homologados com páginas reais
que satisfaçam suas condições de identidade e estrutura.

Testes locais cobrem SKU/variante, domínio permitido, robots, unidade de RAM,
embalagem de CPU e a criação atômica de peça, oferta e histórico após fallback,
com simulação e reexecução idempotente. As respostas de rede desses testes de
persistência são simuladas. Nesta entrega nenhuma peça foi criada na base original.
