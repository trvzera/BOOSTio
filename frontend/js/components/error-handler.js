let redirecionando = false;

function caminhoPaginaErro(codigo) {
  const estaEmPages = window.location.pathname.includes("/pages/");
  const pagina = estaEmPages ? "./erro.html" : "./pages/erro.html";
  return `${pagina}?codigo=${encodeURIComponent(codigo)}`;
}

export function redirecionarParaErro(codigo = 500, erro = null) {
  if (redirecionando || window.location.pathname.endsWith("/erro.html")) return;
  redirecionando = true;

  try {
    sessionStorage.setItem(
      "boostio:ultimo-erro",
      JSON.stringify({
        codigo,
        pagina: window.location.pathname,
        mensagem: erro?.message || String(erro || "Erro inesperado"),
        data: new Date().toISOString(),
      }),
    );
  } catch {
    // O redirecionamento continua mesmo se o armazenamento estiver indisponível.
  }

  window.location.replace(caminhoPaginaErro(codigo));
}

export function iniciarTratamentoGlobalDeErros() {
  window.addEventListener("error", (evento) => {
    redirecionarParaErro(500, evento.error || new Error(evento.message));
  });

  window.addEventListener("unhandledrejection", (evento) => {
    const erro = evento.reason instanceof Error
      ? evento.reason
      : new Error(String(evento.reason || "Promise rejeitada"));
    redirecionarParaErro(500, erro);
  });
}
