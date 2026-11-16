// Slugs da FPSHQ conferidos pela busca da própria API (/gpus?q=) com o nome exato da placa.
// Nem todos seguem um padrão (rx-6500-xt, mas radeon-rx-6600; rtx-3060, mas geforce-rtx-2060), então não são deduzidos.
// Chave: nome do chip sem marca, em maiúsculas; placas com variantes de memória levam a memória (ex.: "GTX 1060 6GB").
const gpus = new Map([
  ["GTX 750 TI","geforce-gtx-750-ti"],
  ["GTX 760","geforce-gtx-760"],
  ["GTX 770","geforce-gtx-770"],
  ["GTX 780","geforce-gtx-780"],
  ["GTX 780 TI","geforce-gtx-780-ti"],
  ["GTX 950","geforce-gtx-950"],
  ["GTX 960","geforce-gtx-960"],
  ["GTX 970","geforce-gtx-970"],
  ["GTX 980","geforce-gtx-980"],
  ["GTX 980 TI","geforce-gtx-980-ti"],
  ["GTX 1050","geforce-gtx-1050"],
  ["GTX 1050 TI","gtx-1050-ti"],
  ["GTX 1060 3GB","geforce-gtx-1060-3gb"],
  ["GTX 1060 6GB","gtx-1060-6gb"],
  ["GTX 1070","gtx-1070"],
  ["GTX 1070 TI","geforce-gtx-1070-ti"],
  ["GTX 1080","gtx-1080"],
  ["GTX 1080 TI","geforce-gtx-1080-ti"],
  ["GTX 1650","gtx-1650"],
  ["GTX 1650 SUPER","gtx-1650-super"],
  ["GTX 1660","gtx-1660"],
  ["GTX 1660 SUPER","gtx-1660-super"],
  ["GTX 1660 TI","gtx-1660-ti"],
  ["RTX 2060","geforce-rtx-2060"],
  ["RTX 2060 SUPER","geforce-rtx-2060-super"],
  ["RTX 2070","geforce-rtx-2070"],
  ["RTX 2070 SUPER","rtx-2070-super"],
  ["RTX 2080","geforce-rtx-2080"],
  ["RTX 2080 SUPER","geforce-rtx-2080-super"],
  ["RTX 2080 TI","rtx-2080-ti"],
  ["RTX 3050","rtx-3050"],
  ["RTX 3060 12GB","rtx-3060"],
  ["RTX 3060 TI","rtx-3060-ti"],
  ["RTX 3070","rtx-3070"],
  ["RTX 3070 TI","rtx-3070-ti"],
  ["RTX 3080","rtx-3080"],
  ["RTX 3080 TI","geforce-rtx-3080-ti"],
  ["RTX 3090","rtx-3090"],
  ["RTX 3090 TI","rtx-3090-ti"],
  ["RTX 4060","rtx-4060"],
  ["RTX 4060 TI","rtx-4060-ti"],
  ["RTX 4070","rtx-4070"],
  ["RTX 4070 SUPER","rtx-4070-super"],
  ["RTX 4070 TI","rtx-4070-ti"],
  ["RTX 4070 TI SUPER","rtx-4070-ti-super"],
  ["RTX 4080","rtx-4080"],
  ["RTX 4080 SUPER","rtx-4080-super"],
  ["RTX 4090","rtx-4090"],
  ["RTX 5050","rtx-5050"],
  ["RTX 5060","rtx-5060"],
  ["RTX 5060 TI","rtx-5060-ti"],
  ["RTX 5070","rtx-5070"],
  ["RTX 5070 TI","rtx-5070-ti"],
  ["RTX 5080","rtx-5080"],
  ["RTX 5090","rtx-5090"],
  ["RX 460","radeon-rx-460"],
  ["RX 470","radeon-rx-470"],
  ["RX 480","radeon-rx-480"],
  ["RX 550","radeon-rx-550"],
  ["RX 560","radeon-rx-560"],
  ["RX 570","radeon-rx-570"],
  ["RX 580","radeon-rx-580"],
  ["RX 590","radeon-rx-590"],
  ["RX 5500 XT","radeon-rx-5500-xt"],
  ["RX 5600 XT","rx-5600-xt"],
  ["RX 5700","rx-5700"],
  ["RX 5700 XT","rx-5700-xt"],
  ["RX 6400","radeon-rx-6400"],
  ["RX 6500 XT","rx-6500-xt"],
  ["RX 6600","radeon-rx-6600"],
  ["RX 6600 XT","rx-6600-xt"],
  ["RX 6650 XT","rx-6650-xt"],
  ["RX 6700","rx-6700"],
  ["RX 6700 XT","radeon-rx-6700-xt"],
  ["RX 6750 XT","rx-6750-xt"],
  ["RX 6800","rx-6800"],
  ["RX 6800 XT","radeon-rx-6800-xt"],
  ["RX 6900 XT","rx-6900-xt"],
  ["RX 6950 XT","rx-6950-xt"],
  ["RX 7600","radeon-rx-7600"],
  ["RX 7600 XT","rx-7600-xt"],
  ["RX 7700 XT","radeon-rx-7700-xt"],
  ["RX 7800 XT","radeon-rx-7800-xt"],
  ["RX 7900 GRE","rx-7900-gre"],
  ["RX 7900 XT","radeon-rx-7900-xt"],
  ["RX 7900 XTX","radeon-rx-7900-xtx"],
  ["RX 9060 XT","rx-9060-xt"],
  ["RX 9070","radeon-rx-9070"],
  ["RX 9070 GRE","rx-9070-gre"],
  ["RX 9070 XT","radeon-rx-9070-xt"],
]);

