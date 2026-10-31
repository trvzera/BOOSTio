import test from "node:test";
import assert from "node:assert/strict";
import { criarHistoricoBuild, acaoAtalhoHistorico } from "../js/build/historico-build.js";
const base=()=>({id:"s-1",titulo:"Build",orcamento:1000,componentes:{ssd:[{id:"ssd",quantidade:1}]},incluirPerifericos:false,incluirRede:false});
test("desfazer restaura peça removida sem perder nome ou orçamento editados depois",()=>{
  const historico=criarHistoricoBuild(),antes=base(),depois={...base(),componentes:{}};
  historico.registrar(antes,depois);
  const atual={...depois,titulo:"Nome novo",orcamento:2000,compatibilidade:{status:"incompativel"}};
  const r=historico.desfazer(atual);
  assert.deepEqual(r.componentes,antes.componentes);assert.equal(r.titulo,"Nome novo");assert.equal(r.orcamento,2000);
  assert.equal(r.compatibilidade,undefined);assert.ok(historico.motivo(r));assert.deepEqual(atual.componentes,{});
});
test("desfaz e refaz várias alterações de quantidade na ordem correta",()=>{
  const h=criarHistoricoBuild(),a=base(),b=base(),c=base();b.componentes.ssd[0].quantidade=2;c.componentes.ssd[0].quantidade=3;
  h.registrar(a,b);h.registrar(b,c);
  const volta=h.desfazer(c),inicio=h.desfazer(volta);
  assert.equal(volta.componentes.ssd[0].quantidade,2);assert.equal(inicio.componentes.ssd[0].quantidade,1);
  assert.throws(()=>h.desfazer(inicio),/Nenhuma alteração/);
  const meio=h.refazer(inicio),fim=h.refazer(meio);
  assert.equal(meio.componentes.ssd[0].quantidade,2);assert.equal(fim.componentes.ssd[0].quantidade,3);
  assert.throws(()=>h.refazer(fim),/Nenhuma alteração/);
});
test("nova ação após desfazer descarta o refazer e respeita o limite de memória",()=>{
  const h=criarHistoricoBuild({limite:2}),a=base(),b=base(),c=base(),d=base();
  b.componentes.ssd[0].quantidade=2;c.componentes.ssd[0].quantidade=3;d.componentes.ssd[0].quantidade=4;
  h.registrar(a,b);h.registrar(b,c);h.registrar(c,d);
  const r=h.desfazer(h.desfazer(d));assert.equal(r.componentes.ssd[0].quantidade,2);
  assert.ok(h.motivo(r));
  const nova={...r,componentes:{}};h.registrar(r,nova);
  assert.ok(h.motivo(nova,"refazer"));assert.deepEqual(h.desfazer(nova).componentes,r.componentes);
});
test("refazer preserva metadados e rejeita tranca ou alteração externa",()=>{
  const h=criarHistoricoBuild(),a=base(),b={...base(),componentes:{}};
  h.registrar(a,b);const volta=h.desfazer(b);
  assert.throws(()=>h.refazer({...volta,travada:true}),/Destranque/);
  assert.throws(()=>h.refazer({...volta,componentes:{}}),/mudou/);
  const r=h.refazer({...volta,titulo:"Nome mantido",orcamento:9000});
  assert.deepEqual(r.componentes,{});assert.equal(r.titulo,"Nome mantido");assert.equal(r.orcamento,9000);
});
test("atalhos respeitam teclado, Shift, composição e edição nativa",()=>{
  const evento={key:"z",ctrlKey:true,target:{closest:()=>null}};
  assert.equal(acaoAtalhoHistorico(evento),"desfazer");
  assert.equal(acaoAtalhoHistorico({...evento,ctrlKey:false,metaKey:true}),"desfazer");
  assert.equal(acaoAtalhoHistorico({...evento,key:"Z",shiftKey:true}),"refazer");
  for(const extra of [{defaultPrevented:true},{isComposing:true},{repeat:true},{altKey:true},{ctrlKey:false},{key:"y"},{target:{closest:()=>({})}}])
    assert.equal(acaoAtalhoHistorico({...evento,...extra}),null);
});
test("mudança concorrente, outra build ou tranca impedem sobrescrever dados",()=>{
  const h=criarHistoricoBuild(),a=base(),b={...base(),componentes:{}};h.registrar(a,b);
  assert.throws(()=>h.desfazer({...b,travada:true}),/Destranque/);
  assert.throws(()=>h.desfazer({...b,id:"s-2"}),/Nenhuma alteração/);
  assert.throws(()=>h.desfazer({...b,componentes:{hd:[{id:"outro",quantidade:1}]}}),/mudou/);
});
test("histórico copia snapshots e restaura opções de periféricos da troca",()=>{
  const h=criarHistoricoBuild(),a=base(),b={...base(),incluirPerifericos:true,componentes:{mouse:{id:"mouse",quantidade:1}}};
  h.registrar(a,b);a.componentes.ssd[0].quantidade=9;
  const r=h.desfazer(b);assert.equal(r.componentes.ssd[0].quantidade,1);assert.equal(r.incluirPerifericos,false);
});
test("limpar ao sair do editor impede reaplicar histórico preservado pelo cache de navegação",()=>{
  const h=criarHistoricoBuild(),a=base(),b={...base(),componentes:{}};
  h.registrar(a,b);assert.equal(h.motivo(b),"");h.limpar();
  assert.throws(()=>h.desfazer(b),/Nenhuma alteração/);
  h.registrar(a,b);assert.deepEqual(h.desfazer(b).componentes,a.componentes);
});
