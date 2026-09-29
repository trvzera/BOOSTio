import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { normalizarBuild, selecionarPeca, limiteRam, guardarRascunho, sincronizarRascunho, abrirBuild, itensRam, removerPeca, informacoesRam,
  salvarNoPerfilLocal, buildsLocais, linkCompartilhado } from "../js/build/estado.js";
import { avaliarBuild, pecaCompativel, selecionarPecaCompativel } from "../js/build/compatibilidade.js";
import { escolherModoLoading, acompanharCarregamento, aguardarCarregamentos } from "../js/components/page-loading.js";
import { ofertasPeca, htmlSeguro, categoriasEditor, categoriaCatalogo } from "../js/build/catalogo.js";

const catalogo = JSON.parse(readFileSync(new URL("../data/catalogo-demo.json", import.meta.url)));
const memoria = new Map();
globalThis.localStorage = { getItem: (k) => memoria.get(k) ?? null, setItem: (k,v) => memoria.set(k,v) };
globalThis.sessionStorage = { getItem: () => null, removeItem: () => {} };
globalThis.location = { href: "http://localhost:5501/frontend/pages/configuracao-build.html", search: "" };
const peca = (id) => catalogo.find((p) => p.id === id);
const base = () => normalizarBuild({ componentes: {
  processador: { id: "SEED-CPU-02", quantidade:1 },
  placa_mae: { id: "SEED-MB-03", quantidade:1 },
  memoria_ram: { id: "SEED-RAM-01", quantidade:1 },
  fonte: { id: "SEED-PSU-01", quantidade:1 },
} });

test("catálogo preserva 750 IDs únicos e 15 categorias da seed", () => {
  assert.equal(catalogo.length, 750);
  assert.equal(new Set(catalogo.map((p) => p.id)).size, 750);
  assert.equal(new Set(catalogo.map((p) => p.categoria)).size, 15);
  assert.ok(catalogo.every((p) => Number.isFinite(p.preco) && p.preco >= 0));
});

test("SSD e HD pertencem ao mesmo grupo obrigatório e qualquer um satisfaz armazenamento", () => {
  const grupo = categoriaCatalogo("armazenamento");
  assert.equal(grupo.obrigatoria,true);
  assert.deepEqual(grupo.tipos,["ssd","hd"]);
  assert.equal(categoriasEditor.filter(c => c.armazenamento).length,1);
  const build = base();
  assert.ok(avaliarBuild(build,catalogo).faltam.includes("Armazenamento"));
  for (const categoria of grupo.tipos) {
    const item = catalogo.find(p => p.categoria === categoria);
    const comDisco = selecionarPeca(build,item,catalogo);
    assert.ok(!avaliarBuild(comDisco,catalogo).faltam.includes("Armazenamento"));
    assert.equal(avaliarBuild(comDisco,catalogo).preenchidos,avaliarBuild(build,catalogo).preenchidos + 1);
  }
});

test("GPU é obrigatória sem vídeo integrado e deixa de ser obrigatória com GPU ou iGPU", () => {
  const build = base();
  assert.equal(peca(build.componentes.processador.id).videointegrado,false);
  assert.ok(avaliarBuild(build,catalogo).faltam.includes("Placa de vídeo"));
  assert.equal(avaliarBuild(build,catalogo).status,"incompleta");
  build.componentes.placa_video = {id:catalogo.find(p => p.categoria === "placa_video").id,quantidade:1};
  assert.ok(!avaliarBuild(build,catalogo).faltam.includes("Placa de vídeo"));
  delete build.componentes.placa_video;
  const cpu = {...peca(build.componentes.processador.id),videointegrado:true};
  const comVideo = catalogo.map(p => p.id === cpu.id ? cpu : p);
  assert.ok(!avaliarBuild(build,comVideo).faltam.includes("Placa de vídeo"));
  assert.equal(avaliarBuild(build,comVideo).preenchidos,avaliarBuild(build,catalogo).preenchidos+1);
});

