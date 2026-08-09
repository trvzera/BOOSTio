// Configurações globais do frontend.
// Em desenvolvimento aponta para o backend Flask local; se existir uma
// variável de ambiente de build (ex.: injetada pelo bundler), ela tem prioridade.
export const API_URL =
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_URL) ||
  "http://127.0.0.1:5000";
