import { htmlSeguro as h } from "../../build/catalogo.js";
import { iconeAnimado } from "../../components/ui.js";
import { perfisUso } from "./objetivos.js";
import { camposHtml, revisaoHtml } from "./campos.js";

export function painelFormularioHtml(ctx, perguntas, etapa) {
  const revisao = etapa === perguntas.length,
    nome = ctx.tipo === "pc" ? "Desktop" : "Notebook";
  const p = revisao
    ? {
        titulo: "Vamos conferir suas preferências?",
        descricao:
          "Revise as regras e conclua esta simulação. Nenhuma chamada à IA será enviada.",
        chave: "revisao",
      }
    : perguntas[etapa];
  return (
    '<div class="test-form-shell"><div class="test-form-toolbar"><span>' +
    nome +
    ' · prévia independente</span><button type="button" class="btn-ghost" data-form-reset aria-label="Reiniciar a prévia de ' +
    nome.toLowerCase() +
    '">Reiniciar prévia</button></div>' +
    '<nav class="test-form-steps" aria-label="Etapas da prévia de ' +
    nome.toLowerCase() +
    '">' +
    [...perguntas, { etapa: "Revisão" }]
      .map(
        (q, i) =>
          '<button type="button" data-form-step="' +
          i +
          '" aria-label="Ir para a etapa ' +
          (i + 1) +
          ": " +
          h(q.etapa) +
          '"' +
          (i === etapa ? ' aria-current="step"' : "") +
          (i > etapa ? " disabled" : "") +
          "><span>" +
          String(i + 1).padStart(2, "0") +
          "</span>" +
          h(q.etapa) +
          "</button>",
      )
      .join("") +
    "</nav>" +
    '<div class="test-form-layout"><div class="test-form-intro"><span class="question-tag font-1-xs">Etapa ' +
    (etapa + 1) +
    " de " +
    (perguntas.length + 1) +
    '</span><h3 class="font-1-xl" id="' +
    ctx.id("question-title") +
    '" tabindex="-1">' +
    h(p.titulo) +
    "</h3><p>" +
    h(p.descricao) +
    "</p>" +
    (p.chave === "objetivo"
      ? '<div class="test-form-help-card"><h4>O que muda na escolha</h4><p data-preview-help-copy>' +
        h(
          perfisUso[ctx.respostas.objetivo]?.prioridade ||
            "Escolha um uso para entender o que será priorizado.",
        ) +
        "</p></div>"
      : "") +
    "</div>" +
    '<form class="test-form-answers" aria-labelledby="' +
    ctx.id("question-title") +
    '"><div class="test-form-scroll" tabindex="0" role="region" aria-label="Respostas desta etapa">' +
    (revisao ? revisaoHtml(ctx) : camposHtml(p, ctx)) +
    '</div><p class="test-form-feedback" role="status" aria-live="polite" data-form-feedback></p><div class="test-form-navigation"><button type="button" class="btn-ghost" data-form-back aria-label="Voltar à etapa anterior da prévia"' +
    (!etapa ? " disabled" : "") +
    ">" +
    iconeAnimado("arrow", "back") +
    'Voltar</button><button type="submit" class="btn-primary" data-form-next aria-label="' +
    (revisao
      ? "Concluir prévia sem gerar build"
      : "Avançar para a próxima etapa") +
    '">' +
    (revisao ? "Concluir prévia" : "Avançar") +
    iconeAnimado("arrow") +
    '</button></div></form></div><section class="test-form-result" data-form-result hidden aria-live="polite"></section><section class="test-form-error" data-form-error hidden role="alert"></section></div>'
  );
}