const MARCAS_GPU = /\b(?:nvidia|geforce|amd|radeon)\b/gi;
const SEM_CORRESPONDENCIA = {motivo:"Uma das peças ainda não tem correspondência exata cadastrada para o benchmark. Não usaremos outro modelo para estimar seu desempenho."};

// "Radeon RX 9060 XT 16 GB" -> "RX 9060 XT"; só aceita nomes inteiros de chips de vídeo, sem variantes comerciais soltas.
function chipDeVideo(texto) {
  const limpo = String(texto || "").replace(/[®™]/g,"").replace(MARCAS_GPU,"").replace(/\b\d{1,2}\s*gb\b/gi,"")
    .replace(/\s+-\s*\d+\b/g,"").replace(/\s+/g," ").trim().toUpperCase();
  const m = /^(RTX|GTX)\s*(\d{3,4})(?:\s+(TI SUPER|TI|SUPER))?$/.exec(limpo) || /^(RX)\s*(\d{3,4})(?:\s+(XTX|XT|GRE))?$/.exec(limpo);
  return m ? [m[1],m[2],m[3]].filter(Boolean).join(" ") : null;
}

// Sem modelo_referencia, o chip só existe dentro do título ("RX 7600 Challenger Radeon"): aceita um único chip,
// sem variantes ambíguas (Ti/Super/XT já entram no nome) e recusa notebook/mobile.
function chipNoTitulo(texto) {
  const t = String(texto || "").replace(/[®™]/g,"").replace(/\s+/g," ").toUpperCase();
  if (/\b(?:LAPTOP|NOTEBOOK|MOBILE|MAX-Q|2048\s*SP)\b/.test(t)) return null;
  const chips = new Set([...t.matchAll(/\b(RTX|GTX|RX)\s*(\d{3,4})(?:\s*(TI\s*SUPER|TI|SUPER|XTX|XT|GRE))?\b/g)]
    .map(m => [m[1],m[2],(m[3] || "").replace(/\s+/g," ")].filter(Boolean).join(" ")));
  return chips.size === 1 ? [...chips][0] : null;
}

// O banco guarda o nome do chip sem marca em modelo_referencia; "modelo" costuma ser só a variante comercial ("PULSE [Black]").
// Se modelo_referencia existe mas não é um chip reconhecido (ex.: notebook), não se recorre ao título.
export function slugVideo(gpu) {
  const referencia = String(gpu?.modelo_referencia || "").trim();
  const chip = referencia ? chipDeVideo(referencia) : chipNoTitulo(gpu?.modelo);
  if (!chip) return null;
  const memoria = Number(gpu.memoria_gb);
  return gpus.get(chip) || (Number.isInteger(memoria) ? gpus.get(chip + " " + memoria + "GB") : null) || null;
}

// "modelo" do processador já vem sem marca (Ryzen 5 5600G, Core i5-12400F); a FPSHQ usa o próprio nome como slug.
export function slugProcessador(cpu) {
  const nome = String(cpu?.modelo || "").replace(/\((?:R|TM)\)|[®™]/gi,"").replace(/\b(?:amd|intel)\b/gi,"")
    .replace(/[‐‑–—]/g,"-").replace(/\s+/g," ").trim();
  let m = /^Ryzen\s+([3579])\s+(\d{4,5}[A-Z0-9]*)$/i.exec(nome);
  if (m) return "ryzen-" + m[1] + "-" + m[2].toLowerCase();
  m = /^Core\s+i([3579])[-\s]+(\d{3,5}[A-Z]{0,2})$/i.exec(nome);
  if (m) return "core-i" + m[1] + "-" + m[2].toLowerCase();
  m = /^Core\s+Ultra\s+([3579])\s+(\d{3}[A-Z]{0,2})$/i.exec(nome);
  return m ? "core-ultra-" + m[1] + "-" + m[2].toLowerCase() : null;
}

