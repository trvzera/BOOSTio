import {
  perguntasPc,
  perguntasNotebook,
  pecasPreview,
  novasRespostasPreview,
} from "../experimentos/formularios/perguntas.js";
import { perfisUso } from "../experimentos/formularios/objetivos.js";
import { carregarCatalogoFormulario } from "../experimentos/formularios/catalogo.js";
import {
  avaliarOrcamentoPreview,
  validarEtapaPreview,
  validarRevisaoPreview,
  resumoFormularioPreview,
  montarPlanoPreview,
  ErroGeracaoFormulario,
  identificarErroFormulario,
} from "../experimentos/formularios/regras.js";
import { painelFormularioHtml } from "../experimentos/formularios/painel.js";
import { redeHtml } from "../experimentos/formularios/campos.js";
import { prepararAparenciaPreview } from "../experimentos/formularios/aparencia.js";
import { redeFormulario } from "../build/rede.js";
import { moeda, htmlSeguro as h } from "../build/catalogo.js";
import { ajustarGuiasConhecimento } from "../conta/preferencias-uso.js";
import { iniciarIcones } from "../components/ui.js";

// Somente laboratório: sem geração real, escrita na conta ou import do fluxo oficial.
function iniciarFormularioTeste(raiz, tipo) {
  const perguntas = tipo === "pc" ? perguntasPc : perguntasNotebook,
    id = (chave) => "preview-form-" + tipo + "-" + chave;
  let respostas = novasRespostasPreview(tipo),
    etapa = 0,
    catalogo;
  const contexto = () => ({ respostas, tipo, id, catalogo });
  function atualizarAvanco() {
    const problema =
      etapa === perguntas.length
        ? validarRevisaoPreview(tipo, respostas)
        : validarEtapaPreview(tipo, perguntas[etapa], respostas, catalogo);
    const proximo = raiz.querySelector("[data-form-next]");
    proximo.disabled = Boolean(problema);
    if (problema) proximo.dataset.disabledReason = problema;
    else delete proximo.dataset.disabledReason;
    const feedback = raiz.querySelector("[data-form-feedback]");
    if (feedback.textContent !== problema) feedback.textContent = problema;
    const d = avaliarOrcamentoPreview(tipo, respostas),
      reserva = raiz.querySelector("[data-allocation]"),
      divisao = raiz.querySelector("[data-budget-split]");
    if (reserva)
      reserva.textContent = Number.isFinite(d.perifericos)
        ? "Até " +
          moeda(d.perifericos) +
          " para acessórios · até " +
          moeda(d.pc) +
          " para o computador."
        : "Informe uma porcentagem inteira de 1 a 99.";
    if (divisao)
      divisao.textContent = d.valido
        ? "Até " +
          moeda(d.pc) +
          " para o computador e " +
          moeda(d.perifericos) +
          " para acessórios."
        : d.mensagem;
    raiz
      .querySelectorAll("[data-budget]")
      .forEach((b) =>
        b.setAttribute(
          "aria-pressed",
          String(Number(b.dataset.budget) === respostas.orcamento),
        ),
      );
    const resumo = raiz.querySelector("[data-preview-answers]");
    if (resumo)
      resumo.textContent = JSON.stringify(
        {
          ...resumoFormularioPreview(tipo, respostas),
          ...(!validarRevisaoPreview(tipo, respostas) && d.valido
            ? { plano: montarPlanoPreview(tipo, respostas) }
            : {}),
        },
        null,
        2,
      );
  }
  function mostrarErro(erro) {
    const e = identificarErroFormulario(erro),
      p = perguntas.find((q) => q.chave === e.etapa),
      alvo = raiz.querySelector("[data-form-error]");
    alvo.hidden = false;
    alvo.innerHTML =
      '<h4 tabindex="-1">Precisamos revisar ' +
      h(p?.etapa.toLowerCase() || "a revisão final") +
      "</h4><p>" +
      h(e.message) +
      '</p><p class="test-form-help">' +
      h(
        p?.titulo ||
          "A falha ocorreu na geração; a origem específica não foi confirmada.",
      ) +
      '</p><button type="button" class="btn-secondary" data-form-revisit="' +
      h(p?.chave || "revisao") +
      '" aria-label="Rever a pergunta relacionada ao erro">Rever ' +
      h(p?.etapa.toLowerCase() || "preferências") +
      "</button>";
    alvo.querySelector("h4").focus();
  }
  function renderizar({ focar = false } = {}) {
    raiz.innerHTML = painelFormularioHtml(contexto(), perguntas, etapa);
    prepararAparenciaPreview(raiz, respostas, id);
    iniciarIcones(raiz);
    ajustarGuiasConhecimento(raiz);
    atualizarAvanco();
    const form = raiz.querySelector("form");
    form.addEventListener("submit", (evento) => {
      evento.preventDefault();
      if (!form.reportValidity()) return;
      try {
        const etapas =
          etapa === perguntas.length ? perguntas : [perguntas[etapa]];
        for (const p of etapas) {
          const problema = validarEtapaPreview(tipo, p, respostas, catalogo);
          if (problema)
            throw new ErroGeracaoFormulario("resposta", p.chave, problema);
        }
        if (etapa < perguntas.length) {
          etapa++;
          renderizar({ focar: true });
          return;
        }
        const plano = montarPlanoPreview(tipo, respostas),
          resultado = raiz.querySelector("[data-form-result]");
        resultado.hidden = false;
        resultado.innerHTML =
          '<h4 tabindex="-1">Prévia concluída</h4><p>As respostas e as regras estão prontas para avaliação. Nenhuma chamada à IA foi enviada, nenhuma build foi criada e nada foi salvo na conta.</p><details class="test-form-summary"><summary>Ver dados e instruções do teste</summary><pre></pre></details>';
        resultado.querySelector("pre").textContent = JSON.stringify(
          { ...resumoFormularioPreview(tipo, respostas), plano },
          null,
          2,
        );
        resultado.querySelector("h4").focus();
      } catch (e) {
        mostrarErro(e);
      }
    });
    form.addEventListener("input", (evento) => {
      const e = evento.target;
      if (e.dataset.number) respostas[e.dataset.number] = e.valueAsNumber;
      if (e.hasAttribute("data-preview-budget-range")) {
        respostas.orcamento = e.valueAsNumber;
        form.querySelector('[data-number="orcamento"]').value = e.value;
      }
      if (e.dataset.number === "orcamento") {
        const range = form.querySelector("[data-preview-budget-range]");
        if (range) {
          range.max = Math.max(20000, e.valueAsNumber || 20000);
          range.value = e.value;
        }
      }
      if (e.dataset.model) respostas.pecasDetalhes[e.dataset.model] = e.value;
      atualizarAvanco();
    });
    form.addEventListener("change", (evento) => {
      const e = evento.target,
        chave = e.dataset.answer;
      if (e.dataset.network) {
        const k = e.dataset.network,
          v =
            k === "possuiAcessorio"
              ? e.value === "confirmar"
                ? null
                : e.value === "true"
              : k === "comprimentoCaboM"
                ? e.value
                  ? Number(e.value)
                  : null
                : e.value;
        respostas.rede = redeFormulario({
          ...respostas.rede,
          [k]: v,
          ...(k === "tipo" ? { comprimentoCaboM: null } : {}),
        });
        const campo = raiz.querySelector("[data-preview-network]");
        campo.innerHTML = redeHtml(contexto());
        atualizarAvanco();
        return;
      }
      if (e.dataset.select) respostas[e.dataset.select] = e.value;
      if (e.hasAttribute("data-webcam")) {
        respostas.incluirWebcam = e.checked;
        respostas.webcamAlterada = true;
        renderizar();
        return;
      }
      if (chave) {
        if (e.type === "checkbox") {
          let lista = new Set(respostas[chave]);
          e.checked ? lista.add(e.value) : lista.delete(e.value);
          if (chave === "pecas") {
            if (e.value === "nenhuma" && e.checked)
              lista = new Set(["nenhuma"]);
            else lista.delete("nenhuma");
          }
          respostas[chave] = [...lista];
          if (chave === "pecas")
            pecasPreview.forEach(([v]) => {
              if (!lista.has(v)) delete respostas.pecasDetalhes[v];
            });
          if (chave === "perifericosProprios" && !e.checked)
            delete respostas.pecasDetalhes[e.value];
        } else respostas[chave] = e.value;
        if (chave === "objetivo") {
          if (tipo === "pc" && !respostas.webcamAlterada)
            respostas.incluirWebcam = e.value === "reunioes";
          raiz.querySelector("[data-preview-help-copy]").textContent =
            perfisUso[e.value].prioridade;
        }
        if (chave === "perifericos" && tipo === "pc") {
          if (e.value === "sem-perifericos") respostas.incluirWebcam = false;
          else if (
            respostas.objetivo === "reunioes" &&
            !respostas.webcamAlterada
          )
            respostas.incluirWebcam = true;
        }
        if (
          [
            "pecas",
            "perifericos",
            "perifericosProprios",
            "extrasNotebook",
          ].includes(chave)
        ) {
          const v = e.value;
          renderizar();
          [...raiz.querySelectorAll("[data-answer]")]
            .find(
              (input) => input.dataset.answer === chave && input.value === v,
            )
            ?.focus({ preventScroll: true });
          return;
        }
      }
      atualizarAvanco();
    });
    if (focar) raiz.querySelector("h3").focus();
  }
  raiz.addEventListener("click", (evento) => {
    const b = evento.target.closest("button");
    if (!b || b.disabled) return;
    if (b.hasAttribute("data-form-reset")) {
      respostas = novasRespostasPreview(tipo);
      etapa = 0;
      renderizar({ focar: true });
    }
    if (b.hasAttribute("data-form-back")) {
      etapa--;
      renderizar({ focar: true });
    }
    if (b.hasAttribute("data-form-step")) {
      etapa = Number(b.dataset.formStep);
      renderizar({ focar: true });
    }
    if (b.dataset.formRevisit) {
      const i = perguntas.findIndex((p) => p.chave === b.dataset.formRevisit);
      etapa = i < 0 ? perguntas.length : i;
      renderizar({ focar: true });
    }
    if (b.dataset.budget) {
      const input = raiz.querySelector('[data-number="orcamento"]');
      input.value = b.dataset.budget;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  });
  raiz.addEventListener("boostio:form-preview-error", (e) =>
    mostrarErro(e.detail),
  );
  renderizar();
  void carregarCatalogoFormulario()
    .then((d) => {
      catalogo = d;
      if (raiz.querySelector("[data-preview-network]"))
        raiz.querySelector("[data-preview-network]").innerHTML =
          redeHtml(contexto());
      atualizarAvanco();
    })
    .catch(() => {});
}
document
  .querySelectorAll("[data-form-preview]")
  .forEach((raiz) => iniciarFormularioTeste(raiz, raiz.dataset.formPreview));
