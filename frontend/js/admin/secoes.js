// Seções do dashboard de administração. Para acrescentar uma, registre aqui o id (igual ao
// data-admin-secao do HTML), o rótulo do menu e a função que a inicia.
import { iniciarPendencias } from "./pendencias-painel.js";

export const secoes = [
  {id: "pendencias", rotulo: "Pendências", iniciar: iniciarPendencias},
];
