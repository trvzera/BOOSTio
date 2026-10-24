import test from "node:test";
import assert from "node:assert/strict";
import {hardwareBlender,hardwareBenchmark} from "../js/benchmark/hardware.js";
import {consultarRenderizacoes,resumirConsultaRenderizacoes,classificarRenderizacoes} from "../js/build/comparacao-renderizacao.js";
import {criarClienteBenchmark} from "../js/api/benchmark/consultarBenchmark.js";

const gpu = modelo => hardwareBlender(null,{modelo,memoria_gb:12}).gpu;
const cpu = (modelo,fabricante="Intel",nucleo=6) => hardwareBlender({modelo,fabricante,nucleo},null).cpu;

for (const [modelo,esperado] of [
  ["RTX 5070 EAGLE OC SFF 12G","NVIDIA GeForce RTX 5070"],
  ["RTX 5060 TI DUAL O8G GeForce","NVIDIA GeForce RTX 5060 Ti"],
  ["GeForce RTX 5060 Ti 8G SHADOW","NVIDIA GeForce RTX 5060 Ti"],
  ["Dual Geforce RTX 5060 Ti Oc","NVIDIA GeForce RTX 5060 Ti"],
  ["GeForce RTX 4070 Ti SUPER GAMING","NVIDIA GeForce RTX 4070 Ti SUPER"],
  ["GeForce GTX 1660 Super","NVIDIA GeForce GTX 1660 SUPER"],
  ["GeForce GT 1030 2GB","NVIDIA GeForce GT 1030"],
  ["GeForce RTX5050 8GB GDDR6","NVIDIA GeForce RTX 5050"],
  ["Swift RX 9070 XT TRIPLE FAN","AMD Radeon RX 9070 XT"],
  ["Radeon RX 7900 XTX 24GB","AMD Radeon RX 7900 XTX"],
  ["Radeon RX 7900 GRE","AMD Radeon RX 7900 GRE"],
  ["Alpha RX 580","AMD Radeon RX 580"],
]) test("Blender identifica o chip explícito sem perder variante: "+modelo,()=>assert.equal(gpu(modelo),esperado));

for (const modelo of ["RTX 3060 Laptop GPU","RTX 3060M","RTX 3060 Mobile","RTX 3060 Max-Q","RX 580 2048SP",
  "RX 6600 M","RTX 3060 GAMING Ti","RTX 3060 / RTX 4060","RTX 3060 / RTX 4060 / RX 6600","RX 6600 ou RX 7600",
  "Placa sem modelo","Arc modelo não identificado"]) test("Blender não troca variante ambígua/mobile: "+modelo,()=>assert.equal(gpu(modelo),null));

test("CPUs preservam gerações antigas, Ultra, X3D e sufixos sem exigir título abreviado",()=>{
  assert.equal(cpu("Core Ultra 5 245KF"),"Intel Core Ultra 5 245KF");
  assert.equal(cpu("Core i3-10100F"),"Intel Core i3-10100F");
  assert.equal(cpu("Core i5-3330, 3.00 Ghz (turbo Até 3.20 Ghz), 4 Núcleos"),"Intel Core i5-3330");
  assert.equal(cpu("12th Gen Intel(R) Core(TM) i3-12100F"),"Intel Core i3-12100F");
  assert.equal(cpu("Ryzen 7 5700X3D, AM4, sem cooler","AMD",8),"AMD Ryzen 7 5700X3D 8-Core Processor");
  assert.equal(cpu("Ryzen 5 5600","AMD",null),null);
  assert.equal(cpu("Core i3-12100F ou Core i5-12400F"),null);
  assert.equal(cpu("Core i3-12100F Core i5-12400F Core Ultra 5 245KF"),null);
  assert.equal(cpu("Ryzen 5 5600 ou Ryzen 5 5500","AMD"),null);
  assert.equal(cpu("Core i5 10500 OEM, Processador Intel Core i5-10500"),"Intel Core i5-10500");
  assert.equal(gpu("Radeon Rx550 Aitek - Delta-Rx550"),"AMD Radeon RX 550");
  assert.equal(gpu("GTX 750 Ti 4GB - GTX750Ti-4G"),"NVIDIA GeForce GTX 750 Ti");
  assert.equal(hardwareBlender(null,{modelo:"RTX 3060 DUAL",memoria_gb:8}).gpu,null);
  assert.equal(hardwareBlender(null,{modelo:"RTX 3060 DUAL"}).gpu,null);
});

