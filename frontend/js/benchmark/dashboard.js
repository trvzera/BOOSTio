import { htmlSeguro as h } from "../build/catalogo.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";
import { painelBenchmarkHtml } from "./painel.js";
import { iniciarPainelBenchmark } from "./interface.js";
import { painelBlenderHtml, iniciarPainelBlender } from "./blender.js";

const vazio = (icone,titulo,descricao,estado = "Aguardando consulta") => '<div class="benchmark-dashboard-empty-icon">' + iconeAnimado(icone)
  + '</div><h4>' + titulo + '</h4><p>' + descricao + '</p><span class="benchmark-dashboard-waiting">' + estado + '</span>';

export function dashboardBenchmarkHtml({prefixo = "build",titulo,cpu,gpu,memoria = null,verificarRequisitos = false,previa = false,dispositivos = {}} = {}) {
  const id = sufixo => h(prefixo + "-" + sufixo);
  const aba = (tipo,rotulo,icone,ativa) => '<button type="button" role="tab" data-benchmark-type="' + tipo
    + '" id="' + id("tab-" + tipo) + '" aria-controls="' + id("panel-" + tipo) + '" aria-selected="' + ativa + '" tabindex="' + (ativa ? 0 : -1) + '" aria-label="' + h(rotulo) + '">'
    + iconeAnimado(icone) + rotulo + '</button>';
  const item = (rotulo,valor) => '<div><dt>' + rotulo + '</dt><dd>' + h(valor) + '</dd></div>';
  return '<div class="benchmark-dashboard-shell glass-card" data-benchmark-dashboard>'
    + '<header class="benchmark-dashboard-build"><div><p class="benchmark-dashboard-eyebrow">' + (previa ? 'Configuração de exemplo' : 'Sua configuração')
    + '</p><h3>' + h(titulo || "Minha build") + '</h3></div>' + (previa ? '<span class="benchmark-dashboard-badge">Prévia</span>' : '') + '</header>'
    + '<dl class="benchmark-dashboard-hardware">' + item("Processador",cpu || "Não identificado") + item("Placa de vídeo",gpu || "Vídeo integrado / a confirmar")
    + item("Memória",memoria == null ? "Capacidade a confirmar" : memoria + " GB de RAM") + '</dl>'
    + '<div class="builds-page-switch benchmark-dashboard-tabs" role="tablist" aria-label="Tipo de desempenho">' + aba("games","Jogos / FPS","gamepad",true)
    + aba("blender","Blender","microchip",false) + '</div>'
    + '<section data-benchmark-pane="games" id="' + id("panel-games") + '" role="tabpanel" aria-labelledby="' + id("tab-games") + '" tabindex="0">'
    + '<div class="benchmark-dashboard-heading"><h3>Como sua build pode rodar?</h3><p>Escolha o jogo e os ajustes que você pretende usar.</p></div>'
    + painelBenchmarkHtml({prefixo:prefixo + "-fps",memoria,verificarRequisitos,mostrarHardware:false}) + '</section>'
    + '<section data-benchmark-pane="blender" id="' + id("panel-blender") + '" role="tabpanel" aria-labelledby="' + id("tab-blender") + '" tabindex="0" hidden>'
    + '<div class="benchmark-dashboard-heading"><h3>E na hora de criar?</h3><p>Consulte a renderização de imagens e cenas 3D no Blender.</p></div>'
    + painelBlenderHtml(dispositivos,{prefixo:prefixo + "-blender"}) + '</section>'
    + '<p class="benchmark-dashboard-footnote">Nenhum teste é executado no seu computador. Os resultados dependem das fontes consultadas e podem variar conforme as peças e configurações.</p></div>';
}

export function iniciarDashboardBenchmark(raiz,{prefixo = "build",hardware,dispositivos = {},buildId = null,publica = false,cliente} = {}) {
  const fps = raiz.querySelector('[data-benchmark-pane="games"]');
  const blender = raiz.querySelector('[data-benchmark-pane="blender"]');
  fps.querySelector(".fpshq-panel").dataset.layout = "panel";
  fps.querySelector(".fpshq-empty").innerHTML = hardware?.motivo
    ? vazio("gamepad","FPS ainda não disponível para esta build","Revise os itens indicados antes de consultar. A aba Blender mostra os testes disponíveis para suas peças.","Revisar montagem")
    : vazio("gamepad","O próximo passo é dar o play.","Consulte o desempenho para ver a expectativa de FPS e comparar os ajustes gráficos.");
  blender.querySelector("[data-blender-result]").innerHTML = '<div class="benchmark-dashboard-empty">' + vazio("microchip","Mais espaço para suas ideias.","A pontuação mostra quantas amostras a peça renderiza por minuto. CPU e GPU são avaliadas separadamente.") + '</div>';
  const pararFps = iniciarPainelBenchmark(fps,{prefixo:prefixo + "-fps",hardware,buildId,publica,cliente});
  const pararBlender = iniciarPainelBlender(blender,dispositivos,{prefixo:prefixo + "-blender",cliente});
  const abas = [...raiz.querySelectorAll('[data-benchmark-type]')];
  const controle = new AbortController();
  function selecionar(aba,focar = false) {
    abas.forEach(item => {
      const ativa = item === aba;
      item.setAttribute("aria-selected",String(ativa)); item.tabIndex = ativa ? 0 : -1;
      raiz.querySelector('[data-benchmark-pane="' + item.dataset.benchmarkType + '"]').hidden = !ativa;
    });
    if (focar) aba.focus();
    iniciarIcones(raiz);
  }
  abas.forEach((aba,indice) => {
    aba.addEventListener("click",() => selecionar(aba),{signal:controle.signal});
    aba.addEventListener("keydown",evento => {
      const destino = {ArrowRight:(indice + 1) % abas.length,ArrowLeft:(indice + abas.length - 1) % abas.length,Home:0,End:abas.length - 1}[evento.key];
      if (destino === undefined) return;
      evento.preventDefault(); selecionar(abas[destino],true);
    },{signal:controle.signal});
  });
  selecionar(abas[0]);
  return () => { controle.abort(); pararFps?.(); pararBlender?.(); };
}
