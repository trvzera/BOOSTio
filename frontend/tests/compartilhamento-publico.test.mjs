import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { idCompartilhamentoPublico, guardarRetornoPublico, consumirRetornoPublico } from '../js/components/sessao-publica.js';
import { paginaPrivada, redirecionamentoSessao } from '../js/components/navigation-config.js';
import { criarClienteBenchmark } from '../js/api/benchmark/consultarBenchmark.js';

const memoria = () => {
  const itens = new Map();
  return {getItem:k=>itens.get(k) ?? null,setItem:(k,v)=>itens.set(k,v),removeItem:k=>itens.delete(k)};
};

test('somente o link público canônico dispensa sessão, nunca o editor ou parâmetros misturados', () => {
  for (const busca of ['?compartilhar_id=s-1','?compartilhar_id=s-25&acao_publica=salvar']) {
    assert.ok(idCompartilhamentoPublico(busca));
    assert.equal(paginaPrivada('configuracao-build.html',busca),false);
    assert.equal(redirecionamentoSessao('configuracao-build.html',false,busca),null);
    assert.equal(paginaPrivada('builds.html',busca),true);
  }
  for (const busca of ['', '?build_id=s-1','?compartilhar_id=s-0','?compartilhar_id=1','?compartilhar_id=s-1&build_id=s-2',
    '?compartilhar_id=s-1&compartilhar_id=s-2','?compartilhar_id=s-1&acao_publica=excluir',
    '?compartilhar_id=s-1&acao_publica=testar&acao_publica=salvar','?compartilhar_id=s-1&next=https://evil.test']) {
    assert.equal(idCompartilhamentoPublico(busca),null);
    assert.equal(redirecionamentoSessao('configuracao-build.html',false,busca),'login.html');
  }
});

test('retorno do login é interno, temporário e consumido uma única vez', () => {
  const storage = memoria();
  assert.equal(guardarRetornoPublico('s-12','salvar',storage,1000),true);
  assert.equal(consumirRetornoPublico(storage,2000),'./configuracao-build.html?compartilhar_id=s-12&acao_publica=salvar');
  assert.equal(consumirRetornoPublico(storage,2000),null);
  assert.equal(guardarRetornoPublico('https://evil.test','salvar',storage,1000),false);
  assert.equal(guardarRetornoPublico('s-1','excluir',storage,1000),false);
  for (const dado of [{id:'s-1',acao:'salvar',criadoEm:0},{id:'s-1',acao:'testar',criadoEm:99999999},
    {id:'s-1',acao:'https://evil.test',criadoEm:1000},{id:'s-1',acao:'salvar',criadoEm:'1000'},null]) {
    storage.setItem('boostio:retorno-build-publica',JSON.stringify(dado));
    assert.equal(consumirRetornoPublico(storage,1000000),null);
    assert.equal(storage.getItem('boostio:retorno-build-publica'),null);
  }
  storage.setItem('boostio:retorno-build-publica','não é JSON');
  assert.equal(consumirRetornoPublico(storage,1000),null);
});

test('requisitos públicos autenticados usam flag explícita e validam a origem da resposta',async () => {
  const fichas = JSON.parse(await readFile(new URL('../../backend/services/benchmark_service/requisitos_jogos.json',import.meta.url),'utf8'));
  const dados = {...structuredClone(fichas.fortnite),game:'fortnite',buildId:'s-1',escopo:'parcial',requisitosVerificados:false,fpsValidado:false,
    ram:{fonte:'build_publica',completa:true,conhecidaGb:4,informadaGb:4,atendeMinimo:false,atendeRecomendado:false,status:'abaixo_minimo',pendencias:[]}};
  const chamadas = [];
  const cliente = criarClienteBenchmark({requisitar:async rota=>{chamadas.push(rota);return {resultado:dados};}});
  assert.equal((await cliente.consultarRequisitosBuild({game:'fortnite',buildId:'s-1',publica:true})).ram.fonte,'build_publica');
  assert.equal(chamadas[0],'/benchmark/requisitos-build?game=fortnite&build_id=s-1&origem_publica=1');
  await assert.rejects(cliente.consultarRequisitosBuild({game:'fortnite',buildId:'s-1'}));
});

test('armazenamento de sessão bloqueado não interrompe o fluxo de autenticação', t => {
  const anterior = Object.getOwnPropertyDescriptor(globalThis,'sessionStorage');
  Object.defineProperty(globalThis,'sessionStorage',{configurable:true,get(){throw new Error('Bloqueado');}});
  t.after(()=>anterior ? Object.defineProperty(globalThis,'sessionStorage',anterior) : delete globalThis.sessionStorage);
  assert.equal(guardarRetornoPublico('s-1','salvar'),false);
  assert.equal(consumirRetornoPublico(),null);
});
