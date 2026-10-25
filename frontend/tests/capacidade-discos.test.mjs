import test from "node:test";
import assert from "node:assert/strict";
import { informacoesArmazenamento, resumoCapacidadeDiscos } from "../js/build/estado.js";
test("total de SSD/HD respeita duplicatas e usa TB decimal do fabricante",()=>{
  const catalogo=[{id:"ssd",categoria:"ssd",capacidade_gb:500},{id:"hd",categoria:"hd",capacidade_gb:2000}];
  const build={componentes:{ssd:[{id:"ssd",quantidade:2}],hd:[{id:"hd",quantidade:1}]}};
  assert.equal(resumoCapacidadeDiscos(informacoesArmazenamento(build,catalogo)),"3 TB no total");
  build.componentes={ssd:[{id:"ssd",quantidade:1}]};
  assert.equal(resumoCapacidadeDiscos(informacoesArmazenamento(build,catalogo)),"500 GB no total");
});
test("capacidade desconhecida não vira total completo nem armazenamento zero confirmado",()=>{
  const itens=[{item:{quantidade:1},peca:{capacidade_gb:500}},{item:{quantidade:1},peca:null}];
  assert.equal(resumoCapacidadeDiscos({itens}),"500 GB conhecidos · parcial");
  for(const capacidade_gb of [null,undefined,NaN,Infinity,-1,0])
    assert.equal(resumoCapacidadeDiscos({itens:[{item:{quantidade:1},peca:{capacidade_gb}}]}),"Capacidade não informada");
});
test("disco próprio só soma com modelo exato e único, sem alterar seleção ou preço",()=>{
  const catalogo=[{id:"ssd:1",categoria:"ssd",fabricante:"Marca",modelo:"Disco 1 TB",capacidade_gb:1000,preco:500}];
  const build={componentes:{ssd:[{proprio:"Marca Disco 1 TB",quantidade:2}]}};
  const info=informacoesArmazenamento(build,catalogo),antes=structuredClone(build);
  assert.equal(resumoCapacidadeDiscos(info,catalogo),"2 TB no total");
  assert.deepEqual(build,antes);
  assert.equal(resumoCapacidadeDiscos(info,[...catalogo,{...catalogo[0],id:"ssd:2"}]),"Capacidade não informada");
});
