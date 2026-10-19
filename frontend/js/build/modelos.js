import { categoriasMultiplas, normalizarBuild } from "./estado.js";

// Curadoria v1: mesmos componentes dos três EXEMPLOS de pages/testes.js.
// Quantidades representam unidades ou kits do catálogo, nunca pentes avulsos.
const MODELOS_V1 = [
  {
    id:"modelo-am4-v1", exemplo:"teste-am4", titulo:"Exemplo AM4",
    descricao:"Build demonstrativa com Ryzen 7 5700X e RTX 3060.",
    objetivo:"jogos", objetivoRotulo:"Jogos e uso diário", plataforma:"AM4",
    pecas:[
      ["SEED-CPU-02",1],["SEED-MB-03",1],["SEED-RAM-02",1],
      ["SEED-SSD-02",1],["SEED-GPU-02",1],["SEED-PSU-01",1],
      ["SEED-CASE-01",1],["SEED-FAN-01",1],["SEED-ACOOL-01",1],
    ],
  },
  {
    id:"modelo-am5-v1", exemplo:"teste-am5", titulo:"Exemplo AM5",
    descricao:"Build demonstrativa com Ryzen 5 7600 e RTX 4060.",
    objetivo:"multitarefa", objetivoRotulo:"Uso geral e multitarefa", plataforma:"AM5",
    pecas:[
      ["SEED-CPU-03",1],["SEED-MB-17",1],["SEED-RAM-03",1],
      ["SEED-SSD-04",1],["SEED-GPU-04",1],["SEED-PSU-02",1],
      ["SEED-CASE-02",1],["SEED-FAN-02",1],
    ],
  },
  {
    id:"modelo-am5-avancado-v1", exemplo:"teste-am5-2", titulo:"Exemplo AM5 avançado",
    descricao:"Build demonstrativa com Ryzen 7 7700X e RTX 5060.",
    objetivo:"criacao", objetivoRotulo:"Criação de conteúdo", plataforma:"AM5",
    pecas:[
      ["SEED-CPU-04",1],["SEED-MB-08",1],["SEED-RAM-05",1],
      ["SEED-SSD-02",1],["SEED-GPU-06",1],["SEED-PSU-03",1],
      ["SEED-CASE-02",1],["SEED-FAN-03",1],["SEED-ACOOL-02",1],
    ],
  },
];

export function modelosProntos(catalogo) {
  return MODELOS_V1.map(modelo => {
    const componentes = {};
    for (const [id,quantidade] of modelo.pecas) {
      const peca = catalogo.find(item => item.id === id);
      if (!peca) throw new Error("A peça " + id + " não foi encontrada no catálogo demonstrativo.");
      const item = {id,quantidade};
      if (categoriasMultiplas.has(peca.categoria)) (componentes[peca.categoria] ??= []).push(item);
      else componentes[peca.categoria] = item;
    }
    return {
      ...normalizarBuild({id:modelo.id,titulo:modelo.titulo,descricao:modelo.descricao,componentes}),
      objetivo:modelo.objetivo,
      metadados:{
        versao:1, origem:"frontend/js/pages/testes.js", exemplo:modelo.exemplo,
        plataforma:modelo.plataforma, objetivoRotulo:modelo.objetivoRotulo,
        precosDemonstrativos:true,
      },
    };
  });
}

export function copiarModelo(build) {
  // A normalização recria todos os componentes e descarta metadados de curadoria.
  return normalizarBuild({
    ...build, id:crypto.randomUUID(), criadoEm:new Date().toISOString(),
    visibilidade:"privado", travada:false,
  });
}
