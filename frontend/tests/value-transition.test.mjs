import test from "node:test";
import assert from "node:assert/strict";
import { atualizarValor, capturarValores, transicionarValores } from "../js/components/value-transition.js";

function elemento(texto,numero,chave="total") {
  const chamadas=[], classes=new Set();
  return {textContent:texto,dataset:{valueKey:chave,...(numero == null ? {} : {valueNumber:String(numero)})},chamadas,
    classList:{add:classe=>classes.add(classe)},classes,
    animate(frames,opcoes) {
      let resolve,reject;
      const animacao={finished:new Promise((sim,nao)=>{resolve=sim;reject=nao;}),cancel(){this.cancelada=true;reject(new Error("Cancelada"));},concluir:()=>resolve()};
      chamadas.push({frames,opcoes,animacao});return animacao;
    }};
}

test("primeira exibição, mesmo valor e mudança só de formato não animam",()=>{
  const el=elemento("",null);
  atualizarValor(el,"R$ 100,00",100);
  atualizarValor(el,"R$ 100,00",100);
  atualizarValor(el,"R$ 100,00",100);
  assert.equal(el.chamadas.length,0);
  assert.equal(el.textContent,"R$ 100,00");
  assert.equal(el.dataset.valueNumber,"100");
});

test("aumento entra de baixo com blur, sem interpolar ou duplicar o preço",async()=>{
  const el=elemento("R$ 100,00",100);
  atualizarValor(el,"R$ 250,00",250);
  assert.equal(el.textContent,"R$ 250,00");
  assert.equal(el.chamadas.length,1);
  assert.equal(el.chamadas[0].frames[0].transform,"translateY(.45em)");
  assert.equal(el.chamadas[0].frames[0].filter,"blur(4px)");
  assert.equal(el.chamadas[0].opcoes.duration,360);
  assert.equal(el.chamadas[0].opcoes.fill,undefined);
  el.chamadas[0].animacao.concluir();await Promise.resolve();
  atualizarValor(el,"R$ 90,00",90);
  assert.equal(el.chamadas[1].frames[0].transform,"translateY(-.45em)");
  el.chamadas[1].animacao.concluir();
});

test("atualizações rápidas mantêm o último valor sem empilhar animações",async()=>{
  const el=elemento("100",100);
  for(let i=101;i<=300;i++)atualizarValor(el,String(i),i);
  assert.equal(el.textContent,"300");assert.equal(el.chamadas.length,1);
  el.chamadas[0].animacao.concluir();await Promise.resolve();
  atualizarValor(el,"301",301);
  assert.equal(el.chamadas.length,2);el.chamadas[1].animacao.cancel();await Promise.resolve();
  atualizarValor(el,"302",302);assert.equal(el.chamadas.length,3);el.chamadas[2].animacao.concluir();
});

test("valores inválidos ou navegador sem Web Animations atualizam sem quebrar",()=>{
  const el=elemento("100",100);delete el.animate;
  atualizarValor(el,"200",200);assert.equal(el.textContent,"200");
  atualizarValor(el,"Informe um valor",NaN);assert.equal(el.dataset.valueNumber,undefined);
  atualizarValor(el,"300",300);assert.equal(el.textContent,"300");
  atualizarValor(null,"Nada",0);
});

test("recriar cards só anima números alterados com a mesma chave estável",()=>{
  const antes=[elemento("R$ 100,00",100),elemento("1",1,"quantidade")];
  const snapshot=capturarValores({querySelectorAll:()=>antes});
  const depois=[elemento("R$ 200,00",200),elemento("1",1,"quantidade"),elemento("55",55,"novo")];
  transicionarValores({querySelectorAll:()=>depois},snapshot);
  assert.equal(depois[0].chamadas.length,1);
  assert.equal(depois[1].chamadas.length,0);assert.equal(depois[2].chamadas.length,0);
  assert.equal(depois[0].textContent,"R$ 200,00");depois[0].chamadas[0].animacao.concluir();
});

test("movimento reduzido cancela animações em curso e exibe valores imediatamente",async()=>{
  const original=globalThis.matchMedia;
  let mudar;
  const media={matches:false,addEventListener(evento,callback){assert.equal(evento,"change");mudar=callback;}};
  globalThis.matchMedia=()=>media;
  try {
    const el=elemento("100",100);atualizarValor(el,"200",200);
    media.matches=true;mudar({matches:true});await Promise.resolve();
    assert.equal(el.chamadas[0].animacao.cancelada,true);
    atualizarValor(el,"300",300);
    assert.equal(el.textContent,"300");assert.equal(el.chamadas.length,1);
    media.matches=false;
  } finally {
    if(original)globalThis.matchMedia=original;else delete globalThis.matchMedia;
  }
});
