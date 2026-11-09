import test from 'node:test';
import assert from 'node:assert/strict';
import { separarCodigos, referenciasPeca } from '../js/build/codigos-pecas.js';
import { completarImagens } from '../js/build/imagens-produtos.js';

test('separa referências antigas e mantém o MPN real e imagens compatíveis', () => {
  const original = {categoria:'memoria_ram',fabricante:'Kingston',modelo:'Fury',part_number:'SEED-RAM-1'};
  const p = separarCodigos(original);
  assert.equal(p.part_number, null);
  assert.equal(p.referencia_interna, 'SEED-RAM-1');
  assert.equal(original.part_number, 'SEED-RAM-1');
  assert.deepEqual(referenciasPeca({...p,part_number:'KF432C16BB/8'}), ['SEED-RAM-1','KF432C16BB/8']);
  const [imagem] = completarImagens([p], {'SEED-RAM-1':{...original,imagem:'foto.webp'}});
  assert.equal(imagem.imagem,'foto.webp');
});
