let manifestoPendente;

export function carregarManifestoImagens() {
  manifestoPendente ??= fetch(new URL("../../data/imagens-produtos.json",import.meta.url),{cache:"no-cache"})
    .then(async resposta => {
      if (!resposta.ok) throw new Error("Mapa de imagens indisponível.");
      const mapa = await resposta.json();
      return mapa && typeof mapa === "object" && !Array.isArray(mapa) ? mapa : {};
    }).catch(() => {
      manifestoPendente = null;
      return {}; // Ausência de fotos não deve impedir a montagem ou o catálogo.
    });
  return manifestoPendente;
}

export function enderecoImagem(valor) {
  if (typeof valor !== "string" || !valor.trim()) return "";
  const caminho = valor.trim();
  // Apenas imagens HTTP(S) ou caminhos locais. Nunca inserir URLs executáveis.
  if (/^[a-z][a-z\d+.-]*:/i.test(caminho) && !/^https?:/i.test(caminho)) return "";
  try {
    const base = new URL("../../pages/",import.meta.url), destino = new URL(caminho,base);
    if (["http:","https:"].includes(destino.protocol)) return destino.href;
    if (base.protocol === "file:" && destino.protocol === "file:" && !caminho.includes(":")) return destino.href;
    return "";
  }
  catch { return ""; }
}

export function completarImagens(pecas,mapa = {}) {
  return pecas.map(peca => {
    const origem = [peca.imagem,peca.imagem_url,Object.hasOwn(mapa,peca.part_number) ? mapa[peca.part_number] : null]
      .find(valor => enderecoImagem(valor));
    return {...peca,imagem:origem?.trim() || null};
  });
}

const observadas = new WeakSet();
export function iniciarImagens(raiz = document) {
  raiz.querySelectorAll("img[data-product-image]").forEach(imagem => {
    if (observadas.has(imagem)) return;
    observadas.add(imagem);
    const falhar = () => {
      imagem.hidden = true;
      const alternativa = imagem.nextElementSibling;
      if (alternativa?.hasAttribute("data-product-placeholder")) alternativa.hidden = false;
    };
    imagem.addEventListener("error",falhar,{once:true});
    if (imagem.complete && imagem.naturalWidth === 0) falhar();
  });
}
