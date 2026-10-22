import test from "node:test";
import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import { paginaPrivada, redirecionamentoSessao } from "../js/components/navigation-config.js";
import { modelosProntos, copiarModelo } from "../js/build/modelos.js";
import { avaliarBuild } from "../js/build/compatibilidade.js";
import { completarCatalogoDemo } from "../js/build/hardware.js";
import { hardwareBlender } from "../js/benchmark/hardware.js";
import { criarClienteBenchmark } from "../js/api/benchmark/consultarBenchmark.js";
import { pecasPropriasFormulario } from "../js/build/pecas-proprias.js";
import { linksAutenticado } from "../js/components/navigation-config.js";
import { verificarEspacoBuild } from "../js/api/build/builds.js";
import { fetchComErro } from "../js/api/_shared/fetchComErro.js";
import { buildDaConta, estadoParaConta } from "../js/build/conta.js";
import { indicadorBuild } from "../js/build/indicador.js";

const catalogo = completarCatalogoDemo(JSON.parse(await readFile(new URL("../data/catalogo-demo.json",import.meta.url),"utf8")));

test("visitante só acessa páginas públicas e recuperação de conta",async () => {
  for (const pagina of ["index.html","termos.html","sobre.html","contato.html","login.html","signin.html","esqueci-senha.html","reset-senha.html","erro.html"])
    assert.equal(redirecionamentoSessao(pagina,false),null,pagina);
  for (const pagina of ["formulario.html","pecas.html","peca.html","configuracao-build.html","builds.html","configuracoes.html","configuracoes-prontas.html","testes.html"])
    assert.equal(redirecionamentoSessao(pagina,false),"login.html",pagina);
  for (const nome of await readdir(new URL("../pages/",import.meta.url))) {
    if (!nome.endsWith(".html") || !paginaPrivada(nome)) continue;
    const html = await readFile(new URL("../pages/" + nome,import.meta.url),"utf8");
    assert.match(html,/<body[^>]*data-private-page/);
  }
});

test("dezesseis modelos sem periféricos estão completos nos dados disponíveis e cobrem usos e valores distintos",() => {
  const modelos = modelosProntos(catalogo);
  assert.equal(modelos.length,16);
  assert.equal(new Set(modelos.map(b=>b.id)).size,16);
  assert.ok(new Set(modelos.map(b=>b.objetivo)).size>=5);
  for (const build of modelos) {
    const avaliacao = avaliarBuild(build,catalogo);
    assert.deepEqual(avaliacao.erros,[],build.titulo);
    assert.deepEqual(avaliacao.faltam,[],build.titulo);
    assert.deepEqual(build.metadados.pendentes,[]);
    assert.equal(build.incluirPerifericos,false);
    for (const categoria of ["monitor","teclado","mouse","fone"]) assert.ok(!build.componentes[categoria]);
    assert.equal(copiarModelo(build).incluirPerifericos,false);
  }
  const precos = modelos.map(b=>avaliarBuild(b,catalogo).preco);
  assert.ok(Math.max(...precos)>Math.min(...precos)*1.5);
});

test("modelos usam IDs e preços da conta e sinalizam peças ausentes sem fingir posse",() => {
  const conta = catalogo.map((peca,i)=>({...peca,id:peca.categoria+":"+(i+1),preco:peca.preco*2}));
  const modelo = modelosProntos(conta,{referencias:catalogo})[0];
  assert.equal(avaliarBuild(modelo,conta).preco,avaliarBuild(modelosProntos(catalogo)[0],catalogo).preco*2);
  assert.ok(modelo.componentes.processador.id.startsWith("processador:"));
  const incompleto = modelosProntos(conta.filter(p=>p.categoria!=="processador"),{referencias:catalogo})[0];
  assert.ok(incompleto.metadados.pendentes.length>0);
  assert.ok(!incompleto.componentes.processador);
});

test("Blender permite CPU sem GPU e mantém sufixos e identidade da peça",() => {
  const cpu = {fabricante:"AMD",modelo:"Ryzen 5 5600",nucleo:6};
  assert.deepEqual(hardwareBlender(cpu,null),{cpu:"AMD Ryzen 5 5600 6-Core Processor",gpu:null});
  assert.equal(hardwareBlender({...cpu,modelo:"Ryzen 5 5600X"},null).cpu,"AMD Ryzen 5 5600X 6-Core Processor");
  assert.equal(hardwareBlender(cpu,{modelo:"GeForce RTX 3060",memoria_gb:12}).gpu,"NVIDIA GeForce RTX 3060");
  assert.equal(hardwareBlender(cpu,{modelo:"GeForce RTX 3060",memoria_gb:8}).gpu,null);
  assert.equal(hardwareBlender({fabricante:"Intel",modelo:"Core i3-12100F"},null).cpu,"Intel Core i3-12100F");
});

