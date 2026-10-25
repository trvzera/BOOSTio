# Periféricos e AliExpress — 24/10/2026

## Seleção já implementada

`CriarBuildService` → `AmostrarCatalogoService` / `PlanejarPerifericosService`
usa critérios de `PreferenciasPerifericosService`. Não muda o banco nem as
ofertas existentes.

- Só monitores novos com painel IPS/VA confirmado entram na amostra e passam
  pela validação final da geração. Fast IPS, Rapid IPS, Nano IPS e Fast VA são
  variantes aceitas. OLED, TN e painel desconhecido não entram nesse fluxo.
  O monitor que o usuário já possui não é substituído e o catálogo manual continua
  exibindo seus produtos; nenhum cadastro foi apagado ou reclassificado.
- Para jogos, a amostra preserva opções de Hz alto. Para edição/trabalho,
  preserva opções de resolução/área útil e polegadas. São critérios de adequação,
  não notas de qualidade. A resolução precisa ser explícita, como 2560x1440;
  números não são deduzidos de rótulos vagos.
- Teclados mecânicos com switch documentado têm alternativas preservadas para
  gamer. O planejamento inclui conjuntos viáveis com essa preferência, mantendo
  opções econômicas se o mecânico não couber. Switch, marca, RGB ou preço isolados
  não garantem qualidade. O prompt não inventa durabilidade/polling rate/avaliações.
- O teto de periféricos continua independente do PC. Não consumir a reserva
  exatamente, não transferir sobras e não retirar itens obrigatórios para financiar
  uma preferência. Não há mínimo universal obrigatório de 144 Hz ou 27 polegadas.
- Tipo de painel não certifica cor, HDR, calibração ou ausência de ghosting. Faltam
  dados de cobertura de cor, Delta E, brilho e ergonomia em boa parte do catálogo;
  somente especificações realmente cadastradas podem orientar essas afirmações.

Verificação somente leitura do catálogo local: 34 monitores IPS, 5 Fast IPS,
10 VA, 1 OLED e 50 sem painel informado. Isso não certifica a ficha ou o estoque
atual. Com reserva de R$ 600, o menor conjunto elegível custava R$ 577,86 e os
exemplos não comportaram mecânico documentado; com R$ 1.200 e R$ 2.500 havia
alternativas mecânicas e de Hz mais alto. São fotografias dos preços locais,
não promessa de cotação em tempo real ou resultado ideal da LLM.

## AliExpress: acesso pendente

O usuário confirmou que **ainda não tem aplicativo/acesso aprovado**. Não foi
implementado um cliente com endpoints presumidos nem acionado cadastro, autenticação,
coleta, afiliação ou alteração de ofertas. O prompt não inventa produtos da loja.

O [acordo oficial da API](https://terms.alicdn.com/legal-agreement/terms/suit_bu1_aliexpress/suit_bu1_aliexpress202201220006_10755.html)
prevê credenciais de aplicativo e obrigações de acesso/uso. A documentação pública
histórica de [acesso](https://developer.alibaba.com/docs/doc.htm?articleId=118193&docType=1&treeId=674)
e [AppKey](https://developer.alibaba.com/docs/doc.htm?articleId=118195&docType=1&treeId=674)
descreve a aprovação; está marcada como legada/depreciada. Antes de implementar,
confirmar no console aprovado a documentação e os escopos vigentes, cotas, custos,
assinatura/autorização e permissão de retenção das informações. Não assumir acesso
anônimo, gratuito ou ilimitado.

### Próximas etapas

1. Obter acesso e confirmar quais endpoints de catálogo/afiliados foram liberados.
2. Configurar segredos somente no servidor, nunca no navegador, Git ou chat.
3. Criar adaptador de busca/detalhes seguindo controller → service, com HTTPS,
   destinos fixos, timeout, cache e tratamento de cota/erros; sem afetar geração se
   o provedor estiver indisponível.
4. Separar identidade técnica e oferta: produto, vendedor e variante exatos.
   Layout, switch e kit precisam corresponder; não juntar preços de variantes diferentes.
5. Identificar moeda/destino, impostos/frete e descontos condicionais. Só tratar
   como preço confirmado o que vier documentado para aquela oferta; não calcular
   tributos por uma porcentagem presumida nem aplicar cupom de usuário novo universalmente.
6. Revisar confiabilidade das fichas e autorização para imagens/dados. Só promover
   candidatos ao catálogo usado pela IA depois dessa validação e da cotação.
7. Homologar com chamadas autorizadas. Informar links de terceiros e eventual
   afiliação conforme as regras aplicáveis; não automatizar compras.
