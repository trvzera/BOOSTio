import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { opcoesUso, prioridadesUso, ajudaCategorias } from '../js/build/uso-formulario.js';

test('os cinco usos mantêm valores e explicam as prioridades sem promessa de resultado',()=>{
  assert.deepEqual(opcoesUso.map(o=>o[0]),['estudos','jogos','trabalho-casual','trabalho-pesado','todos']);
  for(const [valor,,descricao]of opcoesUso){assert.ok(descricao.length>15);assert.ok(prioridadesUso[valor].length>70);}
  assert.match(prioridadesUso.jogos,/placa de vídeo e o processador/);
  assert.match(prioridadesUso['trabalho-pesado'],/memória para arquivos grandes/);
  assert.doesNotMatch(JSON.stringify(opcoesUso),/AAA|FPS/);
});
test('explicações do catálogo preservam limites em vez de garantir encaixe',()=>{
  assert.match(ajudaCategorias.gabinete,/espaço e ventilação/);
  assert.match(ajudaCategorias.memoria_ram,/Não é o espaço/);
  assert.match(ajudaCategorias.monitor,/Hz|resolução/);
});
test('formulário anuncia prioridade selecionada e orienta conferir criações incertas',async()=>{
  const forms=await readFile(new URL('../js/pages/forms.js',import.meta.url),'utf8');
  assert.match(forms,/usage-priority-copy[^>]*aria-live="polite"/);
  assert.match(forms,/prioridadesUso\[respostas.objetivo\]/);
  assert.match(forms,/erro.resultadoIncerto===true/);
  assert.match(forms,/Conferir minhas builds/);
});
