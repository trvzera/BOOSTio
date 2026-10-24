# Geração de builds — revisão de 24/10/2026

## Porte, aparência e periféricos — atualização

### Cor em toda a montagem

- A cor de `aparencia` é preferência para todas as compras novas: componentes,
  gabinete, refrigeração, periféricos e rede. Compatibilidade, limites separados
  de orçamento e recursos adequados ao uso permanecem prioritários. Itens próprios
  não são trocados por estética; não exigir gasto integral da reserva.
- `PreferenciasCoresService` usa `cor` cadastrada primeiro. Se ausente, termos
  inequívocos de cor no nome servem apenas como referência comercial, com
  `cor_referencia`/`fonte_cor_referencia=nome_cadastrado` no catálogo da IA.
  Não altera a cor da ficha, interpreta imagens/slug da loja ou preenche medidas.
  Ignora exemplos conhecidos de linhas, certificação, cores de switch e iluminação;
  casos ambíguos continuam sem confirmação. CPU sem cor cadastrada não recebe
  cor pelo nome de linha. A cobertura comercial não equivale a revisão de todas as variantes.
- A amostra mantém entrada econômica, padrões técnicos e faixas de investimento,
  reservando opções da cor em cada categoria. Conjuntos de periféricos incluem
  exemplos da cor desejada e alternativas por uso, sempre dentro da reserva;
  “preto e branco” pode combinar itens dessas duas cores, sem exigir cada um bicolor.
- Fans automáticas passam pela mesma validação de tamanho, quantidade e posições;
  só depois a cor desempata opções que cabem no saldo do PC. Uma fan já escolhida
  ou própria não é substituída para combinar a cor. Falta da cor não torna o pedido inviável.
- Sem migração, alteração do banco ou chamadas reais à LLM. Validação: 586 JS,
  781 Python +20 subtestes e 216 verificações Chrome em cinco formatos. A geração
  real colorida ainda precisa de homologação com cota autorizada.

### Limites da compatibilidade de ventoinhas

- Regras mecânicas não dependem do rótulo Mini/Mid/Full Tower ou de vidro/aquário:
  usam diâmetro, capacidade, arranjos por posição, fans de fábrica e do radiador.
  Posições alternativas não são somadas; teto de vidro não cria encaixes extras.
- Só há confirmação quando os dados necessários existem. Medidas externas,
  estilo e soma genérica de fans não comprovam todas as posições ou interferências.
  Conectores, corrente elétrica, parafusos e detalhes da instalação continuam a conferir.

- A etapa de aparência usa fotos estáticas como exemplos, sem preço, SKU de compra
  ou seleção de produto. Há tamanho (Mini/Mid/Full Tower), estilo (sem vidro, vidro
  lateral, aquário com frente/lateral de vidro, panorâmico com frente/lateral/teto)
  e cores em radios com amostra e texto. As opções são
  independentes e podem ficar sem preferência; são acessíveis por teclado.
- `aparencia.porte` é validado por enum no Python e persistido no JSON, sem migração;
  registros antigos recebem “sem preferência”. O legado `gabinete_id` continua
  aceito para preservar versões anteriores, mas a nova interface não o define.
