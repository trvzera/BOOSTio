import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizarRede,camposRede,redeFormulario,resumoRede,selecionarAcessorioRede} from '../js/build/rede.js';
import {normalizarBuild} from '../js/build/estado.js';
import {exportarJson,importarBuild} from '../js/build/arquivos.js';
test('Wi-Fi e cabo preservam comprimento e velocidade sem alterar pedidos existentes',()=>{
 const rede=redeFormulario({tipo:'ambos',possuiAcessorio:false,comprimentoCaboM:20});
 assert.equal(rede.tipo,'ambos');assert.equal(rede.comprimentoCaboM,20);assert.equal(rede.velocidadeMbps,500);
 assert.match(resumoRede(rede),/Wi-Fi e cabo/);
 assert.match(camposRede(rede),/value="ambos" selected/);assert.match(camposRede(rede),/Quantos metros/);
 assert.equal(selecionarAcessorioRede({},'ambos:incluir').tipo,'ambos');
 assert.equal(normalizarRede({tipo:'wifi'}).tipo,'wifi');
 assert.equal(redeFormulario({tipo:'ambos',possuiAcessorio:true}).velocidadeMbps,null);
 const b=normalizarBuild({rede,incluirRede:true,componentes:{}});
 assert.equal(importarBuild(exportarJson(b),"json",[]).rede.tipo,'ambos');
});
