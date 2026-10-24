import test from "node:test";
import assert from "node:assert/strict";
import { filtrarPecasCatalogo, motivosCatalogoHtml } from "../js/build/catalogo-filtros.js";
const placa={id:"mb",categoria:"placa_mae",tipo_memoria:"DDR4",quantidade_slots_ram:2,memoria_maxima_gb:32};
const ram={id:"ram",categoria:"memoria_ram",modelo:"RAM teste",ddr:"DDR4",frequencia_mhz:3200,capacidade_gb:8,quantidade_pentes:1};
const base={componentes:{placa_mae:{id:"mb",quantidade:1}}};
test("catálogo distingue DDR incompatível de slots ocupados e respeita busca",()=>{
  const ddr5={...ram,id:"ddr5",ddr:"DDR5",modelo:"Outra RAM"};
  const cat=[placa,ram,ddr5];
  assert.equal(filtrarPecasCatalogo(base,[ddr5],cat).excluidas[0].grupo,"ddr");
  const cheia={componentes:{...base.componentes,memoria_ram:[{id:"ram",quantidade:2}]}};
  assert.equal(filtrarPecasCatalogo(cheia,[ram],cat).excluidas[0].grupo,"slots");
  assert.deepEqual(filtrarPecasCatalogo(base,[ram],cat,{busca:"não existe"}),{incluidas:[],excluidas:[],consideradas:0});
});
test("tamanho excedido, estoque e dados faltantes têm causas distintas",()=>{
  const gabinete={id:"case",categoria:"gabinete",tamanho_max_gpu_mm:200};
  const gpu={id:"gpu",categoria:"placa_video",modelo:"GPU",comprimento_mm:300};
  assert.equal(filtrarPecasCatalogo({componentes:{gabinete:{id:"case",quantidade:1}}},[gpu],[gabinete,gpu]).excluidas[0].grupo,"encaixe");
  assert.equal(filtrarPecasCatalogo(base,[{...ram,esgotado:true}],[placa,ram]).excluidas[0].grupo,"estoque");
  const disco={id:"ssd",categoria:"ssd",tipo:"NVMe"};
  const b={componentes:{...base.componentes,ssd:[{id:"ssd",quantidade:1}]}};
  assert.equal(filtrarPecasCatalogo(b,[disco],[placa,disco]).excluidas[0].grupo,"dados");
});
test("explicações escapam dados e limitam exemplos sem esconder contagem",()=>{
  const itens=Array.from({length:5},()=>({peca:{modelo:"<script>"},motivo:"<erro>",grupo:"dados"}));
  const html=motivosCatalogoHtml(itens,{aberto:true});
  assert.match(html,/ open>/);assert.match(html,/Dados insuficientes · 5/);assert.match(html,/Mais 2 modelo/);
  assert.doesNotMatch(html,/<script>|<erro>/);assert.match(html,/&lt;script&gt;/);
  assert.equal(motivosCatalogoHtml([]),"");
});
