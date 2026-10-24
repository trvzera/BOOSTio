import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { completarMedidas } from "../js/build/medidas-fisicas.js";
import { informacoesFans, encaixeRadiador } from "../js/build/fans.js";
import { validarEncaixe } from "../js/build/hardware.js";
import { fichaTecnica } from "../js/build/catalogo.js";

const ler = caminho => JSON.parse(readFileSync(new URL(caminho,import.meta.url)));
const manifesto = ler("../data/medidas-fisicas.json");
const casos = ler("./fixtures/gabinetes-ventilacao.json");
const base = c => ({categoria:"gabinete",fabricante:c.fabricante,modelo:c.modelo,part_number:c.part_number,
  link:"https://www.kabum.com.br/produto/"+c.produto_kabum});
const gabinete = codigo => completarMedidas(base(casos.find(c=>c.part_number===codigo)),manifesto);
const fans = (quantidade,tamanho=120,kit=1) => quantidade ? [{item:{quantidade},peca:{quantidade:kit,tamanho_mm:tamanho}}] : [];

for (const caso of casos) {
  test("gabinete revisado: identidade, medidas e desconhecidos — "+caso.part_number,()=>{
    const original={...base(caso),fans_inclusos:null,preco:123,imagem:"foto.webp",esgotado:true,ofertas:[{loja:"kabum",preco:123}]};
    const p=completarMedidas(original,manifesto);
    for (const [k,v] of Object.entries(caso.esperado)) assert.deepEqual(p[k],v,k);
    for (const k of ["preco","imagem","esgotado","ofertas","modelo","part_number","link"]) assert.deepEqual(p[k],original[k]);
    assert.equal(original.fans_inclusos,null);
    assert.equal(p.ficha_tecnica_verificada_em,"2026-10-23");
    assert.match(p.fonte_medidas,/^https:\/\//);
    for (const alteracao of [{part_number:"outro"},{modelo:caso.modelo+" RGB"},{fabricante:"outro"},{link:"https://www.kabum.com.br/produto/999999"},{link:null}])
      assert.equal(completarMedidas({...base(caso),...alteracao},manifesto).fonte_medidas,undefined);
    const texto=fichaTecnica(p).map(r=>r.join(": ")).join("\n");
    assert.ok(texto.includes(p.modelo_ficha_tecnica));
    assert.ok(!texto.includes("[object Object]"));
  });

  test("fans de fábrica, espaço adicional e excesso — "+caso.part_number,()=>{
    const p=completarMedidas(base(caso),manifesto), vazio=informacoesFans(p);
    assert.equal(vazio.total,caso.esperado.fans_inclusos);
    assert.equal(vazio.livres,caso.extras);
    assert.equal(vazio.distribuicao,caso.distribuicao_sem_extras);
    const cheio=informacoesFans(p,fans(caso.extras,caso.diametro_extras));
    assert.equal(cheio.total,caso.esperado.quantidade_max_fans);
    assert.equal(cheio.quantidade,true);
    assert.equal(cheio.livres,0);
    const excesso=informacoesFans(p,fans(caso.extras+1,caso.diametro_extras));
    assert.equal(excesso.quantidade,false);
    assert.equal(excesso.distribuicao,false);
    assert.equal(informacoesFans(p,fans(1,360)).tamanhos,false);
  });
}

test("DeepCool conta kits, alternativas e AIO sem duplicar posições",()=>{
  const p=gabinete("SEED-CASE-40");
  assert.equal(informacoesFans(p,fans(2,120,2)).total,8);
  assert.equal(informacoesFans(p,fans(3,120,2)).quantidade,false);
  // Três fans de 140 frontais + uma traseira, duas AIO no topo e duas avulsas na cobertura.
  const water={quantidade_fans:2,tamanho_fan_mm:120,tamanho_radiador_mm:240};
  const info=informacoesFans(p,fans(2),water);
  assert.equal(info.total,8);assert.equal(info.distribuicao,true);
  assert.equal(informacoesFans(p,fans(3),water).quantidade,false);
  assert.equal(informacoesFans(p,fans(3,140)).distribuicao,false);
  assert.equal(encaixeRadiador(p,water),null); // nominal não confirma espessura real
});

test("MSI não aceita fan de 120 mm nem transforma radiador ausente em suporte",()=>{
  const p=gabinete("KABUM-1017873");
  assert.equal(informacoesFans(p,fans(1)).tamanhos,false);
  assert.equal(informacoesFans(p,fans(1)).quantidade,false);
  const r=validarEncaixe({gabinete:p,water:{tamanho_radiador_mm:120}});
  assert.ok(r.avisos.some(a=>/radiador|folgas/.test(a)));
  assert.equal(encaixeRadiador(p,{tamanho_radiador_mm:120}),null);
});

test("H5 separa 2024 e mantém condicionais/desacordos desconhecidos",()=>{
  const p=gabinete("SEED-CASE-43");
  assert.ok(p.posicoes_fans.find(g=>g.nome==="Frente").radiadores_mm.includes(280));
  assert.ok(!p.posicoes_fans.find(g=>g.nome==="Topo").radiadores_mm.includes(280));
  assert.match(p.observacoes_medidas,/perfil baixo/);
  assert.equal(p.tamanho_max_gpu_mm,null);assert.equal(p.tamanho_max_cooler_mm,null);
  const r=validarEncaixe({gabinete:p,gpu:{comprimento_mm:415},air:{altura_mm:172}});
  assert.ok(r.avisos.some(a=>a.includes("Faltam medidas")));
  assert.equal(encaixeRadiador(p,{tamanho_radiador_mm:280}),null);
});

test("Hayom não adivinha eixos, radiadores ou posição das três fans do GB1787",()=>{
  for (const codigo of ["KABUM-938469","KABUM-933255"]) {
    const p=gabinete(codigo);
    for (const k of ["comprimento_mm","largura_mm","altura_mm","tamanho_max_cooler_mm","tamanho_max_fonte_mm"]) assert.equal(p[k],undefined);
    assert.equal(p.suporte_water_cooler,null);
    assert.equal(encaixeRadiador(p,{tamanho_radiador_mm:240}),null);
  }
  assert.equal(gabinete("KABUM-933255").posicoes_fans,undefined);
});
