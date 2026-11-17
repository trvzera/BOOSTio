import { perfisUso } from "./perfis-uso.js";
export { opcoesUso } from "./perfis-uso.js";
export const prioridadesUso = Object.fromEntries(Object.entries(perfisUso).map(([chave, perfil]) => [chave, perfil.prioridade]));

export const orientacoesEtapas = {
  orcamento:"Este valor é o máximo da montagem. Vamos dividir o dinheiro entre as peças necessárias, sem ultrapassar o limite. Reserve também um valor para o frete, que não está incluído.",
  pecas:"Vamos manter suas peças e escolher o que falta. As ventoinhas inclusas no gabinete ou no resfriador também contam. Não sabe o nome da peça? Procure o modelo na caixa, na nota fiscal ou no produto.",
  perifericos:"Periféricos são os itens usados junto do PC, como monitor, teclado, mouse e fone. O percentual é um limite para os novos itens; não precisamos gastar tudo nem usar a sobra no PC.",
  rede:"O cabo liga o computador ao roteador. O adaptador permite usar Wi-Fi sem cabo. Escolha “Sim, incluir” se precisar comprar o acessório, ou “Não incluir” se já tiver o necessário.",
  aparencia:"O gabinete é a caixa do computador. Escolha um visual de que gosta; vamos conferir o espaço das peças. Cor, tamanho e estilo são preferências flexíveis. Se não houver uma opção adequada, podemos adaptar o visual sem ultrapassar o orçamento nem ignorar a compatibilidade.",
};

export const ajudaCategorias = {
  processador:"Executa os programas e os cálculos do computador. Também precisa combinar com a placa-mãe.",
  placa_mae:"Conecta as peças entre si. Ela define quais processadores e memórias você pode usar e quantos encaixes ficam disponíveis.",
  memoria_ram:"Ajuda a manter programas e arquivos em uso ao mesmo tempo. Não é o espaço onde seus arquivos ficam guardados.",
  ssd:"Guarda programas e arquivos. Em geral, abre e carrega dados mais rápido que um HD.",
  hd:"Guarda arquivos e programas. Confira a capacidade em GB ou TB e as conexões disponíveis.",
  armazenamento:"SSD e HD guardam programas e arquivos. A capacidade indica quanto cabe; as conexões precisam combinar com a placa-mãe.",
  placa_video:"Cuida das imagens de jogos e programas de criação. Alguns processadores já fazem essa função sem uma placa separada.",
  fonte:"Fornece energia ao computador. A potência e os conectores precisam atender às outras peças.",
  gabinete:"É a caixa onde as peças ficam. Além do visual, precisa ter espaço e ventilação para a montagem.",
  fan:"Ventoinhas ajudam a circular o ar dentro do gabinete. As que já vêm com o gabinete ou o resfriador também contam.",
  cooler:"Mantém o processador resfriado. Pode usar ar ou líquido; precisa caber no gabinete e encaixar na montagem.",
  air_cooler:"Resfria o processador usando uma ventoinha e uma peça de metal. Confira o encaixe e a altura no gabinete.",
  water_cooler:"Resfria o processador com líquido e um radiador. O gabinete precisa ter espaço e os encaixes corretos.",
  monitor:"Para jogos, mais Hz podem deixar os movimentos mais suaves. Para trabalhar e editar, tamanho e resolução ajudam a ver mais detalhes.",
  teclado:"Compare o tamanho, a disposição das teclas e o tipo de acionamento. Mecânico não significa automaticamente melhor.",
  mouse:"Move o ponteiro e permite selecionar itens na tela. Escolha um formato confortável para a sua mão.",
  fone:"Permite ouvir o computador. Um headset também inclui microfone para conversar em jogos e chamadas.",
  rede:"Escolha cabo de internet ou adaptador Wi-Fi, conforme sua conexão e o que já possui.",
};
