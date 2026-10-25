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
    return {...loja,url,direta,preco,atualizadoEm:oferta?.atualizadoEm || null,esgotado:oferta?.esgotado === true,
      logo:new URL("../../svgs/" + logos[loja.codigo],import.meta.url).href};
  });
}

export const rotulosTecnicos = {
  fabricante: "Fabricante", modelo: "Modelo", part_number: "Referência do catálogo / part number", consumo_energia: "Consumo estimado (W)",
  soquete: "Socket", socket: "Socket", sockets_suporte_condicional: "Sockets que exigem confirmar a versão/kit de montagem", nucleo: "Núcleos", thread: "Threads",
  conectores_alimentacao:"Conectores de alimentação", cabos_pcie_independentes:"Cabos separados para a placa de vídeo",
  conectores_alimentacao_completos:"Dados dos conectores completos", topologia_armazenamento_verificada:"Conexões de armazenamento revisadas",
  configuracoes_baias_completas:"Arranjos de baias revisados",
  cabos_pcie_independentes_minimos:"Cabos separados exigidos pela placa de vídeo", slots_m2:"Detalhes dos slots M.2",
  portas_sata:"Identificação das portas SATA", formato_m2:"Tamanho do SSD M.2", configuracoes_baias:"Opções de instalação dos discos",
  atx_24:"Principal de 24 pinos", eps_8:"CPU de 8 pinos", atx12v_4:"CPU de 4 pinos", eps_4_4:"CPU 4+4 pinos",
  pcie_6:"Placa de vídeo de 6 pinos", pcie_8:"Placa de vídeo de 8 pinos", pcie_6_2:"Placa de vídeo 6+2 pinos",
  '12vhpwr':'12VHPWR', '12v_2x6':'12V-2x6', sata:'SATA', molex_4:'Molex de 4 pinos',
  m2:'NVMe (PCIe)', 'm2-sata':'M.2 SATA',
  clockbase: "Clock base (GHz)", clockmax: "Clock máximo (GHz)", videointegrado: "Vídeo integrado",
  modelo_videointegrado: "GPU integrada", cooler: "Cooler incluso", modelo_cooler: "Cooler incluso",
  chipset: "Chipset", formato: "Formato", tipo_memoria: "Tipo de memória",
  quantidade_slots_ram: "Slots de RAM", memoria_maxima_gb: "RAM máxima (GB)",
  quantidade_slots_m2: "Slots M.2", capacidade_gb: "Capacidade (GB)", ddr: "Geração",
  quantidade_portas_sata:"Portas SATA", quantidade_slots_m2_sata:"Slots M.2 com suporte a SATA",
  portas_sata_desativadas_por_m2_sata:"Portas SATA desativadas por M.2 SATA",
  comprimento_mm:"Comprimento (mm)", largura_mm:"Largura (mm)", altura_mm:"Altura (mm)", espessura_mm:"Espessura (mm)",
  comprimento_radiador_mm:"Comprimento real do radiador (mm)", largura_radiador_mm:"Largura do radiador (mm)",
  espessura_radiador_mm:"Espessura do radiador (mm)", espessura_fan_mm:"Espessura da fan (mm)", tamanho_fan_mm:"Tamanho da fan (mm)",
  tamanho_max_fonte_mm:"Comprimento máximo da fonte (mm)", formatos_fonte:"Formatos de fonte aceitos",
  tamanho_max_altura_gpu_mm:"Altura máxima da GPU (mm)", tamanho_max_espessura_gpu_mm:"Espessura máxima da GPU (mm)",
  slots_ocupados:"Slots ocupados", baias_25:"Baias de 2,5 polegadas", baias_35:"Baias de 3,5 polegadas",
  posicoes_fans:"Posições de fans e radiadores", limites_radiador_mm:"Limites do radiador por posição",
  posicoes_fans_completas:"Lista de arranjos de fans exaustiva", observacoes_medidas:"Condições e folgas a confirmar",
  fonte_medidas:"Fonte das especificações", modelo_ficha_tecnica:"Variante da ficha oficial",
  ficha_tecnica_verificada_em:"Ficha consultada em", fluxo_ar:"Fluxo de ar", fonte_fluxo_ar:"Origem da informação de fluxo",
  numero_pinos:"Pinos", perfis_memoria:"Perfis JEDEC/XMP", durabilidade_tbw:"Endurance anunciada (TBW)",
  conector_fan:"Conector da fan", tensao_fan_v:"Tensão da fan (V)", corrente_fan_a:"Corrente da fan (A)",
  conector_rgb:"Conector da iluminação", tensao_rgb_v:"Tensão da iluminação (V)",
  fluxo_ar_cfm:"Fluxo de ar anunciado (CFM)", pressao_estatica_mmh2o:"Pressão estática anunciada (mmH₂O)",
  rotacao_min_rpm:"Rotação mínima (RPM)", rotacao_max_rpm:"Rotação máxima (RPM)",
  ruido_dba:"Ruído anunciado (dBA)", ruido_sone:"Ruído anunciado (sone)", rolamento:"Rolamento",
  comprimento_cabo_m:"Comprimento do cabo (m)", alcance_sem_fio_m:"Alcance anunciado (m)",
  alimentacao:"Alimentação", microfone_reducao_ruido:"Redução de ruído no microfone",
  driver_mm:"Diâmetro do driver (mm)", impedancia_ohm:"Impedância (Ω)",
  tamanhos_fans_cooler_mm:"Diâmetros das fans do cooler (mm)", comprimento_tubo_mm:"Comprimento dos tubos (mm)",
  placas_mae_incompativeis:"Placas-mãe com incompatibilidade declarada pelo fabricante",
  wifi_integrado:"Wi-Fi integrado", versao_bluetooth:"Versão do Bluetooth", tdp_w:"TDP anunciado (W)",
  tipos_memoria_cpu:"Tipos de RAM suportados pela CPU", memoria_maxima_cpu_gb:"RAM máxima anunciada pela CPU (GB)",
  versao_atx:"Versão ATX", certificacao_fonte:"Certificação da fonte", dimensoes_fabricante:"Dimensões informadas pelo fabricante",
  conectores_cpu_eps:"Conectores CPU/EPS (4+4 pinos)", conectores_pcie_8pinos:"Conectores PCIe (6+2 pinos)",
  conectores_pcie_16pinos:"Conectores PCIe de 16 pinos", conectores_sata:"Conectores de alimentação SATA",
  radiadores_suportados_mm:"Radiadores suportados (mm)", tamanhos_fan_suportados_mm:"Fans suportadas (mm)",
  quantidade_max_fans:"Posições de fans (total)",
  estimativa_fans:"Planejamento de fans (estimativa visual)",
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
  padrao_wifi: "Padrão Wi-Fi", velocidade_mbps: "Velocidade de rede (Mbps)", bluetooth: "Bluetooth",
  comprimento_m: "Comprimento do cabo (m)", conector: "Conector",
};

