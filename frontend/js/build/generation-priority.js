const prioridades = [
  ["desempenho", "Melhor desempenho", "Dar prioridade a peças mais rápidas para o seu uso, dentro do orçamento."],
  ["custo_beneficio", "Maior custo-benefício", "Equilibrar preço e desempenho, evitando pagar mais por ganhos pequenos."],
];

export function prioridadeMontagemValida(valor) {
  return prioridades.some(([chave]) => chave === valor);
}

export function confirmarPrioridadeMontagem(valorAtual) {
  const anterior = document.activeElement;
  const dialogo = document.createElement("dialog");
  dialogo.className = "build-action-dialog generation-priority-dialog";
  dialogo.setAttribute("aria-labelledby", "generation-priority-title");
  dialogo.setAttribute("aria-describedby", "generation-priority-description");
  dialogo.innerHTML = `
    <div class="build-action-heading">
      <h2 id="generation-priority-title" class="font-1-l" tabindex="-1">Antes de gerar sua build</h2>
      <button type="button" class="build-action-close" data-priority-cancel aria-label="Fechar confirmação">×</button>
    </div>
    <p id="generation-priority-description">Escolha a prioridade da montagem. Seu limite de orçamento continua o mesmo.</p>
    <form class="generation-priority-form">
      <fieldset>
        <legend>O que você prefere priorizar?</legend>
        <div class="generation-priority-options">
          ${prioridades.map(([valor, titulo, descricao]) => `
            <label class="generation-priority-option">
              <input type="radio" name="prioridade_montagem" value="${valor}" required ${valorAtual === valor ? "checked" : ""}>
              <span><strong>${titulo}</strong><span>${descricao}</span></span>
            </label>`).join("")}
        </div>
      </fieldset>
      <div class="generation-priority-actions">
        <button type="button" class="btn-ghost" data-priority-cancel aria-label="Voltar às respostas do formulário">Voltar às respostas</button>
        <button type="submit" class="btn-primary-form" aria-label="Gerar build com a prioridade escolhida" ${prioridadeMontagemValida(valorAtual) ? "" : "disabled"}>Gerar build</button>
      </div>
    </form>`;

  return new Promise(resolve => {
    let escolha = null;
    const form = dialogo.querySelector("form");
    form.addEventListener("change", () => {
      form.querySelector('[type="submit"]').disabled = !prioridadeMontagemValida(new FormData(form).get("prioridade_montagem"));
    });
    form.addEventListener("submit", evento => {
      evento.preventDefault();
      const valor = new FormData(form).get("prioridade_montagem");
      if (!prioridadeMontagemValida(valor)) return;
      escolha = valor;
      dialogo.close();
    });
    dialogo.querySelectorAll("[data-priority-cancel]").forEach(botao => botao.addEventListener("click", () => dialogo.close()));
    dialogo.addEventListener("click", evento => {
      const limites = dialogo.getBoundingClientRect();
      if (evento.target === dialogo && (evento.clientX < limites.left || evento.clientX > limites.right || evento.clientY < limites.top || evento.clientY > limites.bottom)) dialogo.close();
    });
    dialogo.addEventListener("close", () => {
      dialogo.remove();
      if (anterior?.isConnected) anterior.focus({preventScroll:true});
      resolve(escolha);
    }, {once:true});
    document.body.append(dialogo);
    dialogo.showModal();
    dialogo.querySelector("h2").focus({preventScroll:true});
  });
}
