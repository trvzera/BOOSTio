import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { importarBuild } from "../js/build/arquivos.js";
import { mostrarFalha } from "../js/build/interface.js";

const ler = caminho => readFile(new URL(caminho,import.meta.url),"utf8");

test("as duas fontes declaradas existem e são arquivos WOFF2 íntegros no caminho do CSS",async () => {
  const caminho = new URL("../styles/utilitarios/tipografia.css",import.meta.url);
  const css = await readFile(caminho,"utf8");
  const faces = [...css.matchAll(/@font-face\s*\{([^}]+)\}/g)].map(m => m[1]);
  for (const familia of ["Lexend","Poppins"]) {
    const face = faces.find(bloco => bloco.includes('font-family: "' + familia + '"'));
    assert.ok(face,familia);
    const arquivo = await readFile(new URL(face.match(/url\("([^"]+)"\)/)[1],caminho));
    assert.equal(arquivo.subarray(0,4).toString(),"wOF2",familia);
    assert.equal(arquivo.readUInt32BE(8),arquivo.length,familia);
    assert.match(face,/font-display: swap/);
  }
});

test("mensagens têm fonte de texto explícita sem alterar títulos ou a escala original",async () => {
  const css = await ler("../styles/componentes/feedback.css");
  for (const seletor of [".form-error",".planning-help",".test-feedback",".prontas-feedback",".compare-feedback",".build-autosave-status",".toast","#toast-text","#builder-feedback","#builds-account-status","#build-import-status","#erro-gerar-build","#ui-tooltip",".catalog-empty > p"])
    assert.ok(css.includes(seletor),seletor);
  assert.match(css,/font-family: var\(--font-body, "Poppins", sans-serif\)/);
  assert.match(css,/overflow-wrap: anywhere/);
  assert.doesNotMatch(css,/(?:^|\n)(?:body|h[1-6]|\.font-[12]-)[^{]*\{/);
  assert.doesNotMatch(css,/font-size:\s*[\d.]+px/);
  const raiz = await ler("../styles/style.css");
  assert.ok(raiz.indexOf('"./componentes/feedback.css"') > raiz.indexOf('"./componentes/benchmark.css"'));
});

test("importação e carregamento de builds distinguem erro de validação bem-sucedida",async () => {
  const js = await ler("../js/pages/builds-conta.js");
  assert.match(js,/status\.dataset\.tone = "error"/);
  assert.match(js,/status\.dataset\.tone = "info"/);
  assert.match(js,/informarImportacao\(erro\.message,"error"\)/);
  assert.match(js,/informarImportacao\(candidata\.titulo \+ " · arquivo validado","success"\)/);
  const css = await ler("../styles/build/recursos.css");
  assert.match(css,/\.planning-help\[data-tone="error"\] \{ color: var\(--status-error\)/);
  assert.match(css,/\.planning-help\[data-tone="success"\] \{ color: var\(--status-success\)/);
});

test("a validação mantém IDs desconhecidos bloqueados independentemente da apresentação",() => {
  const arquivo = JSON.stringify({titulo:"Exemplo",componentes:{processador:{id:"SEED-CPU-02",quantidade:1}}});
  assert.throws(() => importarBuild(arquivo,"json",[{categoria:"processador",id:"processador:1"}]),{
    message:"ID desconhecido para a categoria processador: SEED-CPU-02.",
  });
});

test("falhas do backend são apresentadas como texto e preservam a fonte do título",t => {
  const mensagem = 'Não foi possível carregar <img src=x onerror="alert(1)">';
  const paragrafo = {textContent:""};
  const span = {textContent:""}, attrs = {};
  const voltar = {setAttribute(k,v){attrs[k]=v;},querySelector:()=>span};
  const container = {innerHTML:"",querySelector:seletor => seletor === "a" ? voltar : paragrafo};
  const locationAnterior=globalThis.location;
  globalThis.location={href:"https://boostio.example/pages/pecas.html?build=s-1"};
  t.after(()=>{if(locationAnterior)globalThis.location=locationAnterior;else delete globalThis.location;});
  mostrarFalha(container,new Error(mensagem));
  assert.equal(paragrafo.textContent,mensagem);
  assert.doesNotMatch(container.innerHTML,/<img/);
  assert.match(container.innerHTML,/<h1 class="font-1-l">/);
  assert.match(container.innerHTML,/<p class="font-2-s" role="alert">/);
  assert.equal(attrs.href,"./configuracao-build.html?build_id=s-1");
  assert.equal(attrs["aria-label"],"Voltar à build");
  assert.equal(span.textContent,"Voltar à build");
});
