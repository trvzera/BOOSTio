import test from "node:test";
import assert from "node:assert/strict";
import { readFile,readdir } from "node:fs/promises";
import { criarClienteFPSHQ,normalizarResultado,validarConsulta,REFERENCIA_FPS,JOGOS_INICIAIS } from "../js/experimentos/fpshq.js";
import { resultadoDesempenhoHtml,resolucoesHtml } from "../js/experimentos/benchmark-view.js";

const consulta = {...REFERENCIA_FPS,game:"valorant",res:"1080p",preset:"high"};
const resposta = (extra = {}) => ({ok:true,game:{slug:"valorant",name:"Valorant"},cpu:{slug:consulta.cpu},gpu:{slug:consulta.gpu},res:"1080p",preset:"high",fps:288,low1:261,source:"measured",basis:"measured",confidence:"high",matrix:{"1080p":{high:288}},...extra});
const json = dados => new Response(JSON.stringify(dados),{headers:{"Content-Type":"application/json"}});

test("jogos padrão seguem a seleção e a ordem definidas para o laboratório",() => {
  assert.deepEqual(JOGOS_INICIAIS.map(jogo => jogo.slug),[
    "valorant","cs2","fortnite","cyberpunk-2077","red-dead-redemption-2",
  ]);
});
test("FPSHQ valida IDs e opções antes de chamar a rede",async () => {
  let chamadas = 0;
  const cliente = criarClienteFPSHQ({fetcher:() => { chamadas++; }});
  for (const valor of [{...consulta,cpu:null},{...consulta,game:"../jogo"},{...consulta,res:"8k"},{...consulta,preset:"extreme"}])
    await assert.rejects(cliente.consultar(valor),{codigo:"entrada"});
  assert.equal(chamadas,0);
  assert.deepEqual(validarConsulta(consulta),consulta);
});
test("FPSHQ só aceita o par exato de CPU e GPU e a configuração pedida",() => {
  for (const extra of [{cpu:null},{cpu:{slug:"outra-cpu"}},{gpu:{slug:"outra-gpu"}},{game:{slug:"outro-jogo"}},{res:"4K"},{preset:"low"}])
    assert.throws(() => normalizarResultado(resposta(extra),consulta),{codigo:"resposta"});
});
test("FPSHQ preserva 1% low, origem e base agregada sem inventar campos ausentes",() => {
  const resultado = normalizarResultado(resposta({basis:"aggregate",low1:null,fps_range:null}),consulta);
  assert.equal(resultado.fps,288);
  assert.equal(resultado.low1,null);
  assert.equal(resultado.base,"aggregate");
  assert.equal(resultado.intervalo,null);
  assert.equal(resultado.matriz["1440p"].high,null);
  assert.equal(resultado.verdict,undefined);
});
test("FPSHQ rejeita números inválidos e jogos sem resultado",() => {
  for (const fps of [null,undefined,"288",NaN,Infinity,-1])
    assert.throws(() => normalizarResultado(resposta({fps}),consulta),{codigo:"sem-dados"});
  assert.equal(normalizarResultado(resposta({fps:0}),consulta).fps,0);
});
test("FPSHQ usa GET público sem cookies e reutiliza cache de uma hora",async () => {
  let chamadas = 0, instante = 100000;
  const cliente = criarClienteFPSHQ({agora:() => instante,fetcher:async (url,opcoes) => {
    chamadas++;
    const destino = new URL(url);
    assert.equal(destino.origin,"https://fpshq.com");
    assert.equal(destino.pathname,"/api/public/v1/fps");
    assert.equal(destino.searchParams.get("cpu"),consulta.cpu);
    assert.equal(opcoes.credentials,"omit");
    assert.equal(opcoes.referrerPolicy,"no-referrer");
    return json(resposta());
  }});
  assert.equal((await cliente.consultar(consulta)).cache,false);
  assert.equal((await cliente.consultar(consulta)).cache,true);
  assert.equal(chamadas,1);
  instante += 3600001;
  assert.equal((await cliente.consultar(consulta)).cache,false);
  assert.equal(chamadas,2);
});
test("FPSHQ reaproveita consultas simultâneas idênticas e tolera storage bloqueado",async () => {
  let chamadas = 0;
  const cliente = criarClienteFPSHQ({armazenamento:{getItem:() => { throw Error(); },setItem:() => { throw Error(); }},fetcher:async () => { chamadas++; return json(resposta()); }});
  const resultados = await Promise.all([cliente.consultar(consulta),cliente.consultar(consulta)]);
  assert.equal(resultados.length,2);
  assert.equal(chamadas,1);
});
test("FPSHQ trata 404, falha de rede e JSON inválido",async () => {
  for (const [fetcher,codigo] of [
    [async () => new Response("{}",{status:404}),"nao-encontrado"],
    [async () => { throw new TypeError("Failed to fetch"); },"rede"],
    [async () => new Response("not json"),"resposta"],
    [async () => new Response("{}",{status:503}),"http"],
  ]) await assert.rejects(criarClienteFPSHQ({fetcher}).consultar(consulta),{codigo});
});
test("FPSHQ obedece Retry-After e não repete chamadas automaticamente",async () => {
  let chamadas = 0, instante = 1000;
  const cliente = criarClienteFPSHQ({agora:() => instante,fetcher:async () => { chamadas++; return new Response("{}",{status:429,headers:{"Retry-After":"30"}}); }});
  await assert.rejects(cliente.consultar(consulta),{codigo:"limite",espera:30});
  instante += 5000;
  await assert.rejects(cliente.consultar(consulta),{codigo:"limite",espera:25});
  assert.equal(chamadas,1);
});
test("FPSHQ cancela consultas demoradas",async () => {
  const cliente = criarClienteFPSHQ({timeoutMs:5,fetcher:(_url,{signal}) => new Promise((_resolve,reject) => signal.addEventListener("abort",() => reject(new DOMException("abort","AbortError"))))});
  await assert.rejects(cliente.consultar(consulta),{codigo:"timeout"});
});
test("FPSHQ direto cancela ao sair do laboratório e não inicia consulta já cancelada",async () => {
  let chamadas=0;
  const cliente=criarClienteFPSHQ({fetcher:(_url,{signal}) => new Promise((_resolve,reject) => {
    chamadas++; signal.addEventListener("abort",()=>reject(new DOMException("abort","AbortError")));
  })});
  const controle=new AbortController();
  const consultaAtual=cliente.consultar(consulta,{signal:controle.signal}); controle.abort();
  await assert.rejects(consultaAtual,{codigo:"cancelado"});
  await assert.rejects(cliente.consultar(consulta,{signal:controle.signal}),{codigo:"cancelado"});
  assert.equal(chamadas,1);
});
test("FPSHQ busca jogos por nome com limite do contrato e filtra IDs inválidos",async () => {
  let chamadas = 0;
  const cliente = criarClienteFPSHQ({fetcher:async url => { chamadas++; assert.equal(new URL(url).searchParams.get("q"),"Forza"); return json({ok:true,results:[{slug:"forza-horizon-5",name:"Forza Horizon 5"},{slug:"../jogo",name:"Inválido"}]}); }});
  for (const texto of ["","a","a".repeat(61)]) await assert.rejects(cliente.buscarJogos(texto),{codigo:"entrada"});
  assert.equal(chamadas,0);
  assert.deepEqual(await cliente.buscarJogos(" Forza "),[{slug:"forza-horizon-5",name:"Forza Horizon 5"}]);
});
test("consulta de benchmark permanece exclusiva do laboratório",async () => {
  const paginas = new URL("../pages/",import.meta.url);
  for (const nome of (await readdir(paginas)).filter(n => n.endsWith(".html")))
    assert.doesNotMatch(await readFile(new URL(nome,paginas),"utf8"),/test-benchmark|experimentos\/fpshq/,nome);
  const html = await readFile(new URL("../testes.html",import.meta.url),"utf8");
  assert.match(html,/test-benchmark\.js/);
  assert.match(html,/Desempenho esperado/);
  assert.match(html,/não equivalem necessariamente a queda de FPS/);
});
test("resultado compacto mantém FPS, fonte dos números e detalhes recolhidos",() => {
  const dados = {...normalizarResultado(resposta(),consulta),consultadoEm:Date.now(),cache:true};
  const html = resultadoDesempenhoHtml(dados);
  assert.match(html,/288/);
  assert.match(html,/261/);
  assert.match(html,/Comparar ajustes/);
  assert.match(html,/Sobre os dados/);
  assert.match(html,/Não é uma medição desta máquina/);
  assert.match(html,/Dados em cache/);
  assert.match(html,/<section class="fpshq-alternatives"/);
  assert.doesNotMatch(html,/<details\b[^>]*fpshq-alternatives/);
  assert.doesNotMatch(html,/consultas\/minuto|mil\/dia|Cache de uma hora/);
  assert.doesNotMatch(html,/<table\b|<details\b[^>]*\bopen/);
  assert.equal([...html.matchAll(/type="radio"/g)].length,4);
  assert.match(html,/value="high" checked/);
});
test("comparação local usa a qualidade escolhida e não inventa dados de resolução",() => {
  const matriz = {"1080p":{high:288,low:382},"1440p":{high:200,low:300},"4K":{high:null,low:100}};
  const alta = resolucoesHtml(matriz,"high"), baixa = resolucoesHtml(matriz,"low");
  assert.match(alta,/288/); assert.match(alta,/200/); assert.match(alta,/Sem dados/);
  assert.match(baixa,/382/); assert.match(baixa,/300/); assert.match(baixa,/100/);
  assert.doesNotMatch(baixa,/Sem dados/);
  assert.equal(resolucoesHtml(matriz,"invalida"),alta);
});
test("resultado escapa nomes de jogos e mantém intervalo e 1% low ausente",() => {
  const dados = {...normalizarResultado(resposta({game:{slug:"valorant",name:'<img src=x onerror="alert(1)">'},fps_range:[200,300],low1:null}),consulta),consultadoEm:Date.now()};
  const html = resultadoDesempenhoHtml(dados);
  assert.doesNotMatch(html,/<img\b/);
  assert.match(html,/&lt;img/);
  assert.match(html,/200–300/);
  assert.match(html,/Sem dados/);
});
test("aviso começa oculto e busca exige escolher um resultado",async () => {
  const html = await readFile(new URL("../testes.html",import.meta.url),"utf8");
  const js = await readFile(new URL("../js/benchmark/interface.js",import.meta.url),"utf8");
  assert.match(html,/<aside\b[^>]*id="fpshq-notice"[^>]*\bhidden/);
  assert.match(html,/id="fpshq-search-results"[^>]*\bhidden/);
  assert.match(html,/<details class="test-performance-prototype fpshq-disclosure" data-animated-details>/);
  assert.match(js,/data-fpshq-game/);
  assert.doesNotMatch(js,/jogo\.value = jogos\[0\]\.slug/);
  assert.match(js,/mostrarAviso\(true\)/);
});
test("laboratório alterna três interfaces no mesmo formulário e resultado",async () => {
  const html = await readFile(new URL("../testes.html",import.meta.url),"utf8");
  const js = await readFile(new URL("../js/benchmark/interface.js",import.meta.url),"utf8");
  const css = await readFile(new URL("../styles/componentes/benchmark.css",import.meta.url),"utf8");
  assert.equal([...html.matchAll(/name="fpshq-layout"/g)].length,3);
  for (const layout of ["cards","panel","compact"]) assert.match(html,new RegExp('name="fpshq-layout" value="' + layout + '"'));
  assert.equal([...html.matchAll(/id="fpshq-test-form"/g)].length,1);
  assert.equal([...html.matchAll(/id="fpshq-result"/g)].length,1);
  const troca = js.slice(js.indexOf("const aplicarInterface"),js.indexOf("const informar"));
  assert.match(troca,/painel\.dataset\.layout = opcao\.value/);
  assert.doesNotMatch(troca,/consultar\(|fetch\(|innerHTML|replaceChildren|renderizar\(/);
  assert.match(css,/data-layout="panel"/);
  assert.match(css,/data-layout="compact"/);
  assert.match(css,/\.fpshq-empty:not\(\[hidden\]\)/);
  assert.match(css,/\.fpshq-layouts span\s*\{[^}]*white-space: nowrap/);
  assert.match(css,/@media \(max-width: 900px\)/);
});
test("menus estáticos e resultados da API inicializam a animação compartilhada",async () => {
  const html = await readFile(new URL("../testes.html",import.meta.url),"utf8");
  const js = await readFile(new URL("../js/benchmark/interface.js",import.meta.url),"utf8");
  const resultado = resultadoDesempenhoHtml({...normalizarResultado(resposta(),consulta),consultadoEm:Date.now()});
  for (const disclosure of [...html.matchAll(/<details\b[^>]*fpshq-disclosure[^>]*>/g),...resultado.matchAll(/<details\b[^>]*fpshq-disclosure[^>]*>/g)])
    assert.match(disclosure[0],/data-animated-details/);
  assert.match(js,/iniciarDetalhesAnimados\(resultado\)/);
  assert.match(js,/definirDetalheAberto\(painelBusca,false,\{animar:false\}\)/);
});
