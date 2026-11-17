import { perguntasPc, perguntasNotebook, pecasPreview, perifericosPreview, prioridadesPreview, marcasPreview,
  novasRespostasPreview, percentualPreview, validarEtapaPreview, resumoFormularioPreview } from "../experimentos/formularios.js";
import { htmlSeguro as h, moeda } from "../build/catalogo.js";
import { vincularRede } from "../build/rede.js";
import { aparenciaHtml, normalizarAparencia, guiaPorteGabineteHtml } from "../build/aparencia.js";
import { iniciarRestricoesEstiloGabinete, carregarReferenciasGabinetes } from "../build/estilos-gabinete.js";
import { dividirOrcamento } from "../build/orcamento-formulario.js";
import { prioridadesUso, orientacoesEtapas } from "../build/uso-formulario.js";
import { ajustarGuiasConhecimento } from "../conta/preferencias-uso.js";
import { iconeAnimado, iniciarIcones } from "../components/ui.js";

// Intencionalmente sem imports de geração de build, perfil, preferências salvas ou LLM.
function iniciarFormularioTeste(raiz,tipo) {
  const perguntas = tipo === "pc" ? perguntasPc : perguntasNotebook;
  const prefixo = "preview-form-" + tipo;
  let respostas = novasRespostasPreview(tipo), etapa = 0;
  const nome = tipo === "pc" ? "Desktop" : "Notebook";
  const id = chave => prefixo + "-" + chave;
  const selecionado = (chave,valor) => Array.isArray(respostas[chave]) ? respostas[chave].includes(valor) : respostas[chave] === valor;
  function opcoes(chave,lista,{multipla = false,explicacao = false} = {}) {
    return '<fieldset class="test-form-options"><legend class="sr-only">' + h(chave) + '</legend>' + lista.map(([valor,titulo,descricao]) =>
      '<label class="test-form-choice ui-check"><input type="' + (multipla ? 'checkbox' : 'radio') + '" name="' + id(chave) + '" data-answer="' + h(chave) + '" value="' + h(valor) + '"' + (selecionado(chave,valor) ? ' checked' : '') + '>' + iconeAnimado(multipla ? "checkbox" : "circledot")
      + '<span><strong>' + h(titulo) + '</strong>' + (descricao ? '<small' + (explicacao ? ' data-knowledge-beginner' : '') + '>' + h(descricao) + '</small>' : '') + '</span></label>').join('') + '</fieldset>';
  }
  function detalhePeca(chave,titulo) {
    return '<label class="test-form-field" for="' + id('model-'+chave) + '">Modelo de ' + h(titulo.toLowerCase()) + '<input id="' + id('model-'+chave) + '" data-model="' + h(chave) + '" type="text" maxlength="120" required autocomplete="off" placeholder="Informe a marca e o modelo" value="' + h(respostas.pecasDetalhes[chave] || '') + '"></label>';
  }
  function perifericos() {
    const possui = respostas.perifericos === "alguns-perifericos";
    return (possui ? '<div class="test-form-group"><h4>Quais você já possui?</h4>' + opcoes('perifericosProprios',perifericosPreview,{multipla:true})
      + perifericosPreview.filter(([v])=>selecionado('perifericosProprios',v)).map(([v,t])=>detalhePeca(v,t)).join('') + '</div>' : '')
      + (respostas.perifericos && respostas.perifericos !== "sem-perifericos" && (!possui || respostas.perifericosProprios.length < perifericosPreview.length)
        ? '<label class="test-form-field" for="' + id('percent') + '">Qual porcentagem reservar para os novos periféricos?<input id="' + id('percent') + '" data-number="percentualPerifericos" type="number" min="1" max="99" step="1" required value="' + h(respostas.percentualPerifericos) + '" aria-describedby="' + id('allocation') + '"></label><p class="test-form-help" id="' + id('allocation') + '" data-allocation></p><p class="test-form-help">A reserva é um teto: não precisa gastar tudo. A sobra fica com você e não aumenta o limite do PC. O mínimo atual é R$ 500 para periféricos novos, e o catálogo pode exigir mais.</p>' : '');
  }
  function campoSelecao(chave,titulo,lista) {
    return '<label class="test-form-field" for="' + id(chave) + '">' + titulo + '<select id="' + id(chave) + '" data-select="' + chave + '">' + lista.map(([v,t])=>'<option value="' + v + '"' + (respostas[chave] === v ? ' selected' : '') + '>' + t + '</option>').join('') + '</select></label>';
  }
  function campos(pergunta) {
    if (pergunta.tipo === "orcamento") return '<div class="test-form-budget-presets">' + [3000,5000,8000].map(v=>'<button type="button" class="btn-secondary" data-budget="' + v + '" aria-label="Definir limite de ' + v + ' reais">Até ' + moeda(v) + '</button>').join('') + '</div>'
      + '<label class="test-form-field" for="' + id('budget') + '">Seu limite em reais<input id="' + id('budget') + '" data-number="orcamento" type="number" inputmode="decimal" min="' + (tipo === 'pc' ? '2000' : '0.01') + '" max="1000000" step="0.01" required placeholder="Ex.: 5000" value="' + h(respostas.orcamento ?? '') + '"></label>'
      + (tipo === 'pc' ? '<input class="test-form-budget-range" type="range" min="2000" max="' + Math.max(20000,respostas.orcamento || 20000) + '" step="100" data-preview-budget-range aria-label="Ajustar orçamento de teste de cem em cem reais" value="' + h(respostas.orcamento || 2000) + '">' : '')
      + '<p class="test-form-help">Frete não incluído. ' + (tipo === 'pc' ? 'Os limites são os mesmos do formulário atual.' : 'Valor apenas para testar as perguntas; ainda não avaliamos se há um notebook disponível por esse preço.') + '</p>';
    if (pergunta.tipo === "rede") return '<div data-preview-network></div>';
    if (pergunta.tipo === "aparencia") return '<p class="test-form-scroll-hint">' + iconeAnimado('arrow','down') + 'Role nesta área para ver as cores, os tamanhos e os estilos.</p><div data-preview-appearance-form></div>';
    if (pergunta.tipo === "preferencias") return campoSelecao('memoria','Memória para manter programas abertos',[["sem-preferencia","Quero ajuda para escolher"],["16-gb","Pelo menos 16 GB"],["32-gb","Pelo menos 32 GB"]])
      + campoSelecao('armazenamento','Espaço para arquivos e programas',[["sem-preferencia","Quero ajuda para escolher"],["512-gb","SSD de pelo menos 512 GB"],["1-tb","SSD de pelo menos 1 TB"]])
      + campoSelecao('bateria','Uso longe da tomada',[["sem-preferencia","Ainda não sei"],["priorizar","Quero priorizar a duração da bateria"],["tomada","Vou usar mais ligado à tomada"]])
      + campoSelecao('sistema','Sistema que prefere usar',[["sem-preferencia","Sem preferência"],["windows","Windows"],["macos","macOS"],["linux","Linux"]]);
    return opcoes(pergunta.chave,pergunta.opcoes,{multipla:pergunta.tipo === 'pecas',explicacao:pergunta.tipo === 'pecas'})
      + (pergunta.tipo === 'pecas' ? '<div class="test-form-group">' + pecasPreview.filter(([v])=>v !== 'nenhuma' && selecionado('pecas',v)).map(([v,t])=>detalhePeca(v,t)).join('') + '<p class="test-form-help">Esta prévia não confirma os modelos no catálogo nem verifica a compatibilidade.</p></div>' : '')
      + (pergunta.tipo === 'perifericos' ? perifericos() : '');
  }
  function ajuda(pergunta) {
    const texto = pergunta.chave === 'objetivo' ? prioridadesUso[respostas.objetivo] || 'Escolha um uso para entender o que teria prioridade, respeitando seu limite de gasto.' : tipo === 'pc' ? orientacoesEtapas[pergunta.chave] : '';
    return '<div class="test-form-help-card" data-knowledge-beginner' + (!texto ? ' hidden' : '') + '><h4>Sobre esta escolha</h4><p data-preview-help-copy>' + h(texto || '') + '</p></div>';
  }
  function atualizarAvanco() {
    const problema = etapa === perguntas.length ? prioridadesPreview.some(([v])=>v===respostas.prioridade_montagem) ? '' : 'Escolha a prioridade para concluir a prévia.' : validarEtapaPreview(tipo,perguntas[etapa],respostas);
    const proximo = raiz.querySelector('[data-form-next]');
    proximo.disabled = Boolean(problema);
    if (problema) proximo.dataset.disabledReason = problema;else delete proximo.dataset.disabledReason;
    const reserva = raiz.querySelector('[data-allocation]');
    if (reserva) { const r=dividirOrcamento(respostas.orcamento,percentualPreview(respostas));reserva.textContent=r ? 'Até ' + moeda(r.perifericos) + ' para periféricos · até ' + moeda(r.pc) + ' para o PC.' : 'Informe uma porcentagem inteira de 1 a 99.'; }
  }
  // Aparência é compartilhada; isole IDs e referências para coexistir com a outra prévia de gabinete.
  function isolarIds(campo) {
    const mapa = new Map([...campo.querySelectorAll('[id]')].map(e=>[e.id,id(e.id)]));
    campo.querySelectorAll('[id]').forEach(e=>{e.id=mapa.get(e.id);});
    campo.querySelectorAll('[for],[aria-describedby],[aria-labelledby],[aria-controls]').forEach(e=>{
      for (const a of ['for','aria-describedby','aria-labelledby','aria-controls']) if (e.hasAttribute(a)) e.setAttribute(a,e.getAttribute(a).split(' ').map(v=>mapa.get(v)||v).join(' '));
    });
  }
  function prepararAparencia() {
    const campo = raiz.querySelector('[data-preview-appearance-form]');
    if (!campo) return;
    campo.innerHTML = aparenciaHtml(respostas.aparencia,[],{possuiGabinete:respostas.pecas.includes('gabinete')});
    campo.querySelectorAll('img[src]').forEach(img=>img.src=new URL(img.getAttribute('src'),new URL('../../pages/formulario.html',import.meta.url)).href);
    const restricoes = iniciarRestricoesEstiloGabinete(campo);
    isolarIds(campo);
    const ler = () => normalizarAparencia({porte:campo.querySelector('[name="appearance-size"]:checked')?.value,estilo:campo.querySelector('[name="appearance-style"]:checked')?.value,cor:campo.querySelector('[name="appearance-color"]:checked')?.value});
    let catalogo = [], referencias = [], pronto = false;
    function sincronizar() {
      respostas.aparencia=ler();
      const validacao=restricoes?.atualizar(catalogo,respostas.aparencia,referencias,{pronto});
      if (validacao?.alterado) respostas.aparencia.estilo=validacao.estilo;
      const guia=campo.querySelector('#'+id('appearance-size-guide'));
      if(guia)guia.innerHTML=guiaPorteGabineteHtml(respostas.aparencia.porte);
      // Os IDs de avisos dinâmicos derivam dos IDs já isolados dos cartões.
    }
    campo.addEventListener('change',sincronizar);sincronizar();
    if (restricoes) void Promise.all([
      fetch(new URL('../../data/previa-gabinetes.json',import.meta.url)).then(async r=>{if(!r.ok)throw new Error('Amostra indisponível');return r.json();}),
      carregarReferenciasGabinetes(),
    ]).then(([amostra,fontes])=>{if(!campo.isConnected)return;catalogo=amostra.pecas;referencias=fontes;pronto=true;sincronizar();}).catch(()=>{if(campo.isConnected)restricoes.falhou();});
  }
  function renderizar({focar = false} = {}) {
    const revisao = etapa === perguntas.length;
    const pergunta = revisao ? {titulo:'Vamos conferir suas respostas?',descricao:'Escolha a prioridade e conclua esta simulação. Nenhuma consulta de IA será enviada.',chave:'revisao'} : perguntas[etapa];
    raiz.innerHTML = '<div class="test-form-shell"><div class="test-form-toolbar"><span>' + nome + ' · prévia independente</span><button type="button" class="btn-ghost" data-form-reset aria-label="Reiniciar a prévia de ' + nome.toLowerCase() + '">Reiniciar prévia</button></div>'
      + '<nav class="test-form-steps" aria-label="Etapas da prévia de ' + nome.toLowerCase() + '">' + [...perguntas,{etapa:'Revisão'}].map((p,i)=>'<button type="button" data-form-step="' + i + '" aria-label="Ir para a etapa ' + (i+1) + ': ' + h(p.etapa) + '"' + (i === etapa ? ' aria-current="step"' : '') + (i > etapa ? ' disabled' : '') + '><span>' + String(i+1).padStart(2,'0') + '</span>' + h(p.etapa) + '</button>').join('') + '</nav>'
      + '<div class="test-form-layout"><div class="test-form-intro"><span class="question-tag font-1-xs">Etapa ' + (etapa+1) + ' de ' + (perguntas.length+1) + '</span><h3 class="font-1-xl" id="' + id('question-title') + '" tabindex="-1">' + h(pergunta.titulo) + '</h3><p>' + h(pergunta.descricao) + '</p>' + ajuda(pergunta) + '</div>'
      + '<form class="test-form-answers" aria-labelledby="' + id('question-title') + '"><div class="test-form-scroll" tabindex="0" role="region" aria-label="Respostas desta etapa">'
      + (revisao ? (tipo === 'pc' ? '<h4>Preferência de processador</h4>' + opcoes('preferencia_processador',marcasPreview) : '') + '<h4>Prioridade da escolha</h4>' + opcoes('prioridade_montagem',prioridadesPreview) + '<details class="test-form-summary"><summary>Ver respostas desta prévia</summary><pre data-preview-answers></pre></details>' : campos(pergunta))
      + '</div><p class="test-form-feedback" role="status" aria-live="polite" data-form-feedback></p><div class="test-form-navigation"><button type="button" class="btn-ghost" data-form-back aria-label="Voltar à etapa anterior da prévia"' + (!etapa ? ' disabled' : '') + '>' + iconeAnimado('arrow','back') + 'Voltar</button><button type="submit" class="btn-primary" data-form-next aria-label="' + (revisao ? 'Concluir prévia sem gerar build' : 'Avançar para a próxima etapa') + '">' + (revisao ? 'Concluir prévia' : 'Avançar') + iconeAnimado('arrow') + '</button></div></form></div><section class="test-form-result" data-form-result hidden aria-live="polite"></section></div>';
    const form=raiz.querySelector('form');
    if (revisao) raiz.querySelector('[data-preview-answers]').textContent=JSON.stringify(resumoFormularioPreview(tipo,respostas),null,2);
    if (pergunta.tipo === 'rede') vincularRede(raiz.querySelector('[data-preview-network]'),respostas.rede,{prefixo:id('network'),aoAlterar:rede=>{respostas.rede=rede;atualizarAvanco();},aoRenderizar:campo=>ajustarGuiasConhecimento(campo)});
    prepararAparencia();iniciarIcones(raiz);ajustarGuiasConhecimento(raiz);atualizarAvanco();
    form.addEventListener('submit',evento=>{
      evento.preventDefault();
      if (!form.reportValidity()) return;
      const problema = revisao ? perguntas.map(p=>validarEtapaPreview(tipo,p,respostas)).find(Boolean) : validarEtapaPreview(tipo,pergunta,respostas);
      if(problema){raiz.querySelector('[data-form-feedback]').textContent=problema;return;}
      if(!revisao){etapa++;renderizar({focar:true});return;}
      if(!prioridadesPreview.some(([v])=>v===respostas.prioridade_montagem))return;
      const resultado=raiz.querySelector('[data-form-result]');resultado.hidden=false;
      resultado.innerHTML='<h4 tabindex="-1">Prévia concluída</h4><p>Suas respostas foram organizadas para avaliarmos as perguntas. Nenhuma build ou recomendação foi gerada, e nada foi salvo na conta.</p><details class="test-form-summary"><summary>Ver dados do teste</summary><pre></pre></details>';
      resultado.querySelector('pre').textContent=JSON.stringify(resumoFormularioPreview(tipo,respostas),null,2);resultado.querySelector('h4').focus({preventScroll:true});
    });
    form.addEventListener('input',evento=>{
      const e=evento.target;
      if(e.dataset.number)respostas[e.dataset.number]=e.valueAsNumber;
      if(e.hasAttribute('data-preview-budget-range')){respostas.orcamento=e.valueAsNumber;form.querySelector('[data-number="orcamento"]').value=e.value;}
      if(e.dataset.number==='orcamento'){const range=form.querySelector('[data-preview-budget-range]');if(range){range.max=Math.max(20000,e.valueAsNumber||20000);range.value=e.value;}}
      if(e.dataset.model)respostas.pecasDetalhes[e.dataset.model]=e.value;
      atualizarAvanco();
    });
    form.addEventListener('change',evento=>{
      const e=evento.target,chave=e.dataset.answer;
      if(e.dataset.select)respostas[e.dataset.select]=e.value;
      if(chave){
        if(e.type === 'checkbox'){
          let lista=new Set(respostas[chave]);e.checked?lista.add(e.value):lista.delete(e.value);
          if(chave === 'pecas'){if(e.value==='nenhuma'&&e.checked)lista=new Set(['nenhuma']);else lista.delete('nenhuma');}
          respostas[chave]=[...lista];
          if(chave==='pecas')pecasPreview.forEach(([v])=>{if(!lista.has(v))delete respostas.pecasDetalhes[v];});
          if(chave==='perifericosProprios'&&!e.checked)delete respostas.pecasDetalhes[e.value];
        }else respostas[chave]=e.value;
        if(['pecas','perifericos','perifericosProprios'].includes(chave)){
          const v=e.value;renderizar();const novo=[...raiz.querySelectorAll('[data-answer]')].find(input=>input.dataset.answer===chave&&input.value===v);novo?.focus({preventScroll:true});return;
        }
        if(chave==='objetivo'){
          const guia=raiz.querySelector('.test-form-help-card');guia.querySelector('p').textContent=prioridadesUso[e.value]||'';ajustarGuiasConhecimento(raiz);
        }
      }
      atualizarAvanco();
    });
    if(focar)raiz.querySelector('h3').focus();
  }
  raiz.addEventListener('click',evento=>{
    const botao=evento.target.closest('button');if(!botao||botao.disabled)return;
    if(botao.hasAttribute('data-form-reset')){respostas=novasRespostasPreview(tipo);etapa=0;renderizar({focar:true});}
    if(botao.hasAttribute('data-form-back')){etapa--;renderizar({focar:true});}
    if(botao.hasAttribute('data-form-step')){etapa=Number(botao.dataset.formStep);renderizar({focar:true});}
    if(botao.dataset.budget){const input=raiz.querySelector('[data-number="orcamento"]');input.value=botao.dataset.budget;input.dispatchEvent(new Event('input',{bubbles:true}));}
  });
  renderizar();
}
document.querySelectorAll('[data-form-preview]').forEach(raiz=>iniciarFormularioTeste(raiz,raiz.dataset.formPreview));
