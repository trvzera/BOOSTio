import test from "node:test";
import assert from "node:assert/strict";
import { avaliarOrcamentoGeracao } from "../js/build/orcamento-formulario.js";
import { feedbackGeracao } from "../js/build/generation-feedback.js";
import { fetchComErro, orientacaoGeracaoSegura } from "../js/api/_shared/fetchComErro.js";

test("geração exige teto mínimo do PC e reserva mínima, sem impor gasto mínimo",() => {
  for(const [total,pct,motivo,minimo] of [[1,0,"orcamento",2000],[1999.99,0,"orcamento",2000],[2000,20,"orcamento",2500],[5000,1,"perifericos",50000],[2500,10,"perifericos",5000]]) {
    const r=avaliarOrcamentoGeracao(total,pct);
    assert.equal(r.valido,false);assert.equal(r.motivo,motivo);assert.equal(r.minimoTotal,minimo);
  }
  for(const [total,pct] of [[2000,0],[2500,20],[5000,10],[8000,20]])assert.equal(avaliarOrcamentoGeracao(total,pct).valido,true);
  assert.equal(avaliarOrcamentoGeracao(5000,100).valido,false);
});
test("orientação aceita apenas campos públicos conhecidos e valores monetários limitados",() => {
  const dados={motivo:"orcamento",etapa:"orcamento",titulo:"Ajuste o valor",orcamentoSugerido:6000,segredo:"não copiar",url:"https://outro.example"};
  assert.deepEqual(orientacaoGeracaoSegura(dados),{motivo:"orcamento",etapa:"orcamento",titulo:"Ajuste o valor",orcamentoSugerido:6000});
  assert.equal(orientacaoGeracaoSegura({...dados,etapa:"script"}),undefined);
  assert.equal(orientacaoGeracaoSegura({...dados,motivo:"desconhecido"}),undefined);
  assert.equal(orientacaoGeracaoSegura({...dados,orcamentoSugerido:Infinity}).orcamentoSugerido,undefined);
});
test("erro HTTP preserva a orientação do backend para o formulário",async() => {
  const fetchOriginal=globalThis.fetch;
  globalThis.fetch=async()=>new Response(JSON.stringify({erro:"Reserva insuficiente",codigo:"planejamento-invalido",geracao:{motivo:"perifericos",etapa:"perifericos",titulo:"Revise a reserva",orcamentoSugerido:6000}}),{status:400});
  try {await assert.rejects(fetchComErro('/build/'),e=>e.geracao?.orcamentoSugerido===6000&&e.codigo==='planejamento-invalido');}
  finally {globalThis.fetch=fetchOriginal;}
});
test("erro de orçamento oferece edição explícita, preserva percentual e escapa os textos",() => {
  const {html}=feedbackGeracao({message:'<script>não executar</script>',geracao:{motivo:"orcamento",etapa:"orcamento",titulo:'<img src=x>',orcamentoSugerido:6000}},{total:5000,percentual:20});
  assert.match(html,/generation-budget-form/);assert.match(html,/value="6000"/);
  assert.match(html,/porcentagem dos periféricos será mantida/);assert.match(html,/não garante/);
  assert.doesNotMatch(html,/<script>|<img src=x>|id="tentar-gerar-build"/);
});
test("cor e aparência permitem flexibilizar só por ação do usuário",() => {
  const cor=feedbackGeracao({message:'A IA não concluiu.',geracao:{motivo:"cor",etapa:"aparencia"}},{total:8000,aparencia:{cor:'branco'}}).html;
  assert.match(cor,/generation-without-color/);assert.match(cor,/data-generation-step="aparencia"/);
  assert.doesNotMatch(cor,/generation-budget-form/);
  const aparencia=feedbackGeracao({message:'Não concluiu.',geracao:{motivo:"aparencia",etapa:"aparencia"}},{total:8000}).html;
  assert.match(aparencia,/generation-without-appearance/);
});
test("conexão, cota e resultado incerto não sugerem que aumentar o orçamento resolve",() => {
  for(const codigo of ['offline','conexao','ia-limite','ia-cota-global','ia-timeout']) {
    const {html}=feedbackGeracao({message:'Aguarde ou confira sua conexão.',codigo},{total:5000});
    assert.doesNotMatch(html,/generation-budget-form/);
  }
  const {html}=feedbackGeracao({message:'Resultado incerto',resultadoIncerto:true,geracao:{motivo:'orcamento',etapa:'orcamento'}},{total:5000});
  assert.match(html,/Conferir minhas builds/);assert.doesNotMatch(html,/generation-budget-form|tentar-gerar-build/);
});
