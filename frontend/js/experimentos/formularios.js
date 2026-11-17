import { opcoesUso } from "../build/uso-formulario.js";
import { avaliarOrcamentoGeracao, orcamentoValido } from "../build/orcamento-formulario.js";

// Cópia de trabalho das perguntas. O fluxo oficial continua em pages/forms.js.
export const pecasPreview = [
  ["nenhuma","Ainda não tenho peças"],
  ["processador","Processador","Executa os programas e as tarefas."],
  ["placa-mae","Placa-mãe","Conecta e organiza as peças do computador."],
  ["placa-video","Placa de vídeo","Gera as imagens de jogos e programas."],
  ["memoria","Memória RAM","Mantém os programas abertos em uso."],
  ["ssd","SSD","Guarda arquivos e abre programas com rapidez."],
  ["hd","HD","Guarda seus arquivos e programas."],
  ["fonte","Fonte","Fornece energia às peças."],
  ["gabinete","Gabinete","A caixa onde as peças ficam instaladas."],
  ["cooler","Resfriador a ar","Air cooler · ajuda a resfriar o processador."],
  ["water-cooler","Resfriador a líquido","Water cooler · resfria o processador com líquido."],
  ["fans","Ventoinhas (fans)","Fazem o ar circular dentro do gabinete."],
];
export const perifericosPreview = [["monitor","Monitor"],["teclado","Teclado"],["mouse","Mouse"],["headset","Headset / fone"]];
export const perguntasPc = [
  {chave:"objetivo",etapa:"Objetivo",titulo:"Para que você vai usar o computador?",descricao:"Escolha o uso principal para direcionar a montagem ao que você mais precisa.",tipo:"opcoes",opcoes:opcoesUso},
  {chave:"orcamento",etapa:"Orçamento",titulo:"Quanto você pode gastar no computador?",descricao:"Defina o limite de gasto. Reserve ao menos R$ 2.000 para o PC, além do valor para novos periféricos.",tipo:"orcamento"},
  {chave:"pecas",etapa:"Suas peças",titulo:"O que você já possui?",descricao:"Selecione as peças que vai reaproveitar e informe os modelos. Começando do zero? Marque a primeira opção.",tipo:"pecas",opcoes:pecasPreview},
  {chave:"perifericos",etapa:"Periféricos",titulo:"Quer incluir periféricos na montagem?",descricao:"Além da caixa do computador, você pode precisar de monitor, teclado, mouse e fone. Informe o que já possui e quanto reservar para o que faltar.",tipo:"perifericos",opcoes:[
    ["sem-perifericos","Não incluir periféricos novos","Vou montar apenas o computador."],
    ["todos-perifericos","Preciso de todos","Incluir monitor, teclado, mouse e headset."],
    ["alguns-perifericos","Já possuo alguns ou todos","Informe o que vai reaproveitar; incluímos somente o que faltar."],
  ]},
  {chave:"rede",etapa:"Conexão",titulo:"Como seu PC vai se conectar à internet?",descricao:"Escolha Wi-Fi, cabo de internet ou os dois. Depois, diga se quer incluir os acessórios na montagem.",tipo:"rede"},
  {chave:"aparencia",etapa:"Aparência",titulo:"Como você quer o visual do computador?",descricao:"Escolha tamanho, estilo e cor, ou deixe sem preferência. As escolhas precisam caber no orçamento e combinar com as peças.",tipo:"aparencia"},
];
export const perguntasNotebook = [
  {chave:"objetivo",etapa:"Objetivo",titulo:"Para que você vai usar o notebook?",descricao:"Conte o uso principal. Esta primeira versão vai ajudar a decidir quais perguntas fazem sentido para notebooks.",tipo:"opcoes",opcoes:opcoesUso},
  {chave:"orcamento",etapa:"Orçamento",titulo:"Qual é seu limite de gasto?",descricao:"Informe o máximo para o notebook. Ainda vamos definir as faixas e os critérios para recomendar modelos.",tipo:"orcamento"},
  {chave:"mobilidade",etapa:"Mobilidade",titulo:"Você vai levar o notebook com frequência?",descricao:"Peso, bateria e tamanho da tela fazem diferença na hora de transportar o computador.",tipo:"opcoes",opcoes:[
    ["fixo","Vou usar mais em casa","O tamanho e o peso podem ter menos importância."],
    ["ocasional","Vou levar de vez em quando","Quero equilibrar conforto e facilidade de transporte."],
    ["diaria","Vou levar todos os dias","Quero dar mais atenção ao peso e à bateria."],
  ]},
  {chave:"tela",etapa:"Tela",titulo:"Qual tamanho de tela combina com você?",descricao:"Uma tela menor facilita o transporte. Uma maior oferece mais espaço para ler, trabalhar e organizar janelas.",tipo:"opcoes",opcoes:[
    ["sem-preferencia","Ainda não sei","Quero comparar as opções depois."],
    ["compacta","Menor e fácil de levar","Referência: cerca de 13 a 14 polegadas."],
    ["equilibrada","Tamanho intermediário","Referência: cerca de 15 a 16 polegadas."],
    ["grande","Tela maior","Referência: cerca de 17 polegadas ou mais."],
  ]},
  {chave:"preferencias",etapa:"Preferências",titulo:"Tem algo que não pode faltar?",descricao:"Escolhas opcionais para começarmos a desenhar as próximas perguntas. Elas ainda não filtram um catálogo de notebooks.",tipo:"preferencias"},
];

