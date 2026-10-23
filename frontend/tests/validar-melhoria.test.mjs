import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { avaliarTrocaMelhoria, exigirTrocaMelhoria } from "../js/build/validar-melhoria.js";

const ram = {id:"ram:1",categoria:"memoria_ram",capacidade_gb:16,ddr:"DDR4",frequencia_mhz:3200,latencia:"CL16",quantidade_pentes:2};
const ssd = {id:"ssd:1",categoria:"ssd",capacidade_gb:1000,velocidade_leitura_mbps:3500,velocidade_gravacao_mbps:2800};
const hd = {id:"hd:1",categoria:"hd",capacidade_gb:2000,velocidade_rpm:7200,memoria_cache_mb:256};
const base = (peca,quantidade = 1) => ({componentes:{[peca.categoria]:[{id:peca.id,quantidade}]}});
const comparar = (peca,alteracoes = {},quantidade = 1) => {
  const candidata = {...peca,id:peca.id + "-nova",...alteracoes};
  return avaliarTrocaMelhoria(base(peca,quantidade),candidata,[peca,candidata]);
};

for (const [nome,alteracoes] of [
  ["capacidade",{capacidade_gb:8}], ["frequência",{frequencia_mhz:2666}],
  ["pentes",{quantidade_pentes:1}], ["latência",{latencia:"CL22"}],
]) test("RAM bloqueia redução de " + nome,() => {
  assert.equal(comparar(ram,alteracoes).codigo,"regressao");
});

test("RAM considera todas as unidades/kit atuais, não apenas a primeira",() => {
  assert.equal(comparar(ram,{capacidade_gb:16,quantidade_pentes:4},2).codigo,"regressao");
  assert.equal(comparar(ram,{capacidade_gb:32,quantidade_pentes:2},2).codigo,"regressao");
  assert.equal(comparar(ram,{capacidade_gb:32,quantidade_pentes:4},2).permitida,true);
});

test("RAM compara CL relativo à frequência, permitindo CL maior sem latência pior",() => {
  assert.equal(comparar(ram,{frequencia_mhz:3600,latencia:"CL18"}).permitida,true);
  assert.equal(comparar(ram,{frequencia_mhz:3600,latencia:"CL20"}).codigo,"regressao");
  assert.equal(comparar(ram,{latencia:"16-18-18-38"}).permitida,true);
});

test("modelos de RAM diferentes são comparados contra o mais exigente de cada critério",() => {
  const outra = {...ram,id:"ram:2",frequencia_mhz:3600,latencia:"CL16"};
  const build = base(ram); build.componentes.memoria_ram.push({id:outra.id,quantidade:1});
  const nova = {...ram,id:"ram:3",capacidade_gb:32,quantidade_pentes:4,frequencia_mhz:3600,latencia:"CL18"};
  assert.equal(avaliarTrocaMelhoria(build,nova,[ram,outra,nova]).codigo,"regressao");
  nova.latencia = "CL16";
  assert.equal(avaliarTrocaMelhoria(build,nova,[ram,outra,nova]).permitida,true);
});

for (const alteracoes of [{ddr:"DDR5"},{ddr:null},{latencia:null},{latencia:"desconhecida"},{latencia:0},{frequencia_mhz:null},{quantidade_pentes:null}])
  test("RAM sem comparação segura não é liberada: " + JSON.stringify(alteracoes),() => {
    const resultado = comparar(ram,alteracoes);
    assert.equal(resultado.permitida,false); assert.equal(resultado.codigo,"dados-insuficientes");
  });

for (const [nome,alteracoes] of [
  ["capacidade",{capacidade_gb:500}], ["leitura",{capacidade_gb:2000,velocidade_leitura_mbps:3000}],
  ["gravação",{capacidade_gb:2000,velocidade_gravacao_mbps:2000}],
]) test("SSD bloqueia redução de " + nome + " mesmo com outras especificações melhores",() => {
  assert.equal(comparar(ssd,alteracoes).codigo,"regressao");
});

test("SSD soma a capacidade dos discos substituídos e preserva velocidades",() => {
  assert.equal(comparar(ssd,{capacidade_gb:1000},2).codigo,"regressao");
  assert.equal(comparar(ssd,{capacidade_gb:2000,velocidade_leitura_mbps:6000,velocidade_gravacao_mbps:4000},2).permitida,true);
  const outro = {...ssd,id:"ssd:2",capacidade_gb:500,velocidade_leitura_mbps:7000};
  const build = base(ssd); build.componentes.ssd.push({id:outro.id,quantidade:1});
  const nova = {...ssd,id:"ssd:3",capacidade_gb:2000};
  assert.equal(avaliarTrocaMelhoria(build,nova,[ssd,outro,nova]).codigo,"regressao");
});

for (const [nome,alteracoes] of [
  ["capacidade",{capacidade_gb:1000}], ["rotação",{capacidade_gb:4000,velocidade_rpm:5400}],
  ["cache",{capacidade_gb:4000,memoria_cache_mb:64}],
]) test("HD bloqueia redução de " + nome,() => {
  assert.equal(comparar(hd,alteracoes).codigo,"regressao");
});

test("HD preserva o total de vários discos e permite troca equivalente nas métricas",() => {
  assert.equal(comparar(hd,{capacidade_gb:2000},2).codigo,"regressao");
  assert.equal(comparar(hd,{capacidade_gb:4000},2).permitida,true);
  assert.equal(comparar(hd,{fabricante:"Outra marca",modelo:"Outra linha"}).permitida,true);
});

for (const valor of [null,undefined,0,-1,Infinity,NaN,"",true,false,[],[7000],{},"não informado"])
  test("medidas inválidas não viram aprovação: " + String(valor),() => {
    assert.equal(comparar(ssd,{velocidade_leitura_mbps:valor}).codigo,"dados-insuficientes");
  });

