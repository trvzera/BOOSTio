import { iniciarPainelBenchmark } from "../benchmark/interface.js";

document.addEventListener("DOMContentLoaded",() => {
  const raiz = document.querySelector("#teste-desempenho");
  if (raiz) iniciarPainelBenchmark(raiz);
});
