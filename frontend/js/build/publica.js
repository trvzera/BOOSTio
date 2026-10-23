import { fetchComErro } from '../api/_shared/fetchComErro.js';
import { copiarBuildPublica, verificarEspacoBuild } from '../api/build/builds.js';
import { buildDaConta } from './conta.js';
import { carregarPerfil } from '../conta/perfil.js';
import { htmlSeguro as h, categorias, imagemPeca, moeda, nomePeca } from './catalogo.js';
import { itensSelecionados } from './estado.js';
import { avaliarBuild } from './compatibilidade.js';
import { abrirBenchmark, abrirCompraBuild, motivoBenchmark, avisoFreteHtml } from './acoes-build.js';
import { indicadorBuild, iniciarIndicadores } from './indicador.js';
import { iconeAnimado, iniciarIcones } from '../components/ui.js';
import { navegarPara, acompanharCarregamento } from '../components/page-loading.js';
import { guardarRetornoPublico, idCompartilhamentoPublico } from '../components/sessao-publica.js';

export async function mostrarBuildPublica(main,id) {
  if (idCompartilhamentoPublico(location.search) !== id) throw new Error('Link de compartilhamento inválido.');
  const {build:dados} = await acompanharCarregamento(fetchComErro('/build/' + encodeURIComponent(id) + '/publica',{method:'GET',cache:'no-store'}));
  if (dados.id !== id || dados.estado?.visibilidade !== 'publico' || !Array.isArray(dados.pecas)) throw new Error('Não foi possível confirmar a configuração pública.');
  const build = buildDaConta(dados), catalogo = dados.pecas || [];
  document.title = build.titulo + ' — BOOSTio';
  const itens = itensSelecionados(build,catalogo), avaliacao = avaliarBuild(build,catalogo);
  const parcial = itens.some(({peca}) => !peca || !Number.isFinite(peca.preco) || peca.preco <= 0 || peca.esgotado);
  const linha = ({categoria,item,peca}) => '<section class="component-group"><div class="component-group-heading"><h2>' + h(categorias.find(c=>c.id===categoria)?.nome || categoria) + '</h2></div>'
    + '<article class="component-row component-selected build-public-piece glass-card"><div class="component-selected-main"><div class="component-image">' + imagemPeca(peca || {categoria}) + '</div><div class="component-copy"><h3 class="component-model font-1-m-b">' + h(peca ? nomePeca(peca) : item.proprio || 'Modelo não identificado')
    + '</h3><p>Quantidade: ' + h(item.quantidade) + (peca?.esgotado ? ' · sem estoque confirmado' : !peca ? ' · peça própria, especificações não verificadas' : '') + '</p></div><div class="component-purchase"><strong>'
    + (peca && Number.isFinite(peca.preco) && peca.preco > 0 ? moeda(peca.preco * item.quantidade) : peca ? 'Preço a consultar' : 'Já possuo') + '</strong></div></div></article></section>';
  main.innerHTML = '<header class="builder-heading"><div><a class="builder-back font-1-xs" href="./index.html" aria-label="Voltar ao início">' + iconeAnimado('arrow','back') + 'Voltar ao início</a><div class="builder-title-line">' + indicadorBuild(avaliacao,'public-compatibility') + '<h1>' + h(build.titulo) + '</h1>'
    + '</div><p>Build pública · somente leitura. Alterações na sua cópia não mudam esta configuração.</p>' + (build.descricao ? '<p>' + h(build.descricao) + '</p>' : '') + '</div></header>'
    + '<div class="builder-layout"><div class="component-list">' + (itens.length ? itens.map(linha).join('') : '<p class="planning-help">Esta configuração ainda não tem componentes.</p>') + '</div><aside class="build-sidebar"><section class="build-summary glass-card"><span class="summary-eyebrow">'
    + (parcial ? 'Total parcial dos preços disponíveis' : 'Total das peças') + '</span><strong class="summary-total">' + (avaliacao.preco > 0 ? moeda(avaliacao.preco) : 'Preço a consultar') + '</strong>' + avisoFreteHtml()
    + '<div class="build-public-actions"><button type="button" class="btn-primary" id="public-test" aria-label="Testar build">' + iconeAnimado('magic') + 'Testar build</button><button type="button" class="btn-secondary" id="public-save" aria-label="Salvar cópia no perfil">' + iconeAnimado('plus') + 'Salvar cópia no perfil</button><button type="button" class="btn-secondary" id="public-buy" aria-label="Consultar lojas das peças">' + iconeAnimado('cart') + 'Consultar lojas</button></div><p id="public-feedback" class="planning-help" role="status" aria-live="polite">Entre na sua conta para testar ou salvar uma cópia.</p></section></aside></div>';
  const feedback = main.querySelector('#public-feedback'), salvar = main.querySelector('#public-save'), testar = main.querySelector('#public-test');
  function informar(texto,erro = false) { feedback.textContent = texto; feedback.dataset.tone = erro ? 'error' : 'info'; }
  async function sessao(acao) {
    const perfil = await carregarPerfil();
    if (!perfil.auth) { guardarRetornoPublico(id,acao); navegarPara('./login.html'); return null; }
    return perfil;
  }
  testar.onclick = async () => {
    testar.disabled = true;
    try {
      if (!await sessao('testar')) return;
      // Revalida a visibilidade antes de permitir a interação autenticada.
      const {build:atual} = await fetchComErro('/build/' + encodeURIComponent(id) + '/publica',{method:'GET',cache:'no-store'});
      const estado = buildDaConta(atual), motivo = motivoBenchmark(estado,atual.pecas || []);
      if (motivo) throw new Error(motivo);
      abrirBenchmark(estado,atual.pecas || [],{publica:true});
      informar('A consulta usa a configuração pública; não altera a build.');
    } catch(erro) { informar(erro.message,true); }
    finally { testar.disabled = false; }
  };
  salvar.onclick = async () => {
    salvar.disabled = true;
    try {
      const perfil = await sessao('salvar'); if (!perfil) return;
      await verificarEspacoBuild(perfil);
      const resposta = await copiarBuildPublica(id);
      navegarPara('./configuracao-build.html?' + new URLSearchParams({build_id:resposta.build.id}));
    } catch(erro) { informar(erro.message,true); }
    finally { salvar.disabled = false; }
  };
  main.querySelector('#public-buy').onclick = () => { try { abrirCompraBuild(build,catalogo); } catch(erro) { informar(erro.message,true); } };
  iniciarIndicadores(main); iniciarIcones(main);
  const perfil = await carregarPerfil().catch(()=>({auth:false}));
  if (perfil.auth) informar('Você pode testar ou salvar uma cópia privada, respeitando as vagas da sua conta.');
  const acao = new URLSearchParams(location.search).get('acao_publica');
  if (perfil.auth && acao === 'testar') testar.click(); // Abre apenas a escolha; não consulta API automaticamente.
  else if (perfil.auth && acao === 'salvar') { informar('Para criar uma cópia privada, confirme em “Salvar cópia no perfil”.'); salvar.focus({preventScroll:true}); }
}