test("identificação Blender é independente dos slugs da API de FPS",()=>{
  const cpuPeca={fabricante:"Intel",modelo:"Core Ultra 5 245KF"},gpuPeca={modelo:"RTX 5070 EAGLE OC SFF 12G",memoria_gb:12};
  assert.ok(hardwareBenchmark(cpuPeca,gpuPeca).motivo);
  assert.deepEqual(hardwareBlender(cpuPeca,gpuPeca),{cpu:"Intel Core Ultra 5 245KF",gpu:"NVIDIA GeForce RTX 5070"});
});

test("comparação consulta o backend para modelos comerciais reais de GPU e não soma CPU",async()=>{
  const catalogo=[{id:"a",categoria:"placa_video",modelo:"RTX 5070 EAGLE OC SFF 12G"},
    {id:"b",categoria:"placa_video",modelo:"GeForce RTX 5060 Ti 8G SHADOW"}];
  const builds=catalogo.map(p=>({id:p.id,componentes:{placa_video:{id:p.id,quantidade:1}}}));
  const chamadas=[];
  const cliente=criarClienteBenchmark({requisitar:async rota=>{
    chamadas.push(rota);const dispositivo=new URL(rota,"https://qa.test").searchParams.get("dispositivo");
    return {resultado:{dispositivo,tipo:"gpu",score:dispositivo.includes("5070")?200:100,metodo:"OPTIX",versao:"5.2.0",quantidade:5,consultadoEm:1,
      url:"https://opendata.blender.org/benchmarks/query/?device_name="+encodeURIComponent(dispositivo)}};
  }});
  const resultados=await consultarRenderizacoes(builds,catalogo,{tipo:"gpu",cliente});
  assert.equal(chamadas.length,2);assert.ok(chamadas.every(r=>r.startsWith("/benchmark/blender?")));
  assert.deepEqual(classificarRenderizacoes(resultados).melhores,["a"]);
  assert.equal(resumirConsultaRenderizacoes(resultados).tom,"info");
});

test("sem GPU dedicada, sem resultados, sessão expirada e pausa não viram sucesso",async()=>{
  const build={id:"a",componentes:{placa_video:{id:"gpu",quantidade:1}}};
  const catalogo=[{id:"gpu",categoria:"placa_video",modelo:"GeForce RTX 5070"}];
  for(const erro of [Object.assign(new Error("Não há resultados públicos"),{codigo:"sem-dados",status:422}),
    Object.assign(new Error("Entre na sua conta"),{codigo:"nao-autenticado",status:401}),
    Object.assign(new Error("Aguarde"),{codigo:"limite",status:429,espera:60})]) {
    let chamadas=0;const cliente={consultarBlender:async()=>{chamadas++;throw erro;}};
    const resultados=await consultarRenderizacoes([build,{id:"b",componentes:{}}],catalogo,{tipo:"gpu",cliente});
    assert.equal(chamadas,1);assert.equal(resultados[0].codigo,erro.codigo);
    assert.equal(resultados[0].status,erro.status);assert.match(resultados[1].erro,/não tem uma GPU dedicada/);
    const resumo=resumirConsultaRenderizacoes(resultados);
    assert.equal(resumo.tom,"error");assert.ok(resumo.mensagem.includes(erro.message));
    assert.equal(resumo.espera,erro.espera||0);
  }
});

test("resumo distingue comparação parcial de métodos diferentes",()=>{
  const valor=(metodo="OPTIX")=>({score:100,tipo:"gpu",versao:"5.2.0",metodo});
  assert.equal(resumirConsultaRenderizacoes([{id:"a",dados:valor()},{id:"b",erro:"Sem dados"}]).tom,"warning");
  const mistura=[{id:"a",dados:valor()},{id:"b",dados:valor("HIP")}];
  assert.equal(classificarRenderizacoes(mistura).comparavel,false);
  assert.match(resumirConsultaRenderizacoes(mistura).mensagem,/Versões ou métodos diferentes/);
});
