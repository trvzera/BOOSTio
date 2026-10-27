import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizarAparencia, aparenciaHtml, guiaPorteGabineteHtml, atualizarGuiaPorteGabinete, estilosGabinete, portesGabinete } from '../js/build/aparencia.js';
import { normalizarBuild } from '../js/build/estado.js';
import { estadoParaConta } from '../js/build/conta.js';
import fs from 'node:fs';

test('aparência é opcional, limitada e preservada no salvamento',()=>{
  assert.deepEqual(normalizarAparencia(),{estilo:'sem-preferencia',porte:'sem-preferencia',cor:'sem-preferencia',gabinete_id:null});
  for(const id of [true,-1,1.5,1e12,'2'])assert.equal(normalizarAparencia({gabinete_id:id}).gabinete_id,null);
  const aparencia={estilo:'vidro',porte:'mini-tower',cor:'branco',gabinete_id:17};
  assert.deepEqual(estadoParaConta(normalizarBuild({aparencia})).aparencia,aparencia);
});
test('galeria mostra exemplos por porte/visual, sem preços nem produto obrigatório',()=>{
  const html=aparenciaHtml({porte:'full-tower',estilo:'panoramico'},[{modelo:'<script>alert(1)</script>'}]);
  assert.equal((html.match(/class="appearance-case"/g)||[]).length,7);
  assert.match(html,/value="full-tower"[^>]* checked/);
  assert.match(html,/value="panoramico"[^>]* checked/);
  assert.doesNotMatch(html,/<script>|R\$|case-reference|<small>/);
  for(const tipo of ['Mini Tower','Mid Tower','Full Tower','Sem vidro','Aquário','Panorâmico — 3 faces','Vidro lateral'])assert.ok(html.includes(tipo));
  for(const [,url]of html.matchAll(/src="([^"]+)"/g))assert.ok(fs.existsSync(new URL(url,new URL('../pages/',import.meta.url))));
  assert.doesNotMatch(aparenciaHtml({},[],{possuiGabinete:true}),/appearance-case"/);
});
test('tamanho e estilo são escolhas independentes e preservam valores antigos',()=>{
  for(const porte of ['mini-tower','mid-tower','full-tower'])for(const estilo of ['discreto','vidro','panoramico','panoramico-3-faces']){
    const preferencia={porte,estilo,cor:'branco',gabinete_id:null};
    assert.deepEqual(estadoParaConta(normalizarBuild({aparencia:preferencia})).aparencia,preferencia);
  }
  assert.deepEqual(portesGabinete.map(([v])=>v),['sem-preferencia','mini-tower','mid-tower','full-tower']);
  assert.ok(estilosGabinete.some(([v])=>v==='compacto'));
  assert.doesNotMatch(aparenciaHtml({estilo:'compacto'}),/value="compacto"/);
  const html=aparenciaHtml({porte:'mini-tower',estilo:'panoramico-3-faces'});
  assert.match(html,/name="appearance-style" value="panoramico-3-faces"[^>]*checked/);
  assert.match(html,/name="appearance-size" value="mini-tower"[^>]*checked/);
  assert.match(html,/Tamanho do gabinete/);assert.match(html,/Estilo do gabinete/);
});
test('referências de encaixe são específicas do exemplo, não limites do porte',()=>{
  const mini=guiaPorteGabineteHtml('mini-tower'),mid=guiaPorteGabineteHtml('mid-tower'),full=guiaPorteGabineteHtml('full-tower');
  assert.match(mini,/387 × 230 × 381 mm/);assert.match(mini,/Até 240 mm na frente/);
  assert.match(mid,/493 × 217 × 469 mm/);assert.match(mid,/Até 360 mm/);
  assert.match(full,/550 × 248 × 600 mm/);assert.match(full,/E-ATX até 277 mm/);
  for(const html of [mini,mid,full]){
    assert.match(html,/profundidade × largura × altura/);assert.match(html,/não de todos os gabinetes/);
    assert.doesNotMatch(html,/R\$|<button|<a /);
  }
  for(const valor of ['sem-preferencia','panoramico-3-faces','__proto__','<script>'])assert.match(guiaPorteGabineteHtml(valor),/Não existe uma medida única/);
  const html=aparenciaHtml({});
  assert.match(html,/240 mm costuma usar 2 ventoinhas de 120 mm/);
  assert.match(html,/radiador completo, os tubos e as conexões precisam de espaço extra/);
});
test('guia muda apenas com tamanho, sem reiniciar opções de estilo e cor',()=>{
  const guia={dataset:{porte:'sem-preferencia'},innerHTML:''},aviso={textContent:''};let mudancas=0;
  const raiz={querySelector:s=>s==='#appearance-size-guide'?guia:aviso};
  Object.defineProperty(guia,'innerHTML',{set(v){this.html=v;mudancas++;},get(){return this.html;}});
  atualizarGuiaPorteGabinete(raiz,'mid-tower');
  assert.equal(mudancas,1);assert.match(guia.innerHTML,/TD500/);assert.match(aviso.textContent,/Referência de Médio/);
  atualizarGuiaPorteGabinete(raiz,'mid-tower');assert.equal(mudancas,1);
  atualizarGuiaPorteGabinete(raiz,'sem-preferencia');assert.equal(mudancas,2);assert.equal(aviso.textContent,'Tamanho sem preferência.');
  assert.doesNotThrow(()=>atualizarGuiaPorteGabinete({querySelector:()=>null},'mini-tower'));
});
test('cores são escolhas rotuladas, com amostra visual e sem depender só da cor',()=>{
  const html=aparenciaHtml({cor:'misto'});
  assert.equal((html.match(/class="appearance-swatch"/g)||[]).length,4);
  assert.match(html,/value="misto" checked/);
  assert.match(html,/color-misto" aria-hidden="true"/);
  assert.match(html,/Preto e branco/);
  assert.match(html,/Cor das peças e periféricos/);
  assert.match(html,/cor é uma preferência para todas as peças e periféricos novos/);
  assert.match(html,/incluindo gabinete e ventoinhas/);
  assert.match(html,/peças que você já possui serão mantidas/);
});
