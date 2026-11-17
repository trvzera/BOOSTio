import { htmlSeguro as h } from "../build/catalogo.js";
import { niveisHardware } from "../conta/preferencias-uso.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";

const passosCurtos = [
  ["Uma experiência no seu ritmo", "Qual é seu nível de conhecimento sobre peças de computador? A escolha só muda as explicações: todas as ferramentas continuam disponíveis."],
  ["Duas maneiras de chegar ao seu PC", "Na montagem inteligente, você informa como pretende usar o computador e quanto pode gastar. Na manual, escolhe cada peça. Nos dois caminhos, pode revisar tudo antes de comprar."],
  ["Seu orçamento acompanha suas escolhas", "Separe um valor para o PC, os periféricos e o frete. Confira o total e os avisos: quando faltarem informações de uma peça, a BOOSTio indicará o que ainda precisa ser confirmado."],
];
const passosGuiados = [
  ["budget", "Comece pelo seu orçamento", "Registre quanto pode investir. Esse valor ajuda a planejar a montagem e as próximas melhorias. Você pode ajustá-lo depois."],
  ["montar", "Escolha como quer montar", "O formulário ajuda a encontrar as peças para seu uso. Se preferir escolher por conta própria, use a montagem manual."],
  ["compatibilidade", "Entenda os avisos da sua build", "Aqui você acompanha conflitos e pontos que ainda precisam de confirmação. Ter todas as peças selecionadas não garante que todos os encaixes foram verificados."],
  ["melhorias", "Planeje o próximo upgrade", "Defina o valor disponível e compare peças superiores às atuais. A prévia mostra o que muda; só aplique depois de revisar."],
];

export function abrirPreviaTutorial(tipo,origem = document.activeElement) {
  if (!["curto","guiado"].includes(tipo) || document.querySelector(".test-onboarding-dialog[open]")) return;
  const guiado = tipo === "guiado", passos = guiado ? passosGuiados : passosCurtos;
  let passo = 0, nivel = "";
  const dialogo = document.createElement("dialog");
  dialogo.className = "onboarding-dialog test-onboarding-dialog" + (guiado ? " test-onboarding-guided" : "");
  dialogo.setAttribute("aria-labelledby","tutorial-preview-title");
  dialogo.setAttribute("aria-describedby","tutorial-preview-description");
  function desenhar() {
    const [alvo,titulo,texto] = guiado ? passos[passo] : [null,...passos[passo]];
    const radio = (valor,nome,descricao) => '<label class="onboarding-level ui-check"><input type="radio" name="preview-knowledge" value="'+h(valor)+'"'+(nivel === valor ? ' checked' : '')+'>'+iconeAnimado("circledot")+'<span><strong>'+h(nome)+'</strong><span>'+h(descricao)+'</span></span></label>';
    const visual = guiado ? '<div class="test-tour-site" aria-label="Interface demonstrativa, sem dados da sua conta"><div class="test-tour-header"><strong>BOOSTio</strong><span>Prévia do perfil</span></div><div class="test-tour-grid">'+[
      ["budget","Seu orçamento","Definir orçamento"],
      ["montar","Criar uma build","Inteligente ou manual"],
      ["compatibilidade","Verificações da build","Conflitos e pendências"],
      ["melhorias","Buscar melhorias","Comparar trocas"],
    ].map(([id,nome,descricao]) => '<div class="test-tour-target'+(alvo === id ? ' is-highlighted' : '')+'"'+(alvo === id ? ' aria-current="step"' : '')+'><span>'+h(nome)+'</span><strong>'+h(descricao)+'</strong></div>').join("")+'</div><p>Exemplo de interface · nenhuma build real será alterada.</p></div>' : '';
    const opcoes = !guiado && passo === 0 ? '<fieldset class="onboarding-levels"><legend class="sr-only">Nível de conhecimento, apenas nesta prévia</legend>'+niveisHardware.map(([valor,nome,descricao]) => radio(valor,nome,descricao)).join("")+radio("","Não tenho preferência","Sem explicações extras para iniciantes.")+'</fieldset>' : !guiado && passo === 1 ? '<div class="test-onboarding-routes"><article>'+iconeAnimado("handsparkle")+'<h3>Montagem inteligente</h3><p>Você conta o que precisa. A BOOSTio sugere as peças.</p></article><article>'+iconeAnimado("normalhand")+'<h3>Montagem manual</h3><p>Você escolhe as peças e acompanha as verificações.</p></article></div>' : '';
    dialogo.innerHTML = '<div class="onboarding-top"><span class="onboarding-progress">Prévia '+(guiado ? 'B · guia visual' : 'A · apresentação')+' · '+(passo+1)+' de '+passos.length+'</span><button type="button" class="build-action-close" data-tutorial-action="fechar" aria-label="Fechar prévia do tutorial">×</button></div><div class="onboarding-content">'+visual+'<div class="test-tour-explanation"><h2 id="tutorial-preview-title" tabindex="-1">'+h(titulo)+'</h2><p id="tutorial-preview-description">'+h(texto)+'</p>'+opcoes+'</div></div><div class="onboarding-actions"><button type="button" class="onboarding-skip" data-tutorial-action="fechar" aria-label="Pular prévia do tutorial">Pular prévia</button><div class="onboarding-steps">'+(passo ? '<button type="button" class="btn-secondary" data-tutorial-action="voltar" aria-label="Voltar ao passo anterior">'+iconeAnimado("arrow","back")+'Voltar</button>' : '')+'<button type="button" class="btn-primary" data-tutorial-action="avancar" aria-label="Avançar ou concluir a prévia">'+(passo === passos.length-1 ? 'Concluir prévia' : 'Continuar')+iconeAnimado("arrow")+'</button></div></div>';
    iniciarIcones(dialogo);
    dialogo.querySelector("h2").focus({preventScroll:true});
    dialogo.querySelector(".onboarding-content").scrollTop = 0;
  }
  dialogo.addEventListener("change",evento => { if (evento.target.name === "preview-knowledge") nivel = evento.target.value; });
  dialogo.addEventListener("click",evento => {
    const acao = evento.target.closest("[data-tutorial-action]")?.dataset.tutorialAction;
    if (acao === "fechar" || acao === "avancar" && passo === passos.length-1) { dialogo.close(); return; }
    if (acao === "avancar") passo++;
    else if (acao === "voltar" && passo > 0) passo--;
    else return;
    desenhar();
  });
  dialogo.addEventListener("close",() => { dialogo.remove(); if (origem?.isConnected) origem.focus({preventScroll:true}); },{once:true});
  document.body.append(dialogo); dialogo.showModal(); desenhar();
}

document.querySelectorAll("[data-preview-onboarding]").forEach(botao => {
  botao.addEventListener("click",() => abrirPreviaTutorial(botao.dataset.previewOnboarding,botao));
});
