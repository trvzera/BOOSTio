import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizarAparencia, aparenciaHtml } from '../js/build/aparencia.js';
import { normalizarBuild } from '../js/build/estado.js';
import { estadoParaConta } from '../js/build/conta.js';

test('aparência é opcional, limitada e preservada no salvamento',()=>{
  assert.deepEqual(normalizarAparencia(),{estilo:'sem-preferencia',cor:'sem-preferencia',gabinete_id:null});
  for(const id of [true,-1,1.5,1e12,'2'])assert.equal(normalizarAparencia({gabinete_id:id}).gabinete_id,null);
  const aparencia={estilo:'vidro',cor:'branco',gabinete_id:17};
  assert.deepEqual(estadoParaConta(normalizarBuild({aparencia})).aparencia,aparencia);
});
test('galeria é limitada, mantém a referência e não inventa fotos nem aceita HTML',()=>{
  const pecas=Array.from({length:20},(_,i)=>({id:`gabinete:${i+1}`,categoria:'gabinete',preco:100+i*20,esgotado:false,modelo:i===2?'<script>alert(1)</script>':'Gabinete '+i}));
  const html=aparenciaHtml({gabinete_id:3},pecas,{orcamento:500});
  assert.equal((html.match(/class="appearance-case"/g)||[]).length,6);
  assert.match(html,/value="3" checked/);
  assert.doesNotMatch(html,/<script>|<img/);
  assert.match(html,/&lt;script&gt;/);
  assert.doesNotMatch(aparenciaHtml({},pecas,{possuiGabinete:true}),/case-reference/);
  assert.match(aparenciaHtml({},[],{}),/Nenhum modelo disponível/);
});
