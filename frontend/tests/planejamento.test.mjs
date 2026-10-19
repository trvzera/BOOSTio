import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { normalizarRede, custoRede, selecionarAcessorioRede } from "../js/build/rede.js";
import { normalizarBuild, abrirBuild } from "../js/build/estado.js";
import { planejamentoLocal, salvarPlanejamento } from "../js/build/planejamento.js";
import { avaliarBuild } from "../js/build/compatibilidade.js";
import { modelosProntos, copiarModelo } from "../js/build/modelos.js";

const catalogo = JSON.parse(await readFile(new URL("../data/catalogo-demo.json",import.meta.url),"utf8"));
function armazenamento() {
  const dados = new Map();
  return {getItem:chave => dados.get(chave) ?? null,setItem:(chave,valor) => dados.set(chave,String(valor)),removeItem:chave => dados.delete(chave)};
}

test("rede desconhecida ou própria não inventa preço nem muda conclusão da build",() => {
  const build = modelosProntos(catalogo)[0], antes = avaliarBuild(build,catalogo);
  const depois = avaliarBuild({...build,rede:{tipo:"wifi",possuiAcessorio:true,custoPrevisto:150}},catalogo);
  assert.equal(depois.preco,antes.preco);
  assert.equal(depois.preenchidos,antes.preenchidos);
  assert.equal(depois.total,antes.total);
  assert.equal(custoRede({tipo:"indefinido",possuiAcessorio:false,custoPrevisto:150}),0);
  assert.equal(normalizarRede({velocidadeMbps:-1,custoPrevisto:"x"}).custoPrevisto,null);
});

test("estimativas antigas de rede não entram no preço nem no consumo do PC",() => {
  const build = modelosProntos(catalogo)[0], antes = avaliarBuild(build,catalogo);
  const rede = {tipo:"cabo",possuiAcessorio:false,velocidadeMbps:500,comprimentoCaboM:10,custoPrevisto:45};
  const depois = avaliarBuild(normalizarBuild({...build,rede}),catalogo);
  assert.equal(depois.preco,antes.preco);
  assert.equal(normalizarRede(rede).custoPrevisto,null);
  assert.equal(depois.watts,antes.watts);
  assert.equal(depois.preenchidos,antes.preenchidos);
});

test("selecionar cabo já possuído preserva respostas e retira o custo da compra",() => {
  const rede = {tipo:"cabo",possuiAcessorio:false,velocidadeMbps:500,comprimentoCaboM:10,custoPrevisto:45};
  const propria = selecionarAcessorioRede(rede,"cabo:possuo");
  assert.equal(propria.possuiAcessorio,true);
  assert.equal(propria.comprimentoCaboM,10);
  assert.equal(propria.velocidadeMbps,500);
  assert.equal(custoRede(propria),0);
  assert.equal(custoRede(selecionarAcessorioRede(propria,"cabo:incluir")),0);
  assert.equal(rede.possuiAcessorio,false);
});

test("trocar cabo por adaptador não reaproveita o custo ou comprimento do outro acessório",() => {
  const adaptador = selecionarAcessorioRede({tipo:"cabo",possuiAcessorio:false,velocidadeMbps:500,comprimentoCaboM:10,custoPrevisto:45},"wifi:incluir");
  assert.equal(adaptador.tipo,"wifi");
  assert.equal(adaptador.velocidadeMbps,500);
  assert.equal(adaptador.comprimentoCaboM,null);
  assert.equal(adaptador.custoPrevisto,null);
  assert.equal(custoRede(adaptador),0);
});

test("formulário transfere rede e budget ao editor sem perder peças próprias",() => {
  globalThis.localStorage = armazenamento(); globalThis.sessionStorage = armazenamento();
  sessionStorage.setItem("boostio:respostas-formulario",JSON.stringify({orcamento:"personalizado",orcamentoPersonalizado:4321.75,rede:{tipo:"wifi",possuiAcessorio:false},pecasDetalhes:{processador:"Meu processador"}}));
  const build = abrirBuild(new URLSearchParams());
  assert.equal(build.orcamento,4321.75);
  assert.equal(build.rede.tipo,"wifi");
  assert.equal(build.rede.velocidadeMbps,null);
  assert.equal(build.componentes.processador.proprio,"Meu processador");
  assert.equal(sessionStorage.getItem("boostio:respostas-formulario"),null);
});

test("preferência aplica budget somente a novas builds quando autorizada",() => {
  globalThis.localStorage = armazenamento(); globalThis.sessionStorage = armazenamento();
  salvarPlanejamento({budget:6000,usarBudget:false});
  assert.equal(abrirBuild(new URLSearchParams()).orcamento,null);
  salvarPlanejamento({usarBudget:true});
  const build = abrirBuild(new URLSearchParams());
  assert.equal(build.orcamento,6000);
  build.orcamento = 4000;
  assert.equal(planejamentoLocal().budget,6000);
  assert.throws(() => salvarPlanejamento({budget:-1}),/budget/);
});

test("cópia de configuração pronta não altera os modelos nem reutiliza sua identidade",() => {
  const modelo = modelosProntos(catalogo)[0], copia = copiarModelo(modelo);
  assert.notEqual(copia.id,modelo.id);
  assert.equal(copia.visibilidade,"privado");
  assert.equal(copia.travada,false);
  copia.componentes.memoria_ram[0].quantidade = 5;
  assert.equal(modelo.componentes.memoria_ram[0].quantidade,1);
});
