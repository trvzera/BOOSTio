import { historicoPrecosHtml, iniciarHistoricoPrecos } from "../build/price-history.js";

document.addEventListener("DOMContentLoaded", () => {
  const raiz = document.querySelector("#test-price-history-preview");
  if (!raiz) return;
  const agora = Date.now();
  // Dados exclusivos do laboratório. Não são cotações e não saem desta página.
  const exemplo = {
    historico_precos: [
      [120, 899.90], [100, 849.90], [85, 879.90],
      [65, 799.90], [45, 829.90], [28, 749.90],
      [14, 779.90], [7, 729.90], [0, 699.90],
    ].map(([diasAtras, preco]) => ({
      data: new Date(agora - diasAtras * 86400000).toISOString().slice(0, 10),
      preco,
      loja: "kabum",
    })),
  };
  raiz.innerHTML = historicoPrecosHtml(exemplo, agora);
  iniciarHistoricoPrecos(raiz, exemplo, agora);
});