test("quantidade RAM conta os módulos por kit e impede placa com slots insuficientes", () => {
  const build = base();
  const ram = peca(itensRam(build)[0].id);
  assert.equal(limiteRam(build,catalogo), Math.floor(4 / ram.quantidade_pentes));
  itensRam(build)[0].quantidade = limiteRam(build,catalogo);
  const cat = [...catalogo, { ...peca("SEED-MB-01"), id:"placa-teste", quantidade_slots_ram:1 }];
  delete build.componentes.placa_mae;
  assert.throws(() => selecionarPeca(build, cat.at(-1), cat), /slots/);
  assert.equal(limiteRam(build,catalogo), 0);
});

test("total multiplica preço e consumo ao duplicar RAM", () => {
  const build = base(), antes = avaliarBuild(build,catalogo);
  itensRam(build)[0].quantidade = 2;
  const depois = avaliarBuild(build,catalogo), ram = peca("SEED-RAM-01");
  assert.equal(depois.preco - antes.preco, ram.preco);
  assert.equal(depois.watts - antes.watts, ram.consumo_energia);
});

test("detecta socket e padrão DDR incompatíveis", () => {
  const build = base();
  build.componentes.processador.id = "SEED-CPU-03";
  assert.ok(avaliarBuild(build,catalogo).erros.some((e) => e.includes("socket")));
  const ramDdr5 = catalogo.find((p) => p.categoria === "memoria_ram" && p.ddr === "DDR5");
  itensRam(build)[0].id = ramDdr5.id;
  assert.ok(avaliarBuild(build,catalogo).erros.some((e) => e.includes("DDR5")));
});

test("usa potencia_w da seed e acusa fonte insuficiente", () => {
  const build = base();
  const fraca = { ...peca("SEED-PSU-01"), id:"fonte-teste", potencia_w:10 };
  build.componentes.fonte.id = fraca.id;
  assert.ok(avaliarBuild(build,[...catalogo,fraca]).erros.some((e) => e.includes("potência")));
});

test("não confunde suporte a mATX com suporte a ATX", () => {
  const build = base();
  const placa = { ...peca("SEED-MB-03"), id:"placa-atx", formato:"ATX" };
  const gabinete = { ...peca("SEED-CASE-04"), id:"gabinete-matx", formatos_placa_mae:"mATX, ITX" };
  build.componentes.placa_mae.id = placa.id;
  build.componentes.gabinete = {id:gabinete.id, quantidade:1};
  assert.ok(avaliarBuild(build,[...catalogo,placa,gabinete]).erros.some((e) => e.includes("formato")));
});

test("peças próprias não geram preço inventado ou sucesso de compatibilidade", () => {
  const build = normalizarBuild({ componentes:{ processador:{ proprio:"Meu Ryzen",quantidade:1 } } });
  const resultado = avaliarBuild(build,catalogo);
  assert.equal(resultado.preco,0);
  assert.equal(resultado.status,"incompleta");
  assert.ok(resultado.avisos.some((e) => e.includes("própria")));
});

test("privada não compartilha; pública gera uma cópia com acentos e componentes", () => {
  const build = base();
  assert.throws(() => linkCompartilhado(build), /pública/);
  build.visibilidade = "publico"; build.titulo = "Configuração do João";
  const params = new URL(linkCompartilhado(build)).searchParams;
  const copia = abrirBuild(params);
  assert.equal(copia.titulo,build.titulo);
  assert.deepEqual(copia.componentes,build.componentes);
  assert.notEqual(copia.id,build.id);
  assert.throws(() => abrirBuild(new URLSearchParams({ compartilhar:"invalido" })), /inválido/);
});

test("tranca impede seleção e rascunho preserva alterações ainda não salvas", () => {
  const build = base(); build.travada = true;
  assert.throws(() => selecionarPeca(build,peca("SEED-CPU-03"),catalogo), /Destranque/);
  build.travada = false;
  salvarNoPerfilLocal(build);
  const alterada = selecionarPeca(removerPeca(build,"processador"),peca("SEED-CPU-03"),catalogo);
  guardarRascunho(alterada);
  assert.equal(abrirBuild(new URLSearchParams({id:build.id})).componentes.processador.id,"SEED-CPU-03");
  assert.ok(buildsLocais().some((b) => b.id === build.id));
});

