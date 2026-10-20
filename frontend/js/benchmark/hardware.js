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
].map(([modelo,gb,slug]) => [modelo.toLowerCase() + ":" + gb,slug]));

export function hardwareBenchmark(cpu,gpu) {
  if (!cpu || !gpu) return {motivo:"A consulta precisa de modelos identificados de CPU e GPU dedicada. Vídeo integrado e peças próprias sem identificação ainda não têm correspondência cadastrada."};
  const processador = cpus.get(String(cpu.modelo || "").trim().toLowerCase());
  const video = gpus.get(String(gpu.modelo || "").trim().toLowerCase() + ":" + Number(gpu.memoria_gb));
  if (!processador || !video) return {motivo:"Uma das peças ainda não tem correspondência exata cadastrada para o benchmark. Não usaremos outro modelo para estimar seu desempenho."};
  return {cpu:processador,gpu:video};
}
