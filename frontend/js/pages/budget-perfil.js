import { planejamentoLocal, salvarPlanejamento } from "../build/planejamento.js";
import { moeda } from "../build/catalogo.js";

document.addEventListener("DOMContentLoaded",() => {
  const form = document.querySelector("#budget-profile-form");
  if (!form) return;
  const input = form.querySelector("#profile-budget"), usar = form.querySelector("#profile-budget-use");
  const feedback = form.querySelector("#profile-budget-feedback");
  const salvo = planejamentoLocal();
  input.value = salvo.budget ?? "";
  usar.checked = salvo.usarBudget;
  form.addEventListener("submit",evento => {
    evento.preventDefault();
    if (!form.reportValidity()) return;
    try {
      const budget = input.value.trim() === "" ? null : Number(input.value);
      if (usar.checked && (budget == null || budget <= 0)) throw new Error("Informe um budget maior que zero para usá-lo nas novas configurações.");
      salvarPlanejamento({budget,usarBudget:usar.checked});
      feedback.textContent = budget == null ? "Budget removido deste navegador." : moeda(budget) + " registrados neste navegador. O valor não é descontado automaticamente.";
      feedback.dataset.tone = "success";
    } catch (erro) { feedback.textContent = erro.message; feedback.dataset.tone = "error"; }
  });
});