test("renderização da lista e tranca preservam componentes e nome do rascunho", () => {
  const salva = base();
  salvarNoPerfilLocal(salva);
  const rascunho = selecionarPeca(removerPeca(salva,"processador"),peca("SEED-CPU-03"),catalogo);
  rascunho.titulo = "Nome ainda em edição";
  guardarRascunho(rascunho);
  sincronizarRascunho(salva);
  sincronizarRascunho(salva,{travada:true});
  const reaberta = abrirBuild(new URLSearchParams({id:salva.id}));
  assert.equal(reaberta.componentes.processador.id,"SEED-CPU-03");
  assert.equal(reaberta.titulo,rascunho.titulo);
  assert.equal(reaberta.travada,true);
});

test("perfil local limita três builds, permitindo atualizar uma existente", () => {
  memoria.clear();
  const builds = [base(),base(),base()];
  builds.forEach(salvarNoPerfilLocal);
  assert.throws(() => salvarNoPerfilLocal(base()), /Limite/);
  salvarNoPerfilLocal({...builds[0],titulo:"Atualizada"});
  assert.equal(buildsLocais().length,3);
});

test("ofertas distinguem link de produto das buscas e texto é escapado", () => {
  const ofertas = ofertasPeca(peca("SEED-CPU-02"));
  assert.equal(ofertas.length,3);
  assert.equal(ofertas[0].direta,true);
  assert.equal(ofertas[1].direta,false);
  assert.equal(ofertas[2].direta,false);
  assert.equal(htmlSeguro('<script>"x"</script>'),"&lt;script&gt;&quot;x&quot;&lt;/script&gt;");
});

test("migra a RAM antiga para lista sem perder modelo ou quantidade", () => {
  const build = normalizarBuild({componentes:{memoria_ram:{id:"SEED-RAM-01",quantidade:2}}});
  assert.deepEqual(build.componentes.memoria_ram,[{id:"SEED-RAM-01",quantidade:2}]);
  assert.equal(normalizarBuild({componentes:{memoria_ram:[null,{}]}}).componentes.memoria_ram,undefined);
});

test("adiciona outra marca e capacidade de RAM, com aviso e total correto", () => {
  const build = base(), original = peca("SEED-RAM-01");
  const outra = {...original,id:"ram-outra-marca",fabricante:"Outra marca",capacidade_gb:32,quantidade_pentes:1};
  const cat = [...catalogo,outra], depois = selecionarPecaCompativel(build,outra,cat);
  assert.equal(itensRam(depois).length,2);
  assert.equal(informacoesRam(depois,cat).usados,original.quantidade_pentes + 1);
  assert.equal(avaliarBuild(depois,cat).preco - avaliarBuild(build,cat).preco,outra.preco);
  assert.ok(avaliarBuild(depois,cat).avisos.some(a => a.includes("Misturar")));
});

test("RAM adicional precisa manter DDR e frequência", () => {
  const build = base(), original = peca("SEED-RAM-01");
  for (const outra of [
    {...original,id:"ram-ddr-diferente",ddr:"DDR5"},
    {...original,id:"ram-frequencia-diferente",frequencia_mhz:original.frequencia_mhz + 200},
  ]) {
    const cat = [...catalogo,outra];
    assert.equal(pecaCompativel(build,outra,cat),false);
    assert.throws(() => selecionarPeca(build,outra,cat),/DDR.*frequência/);
  }
});

test("limite e remoção de RAM consideram todos os modelos da build", () => {
  const original = {...peca("SEED-RAM-01"),id:"kit-dois",quantidade_pentes:2,capacidade_gb:16};
  const outra = {...original,id:"kit-um",quantidade_pentes:1};
  const cat = [...catalogo,original,outra];
  let build = base(); build.componentes.memoria_ram = [{id:original.id,quantidade:1}];
  build = selecionarPeca(build,outra,cat);
  assert.equal(limiteRam(build,cat,original.id),1);
  assert.throws(() => selecionarPeca(build,original,cat),/slots/);
  const removida = removerPeca(build,"memoria_ram",outra.id);
  assert.equal(itensRam(removida).length,1);
  assert.equal(limiteRam(removida,cat,original.id),2);
  assert.equal(informacoesRam(selecionarPeca(removida,original,cat),cat).usados,4);
});

