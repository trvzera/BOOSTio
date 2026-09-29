import { atualizarNavegacao } from "../header.js";
export function atualizarMenu(autenticado) { atualizarNavegacao(Boolean(autenticado)); }
