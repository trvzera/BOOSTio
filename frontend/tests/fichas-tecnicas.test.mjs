import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { completarMedidas } from "../js/build/medidas-fisicas.js";
import { completarCatalogoDemo, validarEncaixe, encaixeCoolerPlaca } from "../js/build/hardware.js";
import { fichaTecnica } from "../js/build/catalogo.js";
import { informacoesFans, encaixeRadiador } from "../js/build/fans.js";

const ler = caminho => JSON.parse(readFileSync(new URL(caminho,import.meta.url)));
const manifesto = ler("../data/medidas-fisicas.json");
const fixture = ler("./fixtures/fichas-tecnicas.json");
const peca = categoria => {
  const {esperado,...dados} = fixture.aliases.find(p => p.categoria === categoria);
  return completarMedidas(dados,manifesto);
};

for (const {esperado,...dados} of fixture.aliases) test("ficha revisada Python/JS: " + dados.modelo,() => {
  const original = {...dados,preco:123.45,imagem:"foto-local.webp",preco_atualizado_em:"2026-10-21",esgotado:true};
  const enriquecida = completarMedidas(original,manifesto);
  for (const [chave,valor] of Object.entries(esperado)) assert.deepEqual(enriquecida[chave],valor,chave);
  for (const chave of Object.keys(original)) assert.equal(enriquecida[chave],original[chave],chave);
  assert.equal(enriquecida.ficha_tecnica_verificada_em,"2026-10-23");
  assert.ok(enriquecida.modelo_ficha_tecnica && enriquecida.fonte_medidas.startsWith("https://"));
  assert.equal(original.fonte_medidas,undefined);
  for (const alteracao of [{part_number:"outra-revisao"},{modelo:dados.modelo + " V3"},{categoria:"processador"},{fabricante:"outro"},{link:undefined}]) {
    assert.equal(completarMedidas({...dados,...alteracao},manifesto).fonte_medidas,undefined);
  }
});

const {esperado,...caseBase} = fixture.aliases.find(p => p.categoria === "gabinete");
for (const link of fixture.links_aceitos_gabinete) test("alias aceita apenas produto revisado: " + link,() => {
  assert.ok(completarMedidas({...caseBase,link},manifesto).fonte_medidas);
});
for (const link of fixture.links_rejeitados_gabinete) test("alias não adivinha variante: " + JSON.stringify(link),() => {
  assert.equal(completarMedidas({...caseBase,link},manifesto).fonte_medidas,undefined);
});

test("identidade oficial com part number funciona sem depender de anúncio e não compartilha objetos",() => {
  for (const ficha of manifesto.pecas.filter(f => f.verificado_em && f.part_numbers.length)) {
    const dados = {categoria:ficha.categoria,fabricante:ficha.fabricante.toUpperCase(),modelo:ficha.modelo.toLowerCase(),part_number:ficha.part_numbers[0]};
    assert.equal(completarMedidas(dados,manifesto).fonte_medidas,ficha.fonte);
    assert.equal(completarMedidas({...dados,part_number:"outra"},manifesto).fonte_medidas,undefined);
  }
  const gabinete = peca("gabinete");
  gabinete.posicoes_fans[0].opcoes[0].quantidade = 99;
  assert.equal(peca("gabinete").posicoes_fans[0].opcoes[0].quantidade,3);
  const ambigua = {categoria:"placa_mae",fabricante:"ASRock",modelo:"H610M-HDV/M.2",part_number:"SEED-MB-22",tipo_memoria:"DDR4",link:"https://www.kabum.com.br/produto/587807/placa-mae-d5"};
  assert.equal(completarMedidas(ambigua,manifesto),ambigua);
});

test("todas as variantes ampliadas e aliases mantêm identidade, cotação e isolamento",() => {
  for (const ficha of manifesto.pecas.filter(f=>f.verificado_em)) {
    assert.ok(ficha.part_numbers.length || ficha.aliases_catalogo?.length);
    assert.match(ficha.verificado_em,/^\d{4}-\d{2}-\d{2}$/);
    for (const alias of ficha.aliases_catalogo || []) {
      const dados = {categoria:ficha.categoria,fabricante:alias.fabricante,modelo:alias.modelo,part_number:alias.part_number,
        link:"https://www.kabum.com.br/produto/" + alias.produto_kabum,preco:123.45,esgotado:true,imagem:"foto-local.webp"};
      const enriquecida = completarMedidas(dados,manifesto);
      for (const [k,v] of Object.entries(ficha.medidas)) assert.deepEqual(enriquecida[k],v,alias.part_number + " " + k);
      for (const k of ["preco","esgotado","imagem","modelo","part_number"]) assert.equal(enriquecida[k],dados[k]);
      assert.equal(completarMedidas({...dados,link:undefined},manifesto).fonte_medidas,undefined);
    }
  }
  const enriquecida = codigo => {
    const ficha = manifesto.pecas.find(f=>f.aliases_catalogo?.some(a=>a.part_number===codigo));
    const alias = ficha.aliases_catalogo.find(a=>a.part_number===codigo);
    return completarMedidas({...alias,categoria:ficha.categoria,link:"https://www.kabum.com.br/produto/"+alias.produto_kabum},manifesto);
  };
  const cpu=enriquecida("SEED-CPU-01");
  assert.equal(cpu.videointegrado,true);assert.equal(cpu.cooler,false);assert.equal(cpu.tdp_w,120);
  const fan=enriquecida("SEED-FAN-02");
  assert.equal(fan.quantidade,1);assert.equal(fan.tensao_rgb_v,12);assert.equal(fan.espessura_mm,25);
  assert.equal(enriquecida("SEED-SSD-01").velocidade_gravacao_mbps,2100);
  assert.equal(enriquecida("SEED-SSD-02").velocidade_gravacao_mbps,2100);
  assert.equal(enriquecida("SEED-SSD-03").capacidade_gb,500);
  assert.equal(enriquecida("SEED-SSD-04").velocidade_gravacao_mbps,4000);
  assert.equal(enriquecida("SEED-SSD-06").comprimento_mm,80);
  assert.equal(enriquecida("SEED-RAM-01").altura_mm,34);
});