test("limita capacidade máxima de RAM além dos slots", () => {
  const original = peca("SEED-RAM-01");
  const grande = {...original,id:"ram-grande",capacidade_gb:256,quantidade_pentes:1};
  assert.throws(() => selecionarPeca(base(),grande,[...catalogo,grande]),/capacidade/);
});

test("não troca a peça atual silenciosamente: é necessário remover primeiro", () => {
  assert.throws(() => selecionarPeca(base(),peca("SEED-CPU-03"),catalogo),/Remova/);
  const build = removerPeca(base(),"processador");
  assert.equal(selecionarPeca(build,peca("SEED-CPU-03"),catalogo).componentes.processador.id,"SEED-CPU-03");
});

test("filtragem exclui processadores incompatíveis com a placa já selecionada", () => {
  const build = removerPeca(base(),"processador");
  const socket = peca("SEED-MB-03").socket;
  const outra = catalogo.find(p => p.categoria === "processador" && p.soquete !== socket);
  assert.equal(pecaCompativel(build,outra,catalogo),false);
  assert.equal(pecaCompativel(build,peca("SEED-CPU-02"),catalogo),true);
  assert.throws(() => selecionarPecaCompativel(build,outra,catalogo),/socket/);
});

test("fans são obrigatórias e cooler depende do cooler incluso no processador", () => {
  const build = base(), cpu = peca("SEED-CPU-02");
  const semCooler = {...cpu,cooler:false}, comCooler = {...cpu,cooler:true};
  assert.ok(avaliarBuild(build,catalogo.map(p => p.id === cpu.id ? semCooler : p)).faltam.includes("Cooler para o processador"));
  assert.ok(!avaliarBuild(build,catalogo.map(p => p.id === cpu.id ? comCooler : p)).faltam.includes("Cooler para o processador"));
  assert.ok(avaliarBuild(build,catalogo).faltam.includes("Fans"));
  assert.ok(categoriasEditor.findIndex(c => c.id === "fan") < categoriasEditor.findIndex(c => c.id === "cooler"));
  assert.deepEqual(categoriaCatalogo("cooler").tipos,["air_cooler","water_cooler"]);
});

test("fonte igual ao consumo produz aviso; potência acima dele não gera recomendação", () => {
  const build = base(), watts = avaliarBuild(build,catalogo).watts;
  const igual = {...peca("SEED-PSU-01"),potencia_w:watts};
  const cat = catalogo.map(p => p.id === igual.id ? igual : p);
  assert.ok(avaliarBuild(build,cat).avisos.some(a => a.includes("fonte")));
  igual.potencia_w += 1;
  const resultado = avaliarBuild(build,cat);
  assert.ok(!resultado.avisos.some(a => a.includes("fonte")));
  assert.equal("recomendado" in resultado,false);
});

test("cada loja recebe seu próprio preço, sem usar o preço da seed como cotação", () => {
  const produto = {...peca("SEED-CPU-02"),ofertas:[
    {loja:"kabum",preco:1200,url:"https://www.kabum.com.br/produto/1"},
    {loja:"pichau",preco:1100,url:"https://www.pichau.com.br/produto-exemplo"},
    {loja:"mercadolivre",preco:1250,url:"https://produto.mercadolivre.com.br/MLB-exemplo"},
  ]};
  assert.deepEqual(ofertasPeca(produto).map(o => o.preco),[1200,1100,1250]);
  assert.deepEqual(ofertasPeca(peca("SEED-CPU-02")).map(o => o.preco),[null,null,null]);
  produto.ofertas[1].url = "javascript:alert(1)";
  assert.equal(ofertasPeca(produto)[1].direta,false);
});

test("loading completo apenas na primeira visita da sessão e sempre na home", () => {
  assert.equal(escolherModoLoading({home:false,visitada:false}),"full");
  assert.equal(escolherModoLoading({home:false,visitada:true}),"fade");
  assert.equal(escolherModoLoading({home:true,visitada:true}),"full");
});

test("carregamento aguarda as tarefas reais inclusive quando uma delas falha", async () => {
  let terminou = false;
  acompanharCarregamento(new Promise(resolve => setTimeout(() => { terminou = true; resolve(); },55)));
  acompanharCarregamento(Promise.reject(new Error("Falha simulada"))).catch(() => {});
  await aguardarCarregamentos();
  assert.equal(terminou,true);
});
