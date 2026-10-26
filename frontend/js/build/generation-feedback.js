import { htmlSeguro as h } from "./catalogo.js";
import { avaliarOrcamentoGeracao, MINIMO_PC_GERACAO } from "./orcamento-formulario.js";

export function feedbackGeracao(erro, {total,percentual = 0,aparencia = {}} = {}) {
  const incerto = erro.resultadoIncerto === true, semEspaco = erro.codigo === "limite-builds";
  const titulo = semEspaco ? "Suas três vagas estão ocupadas" : incerto ? "Não conseguimos confirmar sua montagem"
    : erro.geracao?.titulo || ({"ia-timeout":"A IA demorou para responder","ia-limite":"A IA está ocupada agora",
      "ia-cota-global":"O limite de gerações de hoje foi atingido",offline:"Você está sem conexão",conexao:"Não conseguimos acessar a BOOSTio"}[erro.codigo]) || "Não foi possível gerar sua build";
  const motivo = erro.geracao?.motivo;
  const orcamento = !semEspaco && !incerto && ["orcamento","perifericos"].includes(motivo);
  const limites = avaliarOrcamentoGeracao(total,percentual);
  const base = Number.isFinite(total) ? total : MINIMO_PC_GERACAO;
  const sugerido = orcamento ? Math.max(erro.geracao.orcamentoSugerido || Math.ceil(base * 1.1 / 100) * 100, limites.minimoTotal || MINIMO_PC_GERACAO) : null;
  const etapa = erro.geracao?.etapa;
  const html = '<div class="build-generation-error"><h1 class="font-1-m" tabindex="-1">' + h(titulo) + '</h1>'
    + '<p id="erro-gerar-build" class="font-2-s" role="alert">' + h(erro.message) + '</p>'
    + (orcamento ? '<form id="generation-budget-form" class="generation-budget-form"><label class="planning-field" for="generation-budget">Ajustar orçamento total (R$)<input class="input-text" type="number" id="generation-budget" min="' + (limites.minimoTotal || MINIMO_PC_GERACAO) + '" max="1000000" step="0.01" data-number-step="100" inputmode="decimal" required value="' + h(Math.min(1000000,sugerido)) + '" aria-describedby="generation-budget-help generation-budget-feedback"></label><p id="generation-budget-help">A porcentagem dos periféricos será mantida. Este valor é uma sugestão para você editar; não garante uma montagem para todo objetivo. A alteração só vale ao confirmar abaixo.</p><p id="generation-budget-feedback" role="status" aria-live="polite"></p><button type="submit" class="btn-primary" aria-label="Aplicar novo orçamento e tentar gerar novamente">Aplicar orçamento e tentar novamente</button></form>' : '')
    + '<div class="generation-actions">'
    + (semEspaco || incerto ? '<a href="./builds.html" class="btn-primary" aria-label="Conferir minhas builds">Conferir minhas builds</a>'
      : !orcamento ? '<button type="button" id="tentar-gerar-build" class="' + (["cor","aparencia"].includes(motivo) ? 'btn-secondary' : 'btn-primary') + '" aria-label="Tentar gerar build novamente">Tentar novamente</button>' : '')
    + (motivo === "cor" && aparencia.cor !== "sem-preferencia" ? '<button type="button" id="generation-without-color" class="btn-primary" aria-label="Tentar gerar sem preferência de cor">Tentar sem preferência de cor</button>' : '')
    + (motivo === "aparencia" ? '<button type="button" id="generation-without-appearance" class="btn-primary" aria-label="Tentar gerar sem preferências visuais">Tentar sem preferências visuais</button>' : '')
    + '<button type="button" id="revisar-orcamento" class="btn-secondary" aria-label="Revisar orçamento">Revisar orçamento</button>'
    + (percentual || motivo === "perifericos" ? '<button type="button" data-generation-step="perifericos" class="btn-secondary" aria-label="Revisar reserva dos periféricos">Revisar periféricos</button>' : '')
    + (etapa && !["orcamento","perifericos"].includes(etapa) ? '<button type="button" data-generation-step="' + h(etapa) + '" class="btn-secondary" aria-label="Revisar a etapa relacionada ao erro">' + ({aparencia:"Revisar aparência",pecas:"Revisar peças próprias",objetivo:"Revisar objetivo"}[etapa] || "Revisar pedido") + '</button>' : '')
    + (erro.status === 401 ? '<a href="./login.html" class="btn-ghost" aria-label="Entrar na conta">Entrar na conta</a>' : '')
    + '</div></div>';
  return {html,orcamento};
}
