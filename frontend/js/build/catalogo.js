import { acompanharCarregamento } from "../components/page-loading.js";
export const perifericos = ["monitor", "teclado", "mouse", "fone"];
export const categorias = [
  { id: "processador", nome: "Processador", sigla: "CPU", obrigatoria: true },
  { id: "placa_mae", nome: "Placa-mãe", sigla: "MB", obrigatoria: true },
  { id: "memoria_ram", nome: "Memória RAM", sigla: "RAM", obrigatoria: true },
  { id: "ssd", nome: "SSD", sigla: "SSD", armazenamento: true },
  { id: "hd", nome: "HD", sigla: "HD", armazenamento: true },
  { id: "placa_video", nome: "Placa de vídeo", sigla: "GPU" },
  { id: "fonte", nome: "Fonte", sigla: "PSU", obrigatoria: true },
  { id: "gabinete", nome: "Gabinete", sigla: "CASE", obrigatoria: true },
  { id: "fan", nome: "Fans", sigla: "FAN", obrigatoria: true },
  { id: "air_cooler", nome: "Air cooler", sigla: "AIR" },
  { id: "water_cooler", nome: "Water cooler", sigla: "AIO" },
  { id: "monitor", nome: "Monitor", sigla: "MON" },
  { id: "teclado", nome: "Teclado", sigla: "KEY" },
  { id: "mouse", nome: "Mouse", sigla: "MSE" },
  { id: "fone", nome: "Headset / Fone", sigla: "SND" },
];
export const categoriasEditor = categorias.filter(c => !["ssd","hd","air_cooler","water_cooler"].includes(c.id));
categoriasEditor.splice(3, 0,
  {id:"armazenamento",nome:"SSD / HD",sigla:"SSD/HD",tipos:["ssd","hd"],armazenamento:true,obrigatoria:true});
categoriasEditor.splice(categoriasEditor.findIndex(c => c.id === "fan") + 1, 0,
  {id:"cooler",nome:"Coolers",sigla:"COOL",tipos:["air_cooler","water_cooler"]});
export function categoriaCatalogo(id) {
  return categoriasEditor.find(c => c.id === id) || categorias.find(c => c.id === id);
}

let carregamento;
// Trocar somente este carregamento pela API quando /pecas/ estiver pronta.
export function carregarCatalogo() {
  carregamento ??= acompanharCarregamento(fetch(new URL("../../data/catalogo-demo.json", import.meta.url),{cache:"force-cache"})
    .then((resposta) => {
      if (!resposta.ok) throw new Error("Não foi possível carregar o catálogo.");
      return resposta.json();
    }).then(catalogo => {
      try { sessionStorage.setItem("boostio:catalogo-pronto","1"); } catch {}
      return catalogo;
    }).catch(erro => { carregamento = null; throw erro; }));
  return carregamento;
}

export const moeda = (valor) => new Intl.NumberFormat("pt-BR", {
  style: "currency", currency: "BRL",
}).format(valor);

export const htmlSeguro = (valor = "") => String(valor)
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");

export function nomePeca(peca) {
  return peca ? [peca.fabricante, peca.modelo].filter(Boolean).join(" ") : "";
}

export function imagemPeca(peca, classe = "") {
  const categoria = categorias.find((c) => c.id === peca?.categoria);
  // Foto ausente: placeholder neutro, sem fingir que é a foto do produto.
  return peca?.imagem
    ? '<img class="' + classe + '" src="' + htmlSeguro(peca.imagem) + '" alt="' + htmlSeguro(nomePeca(peca)) + '" loading="lazy">'
    : '<span class="component-placeholder ' + classe + '" aria-hidden="true">' + (categoria?.sigla || "PC") + '</span>';
}

