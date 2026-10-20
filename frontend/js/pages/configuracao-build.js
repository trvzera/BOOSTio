import "../header.js";
import "../auth/auth.js";
import { carregarCatalogo,categoriasEditor,perifericos,acessoriosRede,moeda,htmlSeguro as h,nomePeca,imagemPeca,ofertasPeca } from "../build/catalogo.js";
import { abrirBuild,guardarRascunho,buildsLocais,itensCategoria,categoriasMultiplas,informacoesRam,informacoesArmazenamento,motivoSelecao,removerPeca,reduzirQuantidade,linkCompartilhado } from "../build/estado.js";
import { avaliarBuild,selecionarPecaCompativel } from "../build/compatibilidade.js";
import { avisar,copiarTexto,mostrarFalha } from "../build/interface.js";
import { iconeAnimado,iniciarIcones } from "../components/ui.js";
import { indicadorBuild,iniciarIndicadores } from "../build/indicador.js";
import { navegarPara } from "../components/page-loading.js";
import { resumoRede } from "../build/rede.js";
import { salvarAlteracaoLocal } from "../build/autosalvar.js";
import { iniciarDetalhesAnimados } from "../components/animated-details.js";
import { abrirBenchmark, abrirCompraBuild, motivoBenchmark, avisoCompraHtml } from "../build/acoes-build.js";
import { abrirMelhorias } from "../build/melhorias.js";
import { carregarPerfil } from "../conta/perfil.js";
import { acompanharCarregamento } from "../components/page-loading.js";
import { mostrarBuildSalva } from "../build/build-salva.js";
import { carregarCatalogoConta, carregarBuildConta, salvarBuildConta, linkBuildConta, estadoParaConta } from "../build/conta.js";
import { criarBuildManual } from "../api/build/builds.js";

