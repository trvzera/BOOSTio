import { htmlSeguro as h } from "./catalogo.js";
import { resumirCompatibilidade } from "./resumo-compatibilidade.js";
let aberto, fechamentoExternoIniciado = false;

export function indicadorBuild(resultado,id) {
  const resumo = resumirCompatibilidade(resultado);
  const problemas = resumo.erros.length + resumo.faltam.length + resumo.avisos.length;
  const diagnostico = resultado.compatibilidade;
  const desconhecidas = Array.isArray(diagnostico?.naoVerificado) ? diagnostico.naoVerificado : [];
  const tom = resumo.erros.length ? "erro" : problemas || desconhecidas.length ? "aviso" : "ok";
  const nome = tom === "erro" ? "Informações da build: incompatibilidades" : tom === "aviso" ? "Informações da build: pendências" : "Informações e orientações da build";
  const lista = (itens, classe) => itens.length ? '<ul class="compatibility-messages">' + itens.map(v => '<li class="' + classe + '">' + h(v) + '</li>').join('') + '</ul>' : '';
  const avaliacao = diagnostico ? '<p class="compatibility-assessment" data-status="' + h(diagnostico.status) + '">' + h(diagnostico.rotulo) + '</p>' : '';
  const conferencias = resumo.grupos.length ? '<details class="compatibility-unknown compatibility-section"><summary>Conferir antes de comprar <span class="compatibility-count">' + resumo.grupos.length + '</span></summary>' +
    '<p class="compatibility-scope">' + (resumo.verificacoes ? resumo.verificacoes + (resumo.verificacoes === 1 ? ' verificação agrupada por assunto.' : ' verificações agrupadas por assunto.') : 'Informações que precisam de confirmação.') + '</p>' +
    resumo.grupos.map(g => '<details class="compatibility-topic"><summary>' + h(g.titulo) + '</summary><p>' + h(g.resumo) + '</p><ul>' + g.mensagens.map(v => '<li class="tip">' + h(v) + '</li>').join('') + '</ul></details>').join('') + '</details>' : '';
  const orientacoes = resumo.dicas.length || diagnostico?.aviso ? '<details class="compatibility-section compatibility-guidance"><summary>Dicas e limites da avaliação</summary>' +
    lista(resumo.dicas, 'tip') + (diagnostico?.aviso ? '<p class="compatibility-scope">' + h(diagnostico.aviso) + '</p>' : '') + '</details>' : '';
  return '<div class="compatibility-popover build-indicator ' + tom + '">' +
    '<button type="button" class="compatibility-trigger" aria-label="' + nome + '" aria-controls="' + h(id) + '" aria-expanded="false"></button>' +
      '<div id="' + h(id) + '" class="compatibility-details glass-card" role="region" aria-label="Compatibilidade da build" aria-hidden="true" inert>' +
      '<h3>' + (problemas ? 'O que precisa de atenção' : 'Verificações e dicas') + '</h3>' + avaliacao +
      lista(resumo.erros, 'error') + (resumo.faltam.length ? lista(['Falta adicionar: ' + resumo.faltam.join(', ') + '.'], 'warning') : '') + lista(resumo.avisos, 'warning') +
      conferencias + orientacoes + (!problemas && !resumo.grupos.length && !diagnostico ? '<p class="compatibility-scope">Sem conflitos nas verificações disponíveis. Isso não confirma especificações ausentes.</p>' : '') + '</div></div>';
}
export function iniciarIndicadores(raiz) {
  if (!fechamentoExternoIniciado) {
    fechamentoExternoIniciado = true;
    document.addEventListener("pointerdown",e => { if (aberto && !aberto.box.contains(e.target)) aberto.fechar(); });
    window.addEventListener("resize",() => aberto?.fechar());
  }
  raiz.querySelectorAll(".build-indicator").forEach(box => {
    const botao = box.querySelector("button"), painel = box.querySelector(".compatibility-details");
    if (!botao) return;
    let fixo = false;
    const mostrar = aberto => {
      box.toggleAttribute("data-open",aberto);
      botao.setAttribute("aria-expanded",String(aberto));
      painel.setAttribute("aria-hidden",String(!aberto)); painel.inert = !aberto;
      if (aberto) {
        painel.style.left = '0px'; painel.style.right = 'auto';
        painel.style.marginRight = '0px';
        const ancora = botao.getBoundingClientRect();
        const abaixo = innerHeight - ancora.bottom - 26, acima = ancora.top - 26;
        const inverter = abaixo < 180 && acima > abaixo;
        box.toggleAttribute('data-above',inverter);
        painel.style.top = inverter ? 'auto' : 'calc(100% + 10px)';
        painel.style.bottom = inverter ? 'calc(100% + 10px)' : 'auto';
        painel.style.maxHeight = Math.max(80,Math.min(innerHeight * .7,inverter ? acima : abaixo)) + 'px';
        const rect = painel.getBoundingClientRect();
        const ajuste = rect.left < 16 ? 16 - rect.left : rect.right > innerWidth - 16 ? innerWidth - 16 - rect.right : 0;
        painel.style.left = ajuste + 'px';
      }
    };
    const fechar = () => { fixo = false; mostrar(false); };
    const abrir = () => { if (aberto?.box !== box) aberto?.fechar(); aberto = {box,fechar}; mostrar(true); };
    box.addEventListener("pointerenter",e => { if (e.pointerType !== "touch") abrir(); });
    box.addEventListener("pointerleave",() => { if (!fixo && !box.contains(document.activeElement)) mostrar(false); });
    box.addEventListener("focusin",abrir);
    box.addEventListener("focusout",e => { if (!box.contains(e.relatedTarget)) { fixo = false; mostrar(false); } });
    botao.onclick = e => { e.stopPropagation(); fixo = !fixo; if (fixo) abrir(); else mostrar(false); };
    box.addEventListener("keydown",e => {
      if (e.key === "Escape") { e.stopPropagation(); fixo = false; botao.focus(); mostrar(false); }
    });
  });
}