test("dados oficiais prevalecem sobre complemento legado do catálogo demonstrativo",() => {
  const dados = {categoria:"placa_mae",fabricante:"ASUS",modelo:"Prime A520M-K",part_number:"QA"};
  const [placa] = completarCatalogoDemo([dados],{pecas:[{...dados,part_numbers:["QA"],fonte:"https://example.test/ficha",medidas:{quantidade_slots_m2:2}}]});
  assert.equal(placa.quantidade_slots_m2,2);
});

test("dimensões novas são critérios de encaixe, sem certificar folgas desconhecidas",() => {
  const gabinete = peca("gabinete"), gpu = peca("placa_video"), air = peca("air_cooler"), fonte = peca("fonte"), water = peca("water_cooler");
  assert.equal(validarEncaixe({gabinete,gpu,air,fonte}).erros.length,0);
  assert.match(validarEncaixe({gabinete:{...gabinete,tamanho_max_gpu_mm:289},gpu}).erros.join(" "),/ultrapassa/);
  assert.match(validarEncaixe({gabinete:{...gabinete,tamanho_max_cooler_mm:157},air}).erros.join(" "),/ultrapassa/);
  assert.match(validarEncaixe({gabinete:{...gabinete,tamanho_max_fonte_mm:124},fonte}).erros.join(" "),/ultrapassa/);
  const fan = quantidade => [{peca:{quantidade:1,tamanho_mm:120},item:{quantidade}}];
  assert.equal(informacoesFans(gabinete,fan(2),water).quantidade,true); // 3 fábrica + 2 AIO + 2 extras
  assert.equal(informacoesFans(gabinete,fan(3),water).quantidade,false);
  assert.equal(encaixeRadiador(gabinete,water),null); // não inventa limite real do gabinete
  assert.ok(validarEncaixe({gabinete,water}).avisos.some(a => a.includes("folgas")));
  const pequeno = {...gabinete,limites_radiador_mm:[{nome:"Topo",tamanhos_mm:[240],comprimento_mm:276,largura_mm:120,espessura_conjunto_mm:53}]};
  assert.equal(encaixeRadiador(pequeno,water),false);
});

test("placa-mãe não soma M.2 Wi-Fi como armazenamento nem inventa QVL ou frequência máxima",() => {
  const placa = peca("placa_mae");
  assert.equal(placa.quantidade_slots_m2,3);
  assert.equal(placa.quantidade_slots_m2_sata,0);
  assert.equal(placa.frequencia_maxima_mhz,undefined);
  assert.match(placa.observacoes_medidas,/Key E.*não conta/);
});

test("exceções físicas oficiais do cooler bloqueiam só os modelos exatos, mesmo sem gabinete",()=>{
  const air=manifesto.pecas.find(p=>p.modelo==="ASSASSIN IV").medidas;
  const placa={fabricante:"ASUS",modelo:"TUF GAMING B760M-PLUS WIFI"};
  assert.equal(encaixeCoolerPlaca(air,placa),false);
  assert.equal(validarEncaixe({air,placa}).erros.length,1);
  assert.equal(encaixeCoolerPlaca(air,{...placa,modelo:placa.modelo+" D4"}),null);
  assert.equal(encaixeCoolerPlaca(air,{fabricante:"MSI",modelo:"b650m ape wifi"}),false);
  assert.equal(encaixeCoolerPlaca(air,{fabricante:"MSI",modelo:"MAG B650 TOMAHAWK WIFI"}),null);
  assert.equal(encaixeCoolerPlaca({},placa),null);
});

test("ficha na interface mostra rótulos, data e posições legíveis, sem object Object",() => {
  const gabinete = peca("gabinete");
  const tabela = fichaTecnica(gabinete), linhas = Object.fromEntries(tabela);
  assert.equal(linhas["Ficha consultada em"],"23/10/2026");
  assert.match(linhas["Posições de fans e radiadores"],/Frente: 3 × 120 mm ou 2 × 140 mm; de fábrica: 3 × 120 mm/);
  assert.doesNotMatch(JSON.stringify(tabela),/\[object Object\]/);
  assert.equal(Object.fromEntries(fichaTecnica(peca("water_cooler")))["Comprimento real do radiador (mm)"],"277");
  assert.ok(!fichaTecnica({...gabinete,bays_disco:2}).some(([rotulo])=>rotulo==="Baias de armazenamento"));
  assert.ok(!fichaTecnica({...peca("air_cooler"),dimensoes:154}).some(([rotulo])=>rotulo==="Dimensão informada (mm)"));
});
