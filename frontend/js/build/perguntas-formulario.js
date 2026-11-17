import { opcoesUso } from "./uso-formulario.js";

export const perguntas = [
  {
    chave: "objetivo",
    etapa: "Objetivo",
    tag: "Etapa 01",
    titulo: "Para que você vai usar o computador?",
    descricao:
      "Escolha o uso principal para direcionar a montagem ao que você mais precisa.",
    opcoes: opcoesUso,
  },
  {
    chave: "orcamento",
    etapa: "Orçamento",
    tag: "Etapa 02",
    titulo: "Quanto você pode gastar no computador?",
    descricao:
      "Defina seu limite total. O mínimo para as peças depende do uso escolhido; a reserva de periféricos sai desse mesmo valor.",
    opcoes: [
      ["ate-3000", "Até R$ 3.000", "Configuração essencial e econômica."],
      ["3000-5000", "Até R$ 5.000", "Desempenho equilibrado para o dia a dia."],
      [
        "5000-8000",
        "Até R$ 8.000",
        "Mais potência para jogos e tarefas exigentes.",
      ],
    ],
  },
  {
    chave: "pecas",
    etapa: "Suas peças",
    tag: "Etapa 03",
    titulo: "O que você já possui?",
    descricao:
      "Selecione as peças que vai reaproveitar e informe os modelos. Começando do zero? Marque a primeira opção.",
    multipla: true,
    opcoes: [
      ["nenhuma", "Ainda não tenho peças"],
      ["processador", "Processador", "Executa os programas e as tarefas."],
      ["placa-mae", "Placa-mãe", "Conecta e organiza as peças do computador."],
      [
        "placa-video",
        "Placa de vídeo",
        "Gera as imagens de jogos e programas.",
      ],
      ["memoria", "Memória RAM", "Mantém os programas abertos em uso."],
      ["ssd", "SSD", "Guarda arquivos e abre programas com rapidez."],
      ["hd", "HD", "Guarda seus arquivos e programas."],
      ["fonte", "Fonte", "Fornece energia às peças."],
      ["gabinete", "Gabinete", "A caixa onde as peças ficam instaladas."],
      [
        "cooler",
        "Resfriador a ar",
        "Air cooler · ajuda a resfriar o processador.",
      ],
      [
        "water-cooler",
        "Resfriador a líquido",
        "Water cooler · resfria o processador com líquido.",
      ],
      ["fans", "Ventoinhas (fans)", "Fazem o ar circular dentro do gabinete."],
    ],
  },
  {
    chave: "perifericos",
    etapa: "Periféricos",
    tag: "Etapa 04",
    titulo: "Quer incluir periféricos na montagem?",
    descricao:
      "Além da caixa do computador, você pode precisar de monitor, teclado, mouse e fone. Informe o que já possui e quanto reservar para o que faltar.",
    opcoes: [
      [
        "sem-perifericos",
        "Não incluir periféricos novos",
        "Vou montar apenas o computador.",
      ],
      [
        "todos-perifericos",
        "Preciso de todos",
        "Incluir monitor, teclado, mouse e headset.",
      ],
      [
        "alguns-perifericos",
        "Já possuo alguns ou todos",
        "Informe o que vai reaproveitar; incluímos somente o que faltar.",
      ],
    ],
  },
  {
    chave: "rede",
    etapa: "Conexão",
    tag: "Etapa 05",
    titulo: "Como seu PC vai se conectar à internet?",
    descricao:
      "Escolha Wi-Fi, cabo de internet ou os dois. Depois, diga se quer incluir os acessórios na montagem.",
    opcoes: [],
  },
  {
    chave: "aparencia",
    etapa: "Aparência",
    tag: "Etapa 06",
    titulo: "Como você quer o visual do computador?",
    descricao:
      "Escolha tamanho, estilo e cor, ou deixe sem preferência. Vamos tentar seguir suas preferências. Se não houver uma opção adequada, adaptaremos o visual sem ultrapassar o orçamento nem prejudicar a compatibilidade.",
    opcoes: [],
  },
];

export const exemplosPecas = {
  processador: "Ex.: AMD Ryzen 5 5600",
  "placa-mae": "Ex.: ASUS TUF Gaming B550M-Plus",
  "placa-video": "Ex.: GeForce RTX 4060 8 GB",
  memoria: "Ex.: Kingston Fury 16 GB DDR4 3200 MHz",
  ssd: "Ex.: Kingston NV2 1 TB NVMe",
  hd: "Ex.: Seagate Barracuda 2 TB",
  fonte: "Ex.: Corsair CV650 650 W",
  gabinete: "Ex.: Montech Air 100",
  cooler: "Ex.: DeepCool AK400",
  "water-cooler": "Ex.: Corsair H100i",
  fans: "Ex.: Kit 3 fans Rise Mode 120 mm",
  monitor: "Ex.: LG UltraGear 24GN60R-B",
  teclado: "Ex.: Redragon Kumara K552",
  mouse: "Ex.: Logitech G203",
  headset: "Ex.: HyperX Cloud II",
  webcam: "Ex.: Logitech C920",
  microfone: "Ex.: HyperX SoloCast",
};
