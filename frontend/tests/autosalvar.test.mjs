import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { salvarAlteracaoLocal } from "../js/build/autosalvar.js";
import { normalizarBuild, buildsLocais, abrirBuild, selecionarPeca, removerPeca } from "../js/build/estado.js";
import { avaliarBuild } from "../js/build/compatibilidade.js";
import { importarBuild, exportarJson, exportarCsv } from "../js/build/arquivos.js";
import { camposRede } from "../js/build/rede.js";

const catalogo = JSON.parse(await readFile(new URL("../data/catalogo-demo.json",import.meta.url),"utf8"));
function iniciar() {
  const dados = new Map();
  globalThis.localStorage = {getItem:k => dados.get(k) ?? null,setItem:(k,v) => dados.set(k,String(v))};
  globalThis.sessionStorage = {getItem:() => null,removeItem:() => {}};
}
test("alterações salvam novas builds e atualizam a mesma identidade sem duplicar",() => {
  iniciar(); const build = normalizarBuild({titulo:"Build automática"});
  assert.equal(buildsLocais().length,0);
  assert.equal(salvarAlteracaoLocal(build,catalogo).salvo,true);
  build.descricao = "Nova descrição"; build.orcamento = 4000;
  salvarAlteracaoLocal(build,catalogo);
  assert.equal(buildsLocais().length,1);
  const aberta = abrirBuild(new URLSearchParams({id:build.id}));
  assert.equal(aberta.descricao,"Nova descrição"); assert.equal(aberta.orcamento,4000);
  assert.equal(buildsLocais()[0].progresso,0);
});
test("quota mantém rascunho sem criar quarta build e permite editar uma já salva",() => {
  iniciar(); const salvas = [1,2,3].map(n => normalizarBuild({titulo:"Build " + n}));
  salvas.forEach(b => salvarAlteracaoLocal(b,catalogo));
  const nova = normalizarBuild({titulo:"Quarta build"});
  assert.equal(salvarAlteracaoLocal(nova,catalogo).salvo,false);
  assert.equal(buildsLocais().length,3);
  assert.equal(abrirBuild(new URLSearchParams({id:nova.id})).titulo,nova.titulo);
  salvas[0].titulo = "Editada"; assert.equal(salvarAlteracaoLocal(salvas[0],catalogo).salvo,true);
  assert.equal(buildsLocais()[0].titulo,"Editada");
});
test("nome vazio não substitui a build salva e tranca em outra aba bloqueia gravação",() => {
  iniciar(); const build = normalizarBuild({titulo:"Original"});
  salvarAlteracaoLocal(build,catalogo); build.titulo = " ";
  assert.equal(salvarAlteracaoLocal(build,catalogo).salvo,false);
  assert.equal(buildsLocais()[0].titulo,"Original");
  localStorage.setItem("boostio:builds-locais",JSON.stringify([{...build,titulo:"Original",travada:true}]));
  assert.throws(() => salvarAlteracaoLocal({...build,titulo:"Editada"},catalogo),/Destranque/);
  assert.equal(buildsLocais()[0].titulo,"Original");
});
test("rede usa produtos de catálogo, sem custo manual nem exigência de conclusão",() => {
  iniciar(); let build = normalizarBuild();
  const cabo = {id:"TEST-LAN",categoria:"cabo_rede",fabricante:"Teste",modelo:"Cabo",preco:20,consumo_energia:10};
  const cat = [...catalogo,cabo], antes = avaliarBuild(build,cat);
  build = selecionarPeca(build,cabo,cat);
  assert.equal(build.incluirRede,true);
  const depois = avaliarBuild(build,cat);
  assert.equal(depois.preco,antes.preco + 20); assert.equal(depois.watts,antes.watts);
  assert.equal(depois.total,antes.total); assert.equal(depois.preenchidos,antes.preenchidos);
  for (const [tipo,exportar] of [["json",exportarJson],["csv",exportarCsv]]) {
    const copia = importarBuild(exportar(build,cat),tipo,cat);
    assert.equal(copia.incluirRede,true); assert.equal(copia.componentes.cabo_rede.id,cabo.id);
  }
  build = removerPeca(build,"cabo_rede"); assert.equal(build.componentes.cabo_rede,undefined);
  assert.doesNotMatch(camposRede({tipo:"cabo",possuiAcessorio:false}),/data-network="custoPrevisto"/);
});
