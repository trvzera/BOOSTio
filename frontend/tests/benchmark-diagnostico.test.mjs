import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { criarDiagnosticoBenchmark,textoDiagnostico } from "../js/experimentos/benchmark-diagnostico.js";
import { criarClienteBenchmark } from "../js/api/benchmark/consultarBenchmark.js";
import { requisitosHtml } from "../js/experimentos/requisitos-jogos.js";

const consulta = {game:"valorant",cpu:"ryzen-5-5600",gpu:"rtx-3060",res:"1080p",preset:"high"};
const resposta = {ok:true,game:{slug:"valorant",name:"Valorant"},cpu:{slug:consulta.cpu},gpu:{slug:consulta.gpu},res:"1080p",preset:"high",fps:288};
const fichas = JSON.parse(await readFile(new URL("../../backend/services/benchmark_service/requisitos_jogos.json",import.meta.url),"utf8"));
const ficha = () => ({...structuredClone(fichas.fortnite),game:"fortnite",escopo:"parcial",requisitosVerificados:false,fpsValidado:false,
  ram:{status:"abaixo_minimo",informadaGb:4,minimaGb:8,recomendadaGb:16}});

test("diagnóstico direto só consulta no clique, sem cookies, HTTP cache ou cache local",async () => {
  let chamadas = 0; const registros = [];
  const cliente = criarDiagnosticoBenchmark({modo:()=>"direto",aoRegistro:r=>registros.push(r),fetcher:async (url,opcoes) => {
    chamadas++; assert.equal(new URL(url).origin,"https://fpshq.com"); assert.equal(opcoes.credentials,"omit");
    assert.equal(opcoes.cache,"no-store"); assert.equal(opcoes.referrerPolicy,"no-referrer");
    return new Response(JSON.stringify(resposta),{headers:{"Content-Type":"application/json"}});
  }});
  assert.equal(chamadas,0);
  for (let i=0;i<2;i++) assert.equal((await cliente.consultar(consulta)).fps,288);
  assert.equal(chamadas,2); assert.equal(registros.length,2);
  assert.equal(registros[1].http,200); assert.equal(registros[1].cache,false);
});

test("diagnóstico distingue resposta HTTP recebida de falha de validação",async () => {
  let registro;
  const cliente = criarDiagnosticoBenchmark({modo:()=>"direto",aoRegistro:r=>{registro=r;},fetcher:async () => new Response(JSON.stringify({...resposta,cpu:{slug:"outra"}}))});
  await assert.rejects(cliente.consultar(consulta),{codigo:"resposta"});
  assert.equal(registro.http,200); assert.equal(registro.ok,false); assert.equal(registro.codigo,"resposta");
});

test("diagnóstico preserva status da BOOSTio e não o atribui à FPSHQ",async () => {
  let registro, chamadas=0;
  const cliente = criarDiagnosticoBenchmark({aoRegistro:r=>{registro=r;},requisitar:async () => { chamadas++; throw Object.assign(new Error("Timeout no provedor"),{status:504,codigo:"timeout",espera:30}); }});
  await assert.rejects(cliente.consultar(consulta),{status:504});
  assert.equal(chamadas,1); assert.equal(registro.http,504);
  assert.match(textoDiagnostico(registro),/não é o status HTTP do provedor/);
});

test("diagnóstico de rede não inventa status HTTP ou certeza de CORS",async () => {
  let registro;
  const cliente = criarDiagnosticoBenchmark({modo:()=>"direto",aoRegistro:r=>{registro=r;},fetcher:async () => { throw new TypeError("Failed to fetch"); }});
  await assert.rejects(cliente.consultar(consulta),{codigo:"rede"});
  assert.equal(registro.http,null); assert.match(textoDiagnostico(registro),/Nenhuma resposta HTTP/);
  assert.equal(registro.redirecionado,null); assert.match(textoDiagnostico(registro),/acessível ao JavaScript/);
  assert.match(textoDiagnostico(registro),/rede ou CORS/);
});

test("diagnóstico mostra HTTP do provedor sem confundir com resposta local e pausa",async () => {
  let registro;
  const cliente=criarDiagnosticoBenchmark({aoRegistro:r=>{registro=r;},requisitar:async()=>{
    throw Object.assign(new Error("Serviço indisponível"),{status:503,codigo:"redirecionamento",diagnostico:{httpProvedor:302,tipoResposta:"html",redirecionamento:true,pausa:true}});
  }});
  await assert.rejects(cliente.consultar(consulta),{status:503});
  const texto=textoDiagnostico(registro);
  assert.match(texto,/HTTP 503 da BOOSTio/);
  assert.match(texto,/FPSHQ: HTTP 302 · formato html · redirecionamento bloqueado/);
  assert.match(texto,/não consultou a FPSHQ novamente/);
  assert.doesNotMatch(texto,/rede ou CORS/);
});

