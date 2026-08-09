// Entry point da página inicial (index.html).
import "../header.js";
import "../services-carousel.js";
import "../auth/auth.js";

document.addEventListener("DOMContentLoaded", async () => {
  try {
    // Nenhuma lógica adicional específica da home além do bootstrap comum
    // (header, carrossel de serviços e confirmação de autenticação) acima.
  } catch (erro) {
    console.error("Erro ao iniciar a página inicial:", erro);
  }
});
