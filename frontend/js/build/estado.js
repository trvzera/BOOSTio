import { categorias, perifericos } from "./catalogo.js";

const CHAVE_RASCUNHOS = "boostio:rascunhos-build";
export const CHAVE_PERFIL_LOCAL = "boostio:builds-locais";
const categoriasValidas = new Set(categorias.map(c => c.id));
function ler(chave,padrao) {
  try { return JSON.parse(localStorage.getItem(chave)) || padrao; } catch { return padrao; }
}
export function buildsLocais() { const valor = ler(CHAVE_PERFIL_LOCAL,[]); return Array.isArray(valor) ? valor : []; }
export function itensRam(build) {
  const ram = build.componentes.memoria_ram;
  return Array.isArray(ram) ? ram : ram ? [ram] : [];
}
export function itensSelecionados(build,catalogo) {
  return Object.entries(build.componentes).flatMap(([categoria,valor]) =>
    (categoria === "memoria_ram" ? itensRam(build) : [valor]).map(item => ({
      categoria,item,peca:catalogo.find(p => p.id === item.id && p.categoria === categoria),
    })));
}
export function normalizarBuild(valor = {}) {
  const componentes = {};
  function itemValido(item,categoria) {
    if (!item || typeof item !== "object") return null;
    if (typeof item.id !== "string" && typeof item.proprio !== "string") return null;
    const id = typeof item.id === "string" ? item.id.slice(0,120) : "";
    const proprio = typeof item.proprio === "string" ? item.proprio.slice(0,120) : "";
    if (!id && !proprio) return null;
    return { ...(id ? {id} : {proprio}), quantidade:categoria === "memoria_ram"
      ? Math.min(64,Math.max(1,Math.trunc(Number(item.quantidade) || 1))) : 1 };
  }
  for (const [categoria,valorItem] of Object.entries(valor.componentes || {})) {
    if (!categoriasValidas.has(categoria)) continue;
    if (categoria === "memoria_ram") {
      const itens = (Array.isArray(valorItem) ? valorItem : [valorItem]).slice(0,64)
        .map(item => itemValido(item,categoria)).filter(Boolean);
      const agrupados = [];
      itens.forEach(item => {
        const existente = agrupados.find(r => item.id ? r.id === item.id : r.proprio === item.proprio);
        if (existente) existente.quantidade = Math.min(64,existente.quantidade + item.quantidade);
        else agrupados.push(item);
      });
      if (agrupados.length) componentes[categoria] = agrupados;
    } else { const item = itemValido(valorItem,categoria); if (item) componentes[categoria] = item; }
  }
  const data = new Date(valor.criadoEm || Date.now());
  return {
    id:String(valor.id || crypto.randomUUID()).slice(0,100),
    titulo:String(valor.titulo || "Minha build").slice(0,100),
    descricao:String(valor.descricao || "").slice(0,300),
    criadoEm:Number.isFinite(data.getTime()) ? data.toISOString() : new Date().toISOString(),
    visibilidade:valor.visibilidade === "publico" ? "publico" : "privado",
    travada:Boolean(valor.travada),
    incluirPerifericos:typeof valor.incluirPerifericos === "boolean" ? valor.incluirPerifericos : perifericos.some(cat => componentes[cat]),
    componentes,
  };
}
export function abrirBuild(parametros = new URLSearchParams(location.search)) {
  const compartilhada = parametros.get("compartilhar");
  if (compartilhada) {
    try {
      return normalizarBuild({...JSON.parse(decodeURIComponent(escape(atob(compartilhada)))),
        id:crypto.randomUUID(),travada:false});
    } catch { throw new Error("O link da build é inválido ou está incompleto."); }
  }
  const id = parametros.get("id"), rascunhos = ler(CHAVE_RASCUNHOS,{});
  const resumo = buildsLocais().find(b => b.id === id), existente = rascunhos[id] || resumo;
  if (existente) return normalizarBuild({...resumo,...existente});
  if (id === "build-demo-1") return normalizarBuild({
    id,titulo:"Setup Gamer 1440p",visibilidade:"publico",componentes:{
      processador:{id:"SEED-CPU-02",quantidade:1},placa_mae:{id:"SEED-MB-03",quantidade:1},
      memoria_ram:[{id:"SEED-RAM-01",quantidade:1}],placa_video:{id:"SEED-GPU-01",quantidade:1},
      ssd:{id:"SEED-SSD-01",quantidade:1},fonte:{id:"SEED-PSU-01",quantidade:1},
    },
  });
  const nova = normalizarBuild({id:id || undefined});
  if (!id) {
    const mapa = {processador:"processador","placa-mae":"placa_mae","placa-video":"placa_video",
      memoria:"memoria_ram",ssd:"ssd",hd:"hd",fonte:"fonte",gabinete:"gabinete",cooler:"air_cooler",
      fans:"fan",monitor:"monitor",teclado:"teclado",mouse:"mouse",headset:"fone"};
    try {
      const formulario = JSON.parse(sessionStorage.getItem("boostio:respostas-formulario") || "{}");
      for (const [chave,modelo] of Object.entries(formulario.pecasDetalhes || {})) {
        if (mapa[chave] && typeof modelo === "string" && modelo.trim())
          nova.componentes[mapa[chave]] = {proprio:modelo.trim(),quantidade:1};
      }
      sessionStorage.removeItem("boostio:respostas-formulario");
    } catch { /* Funciona também sem o formulário. */ }
  }
  return normalizarBuild(nova);
}
export function guardarRascunho(build) {
  const rascunhos = ler(CHAVE_RASCUNHOS,{});
  rascunhos[build.id] = build;
  localStorage.setItem(CHAVE_RASCUNHOS,JSON.stringify(rascunhos));
}
export function sincronizarRascunho(build,detalhes = {}) {
  const existente = ler(CHAVE_RASCUNHOS,{})[build.id];
  if (!existente || Object.keys(detalhes).length) guardarRascunho({...(existente || build),...detalhes});
}
export function salvarNoPerfilLocal(build) {
  const salvas = buildsLocais(), index = salvas.findIndex(b => b.id === build.id);
  if (index < 0 && salvas.length >= 3) throw new Error("Limite de três builds salvas neste navegador.");
  const pecas = {
    cpu:Boolean(build.componentes.processador),placaMae:Boolean(build.componentes.placa_mae),
    ram:itensRam(build).length > 0,armazenamento:Boolean(build.componentes.ssd || build.componentes.hd),
    gpu:Boolean(build.componentes.placa_video),fonte:Boolean(build.componentes.fonte),
    gabinete:Boolean(build.componentes.gabinete),fans:Boolean(build.componentes.fan),
    cooler:Boolean(build.componentes.air_cooler || build.componentes.water_cooler),
  };
  const resumo = {...build,pecas};
  if (index >= 0) salvas[index] = resumo; else salvas.push(resumo);
  guardarRascunho(build); localStorage.setItem(CHAVE_PERFIL_LOCAL,JSON.stringify(salvas));
}
export function informacoesRam(build,catalogo) {
  const placa = catalogo.find(p => p.id === build.componentes.placa_mae?.id);
  const itens = itensRam(build).map(item => ({item,peca:catalogo.find(p => p.id === item.id)}));
  return {
    slots:Number(placa?.quantidade_slots_ram || 0),
    usados:itens.reduce((n,{item,peca}) => n + Number(peca?.quantidade_pentes || 1) * item.quantidade,0),
    capacidade:itens.reduce((n,{item,peca}) => n + Number(peca?.capacidade_gb || 0) * item.quantidade,0),
    itens,placa,
  };
}
export function limiteRam(build,catalogo,id = itensRam(build)[0]?.id) {
  const ram = catalogo.find(p => p.id === id), info = informacoesRam(build,catalogo);
  if (!info.placa || !ram || !info.slots) return 0;
  const outros = info.itens.filter(r => r.item.id !== id)
    .reduce((n,{item,peca}) => n + Number(peca?.quantidade_pentes || 1) * item.quantidade,0);
  return Math.max(0,Math.floor((info.slots - outros) / Math.max(1,Number(ram.quantidade_pentes) || 1)));
}
export function motivoSelecao(build,peca,catalogo) {
  if (build.travada) return "Destranque a build para alterar os componentes.";
  if (!peca || peca.esgotado) return "Esta peça está indisponível.";
  if (peca.categoria !== "memoria_ram") {
    if (build.componentes[peca.categoria]) return "Remova a peça atual antes de adicionar outra nesta categoria.";
    if (["air_cooler","water_cooler"].includes(peca.categoria) &&
        (build.componentes.air_cooler || build.componentes.water_cooler))
      return "Remova o cooler atual antes de escolher outro.";
    return "";
  }
  const info = informacoesRam(build,catalogo), existentes = info.itens.filter(r => r.peca);
  const referencia = existentes[0]?.peca;
  if (referencia && (referencia.ddr !== peca.ddr || Number(referencia.frequencia_mhz) !== Number(peca.frequencia_mhz)))
    return "A nova RAM precisa ter o mesmo padrão DDR e a mesma frequência das memórias adicionadas.";
  if (info.itens.length && !info.placa) return "Selecione a placa-mãe para adicionar mais memória RAM.";
  const quantidade = (itensRam(build).find(r => r.id === peca.id)?.quantidade || 0) + 1;
  if (info.placa && quantidade > limiteRam(build,catalogo,peca.id))
    return "Os módulos de RAM excedem os slots da placa-mãe.";
  if (info.placa?.memoria_maxima_gb &&
      info.capacidade + Number(peca.capacidade_gb) > Number(info.placa.memoria_maxima_gb))
    return "A capacidade de RAM supera o máximo da placa-mãe.";
  return "";
}
export function selecionarPeca(build,peca,catalogo) {
  const motivo = motivoSelecao(build,peca,catalogo);
  if (motivo) throw new Error(motivo);
  const proxima = normalizarBuild(structuredClone(build));
  if (peca.categoria === "memoria_ram") {
    const itens = itensRam(proxima), existente = itens.find(r => r.id === peca.id);
    if (existente) existente.quantidade++;
    else itens.push({id:peca.id,quantidade:1});
    proxima.componentes.memoria_ram = itens;
  } else proxima.componentes[peca.categoria] = {id:peca.id,quantidade:1};
  const info = informacoesRam(proxima,catalogo);
  if (info.placa && info.usados > info.slots) throw new Error("Os módulos de RAM excedem os slots desta placa-mãe.");
  if (perifericos.includes(peca.categoria)) proxima.incluirPerifericos = true;
  return proxima;
}
export function removerPeca(build,categoria,id) {
  if (build.travada) throw new Error("Destranque a build para remover componentes.");
  const proxima = normalizarBuild(structuredClone(build));
  if (categoria === "memoria_ram") {
    const itens = itensRam(proxima).filter(r => (r.id || r.proprio) !== id);
    if (itens.length) proxima.componentes.memoria_ram = itens; else delete proxima.componentes.memoria_ram;
  } else delete proxima.componentes[categoria];
  return proxima;
}
export function reduzirRam(build,id) {
  if (build.travada) throw new Error("Destranque a build para alterar componentes.");
  const proxima = normalizarBuild(structuredClone(build)), item = itensRam(proxima).find(r => r.id === id);
  if (item?.quantidade > 1) item.quantidade--;
  return proxima;
}
export function linkCompartilhado(build) {
  if (build.visibilidade !== "publico") throw new Error("Torne a build pública antes de compartilhar.");
  const url = new URL("./configuracao-build.html",location.href); url.search = "";
  const dados = {titulo:build.titulo,visibilidade:"publico",componentes:build.componentes,incluirPerifericos:build.incluirPerifericos};
  url.searchParams.set("compartilhar",btoa(unescape(encodeURIComponent(JSON.stringify(dados)))));
  return url.href;
}