export function hardwareBenchmark(cpu,gpu) {
  if (!cpu || !gpu) return {motivo:"A consulta precisa de modelos identificados de CPU e GPU dedicada. Vídeo integrado e peças próprias sem identificação ainda não têm correspondência cadastrada."};
  const processador = slugProcessador(cpu), video = slugVideo(gpu);
  return processador && video ? {cpu:processador,gpu:video} : SEM_CORRESPONDENCIA;
}

export function hardwareBlender(cpu,gpu) {


  const nome = p => String(p?.modelo || "").replace(/\((?:R|TM)\)|[®™]/gi,"")
    .replace(/[‐‑–—]/g,"-").replace(/\s+/g," ").trim();
  const identificadores = (texto,expressao) => [...new Map([...texto.matchAll(expressao)]
    .map(m => [m.slice(1).map(v => (v || "").replace(/\s+/g,"").toUpperCase()).join(":"),m])).values()];
  const unico = (texto,expressao) => {
    const encontrados = identificadores(texto,expressao);
    return encontrados.length === 1 ? encontrados[0] : null;
  };
  const modeloCpu = nome(cpu), marca = String(cpu?.fabricante || "").trim().toUpperCase();
  let nomeCpu = null;
  if (marca === "AMD" && Number.isInteger(cpu.nucleo) && cpu.nucleo > 0) {
    const m = unico(modeloCpu,/\bRyzen\s+([3579])\s+(\d{4}[A-Z0-9]*)\b/gi);
    if (m) nomeCpu = "AMD Ryzen " + m[1] + " " + m[2].toUpperCase() + " " + cpu.nucleo + "-Core Processor";
  } else if (marca === "INTEL") {
    const cores = identificadores(modeloCpu,/\bCore\s+i([3579])[-\s]+(\d{3,5}[A-Z]*)\b/gi);
    const ultras = identificadores(modeloCpu,/\bCore\s+Ultra\s+([3579])\s+(\d{3}[A-Z]*)\b/gi);
    if (cores.length + ultras.length === 1) {
      const core = cores[0], m = core || ultras[0];
      nomeCpu = "Intel Core " + (core ? "i" + m[1] + "-" : "Ultra " + m[1] + " ") + m[2].toUpperCase();
    }
  }
  const modeloGpu = nome(gpu);


  if (/\b(?:laptop|notebook|mobile|max-q|2048\s*sp)\b/i.test(modeloGpu)) return {cpu:nomeCpu,gpu:null};
  const padraoNvidia = /\b(RTX|GTX|GT)\s*(\d{3,4})(?:\s*(TI(?:\s*SUPER)?|SUPER))?\b/gi;
  const padraoAmd = /\bRX\s*(\d{3,4})(?:\s*(XTX|XT|GRE))?\b/gi;
  const nvidias = identificadores(modeloGpu,padraoNvidia), amds = identificadores(modeloGpu,padraoAmd);
  let nomeGpu = null;
  if (nvidias.length + amds.length === 1) {
    const nvidia = nvidias[0], m = nvidia || amds[0];


    if (nvidia && m[1].toUpperCase() === "RTX" && m[2] === "3060" && !m[3] && Number(gpu.memoria_gb) !== 12)
      return {cpu:nomeCpu,gpu:null};
    const restante = modeloGpu.replace(nvidia ? padraoNvidia : padraoAmd,"");
    if (!/\b(?:Ti|SUPER|XTX|XT|GRE|M)\b/i.test(restante)) {
      nomeGpu = nvidia ? "NVIDIA GeForce " + m[1].toUpperCase() + " " + m[2]
        + (m[3] ? " " + m[3].toUpperCase().replace(/\s+/g,"").replace("TI","Ti").replace("TiSUPER","Ti SUPER") : "")
        : "AMD Radeon RX " + m[1] + (m[2] ? " " + m[2].toUpperCase() : "");
    }
  }
  return {cpu:nomeCpu,gpu:nomeGpu};
}
