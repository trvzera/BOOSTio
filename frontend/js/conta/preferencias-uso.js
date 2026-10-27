export const niveisHardware = [
  ["iniciante", "Estou começando", "Ainda não conheço bem as peças e a função de cada uma."],
  ["intermediario", "Conheço o básico", "Reconheço as principais peças e entendo para que servem."],
  ["experiente", "Tenho experiência", "Já conheço as peças e sei avaliar a montagem de um computador."],
];

export function preferenciasUso(usuario) {
  const valor = usuario?.preferencias_uso;
  return {
    nivel_hardware:niveisHardware.some(([nivel]) => nivel === valor?.nivel_hardware) ? valor.nivel_hardware : null,
    tutorial:["pendente","concluido","pulado"].includes(valor?.tutorial) ? valor.tutorial : "nao-oferecido",
    versao_tutorial:Number.isInteger(valor?.versao_tutorial) ? valor.versao_tutorial : 1,
  };
}
export function tutorialPendente(usuario) {
  const p = preferenciasUso(usuario);
  return p.tutorial === "pendente" && p.versao_tutorial === 1;
}
export function ajustarGuiasConhecimento(raiz = document) {
  const nivel = document.documentElement.dataset.hardwareLevel;
  raiz.querySelectorAll("details[data-knowledge-guide]").forEach(guia => {
    if (guia.dataset.knowledgeApplied === (nivel || "padrao")) return;
    guia.open = nivel !== "experiente";
    guia.dataset.knowledgeApplied = nivel || "padrao";
  });
}
export function sincronizarExperiencia(usuario) {
  if (typeof document === "undefined") return;
  const nivel = preferenciasUso(usuario).nivel_hardware;
  if (nivel) document.documentElement.dataset.hardwareLevel = nivel;
  else delete document.documentElement.dataset.hardwareLevel;
  ajustarGuiasConhecimento();
  document.dispatchEvent(new CustomEvent("boostio:experience-changed",{detail:{usuarioId:usuario?.id ?? null}}));
}
