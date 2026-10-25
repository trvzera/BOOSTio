import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { orcamentoValido, dividirOrcamento } from "../js/build/orcamento-formulario.js";
import { normalizarBuild } from "../js/build/estado.js";
import { estadoParaConta, buildDaConta } from "../js/build/conta.js";
import { exportarJson, exportarCsv, importarBuild } from "../js/build/arquivos.js";

test("orçamento digitado aceita centavos, não NaN, zero, excesso ou fração de centavo", () => {
  for (const valor of [0.01, 1234.56, 5000, 1000000]) assert.equal(orcamentoValido(valor),true);
  for (const valor of [NaN,Infinity,0,-1,1000000.01,1.001,"5000",null]) assert.equal(orcamentoValido(valor),false);
});

test("reserva usa o total, não acrescenta custo e mantém os centavos", () => {
  assert.deepEqual(dividirOrcamento(5000,20),{pc:4000,perifericos:1000});
  assert.deepEqual(dividirOrcamento(1234.56,20),{pc:987.65,perifericos:246.91});
  assert.deepEqual(dividirOrcamento(5000,0),{pc:5000,perifericos:0});
  for (const percentual of [-1,100,20.5,"20",NaN]) assert.equal(dividirOrcamento(5000,percentual),null);
});

test("reserva sobrevive à normalização, conta e exportação JSON", () => {
  const build = normalizarBuild({titulo:"Com periféricos",orcamento:5000,percentualPerifericos:20,incluirPerifericos:true});
  const estado = estadoParaConta(build);
  assert.equal(estado.percentualPerifericos,20);
  assert.equal(buildDaConta({id:"s-1",nome:build.titulo,descricao:"",criado_em:build.criadoEm,estado}).percentualPerifericos,20);
  assert.equal(importarBuild(exportarJson(build),"json",[]).percentualPerifericos,20);
  assert.equal(importarBuild(exportarCsv(build,[]),"csv",[]).percentualPerifericos,20);
});

test("slider arredondado não impede digitar o orçamento exato e oferece tetos", async () => {
  const forms = await readFile(new URL("../js/pages/forms.js",import.meta.url),"utf8");
  assert.match(forms,/step="100"/);
  assert.match(forms,/id="budget-input"[^>]+step="0\.01"/);
  assert.doesNotMatch(forms,/De R\$ 3\.000 a R\$ 5\.000|De R\$ 5\.000 a R\$ 8\.000/);
  assert.match(forms,/await verificarEspacoBuild\(\)/);
  assert.match(forms,/finally \{ pararMensagens\(\); \}/);
});

test("periféricos têm teto separado e a sobra não é transferida ao PC", async () => {
  const forms = await readFile(new URL("../js/pages/forms.js",import.meta.url),"utf8");
  assert.match(forms,/Quanto reservar para monitor, teclado, mouse e fone/);
  assert.match(forms,/Se sobrar, o dinheiro fica com você e não aumenta o limite das peças do computador/);
  assert.match(forms,/aria-describedby="peripheral-budget-summary peripheral-budget-help"/);
  assert.doesNotMatch(forms,/meta flexível|sobra pode ser redistribuída|saldo pode ser usado nas peças do PC/i);
});