document.addEventListener("DOMContentLoaded",async () => {
  const main = document.querySelector("#builder-main");
  try {
    await acompanharCarregamento(carregarPerfil().catch(() => null));
    const parametros = new URLSearchParams(location.search);
    let buildId = parametros.get("build_id");
    const compartilhada = parametros.get("compartilhar_id");
    if (compartilhada !== null) {
      await mostrarBuildSalva(main, compartilhada, true);
      return;
    }
    if (buildId === null && !parametros.has("id") && !parametros.has("compartilhar")) {
      const nova = await criarBuildManual(estadoParaConta({titulo:"Minha build",descricao:"",visibilidade:"privado",travada:false,orcamento:null,incluirPerifericos:false,incluirRede:false,rede:{},componentes:{}}));
      buildId = nova.build.id;
      history.replaceState(null,"","./configuracao-build.html?" + new URLSearchParams({build_id:buildId}));
    }
    const conta = buildId !== null;
    const catalogo = await acompanharCarregamento(conta ? carregarCatalogoConta() : carregarCatalogo());
    let build = conta ? await acompanharCarregamento(carregarBuildConta(buildId)) : abrirBuild();
    let filaSalvamento = Promise.resolve();
    let falhaSalvamento = null;
    let mensagemSalvamento = conta ? "Alterações são salvas automaticamente na sua conta." : "Alterações são salvas automaticamente neste navegador.", tomSalvamento = "info";
    if (build.travada) mensagemSalvamento = "Build trancada. Destranque-a para alterar e salvar.";
    else if (!conta && buildsLocais().length >= 3 && !buildsLocais().some(item => item.id === build.id)) {
      mensagemSalvamento = "Limite de três builds atingido. Apenas o rascunho será guardado até liberar espaço.";
      tomSalvamento = "warning";
    }
    if (!conta) {
      history.replaceState(null,"","./configuracao-build.html?" + new URLSearchParams({id:build.id}));
      guardarRascunho(build);
    }
    const get = cat => catalogo.find(p => p.id === build.componentes[cat]?.id);
    const urlCategoria = cat => "./pecas.html?" + new URLSearchParams({categoria:cat,build:build.id});
    const bloqueado = (condicao,motivo) => condicao ? 'disabled data-disabled-reason="' + h(motivo) + '"' : "";
    const trancada = "Destranque a build para alterar os componentes.";
    const badge = obrigatoria => obrigatoria ? '<span class="component-badge">Obrigatório</span>' : "";

    function selecionada(categoria,item) {
      const peca = catalogo.find(p => p.id === item.id), titulo = peca ? nomePeca(peca) : item.proprio || "Modelo não identificado";
      const detalhe = peca ? "./peca.html?" + new URLSearchParams({id:peca.id,build:build.id}) : "";
      const oferta = peca ? ofertasPeca(peca)[0] : null, ram = categoria === "memoria_ram", multipla = categoriasMultiplas.has(categoria);
      const slotsPlaca = categoria === "placa_mae" && peca ? [
        peca.quantidade_slots_ram != null && peca.quantidade_slots_ram + " slots de RAM",
        peca.quantidade_slots_m2 != null && peca.quantidade_slots_m2 + " slots M.2",
        peca.quantidade_portas_sata != null && peca.quantidade_portas_sata + " portas SATA",
      ].filter(Boolean).join(" · ") : "";
      const resumo = ram && peca ? item.quantidade + " kit(s) · " + item.quantidade * (peca.quantidade_pentes || 1) + " pentes · " + peca.ddr + " · " + peca.frequencia_mhz + " MHz"
        : slotsPlaca || (peca ? "Selecionado" : "Peça própria · identifique o modelo para validar.");
      let razaoDuplicar = "";
      if (multipla && peca) { try { selecionarPecaCompativel(build,peca,catalogo); } catch (erro) { razaoDuplicar = erro.message; } }
      const unidades = ram ? item.quantidade * (peca?.quantidade_pentes || 1) : categoria === "fan" ? item.quantidade * (peca?.quantidade || 1) : item.quantidade;
      const nomeUnidades = ram ? "pentes" : categoria === "fan" ? "fans" : "unidades";
      return '<article class="component-row component-selected glass-card"><div class="component-selected-main"><div class="component-image">' +
        imagemPeca(peca || {categoria}) + '</div><div class="component-copy">' +
        (peca ? '<a class="component-model font-1-m-b" href="' + detalhe + '" aria-label="Ver detalhes de ' + h(titulo) + '">' + h(titulo) + '</a>' : '<h3 class="component-model font-1-m-b">' + h(titulo) + '</h3>') +
        '<p>' + h(resumo) + '</p></div><div class="component-purchase">' +
        (peca ? '<a class="component-buy btn-primary" href="' + h(oferta.url) + '" target="_blank" rel="noopener noreferrer" aria-label="' + (oferta.direta ? "Comprar" : "Buscar") + ' ' + h(titulo) + ' na ' + h(oferta.loja) + ' em uma nova aba">' +
          iconeAnimado("cart") + (oferta.direta ? "Comprar" : "Buscar") + '</a><strong>' + moeda(peca.preco * item.quantidade) + '</strong>' : '<span class="font-2-xs">Já possuo</span>') +
        '</div><button class="component-remove" type="button" data-remove="' + categoria + '" data-item="' + h(item.id || item.proprio) +
        '" aria-label="Remover ' + h(titulo) + '" title="Remover peça" ' + bloqueado(build.travada,trancada) + '>' + iconeAnimado("trash") + '</button></div>' +
        (multipla && peca ? '<div class="ram-controls"><span class="component-quantity"><strong>' + unidades + '</strong> ' + nomeUnidades +
          (peca.capacidade_gb ? '<span>· ' + (peca.capacidade_gb * item.quantidade) + ' GB</span>' : '') + '</span><div><button type="button" class="btn-ghost" data-quantity-reduce="' + h(peca.id) + '" data-quantity-category="' + categoria +
          '" aria-label="Diminuir quantidade de ' + h(titulo) + '" ' + bloqueado(build.travada || item.quantidade <= 1,build.travada ? trancada : "Use remover para excluir a última unidade ou kit.") + '>−</button><button type="button" class="btn-ghost" data-quantity-add="' + h(peca.id) +
          '" aria-label="Duplicar ' + h(titulo) + '" ' + bloqueado(Boolean(razaoDuplicar),razaoDuplicar) + '>' + iconeAnimado("plus") + 'Duplicar</button></div></div>' : "") + '</article>';
    }
    function grupo(categoria) {
      const cooler = categoria.id === "cooler", cpu = get("processador");
      const obrigatoria = categoria.obrigatoria || (cooler && cpu && !cpu.cooler) ||
        (categoria.id === "placa_video" && cpu && !cpu.videointegrado);
      const tipos = categoria.tipos || [categoria.id];
      const itens = tipos.flatMap(cat => itensCategoria(build,cat).map(item => ({categoria:cat,item})));
      const info = informacoesRam(build,catalogo), temRam = categoria.id === "memoria_ram" && itens.length;
      const razaoAdicionar = build.travada ? trancada : !info.placa ? "Selecione a placa-mãe antes de adicionar mais RAM."
        : info.usados >= info.slots ? "Todos os slots de RAM da placa-mãe estão ocupados." : "";
      const discos = informacoesArmazenamento(build,catalogo);
      const disponivel = categoria.armazenamento && catalogo.some(p => tipos.includes(p.categoria) && (() => { try { selecionarPecaCompativel(build,p,catalogo); return true; } catch { return false; } })());
      const cabecalho = '<div class="component-group-heading"><h2>' + categoria.nome + ' ' + badge(obrigatoria) + '</h2>' +
        (categoria.id === "memoria_ram" ? '<span class="component-count">' + info.usados + ' / ' + (info.slots || "—") + ' pentes · ' + info.capacidade + ' GB</span>'
          : categoria.armazenamento ? '<span class="component-count">' + discos.ssd + ' SSD · ' + discos.hd + ' HD</span>' : "") + '</div>' +
        (categoria.armazenamento && itens.length ? '<p class="component-connections">M.2: ' + discos.m2 + ' / ' + (discos.limites.m2 ?? "não informado") + ' · SATA: ' + discos.sata + ' / ' + (discos.limites.sata ?? "não informado") + '</p>' : "");
      if (itens.length) return '<section class="component-group">' + cabecalho + itens.map(({categoria,item}) => selecionada(categoria,item)).join("") +
        (temRam ? '<button type="button" class="btn-ghost ram-add-model" data-category="memoria_ram" aria-label="Adicionar outro modelo de RAM" ' + bloqueado(Boolean(razaoAdicionar),razaoAdicionar) + '>' + iconeAnimado("plus") + 'Adicionar outro modelo de RAM</button>' : "") +
        (categoria.armazenamento ? '<button type="button" class="btn-ghost ram-add-model" data-category="armazenamento" aria-label="Adicionar SSD ou HD" ' + bloqueado(!disponivel,build.travada ? trancada : "Não há conexões livres confirmadas. Verifique os dados da placa-mãe e os discos adicionados.") + '>' + iconeAnimado("plus") + 'Adicionar SSD ou HD</button>' : "") +
        (categoria.id === "fan" ? '<button type="button" class="btn-ghost ram-add-model" data-category="fan" aria-label="Adicionar outro modelo de fan" ' + bloqueado(build.travada,trancada) + '>' + iconeAnimado("plus") + 'Adicionar outro modelo de fan</button>' : "") +
        (categoria.rede && itens.length < tipos.length ? '<button type="button" class="btn-ghost ram-add-model" data-category="rede" aria-label="Adicionar outro acessório de rede" ' + bloqueado(build.travada,trancada) + '>' + iconeAnimado("plus") + 'Adicionar outro acessório de rede</button>' : "") + '</section>';
      const incluido = cooler && cpu?.cooler, total = catalogo.filter(p => tipos.includes(p.categoria)).length;
      return '<section class="component-group">' + cabecalho + '<article class="component-row glass-card"><button type="button" class="component-empty' + (perifericos.includes(categoria.id) ? ' component-empty-peripheral' : '') + '" data-category="' + categoria.id +
        '" aria-label="' + (categoria.rede ? 'Adicionar cabo ou adaptador' : 'Selecionar componente') + ': ' + h(categoria.nome) + '" ' + bloqueado(build.travada,trancada) + '><div><span class="component-empty-label">' + (categoria.rede ? 'Adicionar cabo ou adaptador' : 'Selecionar componente') + '</span><p>' + (categoria.rede ? h(resumoRede(build.rede)) + (total ? ' · escolha um modelo no catálogo' : ' · produtos ainda não cadastrados') : incluido ? 'Cooler incluso no processador' + (cpu.modelo_cooler ? " · " + h(cpu.modelo_cooler) : "") + ". Adicional opcional."
          : cooler ? "Air cooler e water cooler" : categoria.armazenamento ? "SSD ou HD · escolha ao menos um armazenamento" : "Escolha um modelo no catálogo") +
        '</p></div><span class="component-add" aria-label="' + total + ' modelos no catálogo">' + iconeAnimado("plus") + '</span></button></article></section>';
    }
    function renderizar() {
      // Preserva o checkbox e sua instância Lottie durante as atualizações da build.
      const opcoes = main.querySelector(".builder-options");
      const detalhesAbertos = main.querySelector(".summary-metadata")?.open;
      const resultado = avaliarBuild(build,catalogo);
      const categorias = categoriasEditor.filter(c => (build.incluirPerifericos || !perifericos.includes(c.id)) && (build.incluirRede || !c.rede));
      main.innerHTML = '<header class="builder-heading"><div><a class="builder-back font-1-xs" href="./builds.html" aria-label="Voltar para Minhas builds">' + iconeAnimado("arrow","back") + 'Voltar para Minhas builds</a><div class="builder-title-line">' + indicadorBuild(resultado,"compatibility-details") +
        '<h1>Configure sua build</h1></div><p>Escolha os componentes da sua configuração.</p></div><button type="button" class="btn-primary benchmark-trigger" id="benchmark-build" aria-label="Testar build" ' + bloqueado(Boolean(motivoBenchmark(build,catalogo)),motivoBenchmark(build,catalogo)) + '>' + iconeAnimado("magic") + 'Testar build</button></header>' +
        '<div class="builder-layout"><section class="component-list" aria-label="Componentes"><div class="builder-options"><label class="ui-check font-2-xs"><input type="checkbox" id="include-peripherals" ' + (build.incluirPerifericos ? "checked " : "") +
        bloqueado(build.travada,trancada) + '>' + iconeAnimado("checkbox") + '<span>Incluir periféricos</span></label><label class="ui-check font-2-xs"><input type="checkbox" id="include-network" ' + (build.incluirRede ? "checked " : "") + bloqueado(build.travada,trancada) + '>' + iconeAnimado("checkbox") + '<span>Incluir rede</span></label></div>' + categorias.map(grupo).join("") +
        '</section><aside class="build-sidebar"><section class="build-summary glass-card"><span class="summary-eyebrow">Total da configuração</span><strong class="summary-total">' + moeda(resultado.preco) +
        '</strong><div class="summary-power"><span>Consumo estimado do PC</span><strong>' + resultado.watts + ' W</strong></div>' +
        '<progress class="summary-progress" value="' + resultado.preenchidos + '" max="' + resultado.total + '" aria-label="Peças selecionadas"></progress><p class="font-2-xs summary-note">' +
        resultado.preenchidos + ' de ' + resultado.total + ' peças selecionadas</p><details class="summary-metadata" data-animated-details' + (detalhesAbertos ? ' open' : '') + '><summary class="font-1-xs"><span>Nome, descrição e orçamento</span>' + iconeAnimado("chevron") + '</summary><div class="summary-details"><label for="build-name">Nome da build</label><input class="input-text" id="build-name" maxlength="100" value="' +
        h(build.titulo) + '" ' + bloqueado(build.travada,trancada) + '><label for="build-visibility">Visibilidade</label><select id="build-visibility" class="input-text" ' + bloqueado(build.travada,trancada) +
        '><option value="privado" ' + (build.visibilidade === "privado" ? "selected" : "") + '>Privada</option><option value="publico" ' + (build.visibilidade === "publico" ? "selected" : "") +
        '>Pública</option></select><label for="build-description">Descrição</label><textarea class="input-text" id="build-description" rows="4" maxlength="300" ' + bloqueado(build.travada,trancada) + '>' + h(build.descricao) + '</textarea><label for="build-budget">Orçamento desta build (R$)</label><input class="input-text" id="build-budget" type="number" min="0" max="1000000" step="any" inputmode="decimal" value="' + h(build.orcamento ?? "") + '" placeholder="Sem limite definido" ' + bloqueado(build.travada,trancada) + '></div></details><p class="planning-help" id="build-budget-note"></p><p class="build-autosave-status" id="build-autosave-status" role="status" aria-live="polite" data-tone="' + tomSalvamento + '">' + h(mensagemSalvamento) + '</p><button class="btn-primary" type="button" id="save-configuration" aria-label="Salvar build e voltar">Salvar build e voltar</button><button class="btn-secondary" type="button" id="buy-configuration" aria-label="Comprar build" ' + bloqueado(!Object.keys(build.componentes).length,"Adicione uma peça para consultar as lojas.") + '>' + iconeAnimado("cart") + 'Comprar build</button><button class="btn-secondary" type="button" id="improve-configuration" aria-label="Buscar melhorias" ' + bloqueado(build.travada,trancada) + '>' + iconeAnimado("magnifying") + 'Buscar melhorias</button><button class="btn-secondary" type="button" id="share-configuration" aria-label="Compartilhar build" ' +
        bloqueado(build.visibilidade !== "publico","Torne a build pública para compartilhar.") +
        '>Compartilhar</button><p class="summary-note">' + (conta ? 'Preços atuais do catálogo, sem frete. Alterações salvas na conta.' : 'Preços demonstrativos, sem frete. Salvamento local neste navegador.') + '</p>' + avisoCompraHtml() +
        (build.travada ? '<p class="summary-note">Build trancada. Destranque-a em Minhas builds.</p>' : "") + '</section></aside></div>';
      if (opcoes) main.querySelector(".builder-options").replaceWith(opcoes);
      const atualizarCustos = () => {
        const total = avaliarBuild(build,catalogo).preco;
        main.querySelector(".summary-total").textContent = moeda(total);
        main.querySelector("#build-budget-note").textContent = build.orcamento == null ? "Defina um orçamento para acompanhar o total." : total > build.orcamento ? "Total acima do orçamento em " + moeda(total - build.orcamento) + "." : "Disponível no orçamento: " + moeda(build.orcamento - total) + ".";
        main.querySelector("#build-budget-note").dataset.tone = build.orcamento != null && total > build.orcamento ? "warning" : "info";
      };
      atualizarCustos();
      main.querySelector("#build-budget").oninput = e => {
        if (!e.target.checkValidity() || build.travada) return;
        build.orcamento = e.target.value === "" ? null : Number(e.target.value); persistir(); atualizarCustos();
      };
      main.querySelector("#build-description").oninput = e => { if (!build.travada) { build.descricao = e.target.value; persistir(); } };
      main.querySelector("#benchmark-build").onclick = () => { try { abrirBenchmark(build,catalogo); } catch (erro) { avisar(erro.message); } };
      main.querySelector("#buy-configuration").onclick = () => { try { abrirCompraBuild(build,catalogo); } catch (erro) { avisar(erro.message); } };
      main.querySelector("#improve-configuration").onclick = () => { try { abrirMelhorias(build,catalogo,proxima => { build = proxima; persistir(); renderizar(); }); } catch (erro) { avisar(erro.message); } };
      main.querySelector("#save-configuration").dataset.disabledReason = build.travada ? trancada : "Informe o nome da build para salvar.";
      main.querySelector("#save-configuration").disabled = build.travada || !build.titulo.trim();
      main.querySelector("#build-name").addEventListener("input",e => {
        if (build.travada) return;
        build.titulo = e.target.value; main.querySelector("#save-configuration").disabled = !build.titulo.trim(); persistir();
      });
      main.querySelector("#build-visibility").addEventListener("change",e => { if (build.travada) return; build.visibilidade = e.target.value; persistir(); renderizar(); });
      if (!opcoes) main.querySelector("#include-peripherals").addEventListener("change",e => {
        if (build.travada) return;
        if (!e.target.checked && perifericos.some(cat => build.componentes[cat]) &&
            !confirm("Remover os periféricos selecionados desta build?")) { e.target.checked = true; return; }
        build.incluirPerifericos = e.target.checked;
        if (!build.incluirPerifericos) perifericos.forEach(cat => delete build.componentes[cat]);
        persistir(); renderizar();
      });
      if (!opcoes) main.querySelector("#include-network").addEventListener("change",e => {
        if (build.travada) return;
        if (!e.target.checked && acessoriosRede.some(cat => build.componentes[cat]) &&
            !confirm("Remover os acessórios de rede selecionados desta build?")) { e.target.checked = true; return; }
        build.incluirRede = e.target.checked;
        if (!build.incluirRede) acessoriosRede.forEach(cat => delete build.componentes[cat]);
        persistir(); renderizar();
      });
      main.querySelector("#save-configuration").onclick = async () => {
        try {
          const invalido = [...main.querySelectorAll("#build-budget")].find(input => !input.checkValidity());
          if (invalido) { main.querySelector(".summary-metadata").open = true; invalido.reportValidity(); return; }
          if (!build.titulo.trim()) throw new Error("Informe um nome para a build.");
          if (conta) { await filaSalvamento; if (falhaSalvamento) throw falhaSalvamento; }
          else {
            const salvo = salvarAlteracaoLocal(build,catalogo);
            if (!salvo.salvo) throw new Error(salvo.motivo);
          }
          navegarPara("./builds.html");
        } catch (erro) { avisar(erro.message); }
      };
      main.querySelector("#share-configuration").onclick = async () => {
        try { if (conta) { await filaSalvamento; if (falhaSalvamento) throw falhaSalvamento; } copiarTexto(conta ? linkBuildConta(build.id) : linkCompartilhado(build)); } catch (erro) { avisar(erro.message); }
      };
      iniciarIndicadores(main); iniciarDetalhesAnimados(main); iniciarIcones(main);
    }
    function persistir() {
      if (conta) {
        const atual = structuredClone(build);
        mensagemSalvamento = "Salvando na sua conta…";
        filaSalvamento = filaSalvamento.then(() => salvarBuildConta(atual)).then(() => {
          falhaSalvamento = null;
          mensagemSalvamento = "Salvo na sua conta."; tomSalvamento = "info";
          const status = main.querySelector("#build-autosave-status");
          if (status) { status.textContent = mensagemSalvamento; status.dataset.tone = tomSalvamento; }
        }).catch(erro => {
          falhaSalvamento = erro;
          mensagemSalvamento = "Não foi possível salvar: " + erro.message; tomSalvamento = "error";
          avisar(mensagemSalvamento);
        });
      } else {
      try {
        const estado = salvarAlteracaoLocal(build,catalogo);
        mensagemSalvamento = estado.motivo; tomSalvamento = estado.salvo ? "info" : "warning";
      } catch (erro) { mensagemSalvamento = "Não foi possível salvar: " + erro.message; tomSalvamento = "error"; }
      }
      const status = main.querySelector("#build-autosave-status");
      if (status) { status.textContent = mensagemSalvamento; status.dataset.tone = tomSalvamento; }
    }
    main.addEventListener("click",async e => {
      const botao = e.target.closest("button");
      if (!botao || botao.disabled) return;
      if (botao.dataset.category) {
        try { if (conta) { await filaSalvamento; if (falhaSalvamento) throw falhaSalvamento; } navegarPara(urlCategoria(botao.dataset.category)); }
        catch (erro) { avisar(erro.message); }
        return;
      }
      try {
        if (botao.dataset.remove) build = removerPeca(build,botao.dataset.remove,botao.dataset.item);
        else if (botao.dataset.quantityAdd) build = selecionarPecaCompativel(build,catalogo.find(p => p.id === botao.dataset.quantityAdd),catalogo);
        else if (botao.dataset.quantityReduce) build = reduzirQuantidade(build,botao.dataset.quantityCategory,botao.dataset.quantityReduce);
        else return;
        persistir(); renderizar();
      } catch (erro) { avisar(erro.message); }
    });
    renderizar();
  } catch (erro) { mostrarFalha(main,erro); }
});
