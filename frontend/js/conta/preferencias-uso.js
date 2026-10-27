export const niveisHardware = [
  ["iniciante", "Estou começando", "Quero entender para que serve cada peça."],
  ["intermediario", "Conheço o básico", "Reconheço as peças, mas ainda preciso de algumas orientações."],
  ["experiente", "Tenho experiência", "Prefiro uma apresentação mais compacta, com ajuda quando precisar."],
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
