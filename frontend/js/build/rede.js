import { htmlSeguro as h } from "./catalogo.js";

const numero = (valor,maximo) => valor !== null && valor !== "" && Number.isFinite(Number(valor)) && Number(valor) > 0 && Number(valor) <= maximo ? Number(valor) : null;
export function normalizarRede(valor = {}) {
  if (!valor || typeof valor !== "object") valor = {};
  return {
    tipo:["cabo","wifi"].includes(valor.tipo) ? valor.tipo : "indefinido",
    possuiAcessorio:typeof valor.possuiAcessorio === "boolean" ? valor.possuiAcessorio : null,
    velocidadeMbps:numero(valor.velocidadeMbps,100000),
    comprimentoCaboM:numero(valor.comprimentoCaboM,1000),
    // Legado v1: mantido nulo para ler arquivos antigos, sem gerar custo estimado.
    custoPrevisto:null,
  };
}
export function resumoRede(valor) {
  const rede = normalizarRede(valor);
  if (rede.tipo === "indefinido") return "Conexão ainda não definida";
  const meio = rede.tipo === "cabo" ? "Cabo Ethernet" : "Wi-Fi";
  const acessorio = rede.possuiAcessorio === true ? "já possuo o necessário" : rede.possuiAcessorio === false ? "incluir acessório" : "acessório a confirmar";
  return meio + " · " + acessorio;
}
export function custoRede(valor) {
  return 0; // Somente produtos do catálogo entram no preço da build.
}
export function selecionarAcessorioRede(valor,opcao) {
  const rede = normalizarRede(valor);
  const [tipo,situacao] = String(opcao).split(":");
  if (!["cabo","wifi"].includes(tipo) || !["incluir","possuo","confirmar"].includes(situacao))
    return normalizarRede({...rede,tipo:"indefinido",possuiAcessorio:null});
  return normalizarRede({...rede,tipo,possuiAcessorio:situacao === "confirmar" ? null : situacao === "possuo",
    ...(rede.tipo !== tipo ? {comprimentoCaboM:null,custoPrevisto:null} : {})});
}
export function vincularRedeBuild(container,valor,{bloqueado = false,aoAlterar = () => {}} = {}) {
  let rede = normalizarRede(valor);
  const selecionada = rede.tipo === "indefinido" ? "indefinido" : rede.tipo + ":" + (rede.possuiAcessorio === null ? "confirmar" : rede.possuiAcessorio ? "possuo" : "incluir");
  const opcoes = [
    ["indefinido","Ainda não definido"],
    ["cabo:incluir","Cabo de rede"],
    ["cabo:possuo","Cabo de rede — já possuo"],
    ["cabo:confirmar","Cabo de rede — a confirmar"],
    ["wifi:incluir","Adaptador Wi-Fi"],
    ["wifi:possuo","Wi-Fi integrado ou adaptador — já possuo"],
    ["wifi:confirmar","Adaptador Wi-Fi — a confirmar"],
  ];
  container.innerHTML = '<label class="planning-field" for="build-network-accessory"><span class="sr-only">Wi-Fi / Rede</span><select id="build-network-accessory"' +
    (bloqueado ? ' disabled data-disabled-reason="Destranque a build para alterar o acessório de rede."' : '') + '>' +
    opcoes.map(([valor,texto]) => '<option value="' + valor + '"' + (selecionada === valor ? " selected" : "") + '>' + texto + '</option>').join("") + '</select></label>';
  container.onchange = evento => {
    if (bloqueado || evento.target.id !== "build-network-accessory") return;
    rede = selecionarAcessorioRede(rede,evento.target.value);
    aoAlterar(rede);
  };
}
function ajudaWifi(rede) {
  return 'Algumas placas-mãe já têm Wi-Fi. Se precisar de adaptador, vamos buscar modelos com taxa anunciada de pelo menos 500 Mb/s. A velocidade real também depende do roteador, do sinal e da conexão.';
}
// Padrões apenas deste formulário. Importações e builds antigas preservam suas medidas.
export function redeFormulario(valor = {}) {
  const rede = normalizarRede(valor);
  return {...rede,velocidadeMbps:rede.tipo === "wifi" && rede.possuiAcessorio === false ? 500 : null};
}
export function camposRede(valor,{prefixo = "rede",bloqueado = false} = {}) {
  const rede = normalizarRede(valor), disabled = bloqueado ? ' disabled data-disabled-reason="Destranque a build para alterar a conexão."' : "";
  const op = (valor,atual,texto) => '<option value="' + valor + '"' + (atual === valor ? " selected" : "") + '>' + texto + '</option>';
  const campo = (chave,texto,input) => '<label class="planning-field" for="' + prefixo + '-' + chave + '"><span>' + texto + '</span>' + input + '</label>';
  const input = (chave,maximo,placeholder) => '<input id="' + prefixo + '-' + chave + '" data-network="' + chave + '" type="number" min="0.01" max="' + maximo + '" step="any" inputmode="decimal" value="' + h(rede[chave] ?? "") + '" placeholder="' + placeholder + '"' + disabled + '>';
  return '<div class="network-fields">' +
    campo("tipo","Como você pretende conectar o PC?",'<select id="' + prefixo + '-tipo" data-network="tipo"' + disabled + '>' + op("indefinido",rede.tipo,"Ainda não sei") + op("cabo",rede.tipo,"Cabo de rede / Ethernet") + op("wifi",rede.tipo,"Wi-Fi") + '</select>') +
    (rede.tipo === "indefinido" ? '<p class="planning-help">Você pode decidir depois. Essa escolha não altera a conclusão da build.</p>' :
      campo("possuiAcessorio",rede.tipo === "wifi" ? "Já tem Wi-Fi integrado ou um adaptador?" : "Já possui um cabo de rede adequado?",'<select id="' + prefixo + '-possuiAcessorio" data-network="possuiAcessorio"' + disabled + '>' + op("confirmar",rede.possuiAcessorio === null ? "confirmar" : String(rede.possuiAcessorio),"Preciso confirmar") + op("true",String(rede.possuiAcessorio),rede.tipo === "cabo" ? "Sim, já possuo um cabo de rede" : "Sim, já tenho Wi-Fi integrado ou adaptador") + op("false",String(rede.possuiAcessorio),rede.tipo === "cabo" ? "Não, preciso de um cabo de rede" : "Não, preciso de um adaptador") + '</select>') +
      (rede.tipo === "cabo" && rede.possuiAcessorio === false ? campo("comprimentoCaboM","Quantos metros de cabo você precisa?",input("comprimentoCaboM",1000,"Ex.: 10")) + '<p class="planning-help">Vamos priorizar cabos Cat6 disponíveis no orçamento. Meça o caminho do roteador ao PC, incluindo curvas e desvios.</p>' : "") +
      (rede.tipo === "wifi" ? '<p class="planning-help" data-network-wifi-help>' + ajudaWifi(rede) + '</p>' : "") +
      (rede.possuiAcessorio === false ? '<p class="planning-help">Adicione o cabo ou adaptador pelo catálogo da build quando houver produtos cadastrados. Nenhum preço será estimado.</p>' : "")) + '</div>';
}
export function vincularRede(container,valor,{prefixo = "rede",bloqueado = false,aoRenderizar = () => {},aoAlterar = () => {}} = {}) {
  let rede = redeFormulario(valor);
  const desenhar = () => { container.innerHTML = camposRede(rede,{prefixo,bloqueado}); aoRenderizar(container); };
  desenhar();
  const alterar = evento => {
    const chave = evento.target.dataset.network;
    if (!chave || bloqueado) return;
    if (evento.type === "input" && evento.target.tagName === "SELECT") return;
    if (evento.target.tagName !== "SELECT" && !evento.target.checkValidity()) { aoAlterar(rede); return; }
    const valor = chave === "possuiAcessorio" ? (evento.target.value === "confirmar" ? null : evento.target.value === "true") : evento.target.value;
    rede = redeFormulario({...rede,[chave]:valor,...(chave === "tipo" && rede.tipo !== valor ? {comprimentoCaboM:null} : {})});
    // Só as escolhas estruturais recriam os campos: digitar ou usar as setas não perde o foco.
    if (evento.type === "change" && evento.target.tagName === "SELECT") desenhar();
    const ajuda = container.querySelector("[data-network-wifi-help]");
    if (ajuda) ajuda.textContent = ajudaWifi(rede);
    aoAlterar(rede);
  };
  container.onchange = alterar;
  container.oninput = alterar;
}
