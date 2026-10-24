import test from "node:test";
import assert from "node:assert/strict";
import { criarHistoricoBuild } from "../js/build/historico-build.js";
const base=()=>({id:"s-1",titulo:"Build",orcamento:1000,componentes:{ssd:[{id:"ssd",quantidade:1}]},incluirPerifericos:false,incluirRede:false});
test("desfazer restaura peça removida sem perder nome ou orçamento editados depois",()=>{
  const historico=criarHistoricoBuild(),antes=base(),depois={...base(),componentes:{}};
  historico.registrar(antes,depois);
  const atual={...depois,titulo:"Nome novo",orcamento:2000,compatibilidade:{status:"incompativel"}};
  const r=historico.desfazer(atual);
  assert.deepEqual(r.componentes,antes.componentes);assert.equal(r.titulo,"Nome novo");assert.equal(r.orcamento,2000);
  assert.equal(r.compatibilidade,undefined);assert.ok(historico.motivo(r));assert.deepEqual(atual.componentes,{});
});
test("apenas a última alteração e sua quantidade são restauradas, sem redo implícito",()=>{
  const h=criarHistoricoBuild(),a=base(),b=base(),c=base();b.componentes.ssd[0].quantidade=2;c.componentes.ssd[0].quantidade=3;
  h.registrar(a,b);h.registrar(b,c);assert.equal(h.desfazer(c).componentes.ssd[0].quantidade,2);
  assert.throws(()=>h.desfazer(c),/Nenhuma alteração/);
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
