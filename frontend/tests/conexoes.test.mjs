import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { avaliarConectores } from '../js/build/conectores.js';
import { avaliarArmazenamento,avaliarBaias } from '../js/build/armazenamento.js';
import { avaliarBuild,selecionarPecaCompativel } from '../js/build/compatibilidade.js';
import { normalizarBuild } from '../js/build/estado.js';
import { completarMedidas } from '../js/build/medidas-fisicas.js';
import { indicadorBuild } from '../js/build/indicador.js';
import { filtrarPecasCatalogo } from '../js/build/catalogo-filtros.js';

const ler=nome=>JSON.parse(readFileSync(new URL(nome,import.meta.url)));
const casos=ler('./fixtures/conexoes.json');
for(const caso of casos.conectores)test('conectores: '+caso.nome,()=>{
  const antes=structuredClone(caso),[resultado,mensagem]=avaliarConectores(caso.fonte,caso.consumidores);
  assert.equal(resultado,caso.esperado,mensagem);assert.deepEqual(caso,antes);
});
for(const [tipo,avaliar] of [['armazenamento',avaliarArmazenamento],['baias',avaliarBaias]])for(const caso of casos[tipo])test(tipo+': '+caso.nome,()=>{
  const antes=structuredClone(caso),regras=Object.fromEntries(avaliar(caso.placa||caso.gabinete,caso.discos).map(r=>[r.codigo,r]));
  for(const [codigo,esperado] of Object.entries(caso.esperado))assert.equal(regras[codigo].condicao,esperado,regras[codigo].mensagem);
  assert.deepEqual(caso,antes);
});
test('editor bloqueia SSD longo e fonte com conector inadequado',()=>{
  const placa={id:'mb',categoria:'placa_mae',...casos.armazenamento[0].placa};
  const ssd={id:'ssd',categoria:'ssd',interface:'NVMe',formato:'M.2 22110'};
  const b=normalizarBuild({componentes:{placa_mae:{id:'mb'}}});
  assert.throws(()=>selecionarPecaCompativel(b,ssd,[placa,ssd]),/Não há distribuição/);
  const fonte={id:'psu',categoria:'fonte',...casos.conectores[2].fonte};
  const p={...placa,...casos.conectores[2].consumidores[0][2]};
  b.componentes.fonte={id:'psu',quantidade:1};
  assert.ok(avaliarBuild(b,[p,fonte]).erros.some(t=>t.includes('conectores suficientes')));
  const gpu={id:'gpu',categoria:'placa_video',conectores_alimentacao:{pcie_8:1},conectores_alimentacao_completos:true};
  const vazio=normalizarBuild({componentes:{fonte:{id:'psu'}}}),fSemPcie={...fonte,conectores_alimentacao:{eps_8:2}};
  assert.equal(filtrarPecasCatalogo(vazio,[gpu],[fSemPcie,gpu]).excluidas[0].grupo,'alimentacao');
});
test('observações vindas do Python são dicas escapadas e sem duplicação',()=>{
  const b=normalizarBuild();b.compatibilidade={status:'nao_verificado',rotulo:'Revisão pendente',naoVerificado:[],orientacoes:[{mensagem:'<script>teste</script>'},{mensagem:'<script>teste</script>'}]};
  const resultado=avaliarBuild(b,[]);
  assert.equal(resultado.dicas.filter(t=>t==='<script>teste</script>').length,1);
  const html=indicadorBuild(resultado,'teste');assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>'));
});
test('fichas exatas fornecem tipos de conectores e dois slots reais',()=>{
  const manifesto=ler('../data/medidas-fisicas.json'),p=(categoria,fabricante,modelo,part_number,produto)=>completarMedidas({categoria,fabricante,modelo,part_number,link:'https://www.kabum.com.br/produto/'+produto},manifesto);
  const placa=p('placa_mae','ASUS','Prime H610M-A D4','SEED-MB-10','276263');
  const fonte=p('fonte','Corsair','CX Series CX650','SEED-PSU-04','516056');
  assert.equal(avaliarConectores(fonte,[['placa_mae',{},placa]])[0],true);
  const nvme={interface:'NVMe',formato:'M.2 2280'};
  assert.equal(avaliarArmazenamento(placa,[[{quantidade:2},nvme]]).find(r=>r.codigo==='discos-compartilhamento').condicao,true);
  assert.equal(avaliarArmazenamento(placa,[[{quantidade:3},nvme]]).find(r=>r.codigo==='discos-compartilhamento').condicao,false);
});
