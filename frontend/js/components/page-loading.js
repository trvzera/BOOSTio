const pendentes = new Set();
export function escolherModoLoading({home,visitada}) { return home || !visitada ? "full" : "fade"; }
export function perfilLoading({home,visitada,frequente=false,cache=false,formulario=false}) {
  return {
    modo:escolherModoLoading({home,visitada}),
    velocidade:frequente && cache && !home ? 2.2 : 1,
    velocidadePronta:frequente && !home ? 2.2 : 1,
    fadeMs:formulario ? 700 : frequente ? (cache ? 180 : 280) : 480,
    minimoMs:formulario ? 800 : 0,
  };
}
export function acompanharCarregamento(promise) {
  pendentes.add(promise);
  // Não cria uma promise rejeitada sem consumidor.
  promise.then(() => pendentes.delete(promise),() => pendentes.delete(promise));
  return promise;
}
export async function aguardarCarregamentos() {
  // Dá aos outros módulos de DOMContentLoaded tempo para registrar suas tarefas.
  await new Promise(resolve => setTimeout(resolve,40));
  while (pendentes.size) await Promise.allSettled([...pendentes]);
}
