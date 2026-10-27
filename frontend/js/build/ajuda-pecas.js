import { ajudaCategorias } from "./uso-formulario.js";
import { htmlSeguro as h } from "./catalogo.js";

export function introducaoPecaHtml(categoria) {
  const texto = ajudaCategorias[categoria];
  return texto ? '<p class="component-beginner-help font-2-xs">' + h(texto) + '</p>' : "";
}
