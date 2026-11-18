import { dashboardBenchmarkHtml, iniciarDashboardBenchmark } from "../benchmark/dashboard.js";

const raiz = document.querySelector("#teste-painel-benchmark");
if (raiz) {
  const prefixo = "preview";
  const dispositivos = {cpu:"AMD Ryzen 5 5600 6-Core Processor",gpu:"NVIDIA GeForce RTX 3060"};
  raiz.querySelector("[data-benchmark-preview-host]").innerHTML = dashboardBenchmarkHtml({prefixo,titulo:"Meu setup gamer",
    cpu:"Ryzen 5 5600",gpu:"GeForce RTX 3060",memoria:16,previa:true,dispositivos});
  const parar = iniciarDashboardBenchmark(raiz.querySelector("[data-benchmark-dashboard]"),{prefixo,dispositivos});
  window.addEventListener("pagehide",parar,{once:true});
}
