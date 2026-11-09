import test from 'node:test';
import assert from 'node:assert/strict';
import { montarConsultaPendencias, listarPendencias, aceitarPendencia, rejeitarPendencia } from '../js/api/admin/pendencias.js';
import {
  rotuloLoja, rotuloSituacao, rotuloCategoria, formatarFaixaPreco, linkSeguro, candidatoSelecionavel,
  descreverCandidato, textoRestricoes,
} from '../js/admin/pendencias-apresentacao.js';
import { nomePagina, paginaDoSite } from '../js/components/page-routes.js';
import { paginaPrivada, redirecionamentoSessao } from '../js/components/navigation-config.js';
import { secoes } from '../js/admin/secoes.js';

const json = (dados, status = 200) => new Response(JSON.stringify(dados), {status, headers: {'Content-Type': 'application/json'}});

test('consulta usa só os filtros informados e a paginação por cursor', () => {
  assert.equal(montarConsultaPendencias(), 'status=em_revisao&limite=20');
  assert.equal(montarConsultaPendencias({status: 'importado', loja: 'shopee', categoria: 'ssd', depoisId: 7, limite: 5}),
    'status=importado&limite=5&loja=shopee&categoria=ssd&depois_id=7');
});

test('listar é GET autenticado; aceitar e rejeitar são POST com CSRF e corpo mínimo', async t => {
  const chamadas = [];
  t.mock.method(globalThis, 'fetch', async (url, config) => {
    chamadas.push([String(url), config]);
    return String(url).endsWith('/auth/csrf') ? json({csrf_token: 'tk'}) : json({ok: true});
  });
  await listarPendencias({loja: 'shopee'});
  await aceitarPendencia(4, 'processador:9');
  await rejeitarPendencia(4, 'Outro produto');
  const [lista, , csrf1, aceitar, , rejeitar] = chamadas;
  assert.match(lista[0], /\/admin\/pendencias\?status=em_revisao&limite=20&loja=shopee$/);
  assert.equal(lista[1].credentials, 'include');
  assert.match(csrf1[0], /\/auth\/csrf$/);
  assert.match(aceitar[0], /\/admin\/pendencias\/4\/aceitar$/);
  assert.equal(aceitar[1].headers['X-CSRF-Token'], 'tk');
  assert.deepEqual(JSON.parse(aceitar[1].body), {peca: 'processador:9'});
  assert.deepEqual(JSON.parse(rejeitar[1].body), {motivo: 'Outro produto'});
});

test('403 do servidor vira erro com status, sem esconder que faltou permissão', async t => {
  t.mock.method(globalThis, 'fetch', async () => json({erro: 'Acesso restrito a administradores', codigo: 'sem-permissao'}, 403));
  await assert.rejects(listarPendencias(), e => e.status === 403 && e.codigo === 'sem-permissao');
});

test('rótulos conhecidos e fallback para valores novos', () => {
  assert.equal(rotuloLoja('mercado_livre'), 'Mercado Livre');
  assert.equal(rotuloLoja('outra'), 'outra');
  assert.equal(rotuloSituacao('importado'), 'Aceita');
  assert.equal(rotuloCategoria('placa_video'), 'Placa de vídeo');
  assert.equal(rotuloCategoria('categoria_nova'), 'categoria nova');
});

test('faixa de preço', () => {
  assert.equal(formatarFaixaPreco(null), 'Preço não informado');
  assert.match(formatarFaixaPreco({minimo: 900, maximo: 900}), /^R\$\s?900,00$/);
  assert.match(formatarFaixaPreco({minimo: 800, maximo: 1200}), /800,00.* a .*1\.200,00/);
});

test('só links https sem credenciais são abertos', () => {
  assert.equal(linkSeguro('https://shopee.com.br/product/1/2'), 'https://shopee.com.br/product/1/2');
  for (const ruim of ['javascript:alert(1)', 'http://x.com', 'data:text/html,1', 'https://u:p@x.com', '', null, 'não é url'])
    assert.equal(linkSeguro(ruim), null, String(ruim));
});

test('candidato com conflito não pode ser escolhido', () => {
  assert.equal(candidatoSelecionavel({conflitos: []}), true);
  assert.equal(candidatoSelecionavel({conflitos: ['marca_divergente']}), false);
  assert.equal(candidatoSelecionavel({}), false);
  assert.equal(candidatoSelecionavel({conflitos: [], vinculada_a_outro_catalogo: 'MLB44455598'}), false);
  assert.equal(descreverCandidato({fabricante: 'AMD', modelo: 'Ryzen 5 5500', part_number: 'X1', peca: 'processador:1'}), 'AMD Ryzen 5 5500 · X1');
  assert.equal(descreverCandidato({peca: 'processador:1'}), 'processador:1');
  assert.deepEqual(textoRestricoes({conflitos: ['modelo_divergente'], pendencias: ['cor_nao_comprovada']}),
    {conflitos: ['modelo divergente'], pendencias: ['cor nao comprovada']});
});

test('a página é privada, redireciona visitante ao login e é uma página do site', () => {
  assert.equal(nomePagina('/admin'), 'admin.html');
  assert.equal(paginaDoSite('/pages/admin.html'), true);
  assert.equal(paginaPrivada('/admin'), true);
  assert.equal(redirecionamentoSessao('admin.html', false), 'login.html');
  assert.equal(redirecionamentoSessao('admin.html', true), null);
});

test('seções do dashboard: hoje só pendências, cada uma com iniciar()', () => {
  assert.deepEqual(secoes.map(s => s.id), ['pendencias']);
  assert.ok(secoes.every(s => s.rotulo && typeof s.iniciar === 'function'));
});

test('o link de administração do menu realmente some quando oculto (display:flex não pode vencer [hidden])', async () => {
  const {readFile} = await import('node:fs/promises');
  const css = await readFile(new URL('../styles/componentes/site-menu.css', import.meta.url), 'utf8');
  assert.match(css, /\.profile-link\[hidden\]\s*\{\s*display:\s*none;\s*\}/);
  const header = await readFile(new URL('../js/header.js', import.meta.url), 'utf8');
  assert.match(header, /data-menu-admin hidden/);
  assert.match(header, /link\.hidden = !\(autenticado && administrador\)/);
});
