import {
  aparenciaHtml,
  normalizarAparencia,
  guiaPorteGabineteHtml,
} from "../../build/aparencia.js";

function isolarIds(campo, id) {
  const mapa = new Map(
    [...campo.querySelectorAll("[id]")].map((e) => [e.id, id(e.id)]),
  );
  campo.querySelectorAll("[id]").forEach((e) => {
    e.id = mapa.get(e.id);
  });
  campo
    .querySelectorAll(
      "[for],[aria-describedby],[aria-labelledby],[aria-controls]",
    )
    .forEach((e) => {
      for (const a of [
        "for",
        "aria-describedby",
        "aria-labelledby",
        "aria-controls",
      ])
        if (e.hasAttribute(a))
          e.setAttribute(
            a,
            e
              .getAttribute(a)
              .split(" ")
              .map((v) => mapa.get(v) || v)
              .join(" "),
          );
    });
}
export function prepararAparenciaPreview(raiz, respostas, id) {
  const campo = raiz.querySelector("[data-preview-appearance-form]");
  if (!campo) return;
  campo.innerHTML = aparenciaHtml(respostas.aparencia, [], {
    possuiGabinete: respostas.pecas.includes("gabinete"),
  });
  campo
    .querySelectorAll("img[src]")
    .forEach(
      (img) =>
        (img.src = new URL(
          img.getAttribute("src"),
          new URL("../../../pages/formulario.html", import.meta.url),
        ).href),
    );
  isolarIds(campo, id);
  // As preferências são livres. O modelo realmente escolhido deverá passar pela compatibilidade.
  campo.addEventListener("change", () => {
    respostas.aparencia = normalizarAparencia({
      porte: campo.querySelector('[name="appearance-size"]:checked')?.value,
      estilo: campo.querySelector('[name="appearance-style"]:checked')?.value,
      cor: campo.querySelector('[name="appearance-color"]:checked')?.value,
    });
    const guia = campo.querySelector("#" + id("appearance-size-guide"));
    if (guia) guia.innerHTML = guiaPorteGabineteHtml(respostas.aparencia.porte);
  });
}