function entradasFichaTecnica(peca) {
  const ignorados = new Set(["id", "categoria", "imagem", "preco", "preco_atualizado_em", "link", "part_number", "esgotado", "ofertas", "topologia_armazenamento_verificada", "conectores_alimentacao_completos", "configuracoes_baias_completas"]);
  // Medidas genéricas antigas não devem contradizer a ficha exata revisada.
  if (peca.modelo_ficha_tecnica && peca.baias_25 != null && peca.baias_35 != null) ignorados.add("bays_disco");
  if (peca.modelo_ficha_tecnica && [peca.comprimento_mm,peca.largura_mm,peca.altura_mm].every(v=>v!=null)) ignorados.add("dimensoes");
  return Object.entries(peca).filter(([chave, valor]) => !ignorados.has(chave) && valor != null && valor !== "");
}

function linhaTecnica([chave, valor]) {
  return [
      rotulosTecnicos[chave] || chave.replaceAll("_", " "),
      formatarEspecificacao(chave,valor),
  ];
}

export function fichaTecnica(peca) {
  return entradasFichaTecnica(peca).map(linhaTecnica);
}

const camposDestaque = {
  processador: ["soquete", "nucleo", "thread", "videointegrado", "cooler", "consumo_energia"],
  placa_mae: ["socket", "tipo_memoria", "quantidade_slots_ram", "memoria_maxima_gb", "quantidade_slots_m2", "quantidade_portas_sata"],
  memoria_ram: ["capacidade_gb", "ddr", "frequencia_mhz", "quantidade_pentes", "latencia", "altura_mm"],
  placa_video: ["memoria_gb", "tipo_memoria", "comprimento_mm", "slots_ocupados", "conectores_energia", "consumo_energia"],
  gabinete: ["formatos_placa_mae", "tamanho_max_gpu_mm", "tamanho_max_cooler_mm", "fans_inclusos", "quantidade_max_fans", "radiadores_suportados_mm"],
  fonte: ["potencia_w", "formato", "comprimento_mm", "certificacao_fonte", "conectores_pcie_8pinos", "conectores_sata"],
  ssd: ["capacidade_gb", "tipo", "interface", "formato", "velocidade_leitura_mbps", "velocidade_gravacao_mbps"],
  hd: ["capacidade_gb", "interface", "formato", "velocidade_rpm", "memoria_cache_mb", "consumo_energia"],
  air_cooler: ["compatibilidade", "altura_mm", "tamanhos_fans_cooler_mm", "quantidade_fans", "iluminacao", "consumo_energia"],
  water_cooler: ["compatibilidade", "tamanho_radiador_mm", "comprimento_radiador_mm", "espessura_radiador_mm", "quantidade_fans", "consumo_energia"],
  fan: ["tamanho_mm", "quantidade", "espessura_mm", "fluxo_ar", "conector_fan", "consumo_energia"],
  adaptador_wifi: ["interface", "padrao_wifi", "velocidade_mbps", "bluetooth"],
  cabo_rede: ["comprimento_m", "conector"],
};

