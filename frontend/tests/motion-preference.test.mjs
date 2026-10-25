import test from "node:test";
import assert from "node:assert/strict";

let sequencia = 0;
async function ambiente(valor, executar, {sistema = false, indisponivel = false} = {}) {
  const originais = new Map(["matchMedia", "localStorage", "document", "addEventListener"].map(chave => [chave, Object.getOwnPropertyDescriptor(globalThis,chave)]));
  const eventos = new Map(), dataset = {}, media = {matches:sistema, addEventListener:(nome,fn) => eventos.set(nome,fn)};
  const storage = new Map(valor == null ? [] : [["boostio:reduce-motion",valor]]);
  let pausas = 0;
  Object.defineProperties(globalThis, {
    matchMedia:{configurable:true,value:() => media},
    localStorage:{configurable:true,value:{getItem:chave => {if(indisponivel)throw Error();return storage.get(chave)??null;},setItem:(chave,valor) => {if(indisponivel)throw Error();storage.set(chave,valor);}}},
    document:{configurable:true,value:{documentElement:{dataset},querySelectorAll:() => [{pause:() => pausas++}]}},
    addEventListener:{configurable:true,value:(nome,fn) => eventos.set(nome,fn)},
  });
  try {
    const modulo = await import("../js/components/motion-preference.js?teste=" + ++sequencia);
    await executar(modulo,{eventos,media,dataset,storage,pausas:() => pausas});
  } finally {
    for (const [chave,descriptor] of originais) {
      if(descriptor)Object.defineProperty(globalThis,chave,descriptor);else delete globalThis[chave];
    }
  }
}

test("sem escolha salva segue o sistema e reage à mudança da preferência",async () => {
  await ambiente(null,(mod,{media,eventos,dataset,pausas}) => {
    assert.equal(mod.movimentoReduzido(),false);
    media.matches = true; eventos.get("change")();
    assert.equal(mod.movimentoReduzido(),true);
    assert.equal(dataset.reducedMotion,"true"); assert.equal(pausas(),1);
  });
});
test("escolha do menu persiste, pausa vídeos e notifica controles sem recarregar",async () => {
  await ambiente("0",(mod,{eventos,media,dataset,storage}) => {
    const mudancas = [], cancelar = mod.observarMovimento(valor => mudancas.push(valor));
    mod.definirMovimentoReduzido(true);
    assert.equal(dataset.reducedMotion,"true"); assert.equal(storage.get("boostio:reduce-motion"),"1");
    mod.definirMovimentoReduzido(false);
    media.matches = true; eventos.get("change")();
    assert.equal(mod.movimentoReduzido(),false);
    assert.deepEqual(mudancas,[true,false,false]);
    cancelar(); mod.definirMovimentoReduzido(true); assert.equal(mudancas.length,3);
  });
});
test("preferência salva é aplicada na próxima página e funciona sem localStorage",async () => {
  await ambiente("1",(mod,{dataset,pausas}) => {
    assert.equal(mod.movimentoReduzido(),true); assert.equal(dataset.reducedMotion,"true"); assert.equal(pausas(),1);
  });
  await ambiente(null,mod => {
    mod.definirMovimentoReduzido(true); assert.equal(mod.movimentoReduzido(),true);
  },{indisponivel:true});
});
test("mudança em outra aba e limpeza da preferência voltam a acompanhar o sistema",async () => {
  await ambiente("0",(mod,{eventos}) => {
    eventos.get("storage")({key:"boostio:reduce-motion",newValue:"1"}); assert.equal(mod.movimentoReduzido(),true);
    eventos.get("storage")({key:"outra",newValue:"0"}); assert.equal(mod.movimentoReduzido(),true);
    eventos.get("storage")({key:null,newValue:null}); assert.equal(mod.movimentoReduzido(),false);
  });
});
