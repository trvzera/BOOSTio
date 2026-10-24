import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizarAparencia, aparenciaHtml } from '../js/build/aparencia.js';
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
  assert.equal((html.match(/class="appearance-case"/g)||[]).length,6);
  assert.match(html,/value="full-tower" checked/);
  assert.match(html,/value="panoramico" checked/);
  assert.doesNotMatch(html,/<script>|R\$|case-reference|<small>/);
  for(const tipo of ['Mini Tower','Mid Tower','Full Tower','Panorâmico','Vidro lateral'])assert.ok(html.includes(tipo));
  for(const [,url]of html.matchAll(/src="([^"]+)"/g))assert.ok(fs.existsSync(new URL(url,new URL('../pages/',import.meta.url))));
  assert.doesNotMatch(aparenciaHtml({},[],{possuiGabinete:true}),/appearance-case"/);
});
test('cores são escolhas rotuladas, com amostra visual e sem depender só da cor',()=>{
  const html=aparenciaHtml({cor:'misto'});
  assert.equal((html.match(/class="appearance-swatch"/g)||[]).length,4);
  assert.match(html,/value="misto" checked/);
  assert.match(html,/color-misto" aria-hidden="true"/);
  assert.match(html,/Preto e branco/);
});
