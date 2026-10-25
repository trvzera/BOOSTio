import test from 'node:test';
import assert from 'node:assert/strict';
import { fetchComErro } from '../js/api/_shared/fetchComErro.js';

function navegador(t,onLine) {
  const original=Object.getOwnPropertyDescriptor(globalThis,'navigator');
  Object.defineProperty(globalThis,'navigator',{configurable:true,value:{onLine}});
  t.after(()=>original?Object.defineProperty(globalThis,'navigator',original):delete globalThis.navigator);
}
const json=(dados,status=200)=>new Response(JSON.stringify(dados),{status,headers:{'Content-Type':'application/json'}});

test('falha sem internet não inventa HTTP nem afirma que o servidor rejeitou',async t=>{
  navegador(t,false);t.mock.method(globalThis,'fetch',async()=>{throw new TypeError('Failed to fetch');});
  await assert.rejects(fetchComErro('/build/'),e=>e.codigo==='offline'&&e.status===undefined&&!e.resultadoIncerto&&/Wi-Fi/.test(e.message));
});
test('navegador online não é prova de internet funcionando',async t=>{
  navegador(t,true);t.mock.method(globalThis,'fetch',async()=>{throw new TypeError('NetworkError');});
  await assert.rejects(fetchComErro('/build/'),e=>e.codigo==='conexao'&&/Confira sua internet/.test(e.message)&&/serviço pode estar indisponível/.test(e.message));
});
test('queda durante leitura não é classificada como JSON inválido',async t=>{
  navegador(t,false);t.mock.method(globalThis,'fetch',async()=>({ok:true,status:200,json:async()=>{throw new TypeError('stream closed');}}));
  await assert.rejects(fetchComErro('/build/'),{codigo:'offline'});
});
test('criação com resposta perdida exige conferir o resultado, sem repetição automática',async t=>{
  navegador(t,true);let chamadas=0;
  t.mock.method(globalThis,'fetch',async()=>++chamadas===1?json({csrf_token:'token-teste'}):{ok:true,status:200,json:async()=>{throw new TypeError('stream closed');}});
  await assert.rejects(fetchComErro('/build/',{method:'POST',body:'{}'}),e=>e.resultadoIncerto===true&&/antes de repetir/.test(e.message));
  assert.equal(chamadas,2);
});
test('CSRF com erro HTTP não vira falha de rede nem envia a ação',async t=>{
  navegador(t,false);let chamadas=0;
  t.mock.method(globalThis,'fetch',async()=>{chamadas++;return new Response('<html>Bad Gateway</html>',{status:503});});
  await assert.rejects(fetchComErro('/build/',{method:'POST'}),{status:503,codigo:'http'});
  assert.equal(chamadas,1);
});
test('CSRF incompleto não envia uma mutação com token undefined',async t=>{
  let chamadas=0;t.mock.method(globalThis,'fetch',async()=>{chamadas++;return json({});});
  await assert.rejects(fetchComErro('/build/',{method:'POST'}),e=>e.codigo==='resposta'&&/segurança/.test(e.message));
  assert.equal(chamadas,1);
});
test('conexão perdida antes do CSRF não indica uma ação enviada',async t=>{
  navegador(t,false);let chamadas=0;
  t.mock.method(globalThis,'fetch',async()=>{chamadas++;throw new TypeError('Failed to fetch');});
  await assert.rejects(fetchComErro('/build/',{method:'POST'}),e=>e.codigo==='offline'&&e.resultadoIncerto===false&&!/alteração foi salva/.test(e.message));
  assert.equal(chamadas,1);
});
test('JSON inválido após POST não afirma que nada foi salvo',async t=>{
  let chamadas=0;t.mock.method(globalThis,'fetch',async()=>++chamadas===1?json({csrf_token:'token-teste'}):new Response('<html>incompleto</html>'));
  await assert.rejects(fetchComErro('/build/',{method:'POST'}),e=>e.codigo==='resposta'&&e.status===200&&e.resultadoIncerto===true&&/antes de repetir/.test(e.message));
  assert.equal(chamadas,2);
});
test('mensagem de erro que não é texto usa orientação padrão',async t=>{
  t.mock.method(globalThis,'fetch',async()=>json({erro:{interno:'não mostrar'}},400));
  await assert.rejects(fetchComErro('/build/'),e=>e.status===400&&/Confira as informações/.test(e.message)&&!/object Object|interno/.test(e.message));
});
test('HTTP recebido mantém mensagem/status/cota mesmo quando aparelho sinaliza offline',async t=>{
  navegador(t,false);t.mock.method(globalThis,'fetch',async()=>new Response(JSON.stringify({erro:'Serviço de testes indisponível',codigo:'provedor',diagnostico:{httpProvedor:302,tipoResposta:'html',redirecionamento:true,cookie:'secreto',url:'https://externo.invalid'}}),{status:503,headers:{'Retry-After':'45'}}));
  await assert.rejects(fetchComErro('/benchmark/fps'),e=>{
    assert.equal(e.status,503);assert.equal(e.codigo,'provedor');assert.equal(e.espera,45);
    assert.deepEqual(e.diagnostico,{httpProvedor:302,tipoResposta:'html',redirecionamento:true});
    assert.equal(e.message,'Serviço de testes indisponível');return true;
  });
});
test('HTML e mensagem genérica de proxy viram orientação simples',async t=>{
  const buscar=t.mock.method(globalThis,'fetch',async()=>new Response('<html>erro</html>',{status:502}));
  await assert.rejects(fetchComErro('/build/'),e=>e.status===502&&/BOOSTio está com dificuldades/.test(e.message));
  buscar.mock.mockImplementation(async()=>json({erro:'Internal Server Error'},500));
  await assert.rejects(fetchComErro('/build/'),e=>e.status===500&&!/Internal Server/.test(e.message));
});
test('aborto deliberado continua sendo aborto, inclusive durante leitura',async t=>{
  const erro=new DOMException('cancelado','AbortError');
  const buscar=t.mock.method(globalThis,'fetch',async()=>{throw erro;});
  await assert.rejects(fetchComErro('/build/'),e=>e===erro);
  buscar.mock.mockImplementation(async()=>({ok:true,status:200,json:async()=>{throw erro;}}));
  await assert.rejects(fetchComErro('/build/'),e=>e===erro);
});
test('corpo interrompido não mascara status de falha já recebido',async t=>{
  navegador(t,false);t.mock.method(globalThis,'fetch',async()=>({ok:false,status:503,json:async()=>{throw new TypeError('connection reset');}}));
  await assert.rejects(fetchComErro('/build/'),{status:503,codigo:'http'});
});
