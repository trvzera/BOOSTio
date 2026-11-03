import test from "node:test";
import assert from "node:assert/strict";
import { obterHistoricoDaPeca } from "../js/build/carregar-historico-precos.js";
import { historicoPrecosHtml } from "../js/build/price-history.js";
const peca={id:"placa_video:12",categoria:"placa_video"};

test("consulta a identidade real e repassa registros sem fabricar dados",async()=>{
  const registros=[{data:"2026-11-02",preco:100,loja:"kabum"}];
  const consultar=async(categoria,id)=>{
    assert.equal(categoria,"placa_video");assert.equal(id,"12");
    return {peca_id:peca.id,loja:"kabum",historico_precos:registros,tem_mais:false};
  };
  assert.deepEqual(await obterHistoricoDaPeca(peca,{conta:true,consultar}),{historico_precos:registros,historico_precos_incompleto:false});
});

test("catálogo demo nunca consulta histórico de IDs do banco",async()=>{
  const consultar=()=>assert.fail("não deve consultar");
  assert.deepEqual(await obterHistoricoDaPeca(peca,{consultar}),{historico_precos:[],historico_precos_incompleto:false});
});

test("rejeita respostas de outra peça, origem ou formato",async()=>{
  const base={peca_id:peca.id,loja:"kabum",historico_precos:[],tem_mais:false};
  for(const alteracao of [{peca_id:"placa_video:13"},{loja:"outra"},{historico_precos:{}},{tem_mais:null}])
    await assert.rejects(obterHistoricoDaPeca(peca,{conta:true,consultar:async()=>({...base,...alteracao})}));
});

test("erro de rede não vira lista vazia",async()=>{
  await assert.rejects(obterHistoricoDaPeca(peca,{conta:true,consultar:async()=>{throw new Error("indisponível");}}),/indisponível/);
});

test("recorte do backend é indicado no gráfico",()=>{
  const html=historicoPrecosHtml({historico_precos:[{data:"2026-11-02",preco:100,loja:"kabum"}],historico_precos_incompleto:true},Date.parse("2026-11-03"));
  assert.match(html,/1.000 registros mais recentes/);assert.match(html,/Todos os registros carregados/);
});

test("consulta histórico do anúncio escolhido e rejeita resposta de outro vendedor/anúncio",async()=>{
  const consultarOferta=async(cat,id,ofertaId)=>({peca_id:peca.id,oferta_id:ofertaId,loja:"mercado_livre",historico_precos:[],tem_mais:false});
  const r=await obterHistoricoDaPeca(peca,{conta:true,ofertaId:7,consultarOferta});
  assert.equal(r.historico_loja,"mercado_livre");
  await assert.rejects(obterHistoricoDaPeca(peca,{conta:true,ofertaId:7,consultarOferta:async()=>({peca_id:peca.id,oferta_id:8,loja:"mercado_livre",historico_precos:[],tem_mais:false})}));
});
