// Mantém o input numérico nativo e acrescenta controles visíveis em qualquer navegador.
export function ajustarNumero(valor, {minimo = -Infinity, maximo = Infinity, passo = 1, direcao = 1} = {}) {
  const atual = valor !== "" && Number.isFinite(Number(valor)) ? Number(valor) : 0;
  const incremento = Number.isFinite(passo) && passo > 0 ? passo : 1;
  const proximo = Number((atual + (direcao < 0 ? -incremento : incremento)).toFixed(6));
  return Math.max(minimo,Math.min(maximo,proximo));
}

export function iniciarControlesNumericos(raiz) {
  raiz.querySelectorAll('input[type="number"]').forEach(input => {
    if (input.closest(".form-number-stepper")) return;
    const grupo = document.createElement("div");
    grupo.className = "form-number-stepper";
    input.before(grupo); grupo.append(input);
    const nome = input.labels?.[0]?.textContent.trim() || input.getAttribute("aria-label") || "valor";
    const minimo = () => input.min === "" ? -Infinity : Number(input.min);
    const maximo = () => input.max === "" ? Infinity : Number(input.max);
    const passo = Number(input.dataset.numberStep || (input.step === "any" ? 1 : input.step) || 1);
    const botoes = [-1,1].map(direcao => {
      const botao = document.createElement("button");
      botao.type = "button";
      botao.className = "number-step-button";
      botao.dataset.numberDirection = String(direcao);
      botao.setAttribute("aria-label",(direcao < 0 ? "Diminuir " : "Aumentar ") + nome);
      botao.setAttribute("aria-controls",input.id);
      botao.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + (direcao < 0 ? 'm6 9 6 6 6-6' : 'm6 15 6-6 6 6') + '"/></svg>';
      botao.addEventListener("click",() => {
        if (input.disabled || input.readOnly) return;
        input.value = ajustarNumero(input.value,{minimo:minimo(),maximo:maximo(),passo,direcao});
        input.dispatchEvent(new Event("input",{bubbles:true}));
      });
      grupo.append(botao);
      return botao;
    });
    const atualizar = () => {
      const valor = input.valueAsNumber;
      botoes.forEach((botao,indice) => {
        botao.disabled = input.disabled || input.readOnly || Number.isFinite(valor) && (indice === 0 ? valor <= minimo() : valor >= maximo());
        botao.dataset.disabledReason = input.disabled || input.readOnly ? "Este campo não pode ser alterado agora." : indice === 0 ? "O valor mínimo foi atingido." : "O valor máximo foi atingido.";
      });
    };
    input.addEventListener("input",atualizar);
    input.addEventListener("change",atualizar);
    atualizar();
  });
}
