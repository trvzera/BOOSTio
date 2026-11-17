import test from 'node:test';
import assert from 'node:assert/strict';
import { perguntasPc, perguntasNotebook, novasRespostasPreview, validarEtapaPreview, resumoFormularioPreview, percentualPreview } from '../js/experimentos/formularios.js';

const pc=chave=>perguntasPc.find(p=>p.chave===chave);
test('prévia de desktop preserva as seis etapas; notebook tem perguntas de mobilidade e tela',()=>{
  assert.deepEqual(perguntasPc.map(p=>p.chave),['objetivo','orcamento','pecas','perifericos','rede','aparencia']);
  assert.ok(perguntasNotebook.some(p=>p.chave==='mobilidade'));
  assert.ok(perguntasNotebook.some(p=>p.chave==='tela'));
  assert.equal(perguntasNotebook.some(p=>['pecas','aparencia'].includes(p.chave)),false);
});
test('rascunhos são independentes e os resumos não alteram as respostas',()=>{
  const a=novasRespostasPreview('pc'),b=novasRespostasPreview('pc'),n=novasRespostasPreview('notebook');
  a.pecas.push('ssd');assert.deepEqual(b.pecas,[]);assert.equal(n.pecas,undefined);
  const r=resumoFormularioPreview('pc',a);r.pecas.push('hd');
  assert.deepEqual(a.pecas,['ssd']);assert.equal(r.previa,true);assert.equal(r.geracaoDisponivel,false);
});
test('periféricos respeitam teto e mínimos; sobra não aumenta o limite do PC',()=>{
  const r={...novasRespostasPreview('pc'),orcamento:8000,perifericos:'todos-perifericos',percentualPerifericos:10};
  assert.equal(validarEtapaPreview('pc',pc('perifericos'),r),'');
  assert.equal(percentualPreview(r),10);
  assert.match(validarEtapaPreview('pc',pc('perifericos'),{...r,orcamento:3000}),/500/);
  assert.match(validarEtapaPreview('pc',pc('perifericos'),{...r,orcamento:2500,percentualPerifericos:50}),/2.000/);
  assert.match(validarEtapaPreview('pc',pc('perifericos'),{...r,percentualPerifericos:NaN}),/porcentagem/);
  const propios={...r,perifericos:'alguns-perifericos',perifericosProprios:['monitor','teclado','mouse','headset']};
  assert.equal(percentualPreview(propios),0);
  assert.match(validarEtapaPreview('pc',pc('perifericos'),propios),/modelo/);
});
test('etapas não permitem objetivo inválido, peça sem modelo ou cabo sem metragem',()=>{
  const r=novasRespostasPreview('pc');
  assert.match(validarEtapaPreview('pc',pc('objetivo'),r),/Escolha/);
  assert.match(validarEtapaPreview('pc',pc('pecas'),{...r,pecas:['ssd']}),/modelo/);
  assert.equal(validarEtapaPreview('pc',pc('pecas'),{...r,pecas:['nenhuma']}),'');
  assert.match(validarEtapaPreview('pc',pc('rede'),{...r,rede:{tipo:'ambos',possuiAcessorio:false}}),/metros/);
  assert.equal(validarEtapaPreview('pc',pc('rede'),{...r,rede:{tipo:'ambos',possuiAcessorio:false,comprimentoCaboM:20}}),'');
});
test('notebook não herda o mínimo de desktop nem promete disponibilidade por preço',()=>{
  const q=perguntasNotebook.find(p=>p.chave==='orcamento');
  assert.equal(validarEtapaPreview('notebook',q,{orcamento:1500}),'');
  for(const valor of [0,NaN,Infinity,1000001])assert.ok(validarEtapaPreview('notebook',q,{orcamento:valor}));
  assert.match(validarEtapaPreview('pc',pc('orcamento'),{orcamento:1500}),/2.000/);
});
