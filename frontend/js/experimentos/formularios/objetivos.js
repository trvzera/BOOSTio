export const perfisUso = {
  jogos: {
    titulo: "Jogos",
    descricao: "Jogar com boa imagem e movimentos suaves.",
    minimo: 3500,
    ram: 16,
    prioridade:
      "Placa de vídeo dedicada e processador têm prioridade. No monitor, buscamos mais fluidez; teclado mecânico com switch identificado e mouse com sensor conhecido, respeitando a reserva.",
    gpu: "dedicada",
    monitor: "fluidez",
    teclado: "mecanico",
  },
  planilhas: {
    titulo: "Planilhas",
    descricao: "Organizar dados, relatórios e trabalhar com várias janelas.",
    minimo: 2500,
    ram: 16,
    prioridade:
      "Priorizamos processador, memória para várias planilhas e SSD. Um monitor com espaço para janelas e um teclado com números à direita podem ajudar. Não exigimos placa de vídeo separada.",
    gpu: "integrada-permitida",
    monitor: "espaco",
    teclado: "numerico",
  },
  reunioes: {
    titulo: "Reuniões",
    descricao: "Chamadas de vídeo, apresentações e trabalho online.",
    minimo: 2500,
    ram: 16,
    prioridade:
      "Damos atenção à câmera, ao microfone ou fone e à estabilidade nas chamadas. Processador, memória e SSD devem manter os programas abertos sem gastar com uma placa de vídeo desnecessária.",
    gpu: "integrada-permitida",
    monitor: "conforto",
    webcam: true,
  },
  "edicao-video": {
    titulo: "Edição de vídeo",
    descricao: "Editar vídeos, imagens e trabalhar com projetos maiores.",
    minimo: 3500,
    ram: 32,
    prioridade:
      "Priorizamos processador, placa de vídeo dedicada, mais memória e SSD para os projetos. No monitor, qualidade de imagem e resolução vêm antes de uma taxa de atualização muito alta.",
    gpu: "dedicada",
    monitor: "imagem",
  },
  programacao: {
    titulo: "Programação",
    descricao:
      "Escrever código, compilar projetos e usar ferramentas de desenvolvimento.",
    minimo: 3500,
    ram: 32,
    prioridade:
      "Priorizamos processador, memória para ferramentas abertas e SSD. A placa de vídeo separada não é obrigatória para programação comum. Projetos de IA, 3D e jogos precisam de uma análise específica.",
    gpu: "integrada-permitida",
    monitor: "espaco",
  },
  estudos: {
    titulo: "Estudos",
    descricao: "Aulas, pesquisas, trabalhos e programas de estudo.",
    minimo: 2500,
    ram: 16,
    prioridade:
      "Priorizamos abrir programas e arquivos com rapidez: processador, memória e SSD. Podemos usar o vídeo do processador para aproveitar melhor o orçamento.",
    gpu: "integrada-permitida",
    monitor: "conforto",
  },
  todos: {
    titulo: "Um pouco de tudo",
    descricao: "Equilibrar estudos, trabalho e jogos ocasionais.",
    minimo: 2500,
    ram: 16,
    prioridade:
      "Buscamos equilíbrio entre processador, memória e SSD. Uma placa de vídeo separada entra quando fizer sentido no orçamento; este uso não promete rodar todos os jogos.",
    gpu: "conforme-orcamento",
    monitor: "equilibrio",
  },
};
export const opcoesUsoPreview = Object.entries(perfisUso).map(([chave, p]) => [
  chave,
  p.titulo,
  p.descricao,
]);
export const minimoUso = (objetivo) => perfisUso[objetivo]?.minimo ?? 2500;
export function memoriaSugerida(objetivo, orcamento) {
  const desejada = perfisUso[objetivo]?.ram ?? 16;
  return desejada === 32 && orcamento >= 5500 ? 32 : 16;
}
