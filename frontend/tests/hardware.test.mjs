import test from "node:test";
import assert from "node:assert/strict";
import { normalizarBuild,selecionarPeca,itensCategoria,informacoesArmazenamento,removerPeca,reduzirQuantidade,linkCompartilhado,abrirBuild } from "../js/build/estado.js";
import { avaliarBuild,selecionarPecaCompativel,pecaCompativel } from "../js/build/compatibilidade.js";
import { completarCatalogoDemo } from "../js/build/hardware.js";
import { indicadorBuild } from "../js/build/indicador.js";

const placa = {id:"mb",categoria:"placa_mae",socket:"AM4",formato:"mATX",quantidade_slots_ram:4,quantidade_slots_m2:2,quantidade_portas_sata:3,quantidade_slots_m2_sata:1,portas_sata_desativadas_por_m2_sata:1};
const nvme = {id:"nvme",categoria:"ssd",interface:"PCIe 4.0",formato:"M.2",capacidade_gb:1000,preco:100,consumo_energia:4};
const sata = {...nvme,id:"sata",interface:"SATA III",formato:"2.5"};
const m2sata = {...sata,id:"m2sata",formato:"M.2"};
const hd = {...sata,id:"hd",categoria:"hd",capacidade_gb:2000};
const gabinete = {id:"case",categoria:"gabinete",formatos_placa_mae:"mATX",tamanho_max_gpu_mm:300,tamanho_max_cooler_mm:160,suporte_water_cooler:true,radiadores_suportados_mm:[120,240],tamanhos_fan_suportados_mm:[120,140],quantidade_max_fans:6,fans_inclusos:1};
const gpu = {id:"gpu",categoria:"placa_video",comprimento_mm:300};
const air = {id:"air",categoria:"air_cooler",altura_mm:160};
const water = {id:"water",categoria:"water_cooler",tamanho_radiador_mm:240,quantidade_fans:2};
const fan = {id:"fan",categoria:"fan",tamanho_mm:120,quantidade:2};
const catalogo = [placa,nvme,sata,m2sata,hd,gabinete,gpu,air,water,fan];
const base = () => normalizarBuild({componentes:{placa_mae:{id:placa.id}}});
const vazio = () => normalizarBuild();
const adicionar = (build,...pecas) => pecas.reduce((b,p) => selecionarPecaCompativel(b,p,catalogo),build);

