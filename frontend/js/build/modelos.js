import { categoriasMultiplas, normalizarBuild } from "./estado.js";

// Referências estáveis do catálogo existente. O total sempre vem dos preços carregados.
// Não são metas de FPS nem ofertas garantidas; todos os modelos são sem periféricos.
const MODELOS = [
  {
    id:"modelo-estudos",titulo:"Estudos e dia a dia",objetivo:"estudos",objetivoRotulo:"Estudos",plataforma:"AM5",nivel:"Entrada",
    descricao:"Navegação, aulas e documentos. Vídeo integrado, 16 GB de RAM e SSD de 500 GB.",
    pecas:[["SEED-CPU-03",1],["SEED-MB-08",1],["SEED-RAM-03",1],["SEED-SSD-01",1],["SEED-PSU-01",1],["SEED-CASE-02",1],["SEED-FAN-01",2]],
  },
  {
    id:"modelo-home-office",titulo:"Home office e multitarefa",objetivo:"trabalho",objetivoRotulo:"Trabalho e produtividade",plataforma:"AM5",nivel:"Intermediária",
    descricao:"32 GB de RAM e SSD de 1 TB para trabalhar com vários aplicativos. Usa o vídeo integrado.",
    pecas:[["SEED-CPU-03",1],["SEED-MB-08",1],["SEED-RAM-03",2],["SEED-SSD-02",1],["SEED-PSU-01",1],["SEED-CASE-02",1],["SEED-FAN-01",2]],
  },
  {
    id:"modelo-programacao",titulo:"Programação e desenvolvimento",objetivo:"programacao",objetivoRotulo:"Programação",plataforma:"AM5",nivel:"Intermediária",
    descricao:"Ryzen 7 e 32 GB de RAM para IDEs, containers e projetos locais. Sem GPU dedicada.",
    pecas:[["SEED-CPU-04",1],["SEED-MB-08",1],["SEED-RAM-05",1],["SEED-SSD-04",1],["SEED-PSU-01",1],["SEED-CASE-02",1],["SEED-FAN-02",2],["SEED-ACOOL-02",1]],
  },
  {
    id:"modelo-jogos-entrada",titulo:"Primeiro PC para jogos",objetivo:"jogos",objetivoRotulo:"Jogos",plataforma:"AM4",nivel:"Entrada",
    descricao:"Plataforma AM4, 16 GB em dois pentes e GTX 1660 Super. Uma base para jogos em Full HD.",
    pecas:[["SEED-CPU-02",1],["SEED-MB-03",1],["SEED-RAM-02",1],["SEED-SSD-01",1],["SEED-GPU-01",1],["SEED-PSU-01",1],["SEED-CASE-01",1],["SEED-FAN-01",2],["SEED-ACOOL-01",1]],
  },
  {
    id:"modelo-jogos-fullhd",titulo:"Jogos Full HD",objetivo:"jogos",objetivoRotulo:"Jogos",plataforma:"AM4",nivel:"Intermediária",
    descricao:"RTX 4060, 16 GB de RAM e SSD de 1 TB. Ajuste a qualidade conforme o jogo e a resolução.",
    pecas:[["SEED-CPU-02",1],["SEED-MB-03",1],["SEED-RAM-02",1],["SEED-SSD-02",1],["SEED-GPU-04",1],["SEED-PSU-01",1],["SEED-CASE-01",1],["SEED-FAN-01",2],["SEED-ACOOL-02",1]],
  },
  {
    id:"modelo-jogos-am5",titulo:"Jogos com plataforma AM5",objetivo:"jogos",objetivoRotulo:"Jogos",plataforma:"AM5",nivel:"Intermediária",
    descricao:"Ryzen 5 7600, RTX 5060 e 32 GB DDR5. Plataforma para personalizar e expandir depois.",
    pecas:[["SEED-CPU-03",1],["SEED-MB-08",1],["SEED-RAM-05",1],["SEED-SSD-04",1],["SEED-GPU-06",1],["SEED-PSU-03",1],["SEED-CASE-02",1],["SEED-FAN-02",2]],
  },
  {
    id:"modelo-jogos-avancado",titulo:"Jogos com CPU X3D",objetivo:"jogos",objetivoRotulo:"Jogos",plataforma:"AM5",nivel:"Avançada",
    descricao:"Ryzen 7 X3D, RX 9070 XT e 32 GB DDR5. Prioriza CPU e GPU; o desempenho depende do jogo.",
    pecas:[["SEED-CPU-01",1],["SEED-MB-08",1],["SEED-RAM-05",1],["SEED-SSD-04",1],["SEED-GPU-07",1],["SEED-PSU-03",1],["SEED-CASE-02",1],["SEED-FAN-02",2],["SEED-ACOOL-02",1]],
  },
  {
    id:"modelo-criacao",titulo:"Criação e armazenamento",objetivo:"criacao",objetivoRotulo:"Criação de conteúdo",plataforma:"AM5",nivel:"Intermediária",
    descricao:"Ryzen 7, RTX 3060 e 32 GB de RAM, com SSD de 1 TB e HD de 2 TB para arquivos.",
    pecas:[["SEED-CPU-04",1],["SEED-MB-08",1],["SEED-RAM-05",1],["SEED-SSD-02",1],["SEED-HDD-02",1],["SEED-GPU-02",1],["SEED-PSU-03",1],["SEED-CASE-02",1],["SEED-FAN-02",2],["SEED-ACOOL-02",1]],
  },
  {
    id:"modelo-blender",titulo:"Modelagem e Blender",objetivo:"renderizacao",objetivoRotulo:"Modelagem e renderização",plataforma:"AM5",nivel:"Avançada",
    descricao:"Ryzen 9, RTX 3060 de 12 GB e 64 GB de RAM para projetos 3D. Confira o consumo de memória de cada cena.",
    pecas:[["SEED-CPU-05",1],["SEED-MB-08",1],["SEED-RAM-05",2],["SEED-SSD-04",1],["SEED-GPU-02",1],["SEED-PSU-03",1],["SEED-CASE-02",1],["SEED-FAN-02",2],["SEED-ACOOL-02",1]],
  },
  {
    id:"modelo-multitarefa",titulo:"Multitarefa e máquinas virtuais",objetivo:"trabalho",objetivoRotulo:"Trabalho e produtividade",plataforma:"LGA1700",nivel:"Avançada",
    descricao:"Core i7, 64 GB de RAM e SSD de 1 TB para ambientes de desenvolvimento e virtualização. Usa vídeo integrado.",
    pecas:[["SEED-CPU-09",1],["SEED-MB-09",1],["SEED-RAM-05",2],["SEED-SSD-04",1],["SEED-PSU-03",1],["SEED-CASE-02",1],["SEED-FAN-02",2],["SEED-ACOOL-04",1]],
  },
];

