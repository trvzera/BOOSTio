// Organiza a apresentação; não altera o diagnóstico nem aprova dados ausentes.
const assuntos = [
  ["processador", "Processador e placa-mãe", "Confira o suporte ao processador e a versão de BIOS necessária."],
  ["memoria", "Memória RAM", "Confira slots, capacidade e suporte aos pentes escolhidos."],
  ["video", "Placa de vídeo", "Confira o espaço para a placa e para os cabos dentro do gabinete."],
  ["ventilacao", "Fans e refrigeração", "Confira posições, tamanhos e espaço para fans, cooler e radiador."],
  ["fonte", "Fonte e alimentação", "Confira o espaço da fonte e os conectores necessários."],
  ["discos", "Armazenamento", "Confira conexões, baias e espaços disponíveis para os discos."],
  ["gabinete", "Gabinete", "Confira os limites de instalação do modelo escolhido."],
  ["rede", "Conexão de rede", "Confira as conexões disponíveis para o acesso à internet."],
  ["outros", "Outras informações", "Confira os dados que ainda não foram informados."],
];
const texto = valor => typeof valor === "string" ? valor.trim() : "";
const chave = valor => texto(valor).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
  .replace(/^conflito confirmado:\s*/, "").replace(/[^a-z0-9]+/g, " ").trim();
const unicos = valores => [...new Map(valores.filter(v => texto(v)).map(v => [chave(v), texto(v)])).values()];
const equivalentesLocais = [
  [/^Faltam medidas para confirmar o encaixe da placa de vídeo/, ["placa_video-medida"]],
  [/^Faltam medidas para confirmar o encaixe da altura da placa de vídeo/, ["gpu-altura"]],
  [/^Faltam medidas para confirmar o encaixe da espessura da placa de vídeo/, ["gpu-espessura"]],
  [/^Faltam medidas para confirmar o encaixe do air cooler/, ["air_cooler-medida"]],
  [/^Faltam medidas para confirmar o encaixe da fonte/, ["fonte-medida"]],
  [/^Faltam os formatos de fonte/, ["fonte-formato"]],
  [/^Falta o tamanho dos encaixes de fans/, ["fans-tamanho"]],
  [/^Falta a capacidade de fans/, ["fans-quantidade"]],
  [/^Confirme a distribuição das fans/, ["fans-posicoes"]],
  [/^Confirme as folgas da GPU/, ["gpu-interferencias"]],
];

function assunto(codigo, mensagem) {
  if (/^(socket$|suporte-cpu)/.test(codigo)) return "processador";
  if (/^ram-/.test(codigo)) return "memoria";
  if (/^(placa_video|gpu)-/.test(codigo)) return "video";
  if (/^(fans?|radiador|air_cooler|water_cooler|cooler)-/.test(codigo)) return "ventilacao";
  if (/^fonte-/.test(codigo)) return "fonte";
  if (/^(armazenamento|baias|m2|sata)/.test(codigo)) return "discos";
  const t = chave(mensagem);
  if (/\b(bios|suporte ao modelo da cpu)\b/.test(t)) return "processador";
  if (/\b(fan|fans|ventoinha|ventoinhas|cooler|radiador|radiadores)\b/.test(t)) return "ventilacao";
  if (/\b(ram|ddr|pentes|memoria|memorias|xmp|expo|qvl)\b/.test(t)) return "memoria";
  if (/\b(gpu|placa de video)\b/.test(t)) return "video";
  if (/\b(fonte|alimentacao|eps)\b/.test(t)) return "fonte";
  if (/\b(ssd|hd|sata|m 2|armazenamento|baias|discos)\b/.test(t)) return "discos";
  if (/\b(wifi|wi fi|roteador|ethernet|rede)\b/.test(t)) return "rede";
  if (/\b(socket|processador|cpu)\b/.test(t)) return "processador";
  if (/\b(gabinete)\b/.test(t)) return "gabinete";
  return "outros";
}
function agrupar(entradas) {
  return assuntos.map(([id, titulo, resumo]) => {
    const itens = entradas.filter(v => assunto(v.codigo || "", v.mensagem) === id);
    return {id, titulo, resumo, mensagens: unicos(itens.map(v => v.mensagem))};
  }).filter(v => v.mensagens.length);
}

export function resumirCompatibilidade(resultado) {
  const diagnostico = resultado.compatibilidade || {};
  const errosServidor = Array.isArray(diagnostico.erros) ? diagnostico.erros : [];
  // O servidor repete a descrição da mesma regra com um título adicional.
  const erros = unicos([...(resultado.erros || []), ...errosServidor.map(v => v.mensagem)]);
  const conflitos = erros.filter((mensagem, i) => !erros.some((outra, j) => i !== j
    && chave(outra).length > chave(mensagem).length && chave(outra).endsWith(chave(mensagem))));
  const desconhecidas = Array.isArray(diagnostico.naoVerificado) ? diagnostico.naoVerificado : [];
  const pendentes = desconhecidas.filter(v => texto(v?.mensagem)).map(v => ({codigo: v.codigo, mensagem: v.mensagem}));
  const codigos = new Set(pendentes.map(v => v.codigo));
  const dicas = [];
  for (const mensagem of unicos(resultado.dicas || [])) {
    if (equivalentesLocais.some(([padrao, regras]) => padrao.test(mensagem) && regras.some(c => codigos.has(c)))) continue;
    // Dúvidas locais sobre medidas não precisam reaparecer em uma segunda lista.
    const faltaDado = /^(faltam?\b|slots .*não informados|este cooler tem versões|confirme no fabricante|confirme quais slots|confirme se o ssd|há discos sem|selecione a placa-mãe)/i.test(mensagem);
    (faltaDado ? pendentes : dicas).push(faltaDado ? {mensagem} : mensagem);
  }
  const grupos = agrupar(pendentes);
  // Uma orientação sobre o mesmo assunto fica junto da conferência técnica.
  const orientacoes = [];
  for (const mensagem of dicas) {
    const grupo = grupos.find(g => g.id === assunto("", mensagem));
    if (grupo) grupo.mensagens = unicos([...grupo.mensagens, mensagem]);
    else orientacoes.push(mensagem);
  }
  // Um aviso sério não é rebaixado a conferência recolhida por coincidência de texto.
  const conhecidos = new Set(conflitos.map(chave));
  return {erros: conflitos, faltam: unicos(resultado.faltam || []),
    avisos: unicos(resultado.avisos || []).filter(v => !conhecidos.has(chave(v))),
    grupos, dicas: unicos(orientacoes), verificacoes: desconhecidas.length};
}
