# Pendências de produto

Este documento registra funcionalidades a implementar. Os itens abaixo **não** estão
publicados no site nem representam funcionalidades concluídas.

As etapas que dependem de preço e ofertas reais ficam **aguardando o avanço do backend
de monitoramento de preços das peças**. Retomar estas pendências quando essa integração
estiver disponível; não tratar os valores demonstrativos atuais como cotações.

## Configurações prontas (requisito 10)

- Criar uma vitrine de builds curadas pela BOOSTio, separada das builds do usuário.
- Permitir filtrar por objetivo de uso e faixa de orçamento, abrir detalhes das peças,
  preço estimado e compatibilidade.
- Oferecer **Usar como base**: criar uma cópia editável para o usuário, sem modificar
  o modelo original. Definir o comportamento para visitantes e para quota cheia.
- Recalcular preços a partir das ofertas disponíveis e exibir a data da cotação;
  não prometer que o preço da build pronta seja fixo.
- Começar com exemplos curados e versionados; depois decidir como administrar e
  publicar modelos pelo backend.

## Aviso sobre links de compra

- Preparar um aviso claro, próximo aos links para lojas e em local apropriado nos
  termos, explicando que a BOOSTio não vende, entrega nem processa o pagamento de
  peças e periféricos. A compra ocorre no site de terceiros.
- Informar que preço, estoque, frete, entrega, garantia, devoluções e eventuais
  problemas da compra devem ser conferidos com a loja responsável.
- Revisar a redação final antes de publicar, especialmente qualquer afirmação
  sobre responsabilidade. **Não adicionar o aviso ao site por enquanto.**

## Conexão com a internet no formulário e na build

- Acrescentar uma pergunta no formulário sobre como a pessoa pretende conectar o PC:
  cabo de rede/Ethernet, Wi-Fi ou ainda não sabe. Perguntar se já possui o acessório
  necessário ou se precisa incluí-lo na configuração.
- Mostrar e permitir alterar a mesma escolha no editor da build, inclusive quando
  a montagem for iniciada manualmente, sem passar pelo formulário.
- Se a opção for Wi-Fi, distinguir placa-mãe com Wi-Fi integrado de necessidade de
  adaptador. Não inferir suporte apenas pelo nome comercial quando o dado técnico
  não estiver cadastrado; nesse caso, pedir confirmação.
- Se a pessoa precisar comprar cabo de rede ou adaptador Wi-Fi, permitir incluí-lo
  no custo estimado e no budget. Definir os dados de catálogo e as verificações
  aplicáveis ao adaptador (por exemplo, interface/porta disponível) antes de
  recomendar um modelo.
- Tratar esses acessórios como opcionais para o progresso da build: não devem
  impedir uma configuração de chegar a 100% só porque a resposta é “ainda não sei”.

## Integrações necessárias para fechar os requisitos existentes

- Persistir builds na conta pelo backend, com componentes múltiplos e validação
  das regras no servidor; hoje as builds são locais ao navegador.
- Levar o comparador e a busca de melhorias da página de testes para o fluxo real
  depois de definir dados confiáveis para desempenho e preço.
- Persistir o budget no perfil e aplicar a opção de uso às novas configurações.
- Implementar importação de JSON/CSV com validação de esquema e melhorar o CSV
  exportado para incluir modelos e quantidades, não apenas categorias presentes.
- Integrar catálogo e ofertas reais, mantendo preços e disponibilidade identificados
  por loja e data de atualização.
