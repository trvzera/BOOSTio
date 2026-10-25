import test from "node:test";
import assert from "node:assert/strict";
import { iniciarFluxoVerificacaoEmail } from "../js/components/verification-flow.js";

const drenar=()=>new Promise(r=>setImmediate(r));
function ambiente(t,{enviar=async()=>{},confirmar=async()=>({usuario:{verificado:true}}),aoConfirmar=()=>{}}={}) {
  let tempo=100000,focos=0,ativo;
  const elemento=()=>({value:"",textContent:"",disabled:false,isConnected:true,handlers:{},
    addEventListener(e,h){this.handlers[e]=h;},setAttribute(k,v){this[k]=v;},focus(){focos++;ativo=this;}});
  const inputs=Array.from({length:6},elemento),classes=new Set();
  const elementos=Object.fromEntries(["btn-send-code","btn-confirm-code","verify-email-error","verify-email-status","verify-email-target"].map(id=>["#"+id,elemento()]));
  const modal={querySelector:s=>elementos[s],querySelectorAll:()=>inputs,addEventListener(){},
    classList:{add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c)}};
  const fluxo=iniciarFluxoVerificacaoEmail({modal,enviar,confirmar,aoConfirmar,agora:()=>tempo});
  t.after(()=>fluxo.destruir());
  return {fluxo,inputs,elementos,modal,focos:()=>focos,ativo:()=>ativo,avancar:ms=>tempo+=ms,
    digitar(codigo){inputs[0].value=codigo;inputs[0].handlers.input();}};
}
const usuario={id:1,email:"teste@example.test",verificado:false};

test("envia uma vez automaticamente e não repete ao reabrir, nem durante o envio",async t=>{
  let envios=0,terminar;
  const a=ambiente(t,{enviar:()=>{envios++;return new Promise(r=>terminar=r);}});
  a.fluxo.abrir(usuario);a.fluxo.fechar();a.fluxo.abrir(usuario);
  assert.equal(envios,1);assert.ok(a.inputs.every(i=>i.disabled));
  terminar();await drenar();a.fluxo.fechar();a.fluxo.abrir(usuario);
  assert.equal(envios,1);assert.ok(a.inputs.every(i=>!i.disabled));
});

test("sexto dígito/autofill confirma uma única vez e não exige clicar",async t=>{
  let consultas=0,sucessos=0,terminar;
  const a=ambiente(t,{confirmar:async(id,codigo)=>{
    assert.equal(id,1);assert.equal(codigo,"123456");consultas++;
    await new Promise(r=>terminar=r);return {usuario:{verificado:true}};
  },aoConfirmar:()=>sucessos++});
  a.fluxo.abrir(usuario);await drenar();a.digitar("123456");
  a.inputs[5].handlers.input();a.elementos["#btn-confirm-code"].handlers.click();
  assert.equal(consultas,1);terminar();await drenar();
  assert.equal(sucessos,1);assert.equal(a.modal.classList.contains("open"),false);
});

test("falha não gasta tentativas repetidas do mesmo código; edição permite nova tentativa",async t=>{
  let consultas=0;
  const a=ambiente(t,{confirmar:async()=>{consultas++;throw Error("Código incorreto");}});
  a.fluxo.abrir(usuario);await drenar();a.digitar("123456");await drenar();
  a.inputs[5].handlers.input();await drenar();assert.equal(consultas,1);
  assert.equal(a.elementos["#verify-email-error"].textContent,"Código incorreto");
  a.inputs[5].value="7";a.inputs[5].handlers.input();await drenar();assert.equal(consultas,2);
});

test("cooldown protege reenvio e falha de rede não dispara loop ao reabrir",async t=>{
  let envios=0;
  const a=ambiente(t,{enviar:async()=>{envios++;if(envios===1)throw Error("Sem conexão");}});
  a.fluxo.abrir(usuario);await drenar();a.fluxo.fechar();a.fluxo.abrir(usuario);await drenar();
  assert.equal(envios,1);assert.equal(a.inputs[0].disabled,true);
  a.elementos["#btn-send-code"].handlers.click();await drenar();assert.equal(envios,2);
  a.elementos["#btn-send-code"].handlers.click();await drenar();assert.equal(envios,2);
  a.avancar(30001);a.elementos["#btn-send-code"].handlers.click();await drenar();assert.equal(envios,3);
});

test("código rejeitado devolve foco ao campo para corrigir e não repete o envio",async t=>{
  let envios=0;
  const a=ambiente(t,{enviar:async()=>envios++,confirmar:async()=>{throw Error("Código incorreto");}});
  a.fluxo.abrir(usuario);await drenar();a.digitar("001234");await drenar();
  assert.equal(a.inputs.map(i=>i.value).join(""),"001234");
  assert.equal(a.ativo(),a.inputs[0]);
  assert.equal(a.inputs[0].disabled,false);
  assert.equal(a.modal.classList.contains("open"),true);
  assert.equal(envios,1);
});

test("resposta de destino anterior não altera a verificação de outro e-mail",async t=>{
  const envios=[];
  const a=ambiente(t,{enviar:id=>new Promise(resolve=>envios.push({id,resolve}))});
  a.fluxo.abrir(usuario);a.fluxo.abrir({...usuario,email:"novo@example.test"});
  envios[0].resolve();await drenar();assert.equal(a.inputs[0].disabled,true);
  envios[1].resolve();await drenar();assert.equal(a.inputs[0].disabled,false);
  assert.equal(a.elementos["#verify-email-target"].textContent,"novo@example.test");
});