test("falha entre servidor e provedor não é atribuída ao Wi-Fi do usuário",async()=>{
  let registro;
  const cliente=criarDiagnosticoBenchmark({aoRegistro:r=>{registro=r;},requisitar:async()=>{
    throw Object.assign(new Error("Provedor não respondeu"),{status:503,codigo:"rede"});
  }});
  await assert.rejects(cliente.consultar(consulta));
  assert.match(textoDiagnostico(registro),/falha ocorreu entre o servidor e a FPSHQ/);
  assert.doesNotMatch(textoDiagnostico(registro),/rede ou CORS/);
});

test("queda na leitura direta é falha de conexão, não de formato JSON",async()=>{
  let registro;
  const cliente=criarDiagnosticoBenchmark({modo:()=>"direto",aoRegistro:r=>{registro=r;},fetcher:async()=>({
    status:200,ok:true,json:async()=>{throw new TypeError("stream closed");},
  })});
  await assert.rejects(cliente.consultar(consulta),{codigo:"rede"});
  assert.equal(registro.http,200);assert.equal(registro.codigo,"rede");
});

test("cancelamento durante leitura direta não vira erro de resposta",async()=>{
  const controle=new AbortController();
  const cliente=criarDiagnosticoBenchmark({modo:()=>"direto",fetcher:async()=>{
    controle.abort();
    return {status:200,ok:true,json:async()=>{throw new DOMException("cancelado","AbortError");}};
  }});
  await assert.rejects(cliente.consultar(consulta,{signal:controle.signal}),{codigo:"cancelado"});
});

test("timeout durante leitura direta continua sendo timeout",async()=>{
  const cliente=criarDiagnosticoBenchmark({modo:()=>"direto",timeoutMs:5,fetcher:async(_url,{signal})=>({
    status:200,ok:true,json:()=>new Promise((_resolver,rejeitar)=>signal.addEventListener("abort",()=>rejeitar(new DOMException("prazo","AbortError")),{once:true})),
  })});
  await assert.rejects(cliente.consultar(consulta),{codigo:"timeout"});
});

test("trocar modo não consulta automaticamente e backend pode devolver cache",async () => {
  let modo="backend", chamadas=0; const registros=[];
  const cliente = criarDiagnosticoBenchmark({modo:()=>modo,aoRegistro:r=>registros.push(r),requisitar:async () => {chamadas++;return {resultado:{fps:288,cache:true}};}});
  modo="direto"; modo="backend"; assert.equal(chamadas,0);
  await cliente.consultar(consulta); assert.equal(registros[0].cache,true);
  assert.match(textoDiagnostico(registros[0]),/não comprova disponibilidade atual/);
});

test("cliente de requisitos valida entrada e consulta só a BOOSTio",async () => {
  const chamadas=[]; const cliente=criarClienteBenchmark({requisitar:async rota=>{chamadas.push(rota);return {resultado:ficha()};}});
  await cliente.consultarRequisitos({game:"fortnite",ramGb:4});
  await cliente.consultarRequisitos({game:"fortnite"});
  assert.deepEqual(chamadas,["/benchmark/requisitos?game=fortnite&ram_gb=4","/benchmark/requisitos?game=fortnite"]);
  for (const dados of [{game:"../jogo"},{game:"fortnite",ramGb:NaN},{game:"fortnite",ramGb:0},{game:"fortnite",ramGb:1.5}])
    await assert.rejects(cliente.consultarRequisitos(dados));
  assert.equal(chamadas.length,2);
});

test("requisitos não aprovam PC completo nem inventam recomendado do CS2",() => {
  const html = requisitosHtml(ficha());
  assert.match(html,/abaixo do mínimo/); assert.match(html,/positivo da API não aprova/);
  assert.match(html,/demais recursos não foram validados/);
  const cs2={...ficha(),...structuredClone(fichas.cs2),ram:{status:"minimo_sem_recomendacao"}};
  assert.match(requisitosHtml(cs2),/Não publicado na fonte consultada/);
});

test("requisitos escapam textos e rejeitam fonte não confiável",() => {
  const dados=ficha(); dados.jogo='<img src=x onerror="alert(1)">';
  assert.doesNotMatch(requisitosHtml(dados),/<img\b/);
  dados.fonte.url="javascript:alert(1)"; assert.throws(()=>requisitosHtml(dados));
});

test("diagnóstico e requisitos novos ficam na página de testes",async () => {
  const laboratorio=await readFile(new URL("../testes.html",import.meta.url),"utf8");
  assert.match(laboratorio,/name="fpshq-route" value="backend" checked/);
  assert.match(laboratorio,/name="fpshq-route" value="direto"/);
  assert.match(laboratorio,/id="requirements-check"/);
  for(const caminho of ["../js/build/acoes-build.js","../js/benchmark/interface.js"])
    assert.doesNotMatch(await readFile(new URL(caminho,import.meta.url),"utf8"),/benchmark-diagnostico|experimentos\/fpshq/);
});
