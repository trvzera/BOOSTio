import { htmlSeguro as h } from "../build/catalogo.js";
import { niveisHardware } from "../conta/preferencias-uso.js";
import { iconeAnimado } from "./ui.js";

export const passosApresentacao = [
  ["Uma experiência no seu ritmo", "Qual é seu nível de conhecimento sobre peças de computador? A escolha só muda as explicações: todas as ferramentas continuam disponíveis."],
  ["Duas maneiras de chegar ao seu PC", "Na montagem inteligente, você informa como pretende usar o computador e quanto pode gastar. Na manual, escolhe cada peça. Nos dois caminhos, pode revisar tudo antes de comprar."],
  ["Seu orçamento acompanha suas escolhas", "Separe um valor para o PC, os periféricos e o frete. Confira o total e os avisos: quando faltarem informações de uma peça, a BOOSTio indicará o que ainda precisa ser confirmado."],
];

export function conteudoApresentacao(passo,nivel,{previa = false} = {}) {
  const prefixo = previa ? "tutorial-preview" : "onboarding";
  const [titulo,texto] = passosApresentacao[passo];
  const radio = (valor,nome,descricao) => '<label class="onboarding-level ui-check"><input type="radio" name="'+prefixo+'-level" value="'+h(valor)+'"'+((nivel || "") === valor ? ' checked' : '')+'>'+iconeAnimado("circledot")+'<span><strong>'+h(nome)+'</strong><span>'+h(descricao)+'</span></span></label>';
  const opcoes = passo === 0 ? '<fieldset class="onboarding-levels"><legend class="sr-only">Escolha seu conhecimento sobre peças de computador para continuar</legend>'+niveisHardware.map(([valor,nome,descricao]) => radio(valor,nome,descricao)).join("")+'</fieldset><p>Escolha uma opção para continuar. Se preferir decidir depois, pule o tutorial: as dicas extras para iniciantes ficam ocultas até você escolher um nível.</p>'
    : passo === 1 ? '<div class="onboarding-routes"><article>'+iconeAnimado("handsparkle")+'<h3>Montagem inteligente</h3><p>Você conta o que precisa. A BOOSTio sugere as peças.</p></article><article>'+iconeAnimado("normalhand")+'<h3>Montagem manual</h3><p>Você escolhe as peças e acompanha as verificações.</p></article></div><p class="onboarding-requirements">Para criar uma build, confirme seu e-mail. Você pode manter até três builds salvas na conta. Depois de montar, use “Testar build” para consultar o desempenho esperado em jogos e no Blender, conforme o suporte às peças e os dados disponíveis.</p>'
      : '<ul class="onboarding-list"><li><h3>Compare antes de comprar</h3><p>Confira as peças, o orçamento e as verificações de compatibilidade. Um dado não informado não significa que a peça é compatível.</p></li><li><h3>A montagem continua no seu perfil</h3><p>Em Minhas builds, você pode comparar, buscar melhorias e compartilhar as públicas. Nas configurações, ajuste seu orçamento ou reveja este tutorial.</p></li></ul>';
  return '<h2 id="'+prefixo+'-title" tabindex="-1">'+h(titulo)+'</h2><p id="'+prefixo+'-description">'+h(texto)+'</p>'+opcoes;
}
