import { htmlSeguro as h } from "../build/catalogo.js";
import { niveisHardware } from "../conta/preferencias-uso.js";
import { iconeAnimado } from "./ui.js";

export const passosApresentacao = [
  ["Vamos conhecer a BOOSTio", "Neste tutorial você vai ver como montar um PC, acompanhar o orçamento e testar sua build. Para começar, qual é seu nível de conhecimento sobre peças de computador?"],
  ["Como funciona a montagem", "Ao abrir “Montar um PC”, você encontrará dois caminhos. Veja como cada um funciona."],
  ["Seu orçamento acompanha suas escolhas", "Separe um valor para o PC, os periféricos e o frete. Confira o total e os avisos: quando faltarem informações de uma peça, a BOOSTio indicará o que ainda precisa ser confirmado."],
];

export function conteudoApresentacao(passo,nivel,{previa = false} = {}) {
  const prefixo = previa ? "tutorial-preview" : "onboarding";
  const [titulo,texto] = passosApresentacao[passo];
  const radio = (valor,nome,descricao) => '<label class="onboarding-level ui-check"><input type="radio" name="'+prefixo+'-level" value="'+h(valor)+'"'+((nivel || "") === valor ? ' checked' : '')+'>'+iconeAnimado("circledot")+'<span><strong>'+h(nome)+'</strong><span>'+h(descricao)+'</span></span></label>';
  const opcoes = passo === 0 ? '<fieldset class="onboarding-levels"><legend class="sr-only">Escolha seu conhecimento sobre peças de computador para continuar</legend>'+niveisHardware.map(([valor,nome,descricao]) => radio(valor,nome,descricao)).join("")+'</fieldset><p>Escolha uma opção para continuar. Se preferir decidir depois, pule o tutorial: as dicas extras para iniciantes ficam ocultas até você escolher um nível.</p>'
    : passo === 1 ? '<ul class="onboarding-routes"><li>'+iconeAnimado("handsparkle")+'<div><h3>Montagem inteligente</h3><p>Informe como vai usar o PC e quanto pode gastar. A BOOSTio sugere as peças para você revisar.</p></div></li><li>'+iconeAnimado("normalhand")+'<div><h3>Montagem manual</h3><p>Escolha as peças uma por uma e acompanhe as verificações de compatibilidade.</p></div></li></ul><p class="onboarding-requirements">Para criar uma build, confirme seu e-mail. Você pode manter até três builds salvas na conta. Depois de montar, use “Testar build” para consultar o desempenho esperado em jogos e no Blender, conforme o suporte às peças e os dados disponíveis.</p>'
      : '<ul class="onboarding-list"><li><h3>Compare antes de comprar</h3><p>Confira as peças, o orçamento e as verificações de compatibilidade. Um dado não informado não significa que a peça é compatível.</p></li><li><h3>A montagem continua no seu perfil</h3><p>Em Minhas builds, você pode comparar, buscar melhorias e compartilhar as públicas. Nas configurações, ajuste seu orçamento ou reveja este tutorial.</p></li></ul>';
  return '<h2 id="'+prefixo+'-title" tabindex="-1">'+h(titulo)+'</h2><p id="'+prefixo+'-description">'+h(texto)+'</p>'+opcoes;
}