test("migra SSD, HD e fan antigos e agrupa os modelos repetidos sem perder quantidades",() => {
  const build = normalizarBuild({componentes:{ssd:[{id:"nvme",quantidade:2},{id:"nvme",quantidade:1}],hd:{id:"hd",quantidade:2},fan:{id:"fan",quantidade:3}}});
  assert.equal(itensCategoria(build,"ssd")[0].quantidade,3);
  assert.equal(itensCategoria(build,"hd")[0].quantidade,2);
  assert.equal(itensCategoria(build,"fan")[0].quantidade,3);
  assert.equal(normalizarBuild({componentes:{hd:[]}}).componentes.hd,undefined);
});
test("limita duplicação NVMe pelos slots M.2, inclusive com modelos diferentes",() => {
  let build = adicionar(base(),nvme,nvme);
  assert.equal(itensCategoria(build,"ssd")[0].quantidade,2);
  assert.throws(() => selecionarPeca(build,nvme,catalogo),/slots M.2/);
  build = reduzirQuantidade(build,"ssd",nvme.id);
  const outro = {...nvme,id:"outro-nvme"}, cat = [...catalogo,outro];
  build = selecionarPecaCompativel(build,outro,cat);
  assert.equal(informacoesArmazenamento(build,cat).m2,2);
  assert.equal(pecaCompativel(build,nvme,cat),false);
});
test("HD e SSD SATA dividem as mesmas portas; NVMe não usa porta SATA",() => {
  const build = adicionar(base(),hd,hd,sata,nvme);
  const info = informacoesArmazenamento(build,catalogo);
  assert.equal(info.hd,2); assert.equal(info.ssd,2); assert.equal(info.sata,3); assert.equal(info.m2,1);
  assert.throws(() => selecionarPeca(build,hd,catalogo),/portas SATA/);
  assert.throws(() => selecionarPeca(build,sata,catalogo),/portas SATA/);
  assert.equal(pecaCompativel(build,nvme,catalogo),true);
});
test("M.2 SATA usa slot M.2 com suporte a SATA e pode desativar uma porta SATA",() => {
  const build = adicionar(base(),hd,hd,m2sata);
  assert.equal(informacoesArmazenamento(build,catalogo).limites.sata,2);
  assert.throws(() => selecionarPeca(build,hd,catalogo),/portas SATA/);
  assert.throws(() => selecionarPeca(build,m2sata,catalogo),/suporte a SATA/);
  const cheio = adicionar(base(),hd,hd,hd);
  assert.throws(() => selecionarPeca(cheio,m2sata,catalogo),/portas SATA/);
});
test("discos próprios ou conexão desconhecida impedem duplicação sem inventar limite",() => {
  const primeira = adicionar(vazio(),nvme);
  assert.throws(() => selecionarPeca(primeira,nvme,catalogo),/placa-mãe/);
  const semSata = {...placa,quantidade_portas_sata:null}, cat = catalogo.map(p => p.id === placa.id ? semSata : p);
  const build = selecionarPeca(base(),hd,cat);
  assert.throws(() => selecionarPeca(build,hd,cat),/Falta.*portas SATA/);
  assert.ok(avaliarBuild(build,cat).dicas.some(a => a.includes("quantidades")));
  const propria = normalizarBuild({componentes:{placa_mae:{id:"mb"},hd:{proprio:"Meu disco"}}});
  assert.throws(() => selecionarPeca(propria,hd,catalogo),/Identifique/);
});
test("selecionar placa-mãe depois dos discos também rejeita slots ou portas insuficientes",() => {
  const build = normalizarBuild({componentes:{ssd:[{id:"nvme",quantidade:3}]}});
  assert.throws(() => selecionarPecaCompativel(build,placa,catalogo),/slots M.2/);
});
test("totais, redução e remoção preservam os outros discos e o link compartilhado",() => {
  let build = adicionar(base(),hd,hd,nvme,nvme);
  const antes = avaliarBuild(build,catalogo);
  build = reduzirQuantidade(build,"hd",hd.id);
  assert.equal(antes.preco - avaliarBuild(build,catalogo).preco,hd.preco);
  assert.equal(antes.watts - avaliarBuild(build,catalogo).watts,hd.consumo_energia);
  const removida = removerPeca(build,"ssd",nvme.id);
  assert.equal(itensCategoria(removida,"ssd").length,0); assert.equal(itensCategoria(removida,"hd").length,1);
  build.visibilidade = "publico";
  globalThis.location = {href:"https://boostio.example/pages/configuracao-build.html"};
  assert.deepEqual(abrirBuild(new URL(linkCompartilhado(build)).searchParams).componentes,build.componentes);
});
test("valida comprimento GPU e altura air cooler em ambas as ordens de seleção",() => {
  for (const [peca,campo] of [[gpu,"comprimento_mm"],[air,"altura_mm"]]) {
    const grande = {...peca,[campo]:peca[campo]+1}, cat = catalogo.map(p => p.id === peca.id ? grande : p);
    assert.equal(pecaCompativel(adicionar(vazio(),gabinete),grande,cat),false);
    assert.equal(pecaCompativel(selecionarPeca(vazio(),grande,cat),gabinete,cat),false);
    assert.equal(pecaCompativel(adicionar(vazio(),gabinete),peca,catalogo),true);
  }
});
test("water cooler 360 mm requer suporte explícito, não apenas um booleano",() => {
  const grande = {...water,tamanho_radiador_mm:360}, cat = catalogo.map(p => p.id === water.id ? grande : p);
  assert.equal(pecaCompativel(adicionar(vazio(),gabinete),grande,cat),false);
  const desconhecido = {...gabinete,radiadores_suportados_mm:undefined}, semMedidas = catalogo.map(p => p.id === gabinete.id ? desconhecido : p);
  const build = selecionarPecaCompativel(selecionarPeca(vazio(),desconhecido,semMedidas),grande,[...semMedidas.filter(p => p.id !== water.id),grande]);
  assert.ok(avaliarBuild(build,semMedidas).dicas.some(a => a.includes("radiador")));
});
test("conta unidades do kit fan, fans inclusas e fans do radiador sem somar diâmetros",() => {
  const build = adicionar(vazio(),gabinete,water,fan);
  assert.equal(pecaCompativel(build,fan,catalogo),false); // 1 + 2 + 4 > 6
  const semWater = adicionar(vazio(),gabinete,fan,fan); // duas duplas de 120, nunca uma fan de 480
  assert.equal(avaliarBuild(semWater,catalogo).erros.length,0);
  assert.equal(pecaCompativel(semWater,fan,catalogo),false);
  const gigante = {...fan,id:"fan360",tamanho_mm:360,quantidade:1};
  assert.equal(pecaCompativel(adicionar(vazio(),gabinete),gigante,[...catalogo,gigante]),false);
});
test("ausência de medidas vira dica, não confirma encaixe nem trata null como zero",() => {
  const sem = {...gpu,comprimento_mm:null}, cat = catalogo.map(p => p.id === gpu.id ? sem : p);
  const build = selecionarPecaCompativel(adicionar(vazio(),gabinete),sem,cat);
  assert.ok(avaliarBuild(build,cat).dicas.some(a => a.includes("placa de vídeo")));
  assert.equal(indicadorBuild({erros:[],avisos:[],dicas:["Confirme as medidas."],faltam:[]},"dicas").includes("build-indicator ok"),true);
  const fansSemLimite = {...gabinete,quantidade_max_fans:undefined}, cat2 = catalogo.map(p => p.id === gabinete.id ? fansSemLimite : p);
  const comFan = selecionarPecaCompativel(selecionarPeca(vazio(),fansSemLimite,cat2),fan,cat2);
  assert.throws(() => selecionarPecaCompativel(comFan,fan,cat2),/Faltam.*encaixes/);
});
test("dica de medida ausente não transforma uma build completa em aviso amarelo",() => {
  const cpu = {id:"cpu",categoria:"processador",soquete:"AM4",videointegrado:true,cooler:true,consumo_energia:65};
  const ram = {id:"ram",categoria:"memoria_ram",ddr:"DDR4",frequencia_mhz:3200,quantidade_pentes:1,capacidade_gb:8};
  const fonte = {id:"psu",categoria:"fonte",potencia_w:500};
  const semLimite = {...gabinete,quantidade_max_fans:null};
  const build = normalizarBuild({componentes:{processador:{id:cpu.id},placa_mae:{id:placa.id},memoria_ram:[{id:ram.id,quantidade:1}],ssd:[{id:nvme.id,quantidade:1}],fonte:{id:fonte.id},gabinete:{id:semLimite.id},fan:[{id:fan.id,quantidade:1}]}});
  const resultado = avaliarBuild(build,[cpu,{...placa,tipo_memoria:"DDR4"},ram,nvme,fonte,semLimite,fan]);
  assert.equal(resultado.status,"completa");
  assert.equal(resultado.avisos.length,0);
  assert.ok(resultado.dicas.some(dica => dica.includes("capacidade de fans")));
  assert.match(indicadorBuild(resultado,"dicas"),/build-indicator ok/);
  assert.match(indicadorBuild(resultado,"dicas"),/class="tip"/);
});
test("catálogo demonstrativo complementa somente modelos de placa identificados",() => {
  const dados = completarCatalogoDemo([{id:"x",categoria:"placa_mae",fabricante:"ASUS",modelo:"Prime A520M-K"},{id:"y",categoria:"placa_mae",fabricante:"Outra",modelo:"Desconhecida"}]);
  assert.equal(dados[0].quantidade_portas_sata,4); assert.equal(dados[1].quantidade_portas_sata,undefined);
});
test("indicador mostra barra azul sem pill no sucesso e pendências escapadas nos avisos",() => {
  const ok = indicadorBuild({erros:[],avisos:[],faltam:[]},"ok");
  assert.match(ok,/build-indicator ok/); assert.doesNotMatch(ok,/button|pill/);
  const aviso = indicadorBuild({erros:[],avisos:["<script>"],faltam:["RAM"]},"aviso");
  assert.match(aviso,/&lt;script&gt;/); assert.match(aviso,/Falta adicionar: RAM/);
  assert.match(indicadorBuild({erros:["erro"],avisos:[],faltam:[]},"erro"),/build-indicator erro/);
});