export function destaquesFichaTecnica(peca) {
  const campos = camposDestaque[peca.categoria];
  if (!campos) return entradasFichaTecnica(peca)
    .filter(([chave]) => !["fabricante", "modelo", "fonte_medidas", "observacoes_medidas"].includes(chave))
    .slice(0, 6).map(linhaTecnica);
  return campos.map(chave => [rotulosTecnicos[chave],
    peca[chave] == null || peca[chave] === "" ? "Não informado" : formatarEspecificacao(chave, peca[chave])]);
}

export function gruposFichaTecnica(peca) {
  const grupos = [
    {titulo: "Identificação", campos: []},
    {titulo: "Desempenho e consumo", campos: []},
    {titulo: "Compatibilidade e instalação", campos: []},
    {titulo: "Recursos e características", campos: []},
    {titulo: "Origem das informações", campos: []},
  ];
  const desempenho = /^(consumo_|tdp_|clock|nucleo$|thread$|capacidade_gb$|memoria_gb$|frequencia_mhz$|latencia$|potencia|velocidade_|rotacao_|ruido_|memoria_cache_|fluxo_ar_cfm$|pressao_estatica_|durabilidade_|taxa_atualizacao_|tempo_resposta_|resolucao$|dpi_max$)/;
  const encaixe = /^(soquete$|socket$|sockets_suporte_condicional$|chipset$|formato|tipo_memoria$|ddr$|interface|quantidade_slots_|quantidade_portas_|portas_sata$|portas_sata_|configuracoes_baias$|cabos_pcie_|memoria_maxima_|tipos_memoria_cpu$|quantidade_pentes$|quantidade_max_fans$|comprimento_|largura_|altura_|espessura_|dimensoes|tamanho_|tamanhos_|slots_|baias_|bays_|posicoes_|limites_radiador_|radiadores_|compatibilidade$|placas_mae_incompativeis$|conector|numero_pinos$|versao_atx$|suporte_water_cooler$|fans_inclusos$|quantidade_fans$|cooler$|modelo_cooler$|videointegrado$|modelo_videointegrado$|observacoes_medidas$)/;
  const entradas = entradasFichaTecnica(peca);
  if (peca.part_number) entradas.push(["part_number", peca.part_number]);
  for (const entrada of entradas) {
    const chave = entrada[0];
    const grupo = ["fabricante", "modelo", "part_number"].includes(chave) ? 0
      : ["fonte_medidas", "fonte_fluxo_ar", "modelo_ficha_tecnica", "ficha_tecnica_verificada_em"].includes(chave) ? 4
      : desempenho.test(chave) ? 1 : encaixe.test(chave) ? 2 : 3;
    grupos[grupo].campos.push(linhaTecnica(entrada));
  }
  return grupos.filter(grupo => grupo.campos.length);
}

