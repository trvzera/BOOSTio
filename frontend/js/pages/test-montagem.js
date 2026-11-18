import { confirmarPrioridadeMontagem } from "../build/generation-priority.js";
import { aparenciaHtml, normalizarAparencia, atualizarGuiaPorteGabinete, portesGabinete, estilosGabinete } from "../build/aparencia.js";
import { avaliarGabinetes } from "../build/disponibilidade-gabinete.js";
import { htmlSeguro as h } from "../build/catalogo.js";
import { iniciarIcones } from "../components/ui.js";
import { iniciarRestricoesEstiloGabinete, carregarReferenciasGabinetes } from "../build/estilos-gabinete.js";

const raiz = document.querySelector("#teste-montagem");
if (raiz) {
  const status = raiz.querySelector("[data-preview-choice]");
  let preferencias;
  raiz.querySelector("[data-preview-preferences]").addEventListener("click", async () => {
    const escolha = await confirmarPrioridadeMontagem(preferencias?.prioridade_montagem, preferencias?.preferencia_processador);
    if (!escolha) return;
    preferencias = escolha;
    status.textContent = "Prévia confirmada: " + ({intel:"Intel",amd:"AMD","sem-preferencia":"sem preferência de marca"}[escolha.preferencia_processador])
      + " · " + (escolha.prioridade_montagem === "desempenho" ? "melhor desempenho" : "maior custo-benefício") + ". Nenhuma build foi gerada.";
  });
  const campo = raiz.querySelector("[data-preview-appearance]");
  campo.innerHTML = aparenciaHtml();
  // As referências originais são relativas às páginas oficiais em /pages/.
  campo.querySelectorAll("img[src]").forEach(img => img.src = new URL(img.getAttribute("src"), new URL("../../pages/formulario.html", import.meta.url)).href);
  iniciarIcones(campo);
  const aviso = raiz.querySelector("[data-preview-availability]");
  const resumo = raiz.querySelector("[data-preview-case-summary]");
  let catalogo = [];
  let referencias = [];
  let catalogoPronto = false;
  const restricoes = iniciarRestricoesEstiloGabinete(campo,{aviso});
  const escolha = () => normalizarAparencia({
    porte:campo.querySelector('[name="appearance-size"]:checked')?.value,
    estilo:campo.querySelector('[name="appearance-style"]:checked')?.value,
    cor:campo.querySelector('[name="appearance-color"]:checked')?.value,
  });
  function atualizar() {
    const preferencias = escolha();
    restricoes.atualizar(catalogo,preferencias,referencias,{pronto:catalogoPronto});
    atualizarGuiaPorteGabinete(campo, preferencias.porte);
  }
  campo.addEventListener("change", atualizar);
  atualizar();
  async function carregar() {
    try {
      const [resposta, fontes] = await Promise.all([fetch(new URL("../../data/previa-gabinetes.json", import.meta.url)),carregarReferenciasGabinetes()]);
      if (!resposta.ok) throw new Error();
      const dados = await resposta.json();
      catalogo = dados.pecas;
      referencias = fontes;
      catalogoPronto = true;
      raiz.querySelector("[data-preview-source]").textContent = `Amostra do banco local: ${catalogo.length} gabinetes · ${dados.data}. Não é uma consulta de estoque em tempo real. As combinações abaixo ignoram a cor.`;
      resumo.innerHTML = portesGabinete.filter(([v]) => v !== "sem-preferencia").map(([porte, nome]) => '<section><h4 class="font-1-s">' + h(nome) + '</h4><ul>' + estilosGabinete.filter(([v]) => !["sem-preferencia", "compacto"].includes(v)).map(([estilo, titulo]) => {
        const r = avaliarGabinetes(catalogo, {porte, estilo});
        const referencia = referencias.find(p => p.porte_referencia === porte && p.estilo_referencia === estilo);
        return '<li><span>' + h(titulo) + '</span><strong>' + (r.identificados.length ? r.identificados.length + ' identificado(s)' : referencia ? 'Confirmado pelo fabricante' : 'Sem referência confirmada') + '</strong>'
          + (referencia ? '<a href="' + h(referencia.fonte) + '" target="_blank" rel="noopener noreferrer" aria-label="Ver ' + h(referencia.modelo) + ' no fabricante (abre em nova aba)">' + h(referencia.modelo) + '</a>' : '') + '</li>';
      }).join("") + '</ul></section>').join("");
      atualizar();
    } catch {
      restricoes.falhou();
      aviso.hidden = false;
      aviso.textContent = "Não foi possível carregar a amostra. As preferências continuam disponíveis; tente recarregar a página para conferir o catálogo.";
    }
  }
  void carregar();
}