export function modelosProntos(catalogo,{referencias = catalogo} = {}) {
  return MODELOS.map(modelo => {
    const componentes = {}, pendentes = [];
    for (const [referencia,quantidade] of modelo.pecas) {
      const original = referencias.find(p => p.id === referencia || p.part_number === referencia);
      const peca = catalogo.find(p => p.id === referencia || p.part_number === referencia) ||
        (original && catalogo.find(p => p.categoria === original.categoria && p.fabricante === original.fabricante && p.modelo === original.modelo));
      if (!peca) { pendentes.push(original ? original.fabricante + " " + original.modelo : referencia); continue; }
      if (peca.esgotado) pendentes.push(peca.fabricante + " " + peca.modelo + " (indisponível)");
      if (!Number.isFinite(peca.preco) || peca.preco <= 0) pendentes.push(peca.fabricante + " " + peca.modelo + " (sem preço válido)");
      const item = {id:peca.id,quantidade};
      if (categoriasMultiplas.has(peca.categoria)) (componentes[peca.categoria] ??= []).push(item);
      else componentes[peca.categoria] = item;
    }
    return {
      ...normalizarBuild({id:modelo.id,titulo:modelo.titulo,descricao:modelo.descricao,componentes,incluirPerifericos:false}),
      objetivo:modelo.objetivo,
      metadados:{versao:2,origem:"Curadoria BOOSTio",plataforma:modelo.plataforma,
        objetivoRotulo:modelo.objetivoRotulo,nivel:modelo.nivel,pendentes},
    };
  });
}

export function copiarModelo(build) {
  return normalizarBuild({
    ...build, id:crypto.randomUUID(), criadoEm:new Date().toISOString(),
    visibilidade:"privado", travada:false,incluirPerifericos:false,
  });
}
