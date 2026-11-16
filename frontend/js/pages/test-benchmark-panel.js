import { painelBenchmarkHtml } from "../benchmark/painel.js";
import { iniciarPainelBenchmark } from "../benchmark/interface.js";
import { painelBlenderHtml, iniciarPainelBlender } from "../benchmark/blender.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";

const raiz = document.querySelector("#teste-painel-benchmark");
if (raiz) {
  const fps = raiz.querySelector("#preview-fps-panel");
  const blender = raiz.querySelector("#preview-blender-panel");
  fps.innerHTML = '<div class="benchmark-preview-heading"><h3>Como sua build pode rodar?</h3><p>Escolha o jogo e os ajustes que você pretende usar.</p></div>'
    + painelBenchmarkHtml({ prefixo: "preview-fps" });
  fps.querySelector(".fpshq-panel").dataset.layout = "panel";
  const vazio = (icone, titulo, descricao) => '<div class="benchmark-preview-empty-icon">' + iconeAnimado(icone) + '</div><h4>' + titulo + '</h4><p>' + descricao + '</p><span class="benchmark-preview-waiting">Aguardando consulta</span>';
  fps.querySelector(".fpshq-empty").innerHTML = vazio("gamepad", "O próximo passo é dar o play.", "Consulte o desempenho para ver a expectativa de FPS e comparar os ajustes gráficos.");
  const dispositivos = { cpu: "AMD Ryzen 5 5600", gpu: "NVIDIA GeForce RTX 3060" };
  blender.innerHTML = '<div class="benchmark-preview-heading"><h3>E na hora de criar?</h3><p>Consulte a renderização de imagens e cenas 3D no Blender.</p></div>' + painelBlenderHtml(dispositivos);
  blender.querySelector("#blender-result").innerHTML = '<div class="benchmark-preview-empty">' + vazio("microchip", "Mais espaço para suas ideias.", "A pontuação mostra quantas amostras a peça renderiza por minuto. CPU e GPU são avaliadas separadamente.") + '</div>';

  const pararFps = iniciarPainelBenchmark(fps, { prefixo: "preview-fps" });
  const pararBlender = iniciarPainelBlender(blender, dispositivos);
  const abas = [...raiz.querySelectorAll('[role="tab"]')];
  function selecionar(aba, focar = false) {
    abas.forEach(item => {
      const ativa = item === aba;
      item.setAttribute("aria-selected", String(ativa));
      item.tabIndex = ativa ? 0 : -1;
      raiz.querySelector("#" + item.getAttribute("aria-controls")).hidden = !ativa;
    });
    if (focar) aba.focus();
    iniciarIcones(raiz);
  }
  abas.forEach((aba, indice) => {
    aba.addEventListener("click", () => selecionar(aba));
    aba.addEventListener("keydown", evento => {
      const destino = {ArrowRight: (indice + 1) % abas.length, ArrowLeft: (indice + abas.length - 1) % abas.length, Home: 0, End: abas.length - 1}[evento.key];
      if (destino === undefined) return;
      evento.preventDefault(); selecionar(abas[destino], true);
    });
  });
  selecionar(abas[0]);
  window.addEventListener("pagehide", () => { pararFps?.(); pararBlender?.(); }, { once: true });
}
