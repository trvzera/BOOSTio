import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { criarClienteBenchmark } from "../js/api/benchmark/consultarBenchmark.js";
import { hardwareBenchmark } from "../js/benchmark/hardware.js";
import { painelBenchmarkHtml } from "../js/benchmark/painel.js";
import { resultadoDesempenhoHtml } from "../js/benchmark/view.js";

const consulta = {game:"valorant",cpu:"ryzen-5-5600",gpu:"rtx-3060",res:"1080p",preset:"high"};
test("cliente de produção consulta somente o backend com os ajustes exatos",async () => {
  const chamadas = [];
  const cliente = criarClienteBenchmark({requisitar:async (rota,opcoes) => {
    chamadas.push(rota);
    assert.ok(opcoes.signal instanceof AbortSignal);
    return {resultado:rota.startsWith("/benchmark/jogos") ? {jogos:[{slug:"valorant",name:"Valorant"}]} : {fps:288}};
  }});
  assert.equal((await cliente.consultar(consulta)).fps,288);
  assert.deepEqual(await cliente.buscarJogos(" Valorant "),[{slug:"valorant",name:"Valorant"}]);
  assert.equal(chamadas[0],"/benchmark/fps?game=valorant&cpu=ryzen-5-5600&gpu=rtx-3060&res=1080p&preset=high");
  assert.equal(chamadas[1],"/benchmark/jogos?q=Valorant");
});
test("cliente de produção valida entrada antes da rede",async () => {
  let chamadas = 0;
  const cliente = criarClienteBenchmark({requisitar:async () => { chamadas++; }});
  for (const entrada of [{...consulta,cpu:"../id"},{...consulta,gpu:null},{...consulta,preset:"extreme"},{...consulta,res:"8k"}])
    await assert.rejects(cliente.consultar(entrada));
  for (const texto of ["", "a", "x".repeat(61)]) await assert.rejects(cliente.buscarJogos(texto));
  assert.equal(chamadas,0);
});
test("cliente preserva erro de sessão e espera do backend sem retentativas",async () => {
  for (const erro of [Object.assign(new Error("Entre na conta"),{status:401}),Object.assign(new Error("Aguarde"),{status:429,espera:90})]) {
    let chamadas = 0;
    const cliente = criarClienteBenchmark({requisitar:async () => { chamadas++; throw erro; }});
    await assert.rejects(cliente.consultar(consulta),e => e === erro);
    assert.equal(chamadas,1);
  }
});
test("cliente cancela consulta por timeout ou fechamento do modal",async () => {
  const requisitar = (_rota,{signal}) => new Promise((_resolve,reject) => {
    if (signal.aborted) reject(new DOMException("abort","AbortError"));
    else signal.addEventListener("abort",() => reject(new DOMException("abort","AbortError")));
  });
  await assert.rejects(criarClienteBenchmark({requisitar,timeoutMs:5}).consultar(consulta),{codigo:"timeout"});
  const controle = new AbortController();
  const promessa = criarClienteBenchmark({requisitar}).consultar(consulta,{signal:controle.signal});
  controle.abort();
  await assert.rejects(promessa,{codigo:"cancelado"});
});
test("registro de hardware não troca variantes nem substitui vídeo integrado",() => {
  const cpu = {modelo:"Ryzen 5 5600"}, gpu = {modelo:"GeForce RTX 3060",memoria_gb:12};
  assert.deepEqual(hardwareBenchmark(cpu,gpu),{cpu:"ryzen-5-5600",gpu:"rtx-3060"});
  assert.ok(hardwareBenchmark(cpu,{...gpu,memoria_gb:8}).motivo);
  assert.ok(hardwareBenchmark({modelo:"Ryzen 5 5600G"},gpu).motivo);
  assert.ok(hardwareBenchmark(cpu,null).motivo);
  assert.notEqual(hardwareBenchmark({modelo:"Core i5-12400F"},gpu).cpu,hardwareBenchmark({modelo:"Core i5-12400"},gpu).cpu);
});
test("painel do modal identifica campos, mostra cinco jogos por controle e isola a comparação",() => {
  const html = painelBenchmarkHtml({prefixo:"build-fpshq",hardware:'<img src=x onerror="alert(1)">',memoria:16});
  assert.match(html,/id="build-fpshq-game"/);
  assert.match(html,/for="build-fpshq-game"/);
  assert.match(html,/RAM · não avaliada/);
  assert.doesNotMatch(html,/<img\b/);
  assert.match(html,/&lt;img/);
  const resultado = resultadoDesempenhoHtml({consulta,jogo:"Valorant",fps:288,low1:null,matriz:{},consultadoEm:Date.now()},"build-fpshq");
  assert.match(resultado,/name="build-fpshq-comparison-quality"/);
  assert.match(resultado,/<section class="fpshq-alternatives"/);
  assert.doesNotMatch(resultado,/<details class="fpshq-alternatives"/);
});
test("cache de reserva tem aviso visível sem precisar expandir os detalhes",() => {
  const html = resultadoDesempenhoHtml({consulta,jogo:"Valorant",fps:288,low1:null,matriz:{},consultadoEm:1,desatualizado:true,cache:true});
  assert.match(html,/<p class="fpshq-cache-notice" role="status">/);
  assert.ok(html.indexOf('fpshq-cache-notice')<html.indexOf('fpshq-data-details'));
  assert.ok(html.includes('não foram atualizados'));
});
test("produção mantém cliente Python e diagnóstico direto fica restrito ao laboratório",async () => {
  for (const arquivo of ["../js/build/acoes-build.js","../js/benchmark/interface.js"])
    assert.doesNotMatch(await readFile(new URL(arquivo,import.meta.url),"utf8"),/experimentos\/fpshq|criarClienteFPSHQ/);
  const laboratorio = await readFile(new URL("../js/pages/test-benchmark.js",import.meta.url),"utf8");
  assert.match(laboratorio,/experimentos\/benchmark-diagnostico/);
  const acoes = await readFile(new URL("../js/build/acoes-build.js",import.meta.url),"utf8");
  assert.match(acoes,/iniciarPainelBenchmark\(dialogo/);
  assert.doesNotMatch(acoes,/Estimativas de FPS em breve/);
});
test("dots acompanha apenas o estado do menu e a tela de erro evita retorno duplicado",async () => {
  const ui = await readFile(new URL("../js/components/ui.js",import.meta.url),"utf8");
  assert.match(ui,/const alternavel = \[[^\]]*"dots"[^\]]*\]/);
  assert.match(ui,/if \(!alternavel \|\| elemento\.dataset\.lottie === "profile"\)/);
  const erro = await readFile(new URL("../pages/erro.html",import.meta.url),"utf8");
  assert.match(erro,/<button[^>]*id="error-back"[^>]*\bhidden/);
  assert.equal([...erro.matchAll(/Ir para o início<\/a>/g)].length,1);
});
