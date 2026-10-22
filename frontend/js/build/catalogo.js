import { acompanharCarregamento } from "../components/page-loading.js";
import { completarCatalogoDemo } from "./hardware.js";
import { carregarManifestoImagens, completarImagens, enderecoImagem } from "./imagens-produtos.js";
export const perifericos = ["monitor", "teclado", "mouse", "fone"];
export const acessoriosRede = ["cabo_rede", "adaptador_wifi"];
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
  { id: "cabo_rede", nome: "Cabo de rede", sigla: "LAN" },
  { id: "adaptador_wifi", nome: "Adaptador Wi-Fi", sigla: "WIFI" },
];
export const categoriasEditor = categorias.filter(c => !["ssd","hd","air_cooler","water_cooler",...acessoriosRede].includes(c.id));
categoriasEditor.splice(3, 0,
  {id:"armazenamento",nome:"SSD / HD",sigla:"SSD/HD",tipos:["ssd","hd"],armazenamento:true,obrigatoria:true});
categoriasEditor.splice(categoriasEditor.findIndex(c => c.id === "fan") + 1, 0,
  {id:"cooler",nome:"Coolers",sigla:"COOL",tipos:["air_cooler","water_cooler"]});
categoriasEditor.push({id:"rede",nome:"Wi-Fi / Rede",sigla:"REDE",tipos:acessoriosRede,rede:true});
export function categoriaCatalogo(id) {
  return categoriasEditor.find(c => c.id === id) || categorias.find(c => c.id === id);
}

let carregamento;
// Trocar somente este carregamento pela API quando /pecas/ estiver pronta.
export function carregarCatalogo() {
  carregamento ??= acompanharCarregamento(Promise.all([
    fetch(new URL("../../data/catalogo-demo.json", import.meta.url),{cache:"force-cache"}),
    carregarManifestoImagens(),
    fetch(new URL("../../data/medidas-fisicas.json", import.meta.url),{cache:"force-cache"}).then(r => r.ok ? r.json() : {pecas:[]}).catch(() => ({pecas:[]})),
  ]).then(async ([resposta, imagens, medidas]) => {
      if (!resposta.ok) throw new Error("Não foi possível carregar o catálogo.");
      const catalogo = await resposta.json();
      try { sessionStorage.setItem("boostio:catalogo-pronto","1"); } catch {}
      return completarCatalogoDemo(completarImagens(catalogo,imagens),medidas);
    }).catch(erro => { carregamento = null; throw erro; }));
  return carregamento;
}

export const moeda = (valor) => new Intl.NumberFormat("pt-BR", {
  style: "currency", currency: "BRL",
}).format(valor);

export function informacoesPreco(peca, conta = false) {
  const informado = typeof peca?.preco === "number" && Number.isFinite(peca.preco) && peca.preco > 0;
  const data = typeof peca?.preco_atualizado_em === "string" && peca.preco_atualizado_em
    ? new Date(peca.preco_atualizado_em) : null;
  const atualizadoEm = data && Number.isFinite(data.getTime()) ? data : null;
  const atualizacao = atualizadoEm
    ? "Última atualização do preço: " + atualizadoEm.toLocaleString("pt-BR") + "."
    : "Data de atualização não informada.";
  return {
    rotulo: conta ? "Preço cadastrado" : "Preço demonstrativo",
    valor: informado ? moeda(peca.preco) : "Preço não informado",
    nota: conta ? "Valor sem frete, não é cotação em tempo real. " + atualizacao
      + (peca?.esgotado ? " Produto marcado como indisponível." : "")
      : "Valor de referência do catálogo demonstrativo, sem atualização em tempo real.",
  };
}

export const htmlSeguro = (valor = "") => String(valor)
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");

export function nomePeca(peca) {
  return peca ? [peca.fabricante, peca.modelo].filter(Boolean).join(" ") : "";
}

export function imagemPeca(peca, classe = "") {
  const categoria = categorias.find((c) => c.id === peca?.categoria);
  const imagem = enderecoImagem(peca?.imagem) || enderecoImagem(peca?.imagem_url);
  const alternativa = '<span class="component-placeholder ' + htmlSeguro(classe) + '" data-product-placeholder' + (imagem ? ' hidden' : '') + ' aria-hidden="true" title="Imagem indisponível">' + (categoria?.sigla || "PC") + '</span>';
  // Foto ausente: placeholder neutro, sem fingir que é a foto do produto.
  return imagem
    ? '<img class="' + htmlSeguro(classe) + '" data-product-image src="' + htmlSeguro(imagem) + '" alt="' + htmlSeguro(nomePeca(peca) || peca?.nome || "Componente") + '" width="160" height="160" loading="lazy" decoding="async">' + alternativa
    : alternativa;
}

export function ofertasPeca(peca) {
  const nome = nomePeca(peca);
  const busca = encodeURIComponent(nome);
  const linkKabum = peca.link?.startsWith("https://www.kabum.com.br/") ? peca.link : null;
  const lojas = [
    { codigo: "kabum", loja: "KaBuM!", url: linkKabum || "https://www.kabum.com.br/busca/" + busca,
      direta: Boolean(linkKabum?.includes("/produto/")) },
    { codigo: "pichau", loja: "Pichau", url: "https://www.pichau.com.br/search?q=" + busca, direta: false },
  ];
  const logos = {kabum:"kabum-logo.svg",pichau:"pichau.png"};
  return lojas.map(loja => {
    const oferta = Array.isArray(peca.ofertas) ? peca.ofertas.find(o => o.loja === loja.codigo) : null;
    let url = loja.url, direta = loja.direta;
    if (oferta?.url) {
      try {
        const endereco = new URL(oferta.url);
        const dominio = loja.codigo + ".com.br";
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
  quantidade_portas_sata:"Portas SATA", quantidade_slots_m2_sata:"Slots M.2 com suporte a SATA",
  portas_sata_desativadas_por_m2_sata:"Portas SATA desativadas por M.2 SATA",
  comprimento_mm:"Comprimento (mm)", altura_mm:"Altura (mm)",
  radiadores_suportados_mm:"Radiadores suportados (mm)", tamanhos_fan_suportados_mm:"Fans suportadas (mm)",
  quantidade_max_fans:"Posições de fans (total)",
  frequencia_mhz: "Frequência (MHz)", latencia: "Latência", quantidade_pentes: "Pentes no kit",
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
  const ignorados = new Set(["id", "categoria", "imagem", "preco", "preco_atualizado_em", "link", "part_number", "esgotado", "ofertas"]);
  return Object.entries(peca).filter(([chave, valor]) => !ignorados.has(chave) && valor != null)
    .map(([chave, valor]) => [
      rotulosTecnicos[chave] || chave.replaceAll("_", " "),
      typeof valor === "boolean" ? (valor ? "Sim" : "Não") : String(valor),
    ]);
}
