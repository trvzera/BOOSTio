import test from 'node:test';
import assert from 'node:assert/strict';
import {processarEnvioIA} from '../js/admin/envio-ia.js';

const sem_espera = () => Promise.resolve();

test('divide em lotes de 20 e soma os resultados', async () => {
  const lotes = [];
  const r = await processarEnvioIA({
    ids: Array.from({length: 45}, (_, i) => i + 1), esperar: sem_espera,
    enviar: async ids => { lotes.push(ids.length); return {sugeridas: ids.length, ids_falhos: []}; },
  });
  assert.deepEqual(lotes, [20, 20, 5]);
  assert.equal(r.sugeridas, 45);
  assert.equal(r.feitos, 45);
  assert.deepEqual(r.falharam, []);
});

test('espera e repete só os que falharam', async () => {
  const chamadas = [];
  const esperas = [];
  let primeira = true;
  const r = await processarEnvioIA({
    ids: [1, 2, 3], esperas: [10, 20], esperar: async ms => { esperas.push(ms); },
    enviar: async ids => {
      chamadas.push(ids);
      if (primeira) { primeira = false; return {sugeridas: 1, ids_falhos: [2, 3]}; }
      return {sugeridas: 2, ids_falhos: []};
    },
  });
  assert.deepEqual(chamadas, [[1, 2, 3], [2, 3]]);
  assert.deepEqual(esperas, [10]);
  assert.equal(r.sugeridas, 3);
  assert.deepEqual(r.falharam, []);
});

test('erro de rede repete o lote e, esgotadas as tentativas, segue para o próximo', async () => {
  let n = 0;
  const r = await processarEnvioIA({
    ids: [1, 2], tamanho: 1, esperas: [1, 1], esperar: sem_espera,
    enviar: async ids => {
      n += 1;
      if (ids[0] === 1) throw new Error('rede');
      return {sugeridas: 1, ids_falhos: []};
    },
  });
  assert.equal(n, 4); // lote 1: 3 tentativas; lote 2: 1
  assert.deepEqual(r.falharam, [1]);
  assert.equal(r.sugeridas, 1);
});

test('parar interrompe antes do próximo lote', async () => {
  let parar = false;
  const r = await processarEnvioIA({
    ids: [1, 2, 3, 4], tamanho: 2, esperar: sem_espera, parou: () => parar,
    enviar: async ids => { parar = true; return {sugeridas: ids.length, ids_falhos: []}; },
  });
  assert.equal(r.parado, true);
  assert.equal(r.sugeridas, 2);
});
