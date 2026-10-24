import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {criarAnunciadorStatus} from "../js/components/status-messages.js";

function relogio() {
  let agora=0,id=0;
  const fila=new Map(),publicadas=[];
  const anunciador=criarAnunciadorStatus({
    publicar:(texto,urgente)=>{publicadas.push({texto,urgente});},
    agendar:(fn,atraso)=>{fila.set(++id,{fn,tempo:agora+atraso});return id;},
    cancelar:id=>fila.delete(id),
  });
  return {anunciador,publicadas,avancar(ms) {
    agora+=ms;
    for (const [id,tarefa] of fila) if (tarefa.tempo<=agora) {fila.delete(id);tarefa.fn();}
  }};
}

test("cem movimentos anunciam só o último resumo após a pausa",()=>{
  const {anunciador,publicadas,avancar}=relogio();
  for(let i=0;i<100;i++){anunciador.anunciar("Total da build: R$ "+i);avancar(10);}
  assert.equal(publicadas.length,0);avancar(700);
  assert.deepEqual(publicadas,[{texto:"Total da build: R$ 99",urgente:false}]);
});
test("erro cancela o sucesso antigo e usa o canal urgente sem esperar o debounce longo",()=>{
  const {anunciador,publicadas,avancar}=relogio();
  anunciador.anunciar("Salvo");avancar(100);
  anunciador.anunciar("Não foi possível salvar",{urgente:true});avancar(50);avancar(1000);
  assert.deepEqual(publicadas,[{texto:"Não foi possível salvar",urgente:true}]);
});
test("deduplica mensagem igual mas permite nova confirmação após uma nova edição",()=>{
  const {anunciador,publicadas,avancar}=relogio();
  anunciador.anunciar("Salvo");avancar(700);anunciador.anunciar("Salvo");avancar(700);
  assert.equal(publicadas.length,1);
  anunciador.cancelar(true);anunciador.anunciar("Salvo");avancar(700);
  assert.equal(publicadas.length,2);
});
test("cancelar ou esvaziar remove mensagens pendentes e mantém texto literal",()=>{
  const {anunciador,publicadas,avancar}=relogio();
  anunciador.anunciar("Página anterior");anunciador.cancelar();avancar(1000);
  anunciador.anunciar("Antigo");anunciador.anunciar(" ");avancar(1000);
  assert.equal(publicadas.length,0);
  anunciador.anunciar("<script>texto</script>");avancar(700);
  assert.equal(publicadas[0].texto,"<script>texto</script>");
});
test("mensagem descartada por contexto inativo pode ser anunciada no contexto correto",()=>{
  const fila=[];let ativo=false,entregas=0;
  const anunciador=criarAnunciadorStatus({agendar:fn=>{fila.push(fn);return fila.length;},cancelar:()=>{},publicar:()=>{if(!ativo)return false;entregas++;}});
  anunciador.anunciar("Salvo");fila.shift()();
  ativo=true;anunciador.anunciar("Salvo");fila.shift()();
  assert.equal(entregas,1);
});
test("formulário não transmite cada porcentagem nem cada frase decorativa da espera",async()=>{
  const forms=await readFile(new URL("../js/pages/forms.js",import.meta.url),"utf8");
  assert.doesNotMatch(forms,/id="peripheral-budget-summary"[^>]*aria-live/);
  assert.doesNotMatch(forms,/<h2[^>]*role="status"[^>]*id="generation-message"/);
  assert.match(forms,/if \(anunciar && resumo\) anunciarStatus\(resumo.textContent\)/);
  const editor=await readFile(new URL("../js/pages/configuracao-build.js",import.meta.url),"utf8");
  assert.doesNotMatch(editor,/id="build-autosave-status"[^>]*(role="status"|aria-live)/);
  assert.match(editor,/if \(revisao === revisaoSalvamento\) anunciarResumoSalvo\(\)/);
  assert.match(editor,/build.titulo.trim\(\) !== tituloSalvo \|\| falhaSalvamento/);
});
