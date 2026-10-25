let manifestoPendente;

export function carregarManifestoImagens() {
  const carregar = (nome,cache) => fetch(new URL("../../data/" + nome,import.meta.url),{cache})
    .then(async r => { if (!r.ok) return null; const m = await r.json(); return m && typeof m === 'object' && !Array.isArray(m) ? m : null; }).catch(() => null);
  manifestoPendente ??= Promise.all([carregar('imagens-referencia.json','force-cache'),carregar('imagens-produtos.json','no-cache'),carregar('../coletados/imagens-produtos.json','no-store')])
    .then(([referencias,geradas,coletadas]) => {
      if (!referencias || !geradas) manifestoPendente = null;
      return {...referencias,...geradas,...coletadas};
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
    const ficha = Object.hasOwn(mapa,peca.part_number) ? mapa[peca.part_number] : null;
    const referencia = typeof ficha === 'string' ? ficha : ficha && ['categoria','fabricante','modelo'].every(c => ficha[c] === peca[c]) ? ficha.imagem : null;
    const origem = [peca.imagem,peca.imagem_url,referencia]
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
