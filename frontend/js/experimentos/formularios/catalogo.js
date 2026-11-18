export function comprimentosDisponiveis(catalogo) {
  return [
    ...new Set(
      (catalogo?.cabos || [])
        .filter(
          (c) =>
            c.disponivel === true &&
            c.categoria?.toUpperCase() === "CAT6" &&
            Number.isFinite(c.metros) &&
            c.metros > 0,
        )
        .map((c) => c.metros),
    ),
  ].sort((a, b) => a - b);
}
let carregamento;
export function carregarCatalogoFormulario() {
  carregamento ??= fetch(
    new URL("../../../data/previa-formularios-catalogo.json", import.meta.url),
  )
    .then(async (r) => {
      if (!r.ok)
        throw new Error(
          "Não foi possível ler a amostra local de cabos e periféricos.",
        );
      const d = await r.json();
      if (!Array.isArray(d.cabos) || !d.perifericos)
        throw new Error("A amostra do catálogo está incompleta.");
      return d;
    })
    .catch((e) => {
      carregamento = null;
      throw e;
    });
  return carregamento;
}