for (const categoria of ["processador","placa_video"])
  test(categoria + " não é classificado por preço, modelo, núcleos, clock ou VRAM",() => {
    const peca = {id:categoria + ":1",categoria,modelo:"Modelo atual",preco:100,nucleo:4,clockmax:3,memoria_gb:4};
    const resultado = comparar(peca,{modelo:"Modelo novo 9999",preco:10000,nucleo:64,clockmax:6,memoria_gb:32});
    assert.equal(resultado.permitida,false); assert.match(resultado.motivo,/benchmarks comparáveis/);
  });

for (const categoria of ["fonte","placa_mae","gabinete","fan","air_cooler","water_cooler","monitor","mouse","teclado","fone","adaptador_wifi","cabo_rede"])
  test(categoria + " sem critério confiável não é anunciado como melhoria",() => {
    const peca = {id:categoria + ":1",categoria,preco:100,potencia_w:650,tamanho_mm:120};
    assert.equal(comparar(peca,{preco:1000,potencia_w:1000,tamanho_mm:360}).codigo,"dados-insuficientes");
  });

test("GPU dedicada não é considerada automaticamente superior ao vídeo integrado",() => {
  const gpu = {id:"gpu:1",categoria:"placa_video"};
  const cpu = {id:"cpu:1",categoria:"processador",videointegrado:true};
  const build = base(cpu);
  assert.equal(avaliarTrocaMelhoria(build,gpu,[cpu,gpu]).codigo,"dados-insuficientes");
  cpu.videointegrado = null;
  assert.equal(avaliarTrocaMelhoria(build,gpu,[cpu,gpu]).permitida,false);
  cpu.videointegrado = false;
  assert.equal(avaliarTrocaMelhoria(build,gpu,[cpu,gpu]).codigo,"adicao");
});

test("categoria vazia permite adição, sem aprovar compatibilidade por conta própria",() => {
  const avaliacao = avaliarTrocaMelhoria({componentes:{}},ssd,[ssd]);
  assert.equal(avaliacao.permitida,true); assert.equal(avaliacao.codigo,"adicao");
  assert.match(avaliacao.motivo,/compatibilidade ainda será validada/);
});

test("peça própria, ID ausente e quantidade inválida da origem bloqueiam a comparação",() => {
  const candidata = {...ssd,id:"ssd:2"};
  for (const item of [{proprio:"Meu SSD",quantidade:1},{id:"ausente",quantidade:1},{id:ssd.id,quantidade:null},{id:ssd.id,quantidade:0},{id:ssd.id,quantidade:1.5},{id:ssd.id,quantidade:65}]) {
    const build = {componentes:{ssd:[item]}};
    assert.equal(avaliarTrocaMelhoria(build,candidata,[ssd,candidata]).codigo,"dados-insuficientes");
  }
});

test("não reaproveita outro item atual nem o mesmo part number com ID diferente",() => {
  const outra = {...ssd,id:"ssd:2",part_number:"ABC-123"};
  const build = base(ssd); build.componentes.ssd.push({id:outra.id,quantidade:1});
  assert.equal(avaliarTrocaMelhoria(build,outra,[ssd,outra]).codigo,"mesma-peca");
  const alias = {...outra,id:"ssd:3",part_number:" abc-123 "};
  assert.equal(avaliarTrocaMelhoria(build,alias,[ssd,outra,alias]).codigo,"mesma-peca");
});

test("não confunde o mesmo ID de categorias diferentes e não altera a build",() => {
  const errada = {...ram,id:ssd.id},nova = {...ssd,id:"ssd:2"};
  const build = base(ssd),antes = structuredClone(build);
  assert.equal(avaliarTrocaMelhoria(build,nova,[errada,nova]).codigo,"dados-insuficientes");
  assert.deepEqual(build,antes);
});

test("a guarda revalida e bloqueia alterações de dados antes de aplicar",() => {
  const nova = {...ssd,id:"ssd:2",capacidade_gb:2000},build = base(ssd),catalogo = [ssd,nova];
  assert.equal(exigirTrocaMelhoria(build,nova,catalogo).permitida,true);
  nova.velocidade_gravacao_mbps = 500;
  assert.throws(() => exigirTrocaMelhoria(build,nova,catalogo),/reduziria/);
});

test("candidata sem categoria/ID e argumentos inválidos não são liberados",() => {
  for (const candidata of [null,{}, {...ssd,id:""},{...ssd,categoria:"inexistente"}])
    assert.equal(avaliarTrocaMelhoria(base(ssd),candidata,[ssd]).permitida,false);
  assert.equal(avaliarTrocaMelhoria(null,ssd,[ssd]).permitida,false);
});

test("modal e laboratório filtram e revalidam as trocas, inclusive na confirmação",async () => {
  const modal = await readFile(new URL("../js/build/melhorias.js",import.meta.url),"utf8");
  const teste = await readFile(new URL("../js/pages/test-upgrades.js",import.meta.url),"utf8");
  assert.match(modal,/avaliarTrocaMelhoria\(original,peca,catalogo,\{modo:modoTroca\(categoria\.id\)\}\)/);
  assert.match(modal,/exigirTrocaMelhoria\(original,peca,catalogo,\{modo:modoTroca\(id\)\}\)/);
  assert.match(modal,/const pecas = escolhidas\(escolhas\)/);
  assert.match(modal,/const confirmada = simular\(trocas,build\)/);
  assert.match(teste,/avaliarTrocaMelhoria\(original,peca,catalogo\)\.permitida/);
  assert.match(teste,/exigirTrocaMelhoria\(original,peca,catalogo\)/);
});
