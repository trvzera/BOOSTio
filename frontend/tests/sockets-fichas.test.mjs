import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { normalizarSocket, listarSockets, suporteSocketCooler } from '../js/build/sockets.js';
import { completarMedidas } from '../js/build/medidas-fisicas.js';
import { avaliarBuild, pecaCompativel } from '../js/build/compatibilidade.js';
import { gruposFichaTecnica } from '../js/build/catalogo.js';

const ler=nome=>JSON.parse(readFileSync(new URL(nome,import.meta.url)));
const casos=ler('./fixtures/sockets.json');
for(const [valor,esperado] of casos.normalizar)test('socket canônico: '+valor,()=>assert.equal(normalizarSocket(valor),esperado));
for(const [valor,esperado] of casos.listar)test('lista de sockets: '+valor,()=>assert.deepEqual(listarSockets(valor),esperado));
for(const [socket,cooler,esperado] of casos.cooler)test('suporte do kit: '+socket+' '+JSON.stringify(cooler),()=>assert.equal(suporteSocketCooler(socket,cooler),esperado));

const manifesto=ler('../data/medidas-fisicas.json');
const originais=ler('./fixtures/revisao-compatibilidade.json');
const cat=originais.map(p=>completarMedidas(p,manifesto));
const get=id=>cat.find(p=>p.id===id);
const build=()=>({componentes:{processador:{id:'processador:6',quantidade:1},placa_mae:{id:'placa_mae:91',quantidade:1},
  gabinete:{id:'gabinete:54',quantidade:1},fonte:{id:'fonte:4',quantidade:1},placa_video:{id:'placa_video:99',quantidade:1},
  air_cooler:{id:'air_cooler:19',quantidade:1},memoria_ram:[{id:'memoria_ram:56',quantidade:2}],ssd:[{id:'ssd:31',quantidade:1}],fan:[{id:'fan:60',quantidade:2}]}});

test('HPM610 permite dois pentes e bloqueia terceiro; M.2/SATA têm limites reais',()=>{
  assert.equal(get('placa_mae:91').quantidade_slots_ram,2);
  assert.equal(get('placa_mae:91').memoria_maxima_gb,64);
  assert.equal(get('placa_mae:91').quantidade_slots_m2,1);
  assert.equal(get('placa_mae:91').quantidade_portas_sata,3);
  assert.deepEqual(avaliarBuild(build(),cat).erros,[]);
  const mais=build();mais.componentes.memoria_ram[0].quantidade=3;
  assert.ok(avaliarBuild(mais,cat).erros.some(t=>t.includes('slots')));
  assert.equal(pecaCompativel(build(),get('ssd:31'),cat),false);
});
test('dados reais de gabinete não transformam dimensões externas em folgas internas',()=>{
  const gabinete=get('gabinete:54');
  assert.equal(gabinete.quantidade_max_fans,3);
  assert.equal(gabinete.slots_expansao,4);
  assert.equal(gabinete.tamanho_max_gpu_mm,null);
  assert.equal(get('placa_video:99').comprimento_mm,161.9);
  assert.equal(get('placa_video:99').espessura_mm,40.2);
  const mais=build();mais.componentes.fan[0].quantidade=4;
  assert.ok(avaliarBuild(mais,cat).erros.some(t=>t.includes('fans')));
  const dicas=avaliarBuild(build(),cat).dicas;
  assert.ok(dicas.some(t=>t.includes('kit')));
  assert.ok(dicas.some(t=>t.includes('placa de vídeo')));
});
test('corrige quatro slots fictícios e separa variantes DDR e ARGB',()=>{
  for(const id of ['placa_mae:10','placa_mae:14','placa_mae:85']){
    assert.equal(get(id).quantidade_slots_ram,2,id);
    assert.equal(get(id).memoria_maxima_gb,64,id);
  }
  assert.equal(get('placa_mae:88').tipo_memoria,'DDR5');
  assert.equal(get('placa_mae:88').memoria_maxima_gb,null);
  assert.equal(get('placa_mae:58').quantidade_slots_ram,2);
  for(const p of originais.filter(p=>p.categoria==='placa_mae')) {
    const errada={...p,link:'https://www.kabum.com.br/produto/999999',preco:1};
    assert.equal(completarMedidas(errada,manifesto).fonte_medidas,undefined);
    assert.equal(completarMedidas({...p,modelo:p.modelo+' V3'},manifesto).fonte_medidas,undefined);
    assert.equal(completarMedidas({...p,preco:123,esgotado:true},manifesto).preco,123);
    assert.equal(completarMedidas({...p,preco:123,esgotado:true},manifesto).esgotado,true);
  }
});
test('grafia equivalente não esconde conflito real, dados ausentes continuam dicas',()=>{
  const b=build();
  const editar=campos=>cat.map(p=>p.id==='placa_mae:91'?{...p,...campos}:p);
  assert.deepEqual(avaliarBuild(b,editar({socket:'Intel Socket LGA 1700'})).erros,[]);
  assert.ok(avaliarBuild(b,editar({socket:'AM5'})).erros.some(t=>t.includes('socket')));
  const sem=avaliarBuild(b,editar({socket:null}));
  assert.deepEqual(sem.erros,[]);assert.ok(sem.dicas.some(t=>t.includes('encaixe (socket)')));
  const grupos=gruposFichaTecnica(get('air_cooler:19'));
  assert.ok(grupos.some(g=>g.campos.some(([nome])=>nome.includes('kit de montagem'))));
});
