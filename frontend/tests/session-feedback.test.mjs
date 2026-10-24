import test from 'node:test';
import assert from 'node:assert/strict';
import { mostrarFalhaSessao, limparFalhaSessao } from '../js/components/session-feedback.js';

function ambiente(t) {
  let atual=null;
  const p={},button={focus(){this.focado=true;}},a={};
  const dialogo={open:false,attrs:{},listeners:{},
    setAttribute(k,v){this.attrs[k]=v;},addEventListener(k,v){this.listeners[k]=v;},
    querySelector(s){return {p,button,a}[s];},
    showModal(){this.open=true;},close(){this.open=false;},remove(){atual=null;},
  };
  const original=Object.getOwnPropertyDescriptor(globalThis,'document');
  const documento={querySelector(){return atual;},createElement(){return dialogo;},body:{append(e){atual=e;}}};
  Object.defineProperty(globalThis,'document',{configurable:true,value:documento});
  t.after(()=>original?Object.defineProperty(globalThis,'document',original):delete globalThis.document);
  return {dialogo,p,button,a};
}

test('falha da sessão abre diálogo, mantém nome acessível e usa texto sem HTML',t=>{
  const {dialogo,p,button,a}=ambiente(t);
  mostrarFalhaSessao(new Error('<img src=x> Falha de conexão'),async()=>{});
  assert.equal(p.textContent,'<img src=x> Falha de conexão');
  assert.equal(dialogo.open,true);assert.equal(button.focado,true);
  assert.equal(dialogo.attrs['aria-describedby'],'session-connection-message');
  assert.equal(a.href,new URL('../pages/index.html',import.meta.url).href);
  let cancelado=false;dialogo.listeners.cancel({preventDefault(){cancelado=true;}});
  assert.equal(cancelado,true);
});

test('repetir a conferência não duplica diálogo e permite tentar outra vez',async t=>{
  const {dialogo,p,button}=ambiente(t);let tentativas=0;
  const repetir=async()=>{tentativas++;mostrarFalhaSessao(new Error('Ainda sem conexão'),repetir);};
  mostrarFalhaSessao(new Error('Sem conexão'),repetir);
  await button.onclick();
  assert.equal(tentativas,1);assert.equal(p.textContent,'Ainda sem conexão');
  assert.equal(button.disabled,false);assert.equal(dialogo.open,true);
});

test('conferência bem-sucedida remove o diálogo de falha',t=>{
  const {dialogo}=ambiente(t);
  mostrarFalhaSessao(new Error('Sem conexão'),async()=>{});
  limparFalhaSessao();
  assert.equal(dialogo.open,false);assert.equal(document.querySelector('#session-connection-dialog'),null);
  assert.doesNotThrow(limparFalhaSessao);
});