- Exemplos: [Q300L / Mini Tower](https://www.coolermaster.com/en-us/products/masterbox-q300l.html),
  [TD500 / Mid Tower](https://www.coolermaster.com/en-global/products/masterbox-td500-argb.html),
  [7000D / Full Tower](https://www.corsair.com/us/en/p/pc-cases/cc-9011218-ww/7000d-airflow-full-tower-atx-pc-case-black-cc-9011218-ww),
  [H5 Flow / vidro lateral](https://support.nzxt.com/hc/en-us/articles/40225168535451-H5-Flow-2024-Specs)
  [O11 Dynamic / vidro frontal e lateral](https://lian-li.com/product/pc-o11-dynamic/)
  e [O11 Vision / três faces de vidro](https://lian-li.com/product/o11-vision/).
  O visual “aquário” não implica Full Tower nem capacidade de peças/fans. Office X1
  usa a fotografia já existente do catálogo como referência discreta.
- Fotos anteriores foram reutilizadas; adicionada uma miniatura oficial 320×320
  WebP do 7000D para Full Tower e uma foto oficial WebP do O11 Vision
  (`O11_Vision_07.webp`, 688×688, cerca de 104 KiB), sem alteração da imagem.
  Apenas material de referência: não cadastra o
  produto nem afirma disponibilidade, preço ou licença aberta da imagem.
- Ao selecionar o tamanho, aparece um guia do exemplo: Q300L, 387×230×381 mm,
  Micro-ATX/Mini-ITX, radiador frontal até 240 mm; TD500 ARGB,
  493×217×469 mm com saliências, radiador até 360 mm; 7000D,
  550×248×600 mm, ATX/E-ATX limitada à largura declarada, radiadores conforme
  posição. Ordem: profundidade × largura × altura. As fontes são as fichas oficiais
  acima, revisadas em 24/10/2026. São exemplos, nunca limites universais do porte.
- O formulário diferencia ventoinhas comuns de 120/140 mm de radiadores nominais
  de 240/360 mm (normalmente 2/3 ventoinhas de 120 mm). Comprimento total,
  espessura, conexões e tubos precisam de espaço real. Não inferir encaixe pela soma.
- Valores antigos `discreto` e `panoramico` permanecem válidos; o novo estilo
  `panoramico-3-faces` também é aceito no Python e no JSON salvo. O prompt recebe
  a distinção entre painéis e não considera um teto de vidro como espaço livre
  para ventoinhas/radiador. Um único `painel_vidro=True` não comprova as três faces.
- Chrome: 216 verificações em cinco formatos, incluindo sete fotos locais,
  teclado, guias por tamanho, fontes/axe, independência entre tamanho/estilo/cor
  e payload simulado. Sem escrita real, migração ou chamadas LLM. Regressão:
  586 testes JavaScript e 738 Python, além de 20 subtestes.
- A seleção técnica de monitores/teclados agora influencia a amostra e os conjuntos
  viáveis, além do prompt. Regras, testes do catálogo local e dependência AliExpress
  estão em [integrações de periféricos](integracoes-perifericos.md).
- Nenhuma chamada real à LLM foi consumida nesta atualização. O prompt está coberto
  por testes controlados; a qualidade da escolha real ainda precisa de homologação.

## Orçamento e catálogo

O formulário continua usando `POST /build/`, `GerarBuildService` e
`CriarBuildService`, sem migrações ou mudanças nas rotas/permissões.

- PC/rede e periféricos mantêm tetos independentes. R$ 3.000 com 20% reserva
  R$ 600 para o conjunto de periféricos e R$ 2.400 para o PC e a rede.
  Peças próprias não são compradas novamente nem descontadas do orçamento.
- `PlanejarPerifericosService` calcula conjuntos completos que cabem na reserva.
  Um conjunto comprovadamente inviável é informado antes de consumir a LLM.
  Sobras não são transferidas entre os dois tetos.
- `AmostrarCatalogoService` preserva entradas por socket/DDR/capacidade/kit e
  faixas de preço, com até 12 opções por categoria. A consulta intermediária
  considera até 200 registros por categoria; antes, oito posições por densidade
  de cadastros omitiam opções econômicas de DDR4 e alternativas intermediárias.
  Preço não é tratado como pontuação de desempenho.
- Núcleos, threads, clocks e velocidades de armazenamento também chegam ao
  prompt quando cadastrados. IDs novos são inteiros; preços vêm do catálogo.

### Preferências e qualidade — complemento de 24/10/2026

- O formulário inclui etapa opcional de aparência com estilo, cor e referência
  visual de gabinete. `aparencia` é validada e persistida no JSON da build, sem
  adicionar tabelas ou colunas. Gabinete próprio não é substituído. Referência
  nova só entra na amostra se disponível e dentro do filtro financeiro; não se
  torna peça obrigatória. A amostra continua limitada a 12 itens por categoria.
- A amostragem agora distingue recursos de monitor, teclado, mouse, fone e gabinete.
  O prompt orienta avaliar adequação/qualidade técnica dos periféricos, sem escolher
  por padrão o primeiro conjunto econômico, nem equiparar preço/DPI/RGB a qualidade.
  As sobras continuam com o usuário. Dados ausentes não são completados pela IA.
- Logs INFO registram duração de catálogo, prompt, LLM e validação e tamanho do
  prompt. Erros da revisão são classificados sem registrar seu conteúdo. Não há
  nomes/e-mails, resposta da IA, tokens ou peças próprias nesses logs. Para analisá-los,
  o logger da aplicação precisa estar configurado para INFO.
- O carregamento mostra tempo decorrido e informa que pode haver revisão, sem
  prometer progresso exato. Não acrescenta chamadas, abortos de criação em andamento,
  fallback pago ou tentativas ilimitadas.
- Validação desta rodada: testes isolados com saídas controladas e navegação real
  no Chrome. Não houve novas chamadas Gemini: os problemas dos cenários reais
  abaixo ainda precisam de homologação online, não são considerados definitivamente
  resolvidos somente por melhorar o prompt.

## Revisão e ventilação

- Erros de orçamento recebem subtotais calculados no Python e valores a reduzir,
  por categoria, para orientar a revisão. Mensagens finais de orçamento/fans
  podem explicar a causa controlada, sem devolver resposta bruta da IA.
- Para jogos/renderização, o prompt prioriza o objetivo e a distribuição de
  investimento. A faixa de 80–100% do teto do PC é uma referência, não um mínimo.
  Jogos com GPU nova também recebem referências de distribuição e o aviso para
  não sacrificar GPU por RAM premium. Não há promessa de FPS ou melhor escolha
  apenas porque uma peça custa mais.
- Pedidos exigentes com teto do PC de pelo menos R$ 10 mil e sugestão abaixo de
  75% podem usar a revisão já disponível para reavaliar o investimento. Não há
  terceira tentativa. Se essa revisão falhar, a primeira sugestão já validada é
  preservada; não se salva uma sugestão inválida para atingir um valor de gasto.
- `CompletarVentilacaoService` pode corrigir a omissão/quantidade de fans antes
  da validação final: desconta as inclusas e as do AIO, respeita kits inteiros,
  tamanho, distribuição conhecida, disponibilidade e teto do PC. Não substitui
  fans próprias, não inventa posições e não configura troca das fans do AIO.
  Ausência de dados/combinação possível continua indo para validação e revisão.
- A validação completa de compatibilidade, obrigatórias e orçamento permanece
  antes da persistência. Limite de três builds, verificação de e-mail e cotas
  continuam vigentes. Não houve alteração nos modelos Gemini ou fallback.

## Verificação realizada

- 658 testes Python e 13 subtestes aprovados, incluindo persistência em SQLite
  temporário, saída inválida sem gravação, periféricos, amostragem, fans e revisão.
- Seis chamadas reais ao Gemini, em dois lotes de até três expressamente
  autorizados. Somente catálogo de produtos lido do banco; nenhuma build salva,
  nenhum fallback pago, SMTP, migração ou coleta de preço acionados.
- Primeiro lote reproduziu excesso no teto do PC no pedido de R$ 3.000 e
  subutilização do investimento no de R$ 20 mil. Serviu para corrigir amostragem
  e detalhamento da revisão; não representa homologação da versão final.
- Segundo lote: o cenário R$ 3.000 + 20% + RTX 4060 própria + Wi-Fi recebeu
  **HTTP 503 do provedor**, antes de haver uma sugestão para validar. Esse cenário
  ainda precisa de nova homologação online; os testes locais não certificam a
  disponibilidade do Gemini.
- O cenário de jogos exigentes de R$ 20 mil passou após uma revisão, com total
  de **R$ 18.907,84**, fans presentes e sem persistência. Isso comprova os tetos
  e as verificações disponíveis, não uma configuração de desempenho ideal. A
  sugestão escolheu uma RAM cotada em R$ 8.833,82, concentrando o custo; os preços
  não foram corrigidos por suposição. A distribuição no prompt foi reforçada
  depois desse resultado e permanece coberta por testes locais.

## Próximas verificações

- Homologar novamente os dois pedidos quando o provedor estiver disponível,
  sempre com autorização de cota e sem declarar todos os cenários aprovados.
- Revisar cotações/variantes que concentram investimento antes de concluir que
  o problema é apenas o prompt. Não alterar preços automaticamente por palpite.
- Continuar ampliando especificações confirmadas de gabinetes e componentes;
  quantidade de peças não certifica BIOS, QVL ou todas as interferências físicas.