function formatarEspecificacao(chave,valor) {
  if(chave==='estimativa_fans'&&valor&&typeof valor==='object')return 'Referência inicial de planejamento: '+String(valor.quantidade_inicial)+' fans. '+String(valor.observacao||'Confirme os encaixes antes de comprar.')+' Estimativa visual; não confirma tamanho, capacidade ou encaixe.';
  if(chave==='conectores_alimentacao'&&valor&&typeof valor==='object')return Object.entries(valor).filter(([,q])=>Number(q)>0)
    .map(([tipo,q])=>q+' × '+(rotulosTecnicos[tipo]||tipo)).join('; ')||'Nenhum conector externo cadastrado';
  if(chave==='configuracoes_baias'&&Array.isArray(valor))return valor.filter(a=>a&&typeof a==='object').map(a=>[
    a.baias_25>0?a.baias_25+' '+(a.baias_25===1?'SSD':'SSDs')+' de 2,5 polegadas':'',
    a.baias_35>0?a.baias_35+' '+(a.baias_35===1?'HD':'HDs')+' de 3,5 polegadas':''
  ].filter(Boolean).join(' + ')||'Sem baia neste arranjo').join(' OU ')||'Dados incompletos';
  if(chave==='slots_m2'&&Array.isArray(valor))return valor.filter(s=>s&&typeof s==='object').map(s=>s.nome+': '+(Array.isArray(s.interfaces)?s.interfaces:[]).map(v=>rotulosTecnicos[v]||v).join(' / ')
    +'; tamanhos: '+(Array.isArray(s.formatos)?s.formatos:[]).join(' / ')+(s.condicional_cpu?' (depende do processador)':'')
    +Object.entries(s.portas_sata_desativadas||{}).filter(([,p])=>Array.isArray(p)&&p.length).map(([tipo,p])=>'; usando '+(rotulosTecnicos[tipo]||tipo)+' desativa '+p.join(', ')).join('')).join(' · ')||'Dados incompletos';
  if (chave === "ficha_tecnica_verificada_em" && /^\d{4}-\d{2}-\d{2}$/.test(valor)) return valor.split("-").reverse().join("/");
  if (chave === "posicoes_fans" && Array.isArray(valor)) {
    const fans = lista => (lista || []).map(f => f.quantidade + " × " + f.tamanho_mm + " mm").join(" ou ");
    return valor.map(p => p.nome + ": " + fans(p.opcoes)
      + (p.fans_inclusas?.length ? "; de fábrica: " + fans(p.fans_inclusas) : "")
      + (p.radiadores_mm?.length ? "; radiadores: " + p.radiadores_mm.join(" / ") + " mm" : "; sem radiador indicado"))
      .join(" · ");
  }
  if (typeof valor === "boolean") return valor ? "Sim" : "Não";
  if (Array.isArray(valor)) return valor.map(v => formatarEspecificacao("",v)).join(", ");
  if (valor && typeof valor === "object") return Object.entries(valor)
    .map(([k,v]) => (rotulosTecnicos[k] || k.replaceAll("_"," ")) + ": " + formatarEspecificacao(k,v)).join("; ");
  return String(valor);
}
