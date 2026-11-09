import { atualizarNavegacao } from "../header.js";
export function atualizarMenu(autenticado, administrador = false) { atualizarNavegacao(Boolean(autenticado), Boolean(administrador)); }
