import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { criarClienteBenchmark } from "../js/api/benchmark/consultarBenchmark.js";
import { resumoRequisitosBuildHtml } from "../js/benchmark/requisitos.js";
import { painelBenchmarkHtml } from "../js/benchmark/painel.js";

const fichas = JSON.parse(await readFile(new URL("../../backend/services/benchmark_service/requisitos_jogos.json",import.meta.url),"utf8"));
const ficha = () => ({...structuredClone(fichas.fortnite),game:"fortnite",buildId:"s-1",escopo:"parcial",requisitosVerificados:false,fpsValidado:false,
  ram:{fonte:"build_salva",completa:true,conhecidaGb:4,informadaGb:4,atendeMinimo:false,atendeRecomendado:false,status:"abaixo_minimo",pendencias:[]}});

test("requisitos da build enviam só jogo e ID e conferem identidade e capacidade",async () => {
  const chamadas = [];
  const cliente = criarClienteBenchmark({requisitar:async rota => { chamadas.push(rota); return {resultado:ficha()}; }});
  const dados = await cliente.consultarRequisitosBuild({game:"fortnite",buildId:"s-1",ramGb:128});
  assert.equal(dados.ram.informadaGb,4);
  assert.deepEqual(chamadas,["/benchmark/requisitos-build?game=fortnite&build_id=s-1"]);
  for (const entrada of [{game:"../jogo",buildId:"s-1"},{game:"fortnite",buildId:"s-qa"},{game:"fortnite",buildId:"s-0"}])
    await assert.rejects(cliente.consultarRequisitosBuild(entrada));
  assert.equal(chamadas.length,1);
});

test("cliente rejeita build trocada, aprovação completa ou RAM inconsistente",async () => {
  for (const mudar of [d => d.buildId="s-2",d => d.requisitosVerificados=true,d => d.fpsValidado=true,
    d => d.ram.atendeMinimo=true,d => d.ram.informadaGb=128,d => d.ram.status="recomendado",d => d.ram.completa=false]) {
    const dados = ficha(); mudar(dados);
    const cliente = criarClienteBenchmark({requisitar:async () => ({resultado:dados})});
    await assert.rejects(cliente.consultarRequisitosBuild({game:"fortnite",buildId:"s-1"}));
  }
});

test("interface destaca RAM insuficiente e mantém limites da verificação visíveis",() => {
  const html = resumoRequisitosBuildHtml(ficha());
  assert.match(html,/abaixo do mínimo/);
  assert.match(html,/data-tone="error"/);
  assert.match(html,/CPU, GPU, VRAM/);
  assert.match(html,/RAM da build salva/);
  assert.doesNotMatch(html,/FPS médio|1% low/);
  const desconhecida = ficha();
  desconhecida.ram={...desconhecida.ram,completa:false,informadaGb:null,conhecidaGb:8,status:"nao_informada",pendencias:["Falta identificar outra memória."]};
  assert.match(resumoRequisitosBuildHtml(desconhecida),/Pelo menos 8 GB identificados/);
});

test("requisitos escapam conteúdo e aceitam apenas fontes oficiais HTTPS",() => {
  const dados = ficha(); dados.jogo='<img src=x onerror="alert(1)">';
  assert.doesNotMatch(resumoRequisitosBuildHtml(dados),/<img\b/);
  dados.fonte.url="https://exemplo.invalid/"; assert.throws(() => resumoRequisitosBuildHtml(dados));
  dados.fonte.url="javascript:alert(1)"; assert.throws(() => resumoRequisitosBuildHtml(dados));
});

test("verificação independente aparece só no painel da build e não depende de FPS",() => {
  const html = painelBenchmarkHtml({prefixo:"build-fpshq",verificarRequisitos:true});
  assert.match(html,/type="button"[^>]*data-check-build-requirements/);
  assert.match(html,/id="build-fpshq-requirements"/);
  assert.doesNotMatch(painelBenchmarkHtml(),/data-check-build-requirements/);
});

test("capacidades extras são parciais, visíveis e validadas sem prometer espaço livre ou FPS",async () => {
  const dados=ficha(); dados.ram={...dados.ram,completa:true,informadaGb:16,conhecidaGb:16,status:'recomendado',atendeMinimo:true,atendeRecomendado:true};
  dados.vram={dedicadaGb:4,minimaGb:6,atendeCapacidadeMinima:false};
  dados.minimos={...dados.minimos,vramGb:6,armazenamentoGb:70,exigeSsd:true};
  dados.armazenamento={maiorUnidadeElegivelGb:40,minimaGb:70,exigeSsd:true,completo:true,atendeCapacidadeMinima:false,espacoLivreVerificado:false};
  dados.impedimentosMinimos=['A VRAM dedicada está abaixo do mínimo publicado.','Nenhuma unidade atende ao mínimo.'];
  const cliente = d => criarClienteBenchmark({requisitar:async()=>({resultado:d})});
  assert.deepEqual(await cliente(dados).consultarRequisitosBuild({game:'fortnite',buildId:'s-1'}),dados);
  const html=resumoRequisitosBuildHtml(dados);
  assert.match(html,/data-tone="error"/); assert.match(html,/VRAM dedicada: 4 GB/);
  assert.match(html,/Espaço livre não verificado/); assert.match(html,/não somamos discos separados/);
  for (const mudar of [d=>d.vram.atendeCapacidadeMinima=true,d=>d.armazenamento.espacoLivreVerificado=true,
    d=>d.impedimentosMinimos=[],d=>d.armazenamento.completo='true',d=>d.vram.dedicadaGb=-1]) {
    const invalida=structuredClone(dados);mudar(invalida);
    await assert.rejects(cliente(invalida).consultarRequisitosBuild({game:'fortnite',buildId:'s-1'}));
  }
});