export function ofertasPeca(peca) {
  const nome = nomePeca(peca);
  const busca = encodeURIComponent(nome);
  const linkKabum = peca.link?.startsWith("https://www.kabum.com.br/") ? peca.link : null;
  const lojas = [
    { codigo: "kabum", loja: "KaBuM!", url: linkKabum || "https://www.kabum.com.br/busca/" + busca,
      direta: Boolean(linkKabum?.includes("/produto/")) },
    { codigo: "pichau", loja: "Pichau", url: "https://www.pichau.com.br/search?q=" + busca, direta: false },
    { codigo: "mercadolivre", loja: "Mercado Livre", url: "https://lista.mercadolivre.com.br/" + encodeURIComponent(nome.replaceAll(" ", "-")), direta: false },
  ];
  const logos = {kabum:"kabum-logo.svg",pichau:"pichau.png",mercadolivre:"mercado-livre-87.svg"};
  return lojas.map(loja => {
    const oferta = Array.isArray(peca.ofertas) ? peca.ofertas.find(o => o.loja === loja.codigo) : null;
    let url = loja.url, direta = loja.direta;
    if (oferta?.url) {
      try {
        const endereco = new URL(oferta.url);
        const dominio = loja.codigo === "mercadolivre" ? "mercadolivre.com.br" : loja.codigo + ".com.br";
        if (endereco.protocol === "https:" && (endereco.hostname === dominio || endereco.hostname.endsWith("." + dominio))) {
          url = endereco.href; direta = true;
        }
      } catch { /* Ignora uma oferta com URL inválida. */ }
    }
    const valor = oferta?.preco;
    const preco = valor != null && valor !== "" && Number.isFinite(Number(valor)) && Number(valor) >= 0 ? Number(valor) : null;
    return {...loja,url,direta,preco,atualizadoEm:oferta?.atualizadoEm || null,
      logo:new URL("../../svgs/" + logos[loja.codigo],import.meta.url).href};
  });
}

export const rotulosTecnicos = {
  fabricante: "Fabricante", modelo: "Modelo", consumo_energia: "Consumo estimado (W)",
  soquete: "Socket", socket: "Socket", nucleo: "Núcleos", thread: "Threads",
  clockbase: "Clock base (GHz)", clockmax: "Clock máximo (GHz)", videointegrado: "Vídeo integrado",
  modelo_videointegrado: "GPU integrada", cooler: "Cooler incluso", modelo_cooler: "Cooler incluso",
  chipset: "Chipset", formato: "Formato", tipo_memoria: "Tipo de memória",
  quantidade_slots_ram: "Slots de RAM", memoria_maxima_gb: "RAM máxima (GB)",
  quantidade_slots_m2: "Slots M.2", capacidade_gb: "Capacidade (GB)", ddr: "Geração",
  frequencia_mhz: "Frequência (MHz)", latencia: "Latência", quantidade_pentes: "Módulos no kit",
  iluminacao: "Iluminação", potencia: "Potência (W)", tamanho_mm: "Tamanho (mm)",
  compatibilidade: "Sockets suportados", interface: "Interface", tipo: "Tipo",
  memoria_gb: "Memória de vídeo (GB)", interface_memoria: "Interface da memória",
  consumo_w: "Consumo informado (W)", quantidade_fans: "Ventoinhas",
  conectores_energia: "Conectores de energia", potencia_w: "Potência (W)",
  velocidade_leitura_mbps: "Leitura (MB/s)", velocidade_gravacao_mbps: "Gravação (MB/s)",
  velocidade_rpm: "Rotação (RPM)", memoria_cache_mb: "Cache (MB)",
  formatos_placa_mae: "Formatos de placa-mãe suportados", slots_expansao: "Slots de expansão",
  bays_disco: "Baias de armazenamento", fans_inclusos: "Ventoinhas inclusas",
  suporte_water_cooler: "Suporte a water cooler", tamanho_max_gpu_mm: "Comprimento máximo da GPU (mm)",
  tamanho_max_cooler_mm: "Altura máxima do cooler (mm)", painel_vidro: "Painel de vidro",
  tamanho_radiador_mm: "Radiador (mm)", dimensoes: "Dimensão informada (mm)", quantidade: "Unidades no kit",
  conexao: "Conexão", microfone: "Microfone", cancelamento_ruido: "Cancelamento de ruído",
  resposta_frequencia: "Resposta de frequência", layout: "Layout", switch: "Switch",
  mecanico: "Mecânico", tamanho: "Tamanho", dpi_max: "DPI máximo", botoes: "Botões", sensor: "Sensor",
  tamanho_polegadas: "Tela (polegadas)", resolucao: "Resolução", taxa_atualizacao_hz: "Taxa de atualização (Hz)",
  tipo_painel: "Tipo de painel", tempo_resposta_ms: "Tempo de resposta (ms)", hdr: "HDR",
};

export function fichaTecnica(peca) {
  const ignorados = new Set(["id", "categoria", "imagem", "preco", "link", "part_number", "esgotado", "ofertas"]);
  return Object.entries(peca).filter(([chave, valor]) => !ignorados.has(chave) && valor != null)
    .map(([chave, valor]) => [
      rotulosTecnicos[chave] || chave.replaceAll("_", " "),
      typeof valor === "boolean" ? (valor ? "Sim" : "Não") : String(valor),
    ]);
}
