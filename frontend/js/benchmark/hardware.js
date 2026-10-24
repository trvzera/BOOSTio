// Registro explícito: nunca remove sufixos F/K/X/G nem troca uma GPU por outra.
// O backend só aceita o resultado se o provedor confirmar os dois IDs exatos.
const cpus = new Map([
  ["Ryzen 5 5600","ryzen-5-5600"], ["Ryzen 7 5700X","ryzen-7-5700x"],
  ["Ryzen 5 7600","ryzen-5-7600"], ["Ryzen 7 7700X","ryzen-7-7700x"],
  ["Ryzen 9 7900X","ryzen-9-7900x"], ["Ryzen 7 9800X3D","ryzen-7-9800x3d"],
  ["Ryzen 7 7800X3D","ryzen-7-7800x3d"], ["Ryzen 7 5800X3D","ryzen-7-5800x3d"],
  ["Ryzen 5 5500","ryzen-5-5500"], ["Ryzen 3 4100","ryzen-3-4100"],
  ["Core i3-12100F","core-i3-12100f"], ["Core i5-12400F","core-i5-12400f"],
  ["Core i5-13400F","core-i5-13400f"], ["Core i7-13700K","core-i7-13700k"],
  ["Core i9-14900K","core-i9-14900k"], ["Core i5-12400","core-i5-12400"],
].map(([modelo,slug]) => [modelo.toLowerCase(),slug]));
const gpus = new Map([
  ["GeForce RTX 3060",12,"rtx-3060"], ["Alpha RTX 3060",12,"rtx-3060"],
  ["GeForce RTX5050 8GB GDDR6",8,"rtx-5050"], ["GeForce RTX 5050",8,"rtx-5050"],
  ["GeForce RTX 3060 Ti",8,"rtx-3060-ti"], ["GeForce RTX 4060",8,"rtx-4060"],
  ["GeForce GTX 1660 Super",6,"gtx-1660-super"], ["GeForce GTX 1660",6,"gtx-1660"],
  ["GeForce GTX 1050 Ti",4,"gtx-1050-ti"], ["Radeon RX 6750 XT",12,"rx-6750-xt"],
  ["RX 7600 Challenger Radeon",8,"rx-7600"],
  ["RTX 5060 Shadow 2X OC GeForce",8,"rtx-5060"],
  ["Swift RX 9070 XT TRIPLE FAN",16,"rx-9070-xt"],
].map(([modelo,gb,slug]) => [modelo.toLowerCase() + ":" + gb,slug]));

export function hardwareBenchmark(cpu,gpu) {
  if (!cpu || !gpu) return {motivo:"A consulta precisa de modelos identificados de CPU e GPU dedicada. Vídeo integrado e peças próprias sem identificação ainda não têm correspondência cadastrada."};
  const processador = cpus.get(String(cpu.modelo || "").trim().toLowerCase());
  const video = gpus.get(String(gpu.modelo || "").trim().toLowerCase() + ":" + Number(gpu.memoria_gb));
  if (!processador || !video) return {motivo:"Uma das peças ainda não tem correspondência exata cadastrada para o benchmark. Não usaremos outro modelo para estimar seu desempenho."};
  return {cpu:processador,gpu:video};
}

export function hardwareBlender(cpu,gpu) {
  // Open Data identifica o chip, não o nome comercial da placa (EAGLE, DUAL,
  // SHADOW etc.). Isso é independente do registro de slugs da API de jogos.
  // Só extrai identificadores explícitos: a API Python ainda exige nome exato
  // na resposta. Nunca remove Ti/SUPER/XT/F nem tenta uma peça parecida no 422.
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
  // Não tratar versões mobile, RX 580 2048SP ou títulos com vários chips como
  // a GPU desktop padrão. Uma variante sem identificação continua indisponível.
  if (/\b(?:laptop|notebook|mobile|max-q|2048\s*sp)\b/i.test(modeloGpu)) return {cpu:nomeCpu,gpu:null};
  const padraoNvidia = /\b(RTX|GTX|GT)\s*(\d{3,4})(?:\s*(TI(?:\s*SUPER)?|SUPER))?\b/gi;
  const padraoAmd = /\bRX\s*(\d{3,4})(?:\s*(XTX|XT|GRE))?\b/gi;
  const nvidias = identificadores(modeloGpu,padraoNvidia), amds = identificadores(modeloGpu,padraoAmd);
  let nomeGpu = null;
  if (nvidias.length + amds.length === 1) {
    const nvidia = nvidias[0], m = nvidia || amds[0];
    // Mantém a restrição já existente: não usar a referência 3060 de 12 GB
    // para a variante de 8 GB (ou capacidade ausente), nem substituir por Ti.
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
