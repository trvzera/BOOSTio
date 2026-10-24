# Geração de builds — revisão de 24/10/2026

## Porte, aparência e periféricos — atualização

- A etapa de aparência usa fotos estáticas como exemplos, sem preço, SKU de compra
  ou seleção de produto. Há porte (Mini/Mid/Full Tower), visual (discreto, vidro
  lateral, panorâmico) e cores em radios com amostra e texto. As opções são
  independentes e podem ficar sem preferência; são acessíveis por teclado.
- `aparencia.porte` é validado por enum no Python e persistido no JSON, sem migração;
  registros antigos recebem “sem preferência”. O legado `gabinete_id` continua
  aceito para preservar versões anteriores, mas a nova interface não o define.
- Exemplos: [Q300L / Mini Tower](https://www.coolermaster.com/en-us/products/masterbox-q300l.html),
  [TD500 / Mid Tower](https://www.coolermaster.com/en-global/products/masterbox-td500-argb.html),
  [7000D / Full Tower](https://www.corsair.com/us/en/p/pc-cases/cc-9011218-ww/7000d-airflow-full-tower-atx-pc-case-black-cc-9011218-ww),
  [H5 Flow / vidro lateral](https://support.nzxt.com/hc/en-us/articles/40225168535451-H5-Flow-2024-Specs)
  e [O11 Dynamic / vidro frontal e lateral](https://lian-li.com/product/pc-o11-dynamic/).
  O visual “aquário” não implica Full Tower nem capacidade de peças/fans. Office X1
  usa a fotografia já existente do catálogo como referência discreta.
- Fotos anteriores foram reutilizadas; adicionada uma miniatura oficial 320×320
  WebP do 7000D para Full Tower. Apenas material de referência: não cadastra o
  produto nem afirma disponibilidade, preço ou licença aberta da imagem.
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
