import { iconeAnimado, iniciarIcones } from "../components/ui.js";

const prioridades = [
  ["desempenho", "Melhor desempenho", "Dar prioridade a peças mais rápidas para o seu uso, dentro do orçamento."],
  ["custo_beneficio", "Maior custo-benefício", "Equilibrar preço e desempenho, evitando pagar mais por ganhos pequenos."],
];

export function prioridadeMontagemValida(valor) {
  return prioridades.some(([chave]) => chave === valor);
}

const marcas = [["sem-preferencia", "Sem preferência"], ["intel", "Intel"], ["amd", "AMD"]];
export const preferenciaProcessadorValida = valor => marcas.some(([chave]) => chave === valor);

export function preferenciasMontagemHtml(valorAtual, marcaAtual = "sem-preferencia") {
  return `
    <div class="build-action-heading">
      <h2 id="generation-priority-title" class="font-1-l" tabindex="-1">Antes de gerar sua build</h2>
      <button type="button" class="build-action-close" data-priority-cancel aria-label="Fechar confirmação">×</button>
    </div>
    <p id="generation-priority-description">Dê o toque final na montagem. Seu limite de orçamento continua o mesmo.</p>
    <form class="generation-priority-form">
      <fieldset aria-describedby="generation-brand-help">
        <legend>Tem preferência pela marca do processador?</legend>
        <div class="generation-brand-options">
          ${marcas.map(([valor, titulo]) => `<label class="generation-priority-option">
            <input type="radio" name="preferencia_processador" value="${valor}" required ${marcaAtual === valor ? "checked" : ""}>
            ${iconeAnimado("circledot")}<span class="generation-choice-copy"><strong>${titulo}</strong></span>
          </label>`).join("")}
        </div>
        <p id="generation-brand-help" class="generation-brand-help">Vamos priorizar essa marca quando ela combinar com suas peças e seu orçamento. A escolha vale para o processador, não para a placa de vídeo.</p>
      </fieldset>
      <fieldset>
        <legend>O que você prefere priorizar?</legend>
        <div class="generation-priority-options">
          ${prioridades.map(([valor, titulo, descricao]) => `
            <label class="generation-priority-option">
              <input type="radio" name="prioridade_montagem" value="${valor}" required ${valorAtual === valor ? "checked" : ""}>
              ${iconeAnimado("circledot")}
              <span class="generation-choice-copy"><strong>${titulo}</strong><span>${descricao}</span></span>
            </label>`).join("")}
        </div>
      </fieldset>
      <div class="generation-priority-actions">
        <button type="button" class="btn-ghost" data-priority-cancel aria-label="Voltar às respostas do formulário">Voltar às respostas</button>
        <button type="submit" class="btn-primary-form" aria-label="Gerar build com as preferências escolhidas" ${prioridadeMontagemValida(valorAtual) && preferenciaProcessadorValida(marcaAtual) ? "" : "disabled"}>Gerar build</button>
      </div>
    </form>`;
}

export function confirmarPrioridadeMontagem(valorAtual, marcaAtual = "sem-preferencia") {
  const anterior = document.activeElement;
  const dialogo = document.createElement("dialog");
  dialogo.className = "build-action-dialog generation-priority-dialog";
  dialogo.setAttribute("aria-labelledby", "generation-priority-title");
  dialogo.setAttribute("aria-describedby", "generation-priority-description");
  dialogo.innerHTML = preferenciasMontagemHtml(valorAtual, marcaAtual);

  return new Promise(resolve => {
    let escolha = null;
    const form = dialogo.querySelector("form");
    form.addEventListener("change", () => {
      const dados = new FormData(form);
      form.querySelector('[type="submit"]').disabled = !prioridadeMontagemValida(dados.get("prioridade_montagem")) || !preferenciaProcessadorValida(dados.get("preferencia_processador"));
    });
    form.addEventListener("submit", evento => {
      evento.preventDefault();
      const dados = new FormData(form);
      const valor = dados.get("prioridade_montagem"), marca = dados.get("preferencia_processador");
      if (!prioridadeMontagemValida(valor) || !preferenciaProcessadorValida(marca)) return;
      escolha = {prioridade_montagem: valor, preferencia_processador: marca};
      dialogo.close();
    });
    dialogo.querySelectorAll("[data-priority-cancel]").forEach(botao => botao.addEventListener("click", () => dialogo.close()));
    dialogo.addEventListener("click", evento => {
      const limites = dialogo.getBoundingClientRect();
      if (evento.target === dialogo && (evento.clientX < limites.left || evento.clientX > limites.right || evento.clientY < limites.top || evento.clientY > limites.bottom)) dialogo.close();
    });
    dialogo.addEventListener("close", () => {
      dialogo.remove();
      iniciarIcones();
      if (anterior?.isConnected) anterior.focus({preventScroll:true});
      resolve(escolha);
    }, {once:true});
    document.body.append(dialogo);
    dialogo.showModal();
    iniciarIcones(dialogo);
    dialogo.querySelector("h2").focus({preventScroll:true});
  });
}
