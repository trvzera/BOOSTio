import { ajudaCategorias } from "./uso-formulario.js";
import { htmlSeguro as h } from "./catalogo.js";

// Ajuda opcional disponível também por toque e teclado, sem alterar a seleção.
export function ajudaPecaHtml(categoria, nome) {
  const texto = ajudaCategorias[categoria];
  if (!texto) return "";
  return '<details class="component-help"><summary aria-label="Para que serve: ' + h(nome) + '"><span aria-hidden="true">?</span></summary><p>' + h(texto) + '</p></details>';
}