export const prioridadesPreview = [["desempenho","Melhor desempenho"],["custo_beneficio","Maior custo-benefício"]];
export const marcasPreview = [["sem-preferencia","Sem preferência"],["intel","Intel"],["amd","AMD"]];
export function novasRespostasPreview(tipo) {
  return tipo === "pc" ? {pecas:[],pecasDetalhes:{},perifericosProprios:[],percentualPerifericos:20,rede:{tipo:"indefinido"},aparencia:{},preferencia_processador:"sem-preferencia"}
    : {memoria:"sem-preferencia",armazenamento:"sem-preferencia",bateria:"sem-preferencia",sistema:"sem-preferencia"};
}
export function percentualPreview(respostas) {
  return respostas.perifericos === "todos-perifericos" || respostas.perifericos === "alguns-perifericos" && (respostas.perifericosProprios || []).length < perifericosPreview.length
    ? respostas.percentualPerifericos : 0;
}
export function validarEtapaPreview(tipo,pergunta,respostas) {
  if (pergunta.tipo === "opcoes" && !pergunta.opcoes.some(([v]) => v === respostas[pergunta.chave])) return "Escolha uma opção para continuar.";
  if (pergunta.tipo === "orcamento") {
    if (!orcamentoValido(respostas.orcamento)) return "Informe um limite de gasto válido, maior que zero e de até R$ 1.000.000.";
    if (tipo === "pc") { const r=avaliarOrcamentoGeracao(respostas.orcamento);if(!r.valido)return r.mensagem; }
  }
  if (pergunta.tipo === "pecas") {
    if (!respostas.pecas?.length) return "Marque as peças que já possui ou escolha “Ainda não tenho peças”.";
    if (respostas.pecas.some(p=>p !== "nenhuma" && !respostas.pecasDetalhes?.[p]?.trim())) return "Informe o modelo de cada peça selecionada.";
  }
  if (pergunta.tipo === "perifericos") {
    if (!pergunta.opcoes.some(([v])=>v===respostas.perifericos)) return "Escolha se deseja incluir periféricos.";
    const r=avaliarOrcamentoGeracao(respostas.orcamento,percentualPreview(respostas));if(!r.valido)return r.mensagem;
    if (respostas.perifericos === "alguns-perifericos" && respostas.perifericosProprios.some(p=>!respostas.pecasDetalhes?.[p]?.trim())) return "Informe o modelo dos periféricos que já possui.";
  }
  if (pergunta.tipo === "rede" && ["cabo","ambos"].includes(respostas.rede.tipo) && respostas.rede.possuiAcessorio === false
    && !(respostas.rede.comprimentoCaboM > 0 && respostas.rede.comprimentoCaboM <= 1000)) return "Informe quantos metros de cabo precisa.";
  return "";
}
export function resumoFormularioPreview(tipo,respostas) {
  return {previa:true,tipo,...structuredClone(respostas),...(tipo === "pc" ? {percentualPerifericos:percentualPreview(respostas)} : {}),geracaoDisponivel:false};
}
