import { iniciarPainelBenchmark } from "../benchmark/interface.js";
import { criarDiagnosticoBenchmark,textoDiagnostico } from "../experimentos/benchmark-diagnostico.js";
import { iniciarRequisitosLaboratorio } from "../experimentos/requisitos-jogos.js";

document.addEventListener("DOMContentLoaded",() => {
  const raiz = document.querySelector("#teste-desempenho");
  if (!raiz) return;
  const rotas = [...raiz.querySelectorAll('input[name="fpshq-route"]')];
  const registro = raiz.querySelector("#fpshq-diagnostic-log");
  const cliente = criarDiagnosticoBenchmark({
    modo:() => rotas.find(input => input.checked)?.value || "backend",
    aoOcupar:ocupado => rotas.forEach(input => { input.disabled = ocupado; }),
    aoRegistro:dados => { registro.textContent = textoDiagnostico(dados); },
  });
  const parar = iniciarPainelBenchmark(raiz,{cliente});
  const pararRequisitos = iniciarRequisitosLaboratorio(raiz);
  window.addEventListener("pagehide",() => { parar?.(); pararRequisitos?.(); },{once:true});
});