test("periféricos próprios viajam separados do hardware e não vazam ao mudar a escolha",() => {
  const respostas = {pecas:["nenhuma"],perifericos:"alguns-perifericos",perifericosProprios:["monitor","headset"],pecasDetalhes:{monitor:" Meu monitor ",headset:"Meu headset",mouse:"Desmarcado"}};
  assert.deepEqual(pecasPropriasFormulario(respostas),{monitor:"Meu monitor",fone:"Meu headset"});
  assert.deepEqual(pecasPropriasFormulario({...respostas,perifericos:"sem-perifericos"}),{});
  assert.deepEqual(pecasPropriasFormulario({...respostas,pecas:["processador"],pecasDetalhes:{...respostas.pecasDetalhes,processador:"Ryzen 5 5600"}}),{processador:"Ryzen 5 5600",monitor:"Meu monitor",fone:"Meu headset"});
});

test("hamburger tem criação, minhas builds autenticadas e navegação pública",() => {
  assert.deepEqual(linksAutenticado.map(l=>l.pagina),["index.html","builds.html","builds.html?criar=1","termos.html","sobre.html"]);
  assert.equal(linksAutenticado.find(l=>l.pagina==="builds.html").autenticado,true);
  assert.ok(linksAutenticado.every(l=>l.icone));
});

test("pré-criação exige sessão, e-mail verificado e uma das três vagas",async t => {
  let chamadas = 0;
  t.mock.method(globalThis,"fetch",async () => { chamadas++; return new Response(JSON.stringify({builds:[{id:1},{id:2},{id:3}]})); });
  await assert.rejects(verificarEspacoBuild({auth:false}),{status:401});
  await assert.rejects(verificarEspacoBuild({auth:true,usuario:{verificado:false}}),{status:403,codigo:"email-nao-verificado"});
  assert.equal(chamadas,0);
  await assert.rejects(verificarEspacoBuild({auth:true,usuario:{verificado:true}}),{codigo:"limite-builds"});
  assert.equal(chamadas,1);
});

test("mensagem offline não mascara aborto nem erro HTTP do provedor",async t => {
  const original = Object.getOwnPropertyDescriptor(globalThis,"navigator");
  Object.defineProperty(globalThis,"navigator",{configurable:true,value:{onLine:false}});
  t.after(() => original ? Object.defineProperty(globalThis,"navigator",original) : delete globalThis.navigator);
  const buscar = t.mock.method(globalThis,"fetch",async () => { throw new TypeError("Failed to fetch"); });
  await assert.rejects(fetchComErro("/build/"),erro=>erro.codigo==="offline"&&erro.message.includes("sem internet"));
  buscar.mock.mockImplementation(async () => { throw new DOMException("Abortado","AbortError"); });
  await assert.rejects(fetchComErro("/build/"),{name:"AbortError"});
  buscar.mock.mockImplementation(async () => new Response(JSON.stringify({erro:"Fonte indisponível",codigo:"provedor"}),{status:503}));
  await assert.rejects(fetchComErro("/benchmark/fps"),{status:503,codigo:"provedor",message:"Fonte indisponível"});
});

test("diagnóstico Python acompanha a leitura mas não vira dado editável/exportável",() => {
  const compatibilidade = {status:"nao_verificado",rotulo:"Compatibilidade não totalmente verificada",naoVerificado:[]};
  const build = buildDaConta({id:"s-1",nome:"Teste",estado:{componentes:{}},compatibilidade});
  assert.equal(build.compatibilidade.status,"nao_verificado");
  assert.equal(estadoParaConta(build).compatibilidade,undefined);
  const resultado = avaliarBuild(build,[]);
  assert.equal(resultado.compatibilidade.status,"nao_verificado");
  assert.match(indicadorBuild(resultado,"teste"),/Compatibilidade não totalmente verificada/);
});

test("dados ausentes não geram aprovação; motivos do servidor são escapados no popover",() => {
  const resultado = avaliarBuild({componentes:{}},[]);
  assert.equal(resultado.compatibilidade.status,"nao_verificado");
  const html = indicadorBuild({...resultado,compatibilidade:{status:"nao_verificado",rotulo:"Não verificada",naoVerificado:[{mensagem:"<script>teste</script>"}]}},"teste");
  assert.ok(!html.includes("<script>"));
  assert.ok(html.includes("&lt;script&gt;"));
});

test("cliente consulta Blender somente pelo backend e rejeita pontuação inventada ou link externo",async () => {
  const entrada = {dispositivo:"AMD Ryzen 5 5600 6-Core Processor",tipo:"cpu"};
  const resultado = {...entrada,score:150,quantidade:20,metodo:"CPU",versao:"4.5.0",consultadoEm:1,url:"https://opendata.blender.org/benchmarks/query/?device_name=AMD"};
  let rota;
  const cliente = criarClienteBenchmark({requisitar:async caminho=>{rota=caminho;return {resultado};}});
  assert.equal((await cliente.consultarBlender(entrada)).score,150);
  assert.ok(rota.startsWith("/benchmark/blender?"));
  for (const mudanca of [{score:NaN},{score:-1},{dispositivo:"Outro modelo"},{url:"javascript:alert(1)"}]) {
    const invalido = criarClienteBenchmark({requisitar:async()=>({resultado:{...resultado,...mudanca}})});
    await assert.rejects(invalido.consultarBlender(entrada));
  }
});
