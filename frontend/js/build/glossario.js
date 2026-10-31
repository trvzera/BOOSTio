import { htmlSeguro as h } from "./catalogo.js";
const observadores = new WeakMap();

const termos = {
  GB:["Gigabyte", "Indica capacidade de memória ou espaço para guardar arquivos. Na RAM, ajuda a indicar quanto pode ficar em uso ao mesmo tempo."],
  TB:["Terabyte", "Indica espaço para arquivos. Um TB corresponde a cerca de mil GB no armazenamento anunciado."],
  MHz:["Megahertz", "Medida de frequência usada nas memórias e em outras peças. Esse número sozinho não define o desempenho."],
  GHz:["Gigahertz", "Medida de frequência comum em processadores. Compare também o modelo e a geração, além desse número."],
  Hz:["Hertz", "No monitor, indica quantas vezes a imagem pode ser atualizada por segundo. Mais Hz podem deixar os movimentos mais suaves se o PC acompanhar."],
  W:["Watt", "Unidade de potência. Aparece no consumo estimado das peças e na capacidade de fornecimento da fonte."],
  mm:["Milímetro", "Unidade de tamanho. Dez milímetros equivalem a um centímetro. Ajuda a conferir se as peças cabem."],
  DDR:["Geração da memória RAM", "DDR4 e DDR5 são gerações diferentes. A memória precisa corresponder ao padrão aceito pela placa-mãe."],
  NVMe:["Comunicação do SSD", "Tecnologia usada por alguns SSDs para se comunicar com o computador. O encaixe e o suporte da placa-mãe precisam combinar."],
  SATA:["Conexão de armazenamento", "Ligação usada por HDs e alguns SSDs. A placa-mãe precisa ter uma conexão disponível para cada unidade."],
  "M.2":["Encaixe de armazenamento", "Formato de encaixe usado por alguns SSDs. Confira o tamanho e o tipo de SSD aceitos pela placa-mãe."],
  USB:["Conexão de acessórios", "Ligação usada para conectar itens como teclado, mouse e alguns adaptadores de Wi-Fi."],
  PCIe:["Conexão de expansão", "Ligação usada por placas de vídeo e outras peças. O encaixe e o espaço disponíveis precisam ser conferidos."],
  socket:["Encaixe do processador", "É onde o processador se conecta à placa-mãe. Os modelos precisam ter encaixe e suporte compatíveis."],
  slot:["Encaixe disponível", "Espaço na placa-mãe para instalar uma peça, como um pente de memória ou uma placa de expansão."],
  kit:["Conjunto vendido junto", "Um produto pode incluir mais de uma peça. Por exemplo, um kit de memória pode trazer dois pentes."],
};

export function termosNoTexto(texto) {
  return Object.keys(termos).filter(termo => {
    const padrao = termo === "socket" ? "(?:socket|soquete)" : termo === "slot" ? "slots?" : termo.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");
    return new RegExp("(^|[^a-zà-ÿ])"+padrao+"(?![a-zà-ÿ])","i").test(String(texto));
  });
}
export function glossarioHtml(chaves) {
  const usados = [...new Set(chaves)].filter(chave => Object.hasOwn(termos,chave));
  if (!usados.length) return "";
  return '<details class="component-glossary"><summary aria-label="Entenda os termos: ' + h(usados.join(", ")) + '"><span aria-hidden="true">?</span></summary><div class="glossary-content" tabindex="0" role="region" aria-label="Definições dos termos usados nesta peça"><dl>' +
    usados.map(chave => '<div><dt>' + h(chave) + ' · ' + h(termos[chave][0]) + '</dt><dd>' + h(termos[chave][1]) + '</dd></div>').join("") + '</dl></div></details>';
}
function posicionarGlossario(detalhe) {
  const caixa = detalhe.querySelector(".glossary-content"), botao = detalhe.querySelector("summary").getBoundingClientRect();
  if(botao.bottom<0 || botao.top>innerHeight){detalhe.open=false;return;}
  const ancora = detalhe.closest(".component-heading-label").getBoundingClientRect(), area = caixa.getBoundingClientRect();
  if(!area.width || !area.height)return;
  const esquerda = Math.max(12,Math.min(botao.left,innerWidth-area.width-12));
  const topo = botao.bottom+area.height+8 <= innerHeight-12 ? botao.bottom+8 : Math.max(12,botao.top-area.height-8);
  caixa.style.left = (esquerda-ancora.left)+"px";
  caixa.style.top = (topo-ancora.top)+"px";
}
export function iniciarGlossarios(raiz) {
  let observador = observadores.get(raiz);
  if (!observador && typeof ResizeObserver === "function") {
    observador = new ResizeObserver(entradas => entradas.forEach(({target}) => {
      const detalhe = target.closest("details");if(detalhe?.open)posicionarGlossario(detalhe);
    }));
    observadores.set(raiz,observador);
  }
  observador?.disconnect();
  raiz.querySelectorAll(".component-group").forEach(grupo => {
    const alvo = grupo.querySelector("[data-glossary-slot]");
    if (!alvo) return;
    const texto = [...grupo.querySelectorAll(".component-copy,.component-count,.component-quantity,.component-connections")].map(e => e.textContent).join(" ");
    alvo.innerHTML = glossarioHtml(termosNoTexto(texto));
    const detalhe = alvo.querySelector("details");
    detalhe?.addEventListener("toggle",() => { if(detalhe.open)requestAnimationFrame(()=>{if(detalhe.open)posicionarGlossario(detalhe);}); });
    if(detalhe)observador?.observe(detalhe.querySelector(".glossary-content"));
  });
  if (raiz.dataset.glossaryEvents) return;
  raiz.dataset.glossaryEvents = "true";
  const fechar = () => raiz.querySelectorAll(".component-glossary[open]").forEach(d => { d.open = false; });
  window.addEventListener("resize",fechar);
  window.addEventListener("scroll",evento => { if (!evento.target.closest?.(".glossary-content")) raiz.querySelectorAll(".component-glossary[open]").forEach(posicionarGlossario); },{capture:true,passive:true});
  raiz.addEventListener("click",evento => {
    raiz.querySelectorAll(".component-glossary[open]").forEach(d => { if (!d.contains(evento.target)) d.open = false; });
  });
  raiz.addEventListener("keydown",evento => {
    if (evento.key !== "Escape") return;
    raiz.querySelectorAll(".component-glossary[open]").forEach(d => { d.open = false; d.querySelector("summary").focus(); });
  });
}
