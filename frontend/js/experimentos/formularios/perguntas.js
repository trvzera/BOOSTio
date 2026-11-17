import { opcoesUsoPreview } from "./objetivos.js";

export const pecasPreview = [
  ["nenhuma", "Ainda não tenho peças"],
  ["processador", "Processador", "Executa os programas e as tarefas."],
  ["placa-mae", "Placa-mãe", "Conecta e organiza as peças."],
  ["placa-video", "Placa de vídeo", "Gera as imagens de jogos e programas."],
  ["memoria", "Memória RAM", "Mantém os programas abertos em uso."],
  ["ssd", "SSD", "Guarda arquivos e abre programas com rapidez."],
  ["hd", "HD", "Guarda seus arquivos."],
  ["fonte", "Fonte", "Fornece energia às peças."],
  ["gabinete", "Gabinete", "A caixa onde as peças ficam instaladas."],
  ["cooler", "Resfriador a ar"],
  ["water-cooler", "Resfriador a líquido"],
  ["fans", "Ventoinhas (fans)"],
];
const objetivo = (notebook) => ({
  chave: "objetivo",
  etapa: "Objetivo",
  titulo: `Para que você vai usar o ${notebook ? "notebook" : "computador"}?`,
  descricao:
    "Escolha o uso principal. Abaixo das opções, mostramos o que muda na escolha das peças.",
  tipo: "opcoes",
  opcoes: opcoesUsoPreview,
});
const orcamento = {
  chave: "orcamento",
  etapa: "Orçamento",
  titulo: "Quanto você pode gastar?",
  descricao:
    "Começamos em até R$ 5.000. Você pode mudar o valor. O mínimo depende do uso e vale para o computador, depois de separar os acessórios.",
  tipo: "orcamento",
};
export const perguntasPc = [
  objetivo(false),
  { ...orcamento },
  {
    chave: "pecas",
    etapa: "Suas peças",
    titulo: "O que você já possui?",
    descricao:
      "Selecione o que vai reaproveitar e informe os modelos, ou comece do zero.",
    tipo: "pecas",
    opcoes: pecasPreview,
  },
  {
    chave: "perifericos",
    etapa: "Periféricos",
    titulo: "Quer incluir periféricos na montagem?",
    descricao:
      "Separe um valor para monitor, teclado, mouse, fone e, se precisar, webcam.",
    tipo: "perifericos",
    opcoes: [
      ["sem-perifericos", "Não incluir periféricos novos"],
      [
        "todos-perifericos",
        "Preciso de todos",
        "Monitor, teclado, mouse e fone; a webcam é opcional.",
      ],
      [
        "alguns-perifericos",
        "Já possuo alguns ou todos",
        "Incluiremos somente o que faltar.",
      ],
    ],
  },
  {
    chave: "rede",
    etapa: "Conexão",
    titulo: "Como seu PC vai se conectar à internet?",
    descricao:
      "Escolha Wi-Fi, cabo ou os dois. Os cabos usam os comprimentos cadastrados, sem medidas personalizadas.",
    tipo: "rede",
  },
  {
    chave: "aparencia",
    etapa: "Aparência",
    titulo: "Como você prefere o visual do computador?",
    descricao:
      "Cor, tamanho e estilo são preferências. Se não houver uma combinação adequada, seguimos com outra aparência, respeitando o orçamento e a compatibilidade.",
    tipo: "aparencia",
  },
];
export const perguntasNotebook = [
  objetivo(true),
  { ...orcamento },
  {
    chave: "mobilidade",
    etapa: "Mobilidade",
    titulo: "Você vai levar o notebook com frequência?",
    descricao:
      "Peso, bateria e tamanho da tela fazem diferença ao transportar.",
    tipo: "opcoes",
    opcoes: [
      ["fixo", "Vou usar mais em casa"],
      ["ocasional", "Vou levar de vez em quando"],
      ["diaria", "Vou levar todos os dias"],
    ],
  },
  {
    chave: "tela",
    etapa: "Tela",
    titulo: "Qual tamanho de tela combina com você?",
    descricao:
      "Uma tela menor facilita o transporte; uma maior oferece mais espaço para trabalhar.",
    tipo: "opcoes",
    opcoes: [
      ["sem-preferencia", "Ainda não sei"],
      ["compacta", "Menor e fácil de levar", "Cerca de 13 a 14 polegadas."],
      ["equilibrada", "Tamanho intermediário", "Cerca de 15 a 16 polegadas."],
      ["grande", "Tela maior", "Cerca de 17 polegadas ou mais."],
    ],
  },
  {
    chave: "perifericos",
    etapa: "Acessórios",
    titulo: "Quer acessórios para usar com o notebook?",
    descricao:
      "O notebook já inclui tela, teclado e touchpad. Escolha apenas os itens externos que fazem sentido para você.",
    tipo: "perifericos",
    opcoes: [
      ["sem-perifericos", "Somente o notebook"],
      ["escolher-extras", "Quero escolher acessórios externos"],
    ],
  },
  {
    chave: "preferencias",
    etapa: "Preferências",
    titulo: "O que mais importa na sua rotina?",
    descricao:
      "Definimos a memória conforme o uso e o orçamento. Você não precisa escolher quantos GB comprar. A preferência de marca fica na revisão final.",
    tipo: "preferencias",
  },
];
export function novasRespostasPreview(tipo) {
  const base = { orcamento: 5000, percentualPerifericos: 20 };
  return tipo === "pc"
    ? {
        ...base,
        pecas: [],
        pecasDetalhes: {},
        perifericosProprios: [],
        incluirWebcam: false,
        webcamAlterada: false,
        rede: { tipo: "indefinido" },
        aparencia: {},
        preferencia_processador: "sem-preferencia",
      }
    : {
        ...base,
        extrasNotebook: [],
        armazenamento: "sem-preferencia",
        bateria: "sem-preferencia",
        marca_notebook: "sem-preferencia",
      };
}
